"""Primeiro acesso por convite: banco descartável, sem tocar contas reais."""
from contextlib import closing
import os
import unittest
from uuid import uuid4

from werkzeug.security import check_password_hash,generate_password_hash

from simpa import db
from simpa.app import criar_app
from simpa.cadastro_contas import gerar_convite
from scripts.preparar_banco import preparar
from simpa.repositorio import RepositorioAcademico


@unittest.skipUnless(os.getenv('SIMPA_TEST_DSN'),'Configure banco descartável')
class CadastroContas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):preparar()

    def setUp(self):
        self.app=criar_app({'TESTING':True,'SECRET_KEY':'cadastro-isolado'})
        self.c=self.app.test_client()
        chave=uuid4().hex[:16]
        self.matricula='CAD-'+chave;self.email=chave+'@exemplo.edu.br'
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            cur.execute("INSERT INTO simpa.usuarios(nome,matricula,senha_hash,perfil) VALUES ('Professor cadastro',%s,%s,'professor') RETURNING id",('PC-'+chave,generate_password_hash('senha-teste')))
            self.prof=cur.fetchone()['id']
            cur.execute("INSERT INTO simpa.alunos(matricula,nome_completo,email_institucional) VALUES (%s,'Aluno do cadastro',%s) RETURNING id",(self.matricula,self.email))
            self.aluno=cur.fetchone()['id']
            cur.execute("SELECT id FROM simpa.disciplinas WHERE codigo='IA-ALG'");disc=cur.fetchone()['id']
            cur.execute("INSERT INTO simpa.turmas(identificador,nome,ano_letivo,semestre) VALUES (%s,'Cadastro teste',2026,2) RETURNING id",('C-'+chave,));turma=cur.fetchone()['id']
            cur.execute('INSERT INTO simpa.turma_disciplinas(turma_id,disciplina_id) VALUES (%s,%s)',(turma,disc))
            cur.execute('INSERT INTO simpa.professor_disciplinas VALUES (%s,%s,%s)',(self.prof,turma,disc))
            cur.execute('INSERT INTO simpa.matriculas(aluno_id,turma_id) VALUES (%s,%s)',(self.aluno,turma))
        self.repo=RepositorioAcademico({'id':self.prof,'perfil':'professor'})
        self.codigo=gerar_convite(self.repo,self.aluno)
        self.c.get('/cadastrar-se')
        with self.c.session_transaction() as s:self.csrf=s['csrf']

    def dados(self,**outros):
        return {'csrf_token':self.csrf,'matricula':self.matricula,'email':self.email,
                'codigo':self.codigo,'senha':'senha-aluno-teste','confirmacao':'senha-aluno-teste',**outros}

    def post(self,**outros):return self.c.post('/cadastrar-se',data=self.dados(**outros))

    def test_cadastro_vincula_aluno_hash_e_login(self):
        r=self.post(perfil='professor',aluno_id=self.aluno+1)
        self.assertEqual(r.status_code,302)
        usuario=db.buscar_usuario(self.matricula)
        self.assertEqual(usuario['perfil'],'aluno');self.assertEqual(usuario['aluno_id'],self.aluno)
        self.assertTrue(check_password_hash(usuario['senha_hash'],'senha-aluno-teste'))
        self.assertNotEqual(usuario['senha_hash'],'senha-aluno-teste')
        self.assertEqual(self.c.post('/login',data={'csrf_token':self.csrf,'identificador':self.email,'password':'senha-aluno-teste'}).status_code,302)
        self.assertEqual(self.c.get('/minhas-notas').status_code,200)
        self.assertEqual(self.c.get('/avaliacoes').status_code,403)
        with self.c.session_transaction() as s:token_login=s['csrf']
        self.assertEqual(self.c.post(f'/alunos/{self.aluno}/convite',data={'csrf_token':token_login}).status_code,403)

    def test_sem_convite_nao_basta_matricula_e_email(self):
        for mudanca in [{'codigo':''},{'codigo':'x'*24},{'email':'outro@exemplo.edu.br'},{'matricula':"' OR 1=1 --"}]:
            with self.subTest(mudanca=mudanca):self.assertEqual(self.post(**mudanca).status_code,422)
        self.assertIsNone(db.buscar_usuario(self.matricula))

    def test_validacao_e_senhas_nao_retornam_no_html(self):
        for mudanca in [{'senha':'curta'},{'confirmacao':'outra-senha'},{'senha':'x'*129},{'email':'invalido'}]:
            r=self.post(**mudanca)
            self.assertEqual(r.status_code,422)
            self.assertNotIn(b'value="senha-aluno-teste"',r.data)
            self.assertNotIn(self.codigo.encode(),r.data)
        self.assertEqual(self.post().status_code,302)

    def test_expirado_e_reutilizado_nao_cadastram(self):
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            cur.execute("UPDATE simpa.convites_cadastro SET expira_em=CURRENT_TIMESTAMP-INTERVAL '1 minute' WHERE aluno_id=%s",(self.aluno,))
        self.assertEqual(self.post().status_code,422)
        self.codigo=gerar_convite(self.repo,self.aluno)
        self.assertEqual(self.post().status_code,302)
        self.assertEqual(self.post().status_code,422)

    def test_novo_codigo_invalida_anterior_e_hash_no_banco(self):
        antigo=self.codigo;self.codigo=gerar_convite(self.repo,self.aluno)
        self.assertEqual(self.post(codigo=antigo).status_code,422)
        with closing(db.conectar()) as con,con.cursor() as cur:
            cur.execute('SELECT codigo_hash FROM simpa.convites_cadastro WHERE aluno_id=%s',(self.aluno,))
            self.assertNotEqual(cur.fetchone()['codigo_hash'],self.codigo)
        self.assertEqual(self.post().status_code,302)

    def test_cadastro_csrf_e_convite_restrito_ao_professor_da_turma(self):
        self.assertEqual(self.post(csrf_token='').status_code,400)
        pagina=self.c.get('/cadastrar-se')
        self.assertEqual(pagina.status_code,200)
        self.assertEqual(pagina.headers['Cache-Control'],'no-store')
        url=f'/alunos/{self.aluno}/convite'
        self.assertEqual(self.c.post(url,data={'csrf_token':self.csrf}).status_code,302)
        with self.c.session_transaction() as s:s['usuario_id']=self.prof
        self.assertEqual(self.c.post(url,data={}).status_code,400)
        r=self.c.post(url,data={'csrf_token':self.csrf})
        self.assertEqual(r.status_code,200);self.assertIn(b'48 horas',r.data)
        self.assertEqual(r.headers['Cache-Control'],'no-store')
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            cur.execute("INSERT INTO simpa.alunos(matricula,nome_completo) VALUES (%s,'Outro aluno') RETURNING id",('OUT-'+uuid4().hex[:16],))
            outro=cur.fetchone()['id']
        self.assertEqual(self.c.post(f'/alunos/{outro}/convite',data={'csrf_token':self.csrf}).status_code,403)

    def test_duplicidade_nao_altera_senha_nem_cria_segunda_conta(self):
        self.assertEqual(self.post().status_code,302)
        self.assertEqual(self.post(senha='outra-senha-teste',confirmacao='outra-senha-teste').status_code,422)
        self.assertTrue(check_password_hash(db.buscar_usuario(self.matricula)['senha_hash'],'senha-aluno-teste'))
        with self.c.session_transaction() as s:s['usuario_id']=self.prof
        self.assertEqual(self.c.post(f'/alunos/{self.aluno}/convite',data={'csrf_token':self.csrf}).status_code,422)
