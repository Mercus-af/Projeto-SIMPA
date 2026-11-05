from conexao import conectar


def salvar_aluno(aluno):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cadastro.alunos (
                    codigo_academico,
                    nome_sintetico
                )
                VALUES (%s, %s)
                RETURNING aluno_id;
                """,
                (aluno.matricula, aluno.nome)
            )

            aluno_id = cursor.fetchone()[0]

    return aluno_id

def buscar_aluno(aluno_id):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT aluno_id, codigo_academico, nome_sintetico
                FROM cadastro.alunos
                WHERE aluno_id = %s;
                """,
                (aluno_id,)
            )

            return cursor.fetchone()