"""Somente em banco descartável configurado em SIMPA_TEST_DSN."""
import io
import os
import unittest
from uuid import uuid4
from werkzeug.security import generate_password_hash

import db
from app import criar_app
from preparar_banco import preparar,carregar_demonstracao
from repositorio import RepositorioAcademico


@unittest.skipUnless(os.getenv('SIMPA_TEST_DSN'),'Configure um banco isolado de teste')
class IntegracaoPerfis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        preparar();preparar();carregar_demonstracao()
        cls.admin=RepositorioAcademico()
        with cls.admin.transacao() as c:
            for mat in ['TEST-P1','TEST-P2']:
                c.execute('''INSERT INTO simpa.usuarios(nome,matricula,senha_hash,perfil)
                    VALUES (%s,%s,%s,'professor') ON CONFLICT(matricula) DO NOTHING''',
                    (mat,mat,generate_password_hash('senha-teste-2026')))
            c.execute("SELECT id FROM simpa.usuarios WHERE matricula='TEST-P1'");cls.p1=c.fetchone()['id']
            c.execute("SELECT id FROM simpa.usuarios WHERE matricula='TEST-P2'");cls.p2=c.fetchone()['id']
            c.execute("SELECT id FROM simpa.disciplinas WHERE codigo='IA-ALG'");cls.d1=c.fetchone()['id']
            c.execute("SELECT id FROM simpa.disciplinas WHERE codigo='IA-DOO'");cls.d2=c.fetchone()['id']
            c.execute("SELECT id FROM simpa.alunos WHERE matricula LIKE 'IADEMO-%%' ORDER BY id LIMIT 2")
            cls.a1,cls.a2=[r['id'] for r in c.fetchall()]
            for aid,mat in [(cls.a1,'TEST-A1'),(cls.a2,'TEST-A2')]:
                c.execute('''INSERT INTO simpa.usuarios(nome,matricula,senha_hash,perfil,aluno_id)
                    VALUES (%s,%s,%s,'aluno',%s) ON CONFLICT(matricula) DO NOTHING''',
                    (mat,mat,generate_password_hash('senha-teste-2026'),aid))
            c.execute("SELECT id FROM simpa.usuarios WHERE matricula='TEST-A1'");cls.u1=c.fetchone()['id']
            c.execute("SELECT id FROM simpa.usuarios WHERE matricula='TEST-A2'");cls.u2=c.fetchone()['id']

    def setUp(self):
        self.app=criar_app({'TESTING':True,'SECRET_KEY':'teste-isolado'})
        self.c=self.app.test_client();self.h={'X-CSRF-Token':'teste-csrf'}
        with self.admin.transacao() as c:
            c.execute("INSERT INTO simpa.turmas(identificador,nome,ano_letivo,semestre) VALUES (%s,'Turma teste',2026,2) RETURNING id",('T-'+uuid4().hex[:10],))
            self.t=c.fetchone()['id']
            for d,p in [(self.d1,self.p1),(self.d2,self.p2)]:
                c.execute('INSERT INTO simpa.turma_disciplinas VALUES (%s,%s)',(self.t,d))
                c.execute('INSERT INTO simpa.professor_disciplinas VALUES (%s,%s,%s)',(p,self.t,d))
                for va in (1,2,3):
                    c.execute('INSERT INTO simpa.regras_va(turma_id,disciplina_id,va) VALUES (%s,%s,%s)',(self.t,d,va))
                    for tipo,maximo in [('A360',10),('VRAU',30),('AFE',30)]:
                        c.execute('''INSERT INTO simpa.atividades_va(turma_id,disciplina_id,va,tipo,titulo,maximo)
                            VALUES (%s,%s,%s,%s,%s,%s)''',(self.t,d,va,tipo,tipo,maximo))
            for aid in [self.a1,self.a2]:c.execute('INSERT INTO simpa.matriculas(aluno_id,turma_id) VALUES (%s,%s)',(aid,self.t))

    def entrar(self,uid):
        with self.c.session_transaction() as s:s.clear();s['usuario_id']=uid;s['csrf']='teste-csrf'

    def post(self,url,dados):return self.c.post(url,json=dados,headers=self.h)
    def criar(self,d=None,tipo='APS',titulo=None):
        return self.post('/api/atividades',{'turma_id':self.t,'disciplina_id':d or self.d1,'va':2,'tipo':tipo,'titulo':titulo or uuid4().hex})

    def test_login_e_sessao_invalidada(self):
        self.assertEqual(self.c.get('/api/dados').status_code,401)
        self.c.get('/login')
        with self.c.session_transaction() as s:token=s['csrf']
        r=self.c.post('/login',data={'csrf_token':token,'identificador':'TEST-P1','password':'senha-teste-2026'})
        self.assertEqual(r.status_code,302)
        self.assertEqual(self.c.get('/api/dados').status_code,200)
        self.entrar(self.u1)
        with self.c.session_transaction() as s:s['perfil']='professor'
        self.assertEqual(self.c.get('/alunos').status_code,403)

    def test_aluno_le_somente_seus_dados(self):
        self.entrar(self.u1)
        dados=self.c.get('/api/dados').get_json()
        self.assertEqual({a['id'] for a in dados['alunos']},{self.a1})
        self.assertTrue(all(n['aluno_id']==self.a1 for n in dados['notas_componentes']))
        self.assertEqual(self.c.get(f'/alunos/{self.a2}').status_code,403)
        for url in ['/alunos','/alunos/novo','/turmas','/disciplinas','/avaliacoes','/importacao','/api/alunos','/api/docs']:
            with self.subTest(url=url):self.assertEqual(self.c.get(url).status_code,403)
        a=self.c.get('/api/meu-boletim').get_json()
        self.assertEqual({r['aluno_id'] for r in a['resultados']},{self.a1})
        self.assertIsNone(a['criterio_aprovacao'])

    def test_aluno_nao_lanca_nota_nem_cria_atividade(self):
        self.entrar(self.p1);atividade=self.criar().json['id']
        self.entrar(self.u1)
        self.assertEqual(self.criar().status_code,403)
        self.assertEqual(self.post(f'/api/atividades/{atividade}/notas',{'notas':[{'aluno_id':self.a1,'nota':2}]}).status_code,403)
        self.assertEqual(self.post('/api/vas/encerrar',{'turma_id':self.t,'disciplina_id':self.d1,'va':2}).status_code,403)

    def test_consulta_de_notas_da_atividade_nao_expoe_colega(self):
        self.entrar(self.p1);atividade=self.criar().json['id']
        self.post(f'/api/atividades/{atividade}/notas',{'notas':[{'aluno_id':self.a1,'nota':1},{'aluno_id':self.a2,'nota':2}]})
        self.entrar(self.u1)
        dados=self.c.get(f'/api/atividades/{atividade}/notas').get_json()
        self.assertEqual({n['aluno_id'] for n in dados['notas']},{self.a1})

    def test_composicao_nao_corta_nota_ja_lancada(self):
        self.entrar(self.p1)
        base=self.c.get(f'/api/dados?turma_id={self.t}').get_json()
        atividade=next(a for a in base['atividades'] if a['tipo']=='VRAU' and a['va']==2)
        self.post(f"/api/atividades/{atividade['id']}/notas",{'notas':[{'aluno_id':self.a1,'nota':29}]})
        dados={'turma_id':self.t,'disciplina_id':self.d1,'va':2,'max_atividades':30,'max_a360':10,
               'max_vrau':20,'max_afe':40,'max_aps':2,'max_daily':3}
        self.assertEqual(self.post('/api/vas/composicao',dados).status_code,422)
        atual=self.c.get(f"/api/atividades/{atividade['id']}/notas").get_json()
        self.assertEqual(atual['atividade']['maximo'],30)
        self.assertEqual(atual['notas'][0]['nota'],29)

    def test_conta_inativada_perde_sessao(self):
        self.entrar(self.u1)
        with self.admin.transacao() as c:c.execute('UPDATE simpa.usuarios SET ativo=FALSE WHERE id=%s',(self.u1,))
        try:self.assertEqual(self.c.get('/api/dados').status_code,401)
        finally:
            with self.admin.transacao() as c:c.execute('UPDATE simpa.usuarios SET ativo=TRUE WHERE id=%s',(self.u1,))

    def test_professor_nao_acessa_disciplina_de_outro(self):
        self.entrar(self.p2);atividade=self.criar(self.d2).json['id']
        self.entrar(self.p1)
        self.assertEqual(self.criar(self.d2).status_code,403)
        self.assertEqual(self.c.get(f'/api/atividades/{atividade}/notas').status_code,403)
        self.assertEqual(self.post(f'/api/atividades/{atividade}/notas',{'notas':[{'aluno_id':self.a1,'nota':1}]}).status_code,403)
        self.assertEqual(self.c.get(f'/api/analises?turma_id={self.t}&disciplina_id={self.d2}').status_code,403)
        dados=self.c.get(f'/api/dados?turma_id={self.t}').get_json()
        self.assertEqual({d['id'] for d in dados['disciplinas']},{self.d1})

    def test_nota_zero_pendencia_e_limite(self):
        self.entrar(self.p1);atividade=self.criar().json['id']
        url=f'/api/atividades/{atividade}/notas'
        self.assertEqual(self.post(url,{'notas':[{'aluno_id':self.a1,'nota':0},{'aluno_id':self.a2,'nota':None}]}).status_code,200)
        self.assertEqual(self.post(url,{'notas':[{'aluno_id':self.a1,'nota':2.1}]}).status_code,422)
        a=self.c.get(f'/api/analises?turma_id={self.t}&va=2').get_json()
        rs={r['id']:r for r in a['resumos']}
        self.assertEqual(rs[self.a1]['media'],0);self.assertIsNone(rs[self.a2]['media'])
        self.assertIsNone(a['resultados'][0]['media_final'])

    def test_aps_daily_cap_30_sem_quantidade_fixa(self):
        self.entrar(self.p1)
        # Quinze APS de dois pontos também preenchem o bloco: não se fixam seis encontros.
        for i in range(15):self.assertEqual(self.criar(titulo=f'APS {i}').status_code,201)
        self.assertEqual(self.criar(titulo='APS excedente').status_code,422)

    def test_encerramento_exige_planejamento_e_todas_as_notas(self):
        self.entrar(self.p1);dados={'turma_id':self.t,'disciplina_id':self.d1,'va':2}
        self.assertEqual(self.post('/api/vas/encerrar',dados).status_code,422)
        for i in range(6):self.criar(titulo=f'APS {i}');self.criar(tipo='DAILY',titulo=f'Daily {i}')
        self.assertEqual(self.post('/api/vas/encerrar',dados).status_code,422)
        base=self.c.get(f'/api/dados?turma_id={self.t}').get_json()
        atividades=[a for a in base['atividades'] if a['va']==2]
        for a in atividades:
            self.assertEqual(self.post(f"/api/atividades/{a['id']}/notas",{'notas':[{'aluno_id':aid,'nota':a['maximo']} for aid in [self.a1,self.a2]]}).status_code,200)
        self.assertEqual(self.post('/api/vas/encerrar',dados).status_code,200)
        aid=atividades[0]['id']
        self.assertEqual(self.post(f'/api/atividades/{aid}/notas',{'notas':[{'aluno_id':self.a1,'nota':0}]}).status_code,422)
        self.assertEqual(self.post('/api/vas/encerrar',{**dados,'acao':'reabrir'}).status_code,200)
        self.assertEqual(self.post(f'/api/atividades/{aid}/notas',{'notas':[{'aluno_id':self.a1,'nota':0}]}).status_code,200)

    def test_importacao_respeita_escopo_e_rollback_estrutural(self):
        self.entrar(self.p1);atividade=self.criar().json['id']
        with self.admin.transacao() as c:
            c.execute('SELECT matricula FROM simpa.alunos WHERE id=%s',(self.a1,));mat=c.fetchone()['matricula']
        csv=f'matricula;atividade_id;nota\n{mat};{atividade};1.5\n{mat};{atividade};99\n'
        resposta=self.c.post('/api/importacao/registros',data={'arquivo':(io.BytesIO(csv.encode()),'notas.csv')},headers=self.h)
        self.assertEqual(resposta.status_code,200)
        self.assertEqual((resposta.json['importados'],resposta.json['recusados']),(1,1))
        quebrado=f'matricula;atividade_id;nota\n{mat};{atividade};1\n"errado\n'
        self.assertEqual(self.c.post('/api/importacao/registros',data={'arquivo':(io.BytesIO(quebrado.encode()),'notas.csv')},headers=self.h).status_code,422)
        self.entrar(self.u1)
        self.assertEqual(self.c.post('/api/importacao/registros',data={'arquivo':(io.BytesIO(csv.encode()),'notas.csv')},headers=self.h).status_code,403)

    def test_paginas_e_filtros_novos(self):
        self.entrar(self.p1)
        atividade=self.criar().json['id']
        for url in ['/dashboard','/alunos','/alunos/novo','/turmas','/disciplinas','/avaliacoes',f'/avaliacoes/{atividade}/notas',f'/alunos/{self.a1}','/importacao','/api/docs']:
            with self.subTest(url=url):self.assertEqual(self.c.get(url).status_code,200)
        self.assertEqual(self.c.get('/api/analises?va=4').status_code,422)
        self.assertEqual(self.c.get('/api/analises?bimestre=2').status_code,422)
        self.entrar(self.u1)
        self.assertEqual(self.c.get('/dashboard').status_code,200)
        self.assertEqual(self.c.get('/minhas-notas').status_code,200)

    def dados_turma(self,**alteracoes):
        return {'identificador':'NOVA-'+uuid4().hex[:10],'nome':'Nova turma de IA',
                'ano_letivo':2026,'semestre':2,'situacao':'ativa','disciplinas':[self.d1],**alteracoes}

    def test_cadastro_turma_integra_avaliacoes_e_cadastro_alunos(self):
        self.entrar(self.p1)
        r=self.post('/api/turmas',self.dados_turma())
        self.assertEqual(r.status_code,201)
        tid=r.json['id']
        base=self.c.get(f'/api/dados?turma_id={tid}').json
        self.assertEqual([d['id'] for d in base['disciplinas']],[self.d1])
        self.assertEqual(len(base['regras']),3)
        self.assertTrue(all(not r['fechada'] for r in base['regras']))
        self.assertEqual(len(base['atividades']),9)
        self.assertEqual({a['tipo'] for a in base['atividades']},{'A360','VRAU','AFE'})
        self.assertEqual(base['alunos'],[]);self.assertEqual(base['notas_componentes'],[])
        self.assertTrue(any(t['id']==tid for t in self.c.get('/api/turmas').json))
        self.assertEqual(self.c.get(f'/avaliacoes?oferta={tid}:{self.d1}&va=2').status_code,200)
        novo={'matricula':'N-'+uuid4().hex[:12],'nome':'Aluno na nova turma','email':'novo@example.com','turma_id':tid}
        self.assertEqual(self.post('/api/alunos',novo).status_code,201)
        self.entrar(self.p2)
        self.assertEqual(self.c.get(f'/api/dados?turma_id={tid}').status_code,403)

    def test_cadastro_turma_recusa_duplicidade_no_contexto(self):
        self.entrar(self.p1);dados=self.dados_turma()
        self.assertEqual(self.post('/api/turmas',dados).status_code,201)
        self.assertEqual(self.post('/api/turmas',dados).status_code,409)
        self.assertEqual(self.post('/api/turmas',{**dados,'ano_letivo':2027}).status_code,201)

    def test_cadastro_turma_recusa_campos_invalidos_sem_criar_registros(self):
        self.entrar(self.p1)
        with self.admin.transacao() as c:
            c.execute('SELECT count(*) AS n FROM simpa.turmas');antes=c.fetchone()['n']
        for alteracao in [{'nome':' '},{'identificador':''},{'ano_letivo':'abc'},
                          {'ano_letivo':32768},{'semestre':3},{'situacao':'desconhecida'},
                          {'disciplinas':[]},{'disciplinas':'1'}]:
            with self.subTest(alteracao=alteracao):
                self.assertEqual(self.post('/api/turmas',self.dados_turma(**alteracao)).status_code,422)
        with self.admin.transacao() as c:
            c.execute('SELECT count(*) AS n FROM simpa.turmas');self.assertEqual(c.fetchone()['n'],antes)

    def test_cadastro_turma_respeita_perfis_e_disciplinas(self):
        self.entrar(self.u1)
        self.assertEqual(self.c.get('/turmas/nova').status_code,403)
        self.assertEqual(self.post('/api/turmas',self.dados_turma()).status_code,403)
        self.entrar(self.p1)
        self.assertEqual(self.post('/api/turmas',self.dados_turma(disciplinas=[self.d2])).status_code,403)
        self.assertEqual(self.post('/api/turmas',self.dados_turma(disciplinas=[99999999])).status_code,403)

    def test_formulario_turma_preserva_preenchimento_e_confere_csrf(self):
        self.entrar(self.p1)
        self.assertEqual(self.c.get('/turmas/nova').status_code,200)
        dados=self.dados_turma()
        self.assertEqual(self.c.post('/turmas/nova',data=dados).status_code,400)
        self.assertEqual(self.c.post('/turmas/nova',data={**dados,'csrf_token':'teste-csrf'}).status_code,302)
        r=self.c.post('/turmas/nova',data={**dados,'csrf_token':'teste-csrf'})
        self.assertEqual(r.status_code,409)
        self.assertIn(dados['identificador'],r.get_data(as_text=True))
        self.assertIn('Já existe uma turma',r.get_data(as_text=True))


if __name__=='__main__':unittest.main()
