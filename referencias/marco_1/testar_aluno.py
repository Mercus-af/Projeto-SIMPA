from aluno_classe import Aluno
from aluno_repositorio import salvar_aluno


aluno = Aluno(
    id_aluno=0,
    nome="Aluno Teste",
    email="teste@example.com",
    matricula="TESTE001",
    semestre=1,
    ano=2026,
    disciplinas=[],
    notas={},
    faltas={}
)

id_gerado = salvar_aluno(aluno)

print("Aluno salvo! ID no banco:", id_gerado)