class Disciplina:

    @property

    def id_disciplina(self):

        return self.__id_disciplina


    def __init__(self, id_disciplina:int, nome:str, semestre:int, ano:int, carga_horaria:int, alunos:list, professores:list):

        self.__id_disciplina = id_disciplina
        self.nome = nome
        self.semestre = semestre
        self.ano = ano
        self.carga_horaria = carga_horaria
        self.alunos = alunos
        self.professores = professores


    def __str__(self):

        return f"Disciplina: {self.nome}, ID: {self.id_disciplina}"


    def adicionar_aluno(self, aluno:str|list):

        if isinstance(aluno, list):
            self.alunos.extend(aluno)

        else:
            self.alunos.append(aluno)

        return f"Aluno(s) {aluno} adicionado(s) com sucesso"


    def remover_aluno(self, aluno:str|list):

        if isinstance(aluno, list):
            for a in aluno:
                if a in self.alunos:
                    self.alunos.remove(a)

        else:
            if aluno in self.alunos:
                self.alunos.remove(aluno)

        return f"Aluno(s) {aluno} removido(s) com sucesso"


    def adicionar_professor(self, professor:str|list):

        if isinstance(professor, list):
            self.professores.extend(professor)

        else:
            self.professores.append(professor)

        return f"Professor(es) {professor} adicionado(s) com sucesso"


    def remover_professor(self, professor:str|list):

        if isinstance(professor, list):
            for p in professor:
                if p in self.professores:
                    self.professores.remove(p)

        else:
            if professor in self.professores:
                self.professores.remove(professor)

        return f"Professor(es) {professor} removido(s) com sucesso"


    def get_total_alunos(self):
        return len(self.alunos) if self.alunos else 0


    def get_total_professores(self):
        return len(self.professores) if self.professores else 0


    def get_alunos(self):
        return self.alunos if self.alunos else "Nenhum aluno matriculado."


    def get_professores(self):
        return self.professores if self.professores else "Nenhum professor cadastrado."


    def to_dict(self):
        return {
            "id_disciplina": self.id_disciplina,
            "nome": self.nome,
            "semestre": self.semestre,
            "ano": self.ano,
            "carga_horaria": self.carga_horaria,
            "total_alunos": self.get_total_alunos(),
            "total_professores": self.get_total_professores(),
            "alunos": [
                aluno.to_dict() if hasattr(aluno, 'to_dict') else aluno
                for aluno in self.alunos
            ],
            "professores": self.professores
        }
