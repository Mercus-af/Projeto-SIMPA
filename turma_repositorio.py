from conexao import conectar


def salvar_turma(turma, disciplina_id, codigo_turma):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO academico.turmas (
                    disciplina_id,
                    ano_letivo,
                    semestre_letivo,
                    codigo_turma
                )
                VALUES (%s, %s, %s, %s)
                RETURNING turma_id;
                """,
                (
                    disciplina_id,
                    turma.ano,
                    turma.semestre,
                    codigo_turma
                )
            )

            turma_id = cursor.fetchone()[0]

    return turma_id