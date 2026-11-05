"""Histórico em banco descartável: isolamento, persistência e exclusão atômica."""
from contextlib import closing
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from langchain_core.messages import AIMessage
from werkzeug.security import generate_password_hash

from simpa import db
from simpa.app import criar_app
from simpa.chats import RepositorioChats
from scripts.preparar_banco import preparar
from simpa.repositorio import PermissaoNegada


@unittest.skipUnless(os.getenv('SIMPA_TEST_DSN'),'Configure um banco descartável')
class HistoricoChats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        preparar()
        cls.ids=[]
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            for i in range(2):
                cur.execute("INSERT INTO simpa.usuarios(nome,matricula,senha_hash,perfil) VALUES (%s,%s,%s,'professor') RETURNING id",
                    ('Professor de teste do histórico','CHAT-'+uuid4().hex[:20],generate_password_hash('teste-isolado')))
                cls.ids.append(cur.fetchone()['id'])

    def setUp(self):
        self.app=criar_app({'TESTING':True,'SECRET_KEY':'teste-chats'})
        self.usuario={'id':self.ids[0],'perfil':'professor','aluno_id':None}
        self.outro={'id':self.ids[1],'perfil':'professor','aluno_id':None}
        self.r=RepositorioChats(self.usuario)
        self.c=self.cliente(self.ids[0]);self.h={'X-CSRF-Token':'chat-csrf'}

    def cliente(self,uid):
        c=self.app.test_client()
        with c.session_transaction() as s:s['usuario_id']=uid;s['csrf']='chat-csrf'
        return c

    def test_criar_listar_e_reabrir_apos_novo_login(self):
        r=self.c.post('/api/assistente/chats',json={'base':'curso','va':2},headers=self.h)
        self.assertEqual(r.status_code,201)
        cid=r.json['id']
        self.r.salvar_turno(cid,'Como funciona o assistente?','Posso ajudar com **notas**.',[],{})
        novo=self.cliente(self.ids[0])
        d=novo.get('/api/assistente/chats/'+cid)
        self.assertEqual(d.status_code,200)
        self.assertEqual(len(d.json['mensagens']),2)
        self.assertIn('<strong>notas</strong>',d.json['mensagens'][1]['resposta_html'])
        self.assertEqual(d.json['chat']['titulo'],'Como funciona o assistente?')
        self.assertTrue(any(x['id']==cid for x in novo.get('/api/assistente/chats').json['chats']))

    def test_outro_usuario_nao_le_apaga_ou_lista_chat(self):
        cid=self.r.criar({})['id'];self.r.salvar_turno(cid,'Privado','Resposta privada.',[],{})
        outro=self.cliente(self.ids[1])
        self.assertEqual(outro.get('/api/assistente/chats/'+str(cid)).status_code,403)
        self.assertEqual(outro.delete('/api/assistente/chats/'+str(cid),headers=self.h).status_code,403)
        self.assertFalse(any(x['id']==str(cid) for x in outro.get('/api/assistente/chats').json['chats']))
        self.assertEqual(len(self.r.mensagens(cid)),2)

    def test_apagar_remove_so_chat_escolhido_e_mensagens(self):
        a=self.r.criar({})['id'];b=self.r.criar({})['id']
        self.r.salvar_turno(a,'Primeiro','Resposta A.',[],{})
        self.r.salvar_turno(b,'Segundo','Resposta B.',[],{})
        self.assertEqual(self.c.delete('/api/assistente/chats/'+str(a),headers=self.h).status_code,204)
        with closing(db.conectar()) as con,con.cursor() as cur:
            cur.execute('SELECT count(*) AS n FROM simpa.mensagens_assistente WHERE chat_id=%s',(str(a),))
            self.assertEqual(cur.fetchone()['n'],0)
        self.assertEqual(len(self.r.mensagens(b)),2)
        with self.assertRaises(PermissaoNegada):self.r.salvar_turno(a,'Mensagem tardia','Não ressuscitar.',[],{})

    def test_csrf_autenticacao_e_uuid(self):
        cid=self.r.criar({})['id']
        self.assertEqual(self.c.post('/api/assistente/chats',json={}).status_code,400)
        self.assertEqual(self.c.delete('/api/assistente/chats/'+str(cid)).status_code,400)
        self.assertEqual(self.app.test_client().get('/api/assistente/chats').status_code,401)
        self.assertEqual(self.c.get('/api/assistente/chats/invalido').status_code,422)

    def test_resposta_real_da_rota_e_persistida_sem_modelo_externo(self):
        llm=unittest.mock.MagicMock()
        llm.bind_tools.return_value.bind.return_value.invoke.return_value=AIMessage('Olá! Posso ajudar com **seus dados acadêmicos**.')
        with patch('simpa.assistente.verificar_ollama',return_value={'configurado':True}),patch('simpa.assistente_agente.modelo',return_value=llm):
            r=self.c.post('/api/assistente',json={'pergunta':'Olá!'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        cid=r.json['conversa_id']
        self.assertEqual(len(self.r.mensagens(cid)),2)
        self.assertEqual(self.cliente(self.ids[0]).get('/api/assistente/chats/'+cid).status_code,200)

    def test_mudanca_de_perfil_nao_expoe_historico_antigo(self):
        cid=self.r.criar({})['id']
        novo_perfil={**self.usuario,'perfil':'aluno','aluno_id':999}
        self.assertEqual(RepositorioChats(novo_perfil).listar()['chats'],[])
        with self.assertRaises(PermissaoNegada):RepositorioChats(novo_perfil).obter(cid)


if __name__=='__main__':unittest.main()
