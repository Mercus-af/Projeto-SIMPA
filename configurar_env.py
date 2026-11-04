"""Cria o .env local somente se ele ainda não existir."""
from pathlib import Path
import secrets

def criar_env():
    caminho=Path(__file__).resolve().parent/'.env'
    if caminho.exists():
        print('.env existente preservado. Confira DB_PASSWORD antes de conectar.')
        return
    texto=(Path(__file__).resolve().parent/'.env.example').read_text(encoding='utf-8')
    texto=texto.replace('SECRET_KEY=gerar-com-configurar_env.py','SECRET_KEY='+secrets.token_hex(32))
    with caminho.open('x',encoding='utf-8') as arquivo:
        arquivo.write(texto)
    print('.env criado com chave de sessão. Preencha DB_PASSWORD com a senha do PostgreSQL local.')

if __name__=='__main__':
    criar_env()
