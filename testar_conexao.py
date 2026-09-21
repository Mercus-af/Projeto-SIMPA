from getpass import getpass
import psycopg

senha = getpass("Senha do PostgreSQL: ")

with psycopg.connect(
    host="localhost",
    port=5432,
    dbname="SIMPA",
    user="postgres",
    password=senha
) as conexao:
    with conexao.cursor() as cursor:
        cursor.execute("SELECT current_database();")
        resultado = cursor.fetchone()
        print("Conectado ao banco:", resultado[0])