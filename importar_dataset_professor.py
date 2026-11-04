"""Carga do material sintético do professor, sem conversão para as VAs do curso."""
import argparse
import csv
import hashlib
import json
from contextlib import closing
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

import db
from importacao.validacoes import DadosInvalidos

PASTA = Path(__file__).resolve().parent
REFERENCIA = PASTA / 'data' / 'dataset_professor'


def ler_dataset(pasta=None):
    """Confere os arquivos da edição recebida antes de abrir uma transação."""
    pasta = Path(pasta) if pasta else REFERENCIA
    if (pasta / 'CSV Normalizado').is_dir():
        pasta = pasta / 'CSV Normalizado'
    manifesto = json.loads((REFERENCIA / 'manifesto.json').read_text(encoding='utf-8'))
    tabelas = []
    assinatura = hashlib.sha256()
    for tabela in manifesto['tabelas']:
        nome = tabela['nome']
        arquivo = pasta / (nome + '.csv')
        if not arquivo.is_file():
            raise DadosInvalidos(f'Arquivo ausente: {arquivo.name}.')
        conteudo = arquivo.read_bytes()
        digest = hashlib.sha256(conteudo).hexdigest()
        if digest != tabela['sha256']:
            raise DadosInvalidos(f'{arquivo.name}: conteúdo diferente da edição de referência. Nenhum dado foi importado.')
        assinatura.update(nome.encode('utf-8') + b'\0' + bytes.fromhex(digest))
        campos = tabela['campos']
        with arquivo.open(encoding='utf-8-sig', newline='') as entrada:
            leitor = csv.DictReader(entrada)
            if leitor.fieldnames != list(campos):
                raise DadosInvalidos(f'{arquivo.name}: cabeçalho incompatível.')
            linhas = []
            for numero, linha in enumerate(leitor, 2):
                valores = []
                for campo, regra in campos.items():
                    valor = linha.get(campo)
                    if valor is None or (valor == '' and not regra['nulo']):
                        raise DadosInvalidos(f'{arquivo.name}, linha {numero}: {campo} obrigatório.')
                    if valor == '':
                        valores.append(None)
                        continue
                    try:
                        if regra['tipo'] == 'INTEGER':
                            valor = int(valor)
                        elif regra['tipo'] == 'REAL':
                            valor = Decimal(valor)
                            if not valor.is_finite():
                                raise ValueError
                    except (ValueError, InvalidOperation):
                        raise DadosInvalidos(f'{arquivo.name}, linha {numero}: {campo} inválido.')
                    valores.append(valor)
                linhas.append(tuple(valores))
        if len(linhas) != tabela['linhas']:
            raise DadosInvalidos(f'{arquivo.name}: quantidade de registros incompatível.')
        tabelas.append((nome, list(campos), linhas))
    return manifesto, assinatura.hexdigest(), tabelas


def importar(pasta=None):
    manifesto, digest, tabelas = ler_dataset(pasta)
    with closing(db.conectar()) as con, con, con.cursor() as cur:
        cur.execute((PASTA / 'sql' / '004_dataset_professor.sql').read_text(encoding='utf-8'))
        cur.execute('SELECT sha256 FROM simpa_dataset.cargas WHERE identificador=%s', (manifesto['identificador'],))
        anterior = cur.fetchone()
        if anterior:
            if anterior['sha256'] != digest:
                raise DadosInvalidos('Já existe outra edição do dataset. A base existente foi preservada.')
            for nome, campos, linhas in tabelas:
                cur.execute(f'SELECT count(*) AS total FROM simpa_dataset.{nome}')
                if cur.fetchone()['total'] != len(linhas):
                    raise DadosInvalidos(f'A carga existente de {nome} está incompleta. Nenhuma reposição automática foi feita.')
            return {'status': 'ja_importado', 'tabelas': len(tabelas), 'sha256': digest}
        for nome, campos, linhas in tabelas:
            # Nomes de tabela/coluna vêm exclusivamente do manifesto incluído no projeto.
            execute_values(cur, f'INSERT INTO simpa_dataset.{nome} ({",".join(campos)}) VALUES %s', linhas)
        cur.execute('INSERT INTO simpa_dataset.cargas(identificador,sha256,origem) VALUES (%s,%s,%s)',
                    (manifesto['identificador'], digest, manifesto['origem']))
    return {'status': 'importado', 'tabelas': len(tabelas),
            'registros': sum(len(linhas) for nome, campos, linhas in tabelas), 'sha256': digest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pasta', help='Pasta recebida do professor ou sua pasta CSV Normalizado; padrão: cópia incluída no projeto.')
    args = parser.parse_args()
    try:
        print(json.dumps(importar(args.pasta), ensure_ascii=False))
    except (DadosInvalidos, psycopg2.Error) as erro:
        print(str(erro) if isinstance(erro, DadosInvalidos) else f'Falha PostgreSQL ({type(erro).__name__}); a transação foi desfeita.')
        raise SystemExit(1)
