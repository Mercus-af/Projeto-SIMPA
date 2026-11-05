"""Leitura segura de planilhas e CSV, sem escrever arquivos recebidos no disco."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from pathlib import Path

from .validacoes import normalizar_coluna, texto

MAX_ARQUIVO = 2 * 1024 * 1024
MAX_LINHAS = 10_000
CAMPOS = {
    "alunos": ("matricula", "nome", "email", "turma_id"),
    "registros": ("matricula", "atividade_id", "nota"),
}


class ArquivoInvalido(ValueError):
    """Arquivo ausente, inválido ou incompatível com o modelo."""


def validar_cabecalho(cabecalho: list, tipo: str) -> list[str]:
    nomes = [normalizar_coluna(nome) for nome in cabecalho]
    if not nomes or not any(nomes):
        raise ArquivoInvalido("O arquivo não contém cabeçalho.")
    if any(not nome for nome in nomes):
        raise ArquivoInvalido("Há colunas sem nome no cabeçalho.")
    if len(nomes) != len(set(nomes)):
        raise ArquivoInvalido("O cabeçalho contém colunas repetidas.")
    faltando = [coluna for coluna in CAMPOS[tipo] if coluna not in nomes]
    if faltando:
        raise ArquivoInvalido("Colunas obrigatórias ausentes: " + ", ".join(faltando))
    return nomes


def _csv(conteudo: bytes) -> Iterator[tuple[int, list]]:
    try:
        entrada = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ArquivoInvalido("CSV deve estar em UTF-8. Exporte novamente usando UTF-8.") from exc
    amostra = entrada[:4096]
    try:
        separador = csv.Sniffer().sniff(amostra, delimiters=",;\t").delimiter
    except csv.Error:
        separador = max((";", ",", "\t"), key=lambda item: amostra.splitlines()[0].count(item)) if amostra else ","
    leitor = csv.reader(io.StringIO(entrada, newline=""), delimiter=separador, strict=True)
    try:
        for linha in leitor:
            yield leitor.line_num, linha
    except (csv.Error, UnicodeError) as exc:
        raise ArquivoInvalido(f"CSV malformado: {exc}") from exc


def _excel(conteudo: bytes) -> Iterator[tuple[int, list]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ArquivoInvalido("Instale openpyxl para importar arquivos XLSX.") from exc
    try:
        planilha = load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    except Exception as exc:
        raise ArquivoInvalido("Arquivo XLSX inválido ou corrompido.") from exc
    try:
        aba = planilha.active
        for numero, linha in enumerate(aba.iter_rows(values_only=True), start=1):
            yield numero, list(linha)
            if numero > MAX_LINHAS + 1:
                raise ArquivoInvalido(f"Limite de {MAX_LINHAS} registros por arquivo excedido.")
    finally:
        planilha.close()


def extrair_linhas(nome_arquivo: str, conteudo: bytes, tipo: str) -> Iterator[tuple[int, dict | None, str | None]]:
    """Emite (linha, valores, erro estrutural); ignora linhas totalmente vazias."""
    if tipo not in CAMPOS:
        raise ArquivoInvalido("Tipo inválido. Escolha alunos ou registros.")
    extensao = Path(nome_arquivo).suffix.lower()
    if extensao not in {".csv", ".xlsx"}:
        raise ArquivoInvalido("Formato não permitido. Utilize .csv ou .xlsx.")
    if not conteudo:
        raise ArquivoInvalido("O arquivo está vazio.")
    if len(conteudo) > MAX_ARQUIVO:
        raise ArquivoInvalido("Arquivo muito grande. Limite de 2 MB.")
    leitor = _csv(conteudo) if extensao == ".csv" else _excel(conteudo)
    try:
        numero_cabecalho, colunas = next(leitor)
    except StopIteration as exc:
        raise ArquivoInvalido("O arquivo está vazio.") from exc
    nomes = validar_cabecalho(colunas, tipo)
    contagem = 0
    for numero, linha in leitor:
        if not any(texto(campo) for campo in linha):
            continue
        contagem += 1
        if contagem > MAX_LINHAS:
            raise ArquivoInvalido(f"Limite de {MAX_LINHAS} registros por arquivo excedido.")
        if len(linha) > len(nomes) and any(texto(valor) for valor in linha[len(nomes):]):
            yield numero, None, "Linha possui mais valores do que colunas."
        else:
            valores = dict(zip(nomes, list(linha)[:len(nomes)] + [""] * max(0, len(nomes)-len(linha))))
            yield numero, valores, None
