class Turma:

    @property
    def id_turma(self):
        return self.__id_turma

    def __init__(self, id_turma:int, nome:str, semestre:int, ano:int, alunos:list, disciplinas:list, professores:list):
        self.__id_turma = id_turma
        self.nome = nome
        self.semestre = semestre
        self.ano = ano
        self.alunos = alunos
        self.disciplinas = disciplinas
        self.professores = professores

    def matricular_aluno(self, aluno:str|list):
        if isinstance(aluno, list):
            self.alunos.extend(aluno)
        else:
            self.alunos.append(aluno)
        return f"Aluno(s) {aluno} matriculados com sucesso!"

    def remover_aluno(self, aluno:str|list):
        if isinstance(aluno, list):
            for a in aluno:
                if a in self.alunos:
                    self.alunos.remove(a)
        else:
            if aluno in self.alunos:
                self.alunos.remove(aluno)
        return f"Aluno(s) {aluno} removido(s) com sucesso!"

    def adicionar_disciplina(self, disciplina:str|list):
        if isinstance(disciplina, list):
            self.disciplinas.extend(disciplina)
        else:
            self.disciplinas.append(disciplina)
        return f"Disciplina(s) {disciplina} adicionada(s) com sucesso!"

    def remover_disciplina(self, disciplina:str|list):
        if isinstance(disciplina, list):
            for d in disciplina:
                if d in self.disciplinas:
                    self.disciplinas.remove(d)
        else:
            if disciplina in self.disciplinas:
                self.disciplinas.remove(disciplina)
        return f"Disciplina(s) {disciplina} removida(s) com sucesso!"

    def adicionar_professor(self, professor:str|list):
        if isinstance(professor, list):
            self.professores.extend(professor)
        else:
            self.professores.append(professor)
        return f"Professor(es) {professor} adicionado(s) com sucesso!"

    def remover_professor(self, professor:str|list):
        if isinstance(professor, list):
            for p in professor:
                if p in self.professores:
                    self.professores.remove(p)
        else:
            if professor in self.professores:
                self.professores.remove(professor)
        return f"Professor(es) {professor} removido(s) com sucesso!"

    def calcular_media_turma(self):
        medias = []
        for aluno in self.alunos:
            notas = getattr(aluno, "notas", {})
            if notas:
                medias.append(sum(notas.values()) / len(notas))
        return sum(medias) / len(medias) if medias else 0.0

    def calcular_taxa_aprovacao(self):
        if not self.alunos:
            return 0.0
        aprovados = sum(1 for aluno in self.alunos if aluno.get_aprovacao())
        return (aprovados / len(self.alunos)) * 100
    
    def get_total_alunos(self):
        return len(self.alunos) if self.alunos else 0

    def get_total_disciplinas(self):
        return len(self.disciplinas) if self.disciplinas else 0

    def get_total_professores(self):
        return len(self.professores) if self.professores else 0

    def to_dict(self):
        return {
            "id_turma": self.id_turma,
            "nome": self.nome,
            "semestre": self.semestre,
            "ano": self.ano,
            "total_alunos": self.get_total_alunos(),
            "media_turma": self.calcular_media_turma(),
            "taxa_aprovacao": self.calcular_taxa_aprovacao(),
            "alunos": [aluno.to_dict() if hasattr(aluno, 'to_dict') else aluno for aluno in self.alunos],
            "disciplinas": self.disciplinas,
            "professores": self.professores
        }
