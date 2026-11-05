"""Consultas exclusivas à base sintética, sem vínculo com contas ou notas reais."""
from contextlib import closing

from simpa import db
from simpa.repositorio import PermissaoNegada, numeros


class RepositorioDatasetProfessor:
    def __init__(self, usuario):
        if not usuario or usuario['perfil'] != 'professor':
            raise PermissaoNegada('A demonstração do dataset é exclusiva de professores.')

    def dados(self):
        with closing(db.conectar()) as con, con.cursor() as cur:
            cur.execute("SELECT to_regclass('simpa_dataset.cargas') AS tabela")
            if cur.fetchone()['tabela'] is None:
                return None
            cur.execute('SELECT identificador,origem,sha256,carregado_em FROM simpa_dataset.cargas ORDER BY carregado_em DESC LIMIT 1')
            carga = cur.fetchone()
            if not carga:
                return None
            cur.execute('SELECT nome FROM simpa_dataset.cursos ORDER BY curso_id LIMIT 1')
            curso = cur.fetchone()['nome']
            cur.execute('SELECT aluno_id,codigo_academico,nome_sintetico FROM simpa_dataset.alunos ORDER BY nome_sintetico,aluno_id')
            alunos = [dict(r) for r in cur.fetchall()]
            cur.execute('''SELECT r.*,m.aluno_id,m.periodo_atual,t.ano_letivo,t.semestre_letivo,
                d.disciplina_id,d.nome AS disciplina,d.codigo,p.numero_periodo
                FROM simpa_dataset.registros_academicos r
                JOIN simpa_dataset.matriculas_curso m USING(matricula_curso_id)
                JOIN simpa_dataset.turmas t USING(turma_id)
                JOIN simpa_dataset.disciplinas d USING(disciplina_id)
                JOIN simpa_dataset.periodos_curriculares p USING(periodo_id)
                ORDER BY t.ano_letivo,t.semestre_letivo,r.registro_id''')
            registros = [dict(r) for r in cur.fetchall()]
        return numeros({'fonte': {**dict(carga), 'curso': curso, 'sintetico': True},
                        'alunos': alunos, 'registros': registros})
