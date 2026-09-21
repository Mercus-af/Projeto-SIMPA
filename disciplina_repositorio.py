from conexao import conectar


def salvar_disciplina(disciplina, periodo_id, codigo):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO academico.disciplinas (
                    periodo_id,
                    codigo,
                    nome,
                    carga_horaria
                )
                VALUES (%s, %s, %s, %s)
                RETURNING disciplina_id;
                """,
                (
                    periodo_id,
                    codigo,
                    disciplina.nome,
                    disciplina.carga_horaria
                )
            )

            disciplina_id = cursor.fetchone()[0]

    return disciplina_id