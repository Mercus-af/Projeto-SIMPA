from aluno_classe import Aluno
from turma_classe import Turma
from RA_classe import RegistroAcademico
from registro_repositorio import salvar_registro


aluno = Aluno(
    id_aluno=1,
    nome="Aluno Teste",
    email="teste@example.com",
    matricula="TESTE001",
    semestre=1,
    ano=2026,
    disciplinas=[],
    notas={},
    faltas={}
)

turma = Turma(
    id_turma=1,
    nome="Turma Teste",
    semestre=1,
    ano=2026,
    alunos=[],
    disciplinas=[],
    professores=[]
)

registro = RegistroAcademico(
    id_registro=0,
    aluno=aluno,
    turma=turma,
    disciplinas=["PROG_TESTE01"],
    notas={"PROG_TESTE01": 8.5},
    faltas={}
)

id_gerado = salvar_registro(
    registro,
    matricula_curso_id=1,
    codigo_disciplina="PROG_TESTE01"
)

print("Registro salvo! ID no banco:", id_gerado)