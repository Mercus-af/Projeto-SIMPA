"""Regras de login do SIMPA: conferir a senha e proteger as páginas."""

from functools import wraps

from flask import redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from simpa import db
# Hash de uma senha qualquer. Serve só para gastar o mesmo tempo quando o
# usuário não existe, assim ninguém descobre quais matrículas existem.
_HASH_FALSO = generate_password_hash("senha-falsa-para-igualar-o-tempo")


def autenticar(identificador, senha):
    """Confere matrícula/e-mail e senha.

    Devolve os dados do usuário se estiver tudo certo, senão devolve None.
    Não diz se o erro foi no usuário ou na senha (RNF05).
    """
    usuario = db.buscar_usuario(identificador.strip())

    if usuario is None:
        check_password_hash(_HASH_FALSO, senha)
        return None

    senha_correta = check_password_hash(usuario["senha_hash"], senha)
    if not senha_correta or not usuario["ativo"]:
        return None

    return usuario


def iniciar_sessao(usuario):
    """Guarda quem entrou. O navegador recebe só um cookie assinado."""
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session['perfil']=usuario['perfil']


def encerrar_sessao():
    session.clear()


def login_obrigatorio(rota):
    """Use acima de uma rota para só deixar entrar quem fez login."""

    @wraps(rota)
    def protegida(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return rota(*args, **kwargs)

    return protegida
