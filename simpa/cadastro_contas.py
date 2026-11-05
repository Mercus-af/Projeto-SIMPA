"""Cadastro de aluno por convite de uso único; perfil definido pelo servidor."""
from contextlib import closing
from hashlib import sha256
import secrets

import psycopg2
from werkzeug.security import generate_password_hash

from simpa import db
from simpa.importacao.validacoes import DadosInvalidos, EMAIL

ERRO_CONVITE='Confira matrícula, e-mail e código de cadastro. Solicite um novo código ao professor se necessário.'


def gerar_convite(repositorio,aluno_id):
    repositorio.exigir_professor()
    repositorio.exigir_aluno(aluno_id)
    codigo=secrets.token_urlsafe(18)
    with closing(db.conectar()) as con,con,con.cursor() as cur:
        cur.execute('SELECT id FROM simpa.alunos WHERE id=%s FOR UPDATE',(aluno_id,))
        cur.execute('SELECT 1 FROM simpa.usuarios WHERE aluno_id=%s',(aluno_id,))
        if cur.fetchone():raise DadosInvalidos('Este aluno já possui conta de acesso.')
        cur.execute('''INSERT INTO simpa.convites_cadastro(aluno_id,codigo_hash,criado_por,expira_em)
            VALUES (%s,%s,%s,CURRENT_TIMESTAMP+INTERVAL '48 hours')
            ON CONFLICT(aluno_id) DO UPDATE SET codigo_hash=excluded.codigo_hash,
            criado_por=excluded.criado_por,expira_em=excluded.expira_em,utilizado_em=NULL''',
            (aluno_id,sha256(codigo.encode()).hexdigest(),repositorio.usuario['id']))
    return codigo


def cadastrar_conta(entrada):
    matricula=str(entrada.get('matricula','')).strip()
    email=str(entrada.get('email','')).strip().lower()
    codigo=str(entrada.get('codigo','')).strip()
    senha=entrada.get('senha','')
    confirmacao=entrada.get('confirmacao','')
    if not 1<=len(matricula)<=30 or not 1<=len(email)<=254 or not EMAIL.fullmatch(email):
        raise DadosInvalidos('Informe sua matrícula e seu e-mail institucional válidos.')
    if not 20<=len(codigo)<=100:raise DadosInvalidos(ERRO_CONVITE)
    if not isinstance(senha,str) or not 8<=len(senha)<=128:
        raise DadosInvalidos('A senha deve ter de 8 a 128 caracteres.')
    if senha!=confirmacao:raise DadosInvalidos('As senhas não conferem.')
    senha_hash=generate_password_hash(senha)
    try:
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            cur.execute('''SELECT id,nome_completo,email_institucional FROM simpa.alunos
                WHERE matricula=%s AND lower(email_institucional)=%s
                AND situacao_academica='ativo' FOR UPDATE''',(matricula,email))
            aluno=cur.fetchone()
            if not aluno:raise DadosInvalidos(ERRO_CONVITE)
            cur.execute('''SELECT aluno_id FROM simpa.convites_cadastro WHERE aluno_id=%s
                AND codigo_hash=%s AND utilizado_em IS NULL AND expira_em>CURRENT_TIMESTAMP FOR UPDATE''',
                (aluno['id'],sha256(codigo.encode()).hexdigest()))
            if not cur.fetchone():raise DadosInvalidos(ERRO_CONVITE)
            cur.execute('''INSERT INTO simpa.usuarios(nome,matricula,email_institucional,senha_hash,perfil,aluno_id)
                VALUES (%s,%s,%s,%s,'aluno',%s) RETURNING id''',
                (aluno['nome_completo'],matricula,aluno['email_institucional'],senha_hash,aluno['id']))
            uid=cur.fetchone()['id']
            cur.execute('UPDATE simpa.convites_cadastro SET utilizado_em=CURRENT_TIMESTAMP WHERE aluno_id=%s',(aluno['id'],))
            return uid
    except psycopg2.IntegrityError:
        raise DadosInvalidos('Não foi possível criar a conta. Se você já possui acesso, entre pelo login ou procure o responsável.') from None
