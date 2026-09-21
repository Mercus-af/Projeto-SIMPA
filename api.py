import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from sqlite_repositorio import (
    MatriculaDuplicadaError,
    RepositorioSQLite,
    TurmaNaoEncontradaError,
)


CAMINHO_BANCO_PADRAO = Path(__file__).parent / "data" / "simpa.db"


class AlunoEntrada(BaseModel):
    matricula: str = Field(min_length=1, max_length=30)
    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=120)
    turma_id: int = Field(gt=0)

    @field_validator("matricula", "nome", "email", mode="before")
    @classmethod
    def remover_espacos(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor):
        partes = valor.rsplit("@", 1)
        if len(partes) != 2 or not partes[0] or "." not in partes[1]:
            raise ValueError("Informe um e-mail válido.")
        return valor


class AlunoSaida(AlunoEntrada):
    id: int
    turma: str
    situacao: str


class TurmaSaida(BaseModel):
    id: int
    nome: str
    semestre: int
    ano: int
    situacao: str
    total_alunos: int


class DisciplinaSaida(BaseModel):
    id: int
    codigo: str
    nome: str
    situacao: str


def create_app(caminho_banco=None):
    caminho = caminho_banco or os.getenv("SIMPA_DB_PATH", CAMINHO_BANCO_PADRAO)
    repositorio = RepositorioSQLite(caminho)

    @asynccontextmanager
    async def lifespan(_app):
        repositorio.inicializar()
        yield

    api = FastAPI(
        title="SIMPA - Marco 1",
        description="API básica para cadastro e consulta de dados acadêmicos.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @api.get("/saude", tags=["Sistema"])
    def verificar_saude():
        return {"status": "ok"}

    @api.get("/alunos", response_model=list[AlunoSaida], tags=["Alunos"])
    def listar_alunos():
        return repositorio.listar_alunos()

    @api.post(
        "/alunos",
        response_model=AlunoSaida,
        status_code=201,
        tags=["Alunos"],
    )
    def cadastrar_aluno(aluno: AlunoEntrada):
        try:
            return repositorio.cadastrar_aluno(**aluno.model_dump())
        except MatriculaDuplicadaError as erro:
            raise HTTPException(
                status_code=409, detail="Matrícula já cadastrada."
            ) from erro
        except TurmaNaoEncontradaError as erro:
            raise HTTPException(
                status_code=422, detail="Turma não encontrada."
            ) from erro

    @api.get(
        "/alunos/{matricula}", response_model=AlunoSaida, tags=["Alunos"]
    )
    def consultar_aluno(matricula: str):
        aluno = repositorio.buscar_aluno_por_matricula(matricula)
        if aluno is None:
            raise HTTPException(status_code=404, detail="Aluno não encontrado.")
        return aluno

    @api.get("/turmas", response_model=list[TurmaSaida], tags=["Turmas"])
    def listar_turmas():
        return repositorio.listar_turmas()

    @api.get(
        "/disciplinas",
        response_model=list[DisciplinaSaida],
        tags=["Disciplinas"],
    )
    def listar_disciplinas():
        return repositorio.listar_disciplinas()

    return api


app = create_app()
