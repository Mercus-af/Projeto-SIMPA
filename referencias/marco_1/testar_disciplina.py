from disciplina_classe import Disciplina
from disciplina_repositorio import salvar_disciplina


disciplina = Disciplina(
    id_disciplina=0,
    nome="Programação Teste",
    semestre=1,
    ano=2026,
    carga_horaria=60,
    alunos=[],
    professores=[]
)

id_gerado = salvar_disciplina(
    disciplina,
    periodo_id=1,
    codigo="PROG_TESTE01"
)

print("Disciplina salva! ID no banco:", id_gerado)