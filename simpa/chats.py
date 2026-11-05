"""Persistência do histórico privado do assistente, sem depender da sessão de login."""
from contextlib import closing
from uuid import UUID, uuid4

from psycopg2.extras import Json

from simpa import db
from simpa.importacao.validacoes import DadosInvalidos
from simpa.repositorio import PermissaoNegada

CAMPOS=('base','va','turma_id','disciplina_id','aluno_id','semestre')


def filtros_chat(entrada):
    return {'base':entrada.get('base') or 'curso','va':entrada.get('va') or 2,
            **{k:entrada.get(k) or None for k in CAMPOS if k not in ('base','va')}}


def id_chat(valor):
    try:return str(UUID(str(valor)))
    except (ValueError,TypeError,AttributeError):raise DadosInvalidos('Identificador de chat inválido.')


class RepositorioChats:
    def __init__(self,usuario):
        self.usuario=usuario

    def parametros(self):
        return (self.usuario['id'],self.usuario['perfil'],self.usuario.get('aluno_id'))

    @staticmethod
    def condicao():
        return 'usuario_id=%s AND perfil=%s AND aluno_id IS NOT DISTINCT FROM %s'

    def obter(self,cid,cur=None,bloquear=False):
        cid=id_chat(cid)
        if cur is None:
            with closing(db.conectar()) as con,con.cursor() as c:return self.obter(cid,c,bloquear)
        cur.execute('SELECT * FROM simpa.chats_assistente WHERE id=%s AND '+self.condicao()+
                    (' FOR UPDATE' if bloquear else ''),(cid,*self.parametros()))
        chat=cur.fetchone()
        if chat is None:raise PermissaoNegada('Chat não encontrado para esta conta.')
        return dict(chat)

    def criar(self,entrada):
        cid=str(uuid4())
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            cur.execute('''INSERT INTO simpa.chats_assistente(id,usuario_id,perfil,aluno_id,filtros)
                VALUES(%s,%s,%s,%s,%s) RETURNING *''',(cid,*self.parametros(),Json(filtros_chat(entrada))))
            return dict(cur.fetchone())

    def listar(self,pagina=1):
        with closing(db.conectar()) as con,con.cursor() as cur:
            cur.execute('''SELECT id,titulo,criado_em,atualizado_em FROM simpa.chats_assistente WHERE '''+
                        self.condicao()+' ORDER BY atualizado_em DESC,id DESC LIMIT 51 OFFSET %s',
                        (*self.parametros(),(pagina-1)*50))
            linhas=[dict(x) for x in cur.fetchall()]
        return {'chats':linhas[:50],'pagina':pagina,'tem_mais':len(linhas)>50}

    def mensagens(self,cid,limite=None):
        with closing(db.conectar()) as con,con.cursor() as cur:
            self.obter(cid,cur)
            if limite:
                cur.execute('''SELECT * FROM (SELECT papel,texto,fontes,criado_em,id FROM simpa.mensagens_assistente
                    WHERE chat_id=%s ORDER BY id DESC LIMIT %s) m ORDER BY id''',(id_chat(cid),limite))
            else:
                cur.execute('''SELECT papel,texto,fontes,criado_em FROM simpa.mensagens_assistente
                    WHERE chat_id=%s ORDER BY id''',(id_chat(cid),))
            return [dict(x) for x in cur.fetchall()]

    def salvar_turno(self,cid,pergunta,resposta,fontes,selecao):
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            chat=self.obter(cid,cur,bloquear=True)
            cur.execute('SELECT EXISTS(SELECT 1 FROM simpa.mensagens_assistente WHERE chat_id=%s) AS existe',(id_chat(cid),))
            primeiro=not cur.fetchone()['existe']
            titulo=(' '.join(pergunta.split())[:77]+'…') if len(' '.join(pergunta.split()))>80 else ' '.join(pergunta.split())
            cur.execute('''INSERT INTO simpa.mensagens_assistente(chat_id,papel,texto,fontes)
                VALUES (%s,'user',%s,'[]'::jsonb),(%s,'assistant',%s,%s)''',
                (id_chat(cid),pergunta,id_chat(cid),resposta,Json(fontes)))
            cur.execute('''UPDATE simpa.chats_assistente SET selecao=%s,atualizado_em=CURRENT_TIMESTAMP,
                titulo=%s WHERE id=%s''',(Json(selecao),titulo if primeiro else chat['titulo'],id_chat(cid)))

    def apagar(self,cid):
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            self.obter(cid,cur,bloquear=True)
            cur.execute('DELETE FROM simpa.chats_assistente WHERE id=%s',(id_chat(cid),))
