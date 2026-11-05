from aluno_repositorio import buscar_aluno


resultado = buscar_aluno(1)

if resultado is None:
    print("Aluno não encontrado.")
else:
    print("ID:", resultado[0])
    print("Matrícula:", resultado[1])
    print("Nome:", resultado[2])