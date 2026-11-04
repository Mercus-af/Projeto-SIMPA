"""Estatística do dataset: cada registro representa uma tentativa em uma turma."""
from collections import defaultdict
from statistics import mean

from academico import inteiro
from importacao.validacoes import DadosInvalidos
from modulo1_estatisticas import ModuloEstatisticaAcademica as Estatistica
from modulo2_parte1 import ModuloCorrelacaoFrequenciaNota as Correlacao
from modulo2_regressao import ModuloRegressao as Regressao


def indice_semestre(registro):
    return registro['ano_letivo'] * 2 + registro['semestre_letivo'] - 1


def rotulo_semestre(indice):
    ano, semestre = divmod(int(indice), 2)
    return f'{ano}-{semestre + 1}'


def media_disponivel(valores):
    validos = [v for v in valores if v is not None]
    return mean(validos) if validos else None


def analisar_historico(base, semestre=None, aluno_id=None):
    registros = base['registros']
    semestres = sorted({indice_semestre(r) for r in registros})
    if not semestres:
        raise DadosInvalidos('O dataset não possui registros acadêmicos.')
    opcoes_semestres = [rotulo_semestre(s) for s in semestres]
    semestre = semestre or opcoes_semestres[-1]
    if semestre not in opcoes_semestres:
        raise DadosInvalidos('Semestre não disponível no dataset.')
    indice = semestres[opcoes_semestres.index(semestre)]
    if aluno_id not in (None, ''):
        aluno_id = inteiro(aluno_id, 'aluno_id')
        if aluno_id not in {a['aluno_id'] for a in base['alunos']}:
            raise DadosInvalidos('Aluno não encontrado no dataset sintético.')
    else:
        aluno_id = None
    selecionados = [r for r in registros if aluno_id is None or r['aluno_id'] == aluno_id]
    recorte = [r for r in selecionados if indice_semestre(r) == indice]
    parcial = any(r['situacao'] == 'EM_CURSO' for r in recorte)
    campo = 'nota_parcial' if parcial else 'nota_final'
    valores = [r[campo] for r in recorte if r[campo] is not None]
    fs = [r['frequencia_percentual'] for r in recorte if r['frequencia_percentual'] is not None]
    ids = {r['aluno_id'] for r in recorte}
    por_aluno = defaultdict(list)
    for r in recorte:
        por_aluno[r['aluno_id']].append(r)
    resumos = []
    for aluno in base['alunos']:
        linhas = por_aluno[aluno['aluno_id']]
        if not linhas:
            continue
        resumos.append({**aluno, 'media': media_disponivel([r[campo] for r in linhas]),
                        'frequencia': media_disponivel([r['frequencia_percentual'] for r in linhas]),
                        'registros': len(linhas)})
    pares = [r for r in resumos if r['media'] is not None and r['frequencia'] is not None]
    pearson = Correlacao.calcular_correlacao_frequencia_nota(
        [r['frequencia'] for r in pares], [r['media'] for r in pares])
    grupos = defaultdict(list)
    for r in recorte:
        if r[campo] is not None:
            grupos[r['numero_periodo']].append(r[campo])
    comparacao = [{'periodo': p, 'media': mean(ns), 'registros': len(ns)} for p, ns in sorted(grupos.items())]

    # Histórico individual: somente notas finais anteriores/até o semestre consultado.
    # Não usa o score pronto, desfechos futuros nem disciplinas distintas como VAs.
    serie = []
    previsao = None
    if aluno_id is not None:
        historico = defaultdict(list)
        for r in selecionados:
            s = indice_semestre(r)
            if s <= indice and r['situacao'] != 'EM_CURSO' and r['nota_final'] is not None:
                historico[s].append(r['nota_final'])
        serie = [{'semestre': rotulo_semestre(s), 'indice': s, 'media': mean(ns), 'registros': len(ns)}
                 for s, ns in sorted(historico.items())]
        previsao = Regressao.prever_proxima_nota([s['media'] for s in serie], [s['indice'] for s in serie])
        if previsao['status'] == 'ok':
            previsao['semestre_estimado'] = rotulo_semestre(previsao['proximo_periodo'])
    estatisticas = Estatistica.calcular_estatisticas_lista(valores)
    if valores:
        interpretacao = (f'{semestre}: média {estatisticas["media"]:.2f} e desvio-padrão '
                        f'{estatisticas["desvio_padrao"]:.2f} pontos em {len(valores)} registros com nota {"parcial" if parcial else "final"}.')
    else:
        interpretacao = 'Sem notas disponíveis para este aluno neste semestre.'
    if parcial:
        interpretacao += ' Resultados parciais não comprovam queda em relação aos semestres concluídos.'
    return {'fonte': base['fonte'], 'filtros': {'semestre': semestre, 'aluno_id': aluno_id},
            'opcoes': {'semestres': opcoes_semestres, 'alunos': base['alunos']},
            'tipo_nota': 'parcial' if parcial else 'final', 'escala': 100,
            'indicadores': {'total_alunos': len(ids), 'media': estatisticas['media'],
                            'frequencia_media': mean(fs) if fs else None, 'total_registros': len(recorte)},
            'cobertura': {'notas_disponiveis': len(valores), 'notas_ausentes': len(recorte)-len(valores),
                          'frequencias_disponiveis': len(fs), 'frequencias_ausentes': len(recorte)-len(fs)},
            'estatisticas': estatisticas, 'comparacao': comparacao, 'alunos': resumos,
            'correlacao': {'coeficiente': pearson, 'amostras': len(pares),
                           'interpretacao': Correlacao.interpretar_coeficiente(pearson)},
            'serie': serie, 'previsao': previsao, 'interpretacao': interpretacao,
            'metodo': 'Notas: média por registro (tentativa em turma), sem substituir ausências por zero. '
                      'Frequência: média simples dos percentuais disponíveis; não há contagem de aulas/presenças nesta análise. '
                      'Série individual: médias de notas finais por semestre; não representa evolução na mesma disciplina.'}
