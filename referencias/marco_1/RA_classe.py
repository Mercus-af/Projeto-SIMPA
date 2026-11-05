class RegistroAcademico:

    @property
    def id_registro(self):
        return self.__id_registro

    def __init__(
        self,
        id_registro: int,
        aluno,
        turma,
        disciplinas: list,
        notas: dict,
        faltas: dict,
        frequencias: dict | None = None
    ):
        for nota in notas.values():
            self._validar_nota(nota)
        for frequencia in (frequencias or {}).values():
            self._validar_frequencia(frequencia)

        self.__id_registro = id_registro
        self.aluno = aluno
        self.turma = turma
        self.disciplinas = disciplinas
        self.notas = notas
        self.faltas = faltas
        self.frequencias = frequencias or {}

    def __str__(self):
        return (
            f"Registro Acadêmico - "
            f"Aluno: {self.aluno.nome}, "
            f"Turma: {self.turma.nome}, "
            f"ID: {self.id_registro}"
        )

    def adicionar_disciplina(self, disciplina: str | list):
        if isinstance(disciplina, list):
            self.disciplinas.extend(disciplina)
        else:
            self.disciplinas.append(disciplina)

        return f"Disciplina(s) {disciplina} adicionada(s) com sucesso"

    def remover_disciplina(self, disciplina: str | list):
        if isinstance(disciplina, list):
            for d in disciplina:
                if d in self.disciplinas:
                    self.disciplinas.remove(d)
        else:
            if disciplina in self.disciplinas:
                self.disciplinas.remove(disciplina)

        return f"Disciplina(s) {disciplina} removida(s) com sucesso"

    @staticmethod
    def _validar_nota(nota: float):
        if not 0 <= nota <= 10:
            raise ValueError("A nota deve estar entre 0 e 10.")

    @staticmethod
    def _validar_frequencia(frequencia: float):
        if not 0 <= frequencia <= 100:
            raise ValueError("A frequência deve estar entre 0 e 100.")

    def registrar_nota(self, disciplina, nota: float):
        self._validar_nota(nota)
        self.notas[disciplina] = nota
        return f"Nota {nota} registrada para {disciplina}."

    def registrar_frequencia(self, disciplina, frequencia: float):
        self._validar_frequencia(frequencia)
        self.frequencias[disciplina] = frequencia
        return f"Frequência {frequencia}% registrada para {disciplina}."

    def registrar_falta(self, disciplina, faltas: int):
        self.faltas[disciplina] = faltas
        return f"{faltas} falta(s) registrada(s) para {disciplina}."

    def calcular_cr(self):
        if not self.notas:
            return 0.0

        return round(
            sum(self.notas.values()) / len(self.notas),
            2
        )

    def get_aprovacao(self):
        if not self.notas:
            return True

        return all(
            nota >= 6.0
            for nota in self.notas.values()
        )

    def disciplinas_abaixo_media(self):
        return [
            disciplina
            for disciplina, nota in self.notas.items()
            if nota < 6.0
        ]

    def get_disciplinas_em_risco(self):
        return [
            disciplina
            for disciplina, falta in self.faltas.items()
            if falta > 20
        ]

    def get_total_disciplinas(self):
        return len(self.disciplinas)

    def get_disciplinas(self):
        return self.disciplinas

    def get_notas(self):
        return self.notas

    def get_faltas(self):
        return self.faltas

    def get_frequencias(self):
        return self.frequencias

    def get_turma(self):
        return self.turma

    def alterar_turma(self, nova_turma):
        self.turma = nova_turma
        return f"Aluno transferido para a turma {nova_turma.nome}."

    def to_dict(self):
        return {
            "id_registro": self.id_registro,
            "aluno": (
                self.aluno.to_dict()
                if hasattr(self.aluno, "to_dict")
                else self.aluno
            ),
            "turma": (
                self.turma.to_dict()
                if hasattr(self.turma, "to_dict")
                else self.turma
            ),
            "total_disciplinas": self.get_total_disciplinas(),
            "cr": self.calcular_cr(),
            "aprovado": self.get_aprovacao(),
            "disciplinas_abaixo_media": self.disciplinas_abaixo_media(),
            "disciplinas_em_risco": self.get_disciplinas_em_risco(),
            "disciplinas": [
                disciplina.to_dict()
                if hasattr(disciplina, "to_dict")
                else disciplina
                for disciplina in self.disciplinas
            ],
            "notas": self.notas,
            "faltas": self.faltas,
            "frequencias": self.frequencias
        }