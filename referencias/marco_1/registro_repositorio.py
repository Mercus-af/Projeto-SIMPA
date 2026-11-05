from conexao import conectar


def salvar_registro(registro, matricula_curso_id, codigo_disciplina):
    nota = registro.notas[codigo_disciplina]

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO academico.registros_academicos (
                    matricula_curso_id,
                    turma_id,
                    nota_final
                )
                VALUES (%s, %s, %s)
                RETURNING registro_id;
                """,
                (
                    matricula_curso_id,
                    registro.turma.id_turma,
                    nota
                )
            )

            registro_id = cursor.fetchone()[0]

    return registro_id