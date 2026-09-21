import sqlite3
from pathlib import Path


class MatriculaDuplicadaError(Exception):
    pass


class TurmaNaoEncontradaError(Exception):
    pass


class RepositorioSQLite:
    def __init__(self, caminho_banco):
        self.caminho_banco = Path(caminho_banco)

    def _conectar(self):
        conexao = sqlite3.connect(self.caminho_banco)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    def inicializar(self):
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as conexao:
            conexao.executescript(
                """
                CREATE TABLE IF NOT EXISTS turmas (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE,
                    semestre INTEGER NOT NULL CHECK (semestre BETWEEN 1 AND 2),
                    ano INTEGER NOT NULL,
                    situacao TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS disciplinas (
                    id INTEGER PRIMARY KEY,
                    codigo TEXT NOT NULL UNIQUE,
                    nome TEXT NOT NULL,
                    situacao TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS alunos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matricula TEXT NOT NULL UNIQUE,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL,
                    turma_id INTEGER NOT NULL,
                    situacao TEXT NOT NULL DEFAULT 'ativo',
                    FOREIGN KEY (turma_id) REFERENCES turmas(id)
                );
                """
            )
            conexao.executemany(
                """
                INSERT OR IGNORE INTO turmas (id, nome, semestre, ano, situacao)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (1, "IA - 2º período", 2, 2026, "ativa"),
                    (2, "ADS - 2º período", 2, 2026, "ativa"),
                ],
            )
            conexao.executemany(
                """
                INSERT OR IGNORE INTO disciplinas (id, codigo, nome, situacao)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (1, "POO", "Programação Orientada a Objetos", "ativa"),
                    (2, "EST", "Estatística Aplicada", "ativa"),
                    (3, "RDS", "Redes e Segurança", "ativa"),
                ],
            )
            conexao.executemany(
                """
                INSERT OR IGNORE INTO alunos
                    (matricula, nome, email, turma_id, situacao)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    ("2026001", "Ana Martins", "ana.martins@faculdade.edu.br", 1, "ativo"),
                    ("2026002", "Bruno Lima", "bruno.lima@faculdade.edu.br", 1, "ativo"),
                ],
            )

    def listar_alunos(self):
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT a.id, a.matricula, a.nome, a.email, a.turma_id,
                       t.nome AS turma, a.situacao
                FROM alunos AS a
                JOIN turmas AS t ON t.id = a.turma_id
                ORDER BY a.nome
                """
            ).fetchall()
        return [dict(linha) for linha in linhas]

    def buscar_aluno_por_matricula(self, matricula):
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT a.id, a.matricula, a.nome, a.email, a.turma_id,
                       t.nome AS turma, a.situacao
                FROM alunos AS a
                JOIN turmas AS t ON t.id = a.turma_id
                WHERE a.matricula = ?
                """,
                (matricula,),
            ).fetchone()
        return dict(linha) if linha else None

    def cadastrar_aluno(self, matricula, nome, email, turma_id):
        with self._conectar() as conexao:
            turma = conexao.execute(
                "SELECT id FROM turmas WHERE id = ?", (turma_id,)
            ).fetchone()
            if turma is None:
                raise TurmaNaoEncontradaError

            try:
                conexao.execute(
                    """
                    INSERT INTO alunos (matricula, nome, email, turma_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (matricula, nome, email, turma_id),
                )
            except sqlite3.IntegrityError as erro:
                if "alunos.matricula" in str(erro):
                    raise MatriculaDuplicadaError from erro
                raise

        return self.buscar_aluno_por_matricula(matricula)

    def listar_turmas(self):
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT t.id, t.nome, t.semestre, t.ano, t.situacao,
                       COUNT(a.id) AS total_alunos
                FROM turmas AS t
                LEFT JOIN alunos AS a ON a.turma_id = t.id
                GROUP BY t.id
                ORDER BY t.nome
                """
            ).fetchall()
        return [dict(linha) for linha in linhas]

    def listar_disciplinas(self):
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT id, codigo, nome, situacao
                FROM disciplinas
                ORDER BY nome
                """
            ).fetchall()
        return [dict(linha) for linha in linhas]
