class Aluno:
    @property
    def id_aluno(self):
        return self.__id_aluno

    def __init__(self, id_aluno:int, nome:str, email:str, matricula:str, semestre:int, ano:int, disciplinas:list, notas:dict, faltas:dict):
        for nota in notas.values():
            if not 0 <= nota <= 10:
                raise ValueError("A nota deve estar entre 0 e 10.")

        self.__id_aluno = id_aluno
        self.nome = nome
        self.matricula = matricula
        self.email = email
        self.semestre = semestre
        self.ano = ano
        self.disciplinas = disciplinas
        self.notas = notas
        self.faltas = faltas

    def __str__(self):
        return f"Aluno: {self.nome}, Matrícula: {self.matricula}, ID: {self.id_aluno}"

    def atualizar_email(self, novo_email:str):
        self.email = novo_email
        return self.email

    def get_disciplinas_em_risco(self):
        return [disciplina for disciplina, falta in self.faltas.items() if falta > 20]

    def disciplinas_abaixo_media(self):
        return [disciplina for disciplina, nota in self.notas.items() if nota < 6.0]

    def get_aprovacao(self) -> bool:
        if not self.notas:
            return False
        return all(nota >= 6.0 for nota in self.notas.values())

    def calcular_cr(self):
        if not self.notas:
            return None
        return sum(self.notas.values()) / len(self.notas)

    def get_disciplinas(self):
        return self.disciplinas if self.disciplinas else "Nenhuma disciplina cadastrada."

    def calcular_frequencia_global(self):
        registros = getattr(self, 'registros_frequencia', [])
        if not registros:
            return None
        if all(r.get('aulasPrevistas') is not None for r in registros):
            aulas = sum(r['aulasPrevistas'] for r in registros)
            return sum(r['presencas'] for r in registros) / aulas * 100 if aulas else None
        # Sem totais de aulas, só podemos calcular a média dos percentuais.
        valores = [r['percentual'] for r in registros if r.get('percentual') is not None]
        return sum(valores)/len(valores) if valores else None

    def get_notas(self):
        return self.notas if self.notas else "Nenhuma nota cadastrada."

    def get_faltas(self):
        return self.faltas if self.faltas else "Nenhuma falta registrada."

    def to_dict(self):
        return {
            "id_aluno": self.id_aluno,
            "nome": self.nome,
            "email": self.email,
            "matricula": self.matricula,
            "semestre": self.semestre,
            "ano": self.ano,
            "cr": self.calcular_cr(),
            "em_risco": len(self.get_disciplinas_em_risco()) > 0
        }

