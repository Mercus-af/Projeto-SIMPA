"""Conexão PostgreSQL e consultas de usuários, adaptadas do login do grupo."""
import os
from contextlib import closing
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

PASTA = Path(__file__).resolve().parents[1]
load_dotenv(PASTA / '.env')


def conectar():
    # Usada somente pela verificação isolada, sem mudar o .env pessoal.
    if os.getenv('SIMPA_TEST_DSN'):
        return psycopg2.connect(os.environ['SIMPA_TEST_DSN'], cursor_factory=RealDictCursor)
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'), port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'simpa'), user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''), connect_timeout=5,
        cursor_factory=RealDictCursor,
    )


def buscar_usuario(identificador):
    with closing(conectar()) as con, con.cursor() as cur:
        cur.execute('''SELECT id, nome, matricula, email_institucional, senha_hash, ativo, perfil, aluno_id
                       FROM simpa.usuarios WHERE matricula=%s
                       OR lower(email_institucional)=lower(%s) LIMIT 1''',
                    (identificador, identificador))
        linha = cur.fetchone()
        return dict(linha) if linha else None


def usuario_por_id(usuario_id):
    with closing(conectar()) as con,con.cursor() as cur:
        cur.execute('''SELECT id,nome,matricula,email_institucional,ativo,perfil,aluno_id
            FROM simpa.usuarios WHERE id=%s''',(usuario_id,))
        linha=cur.fetchone()
        return dict(linha) if linha else None


def inserir_usuario(nome, matricula, email, senha_hash,perfil='professor',aluno_id=None):
    with closing(conectar()) as con, con, con.cursor() as cur:
        cur.execute('''INSERT INTO simpa.usuarios(nome,matricula,email_institucional,senha_hash,perfil,aluno_id)
                       VALUES (%s,%s,%s,%s,%s,%s) RETURNING id''',
                    (nome, matricula, email, senha_hash,perfil,aluno_id))
        return cur.fetchone()['id']
