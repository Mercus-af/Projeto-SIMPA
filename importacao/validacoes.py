"""Regras de validação da base acadêmica."""

from __future__ import annotations

import math
import re
import unicodedata

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class DadosInvalidos(ValueError):
    """Um registro não atende às regras de negócio."""


def texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def normalizar_coluna(nome) -> str:
    nome = unicodedata.normalize("NFKD", texto(nome))
    nome = "".join(letra for letra in nome if not unicodedata.combining(letra))
    nome = re.sub(r"[^a-zA-Z0-9]+", "_", nome.casefold()).strip("_")
    alias = {"e_mail": "email", "codigo_da_disciplina": "codigo_disciplina",
             "frequencia_percentual": "frequencia", "id_turma": "turma_id"}
    return alias.get(nome, nome)


def obrigatorio(dados: dict, campo: str, minimo: int = 1, maximo: int = 120) -> str:
    valor = texto(dados.get(campo))
    if not minimo <= len(valor) <= maximo:
        raise DadosInvalidos(f"{campo}: deve conter de {minimo} a {maximo} caracteres")
    return valor


def numero(dados: dict, campo: str, minimo: float, maximo: float) -> float:
    valor = texto(dados.get(campo)).replace("%", "").replace(" ", "").replace(",", ".")
    if not valor:
        raise DadosInvalidos(f"{campo}: preenchimento obrigatório")
    try:
        resultado = float(valor)
    except ValueError as exc:
        raise DadosInvalidos(f"{campo}: informe um número válido") from exc
    if not math.isfinite(resultado) or not minimo <= resultado <= maximo:
        raise DadosInvalidos(f"{campo}: deve estar entre {minimo:g} e {maximo:g}")
    return resultado


def validar_aluno(dados: dict) -> dict:
    matricula = obrigatorio(dados, "matricula", 1, 30)
    nome = obrigatorio(dados, "nome", 3, 120)
    email = obrigatorio(dados, "email", 5, 120).lower()
    if not EMAIL.fullmatch(email):
        raise DadosInvalidos("email: formato inválido")
    bruto = texto(dados.get("turma_id"))
    if not re.fullmatch(r"[0-9]+", bruto) or int(bruto) <= 0:
        raise DadosInvalidos("turma_id: informe um inteiro maior que zero")
    return {"matricula": matricula, "nome": nome, "email": email, "turma_id": int(bruto)}


# Validação das notas por atividade: academico.pontos e RepositorioAcademico.salvar_notas.
