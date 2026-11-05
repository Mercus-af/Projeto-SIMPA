from turma_classe import Turma
from turma_repositorio import salvar_turma


turma = Turma(
    id_turma=0,
    nome="Turma Teste",
    semestre=1,
    ano=2026,
    alunos=[],
    disciplinas=[],
    professores=[]
)

id_gerado = salvar_turma(
    turma,
    disciplina_id=1,
    codigo_turma="TURMA_TESTE01"
)

print("Turma salva! ID no banco:", id_gerado)