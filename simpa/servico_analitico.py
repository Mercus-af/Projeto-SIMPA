"""Resultados por VA na escala 0–100, preservando pendências e permissões."""
from collections import defaultdict
from statistics import mean

from simpa.academico import ResultadoVA,calcular_media_final
from simpa.modulo1_estatisticas import ModuloEstatisticaAcademica as Estatistica
from simpa.modulo2_parte1 import ModuloCorrelacaoFrequenciaNota as Correlacao
from simpa.modulo2_regressao import ModuloRegressao as Regressao


def frequencia_global(registros):
    if not registros:return None
    aulas=sum(f['aulas'] for f in registros)
    return sum(f['presencas'] for f in registros)/aulas*100 if aulas else None


def resultados_disciplinas(base):
    notas=defaultdict(dict)
    for n in base['notas_componentes']:notas[n['aluno_id']][n['atividade_id']]=n['nota']
    atividades=defaultdict(list)
    for a in base['atividades']:atividades[(a['turma_id'],a['disciplina_id'],a['va'])].append(a)
    regras={(r['turma_id'],r['disciplina_id'],r['va']):r for r in base['regras']}
    alunos={a['id']:a for a in base['alunos']}
    saida=[]
    for oferta in base['ofertas']:
        t,d=oferta['turma_id'],oferta['disciplina_id']
        for m in base['matriculas']:
            if m['turma_id']!=t:continue
            aid=m['aluno_id'];vas=[]
            for va in (1,2,3):
                chave=(t,d,va)
                if chave in regras:vas.append(ResultadoVA(regras[chave],atividades[chave],notas[aid]).calcular())
            concluidas=[v['nota'] for v in vas if v['fechada']]
            saida.append({'aluno_id':aid,'nome':alunos[aid]['nome'],'matricula':alunos[aid]['matricula'],
                'turma_id':t,'turma':oferta['turma'],'disciplina_id':d,'disciplina':oferta['disciplina'],
                'codigo':oferta['codigo'],'vas':vas,'media_final':calcular_media_final(vas),
                'media_vas_concluidas':mean(concluidas) if concluidas else None,
                'criterio_aprovacao':None})
    return saida


def analisar(base,disciplina=None,va=2):
    resultados=resultados_disciplinas(base)
    if disciplina is not None:resultados=[r for r in resultados if r['disciplina_id']==int(disciplina)]
    notas=[];por_aluno=defaultdict(list);pendencias=defaultdict(int)
    for r in resultados:
        v=next((v for v in r['vas'] if v['va']==va),None)
        if not v:continue
        notas.append({'alunoId':r['aluno_id'],'disciplinaId':r['disciplina_id'],'turmaId':r['turma_id'],
                      'va':va,'nota':v['parcial'],'fechada':v['fechada']})
        if v['parcial'] is not None:por_aluno[r['aluno_id']].append(v['parcial'])
        pendencias[r['aluno_id']]+=v['pendencias']
    ids={r['aluno_id'] for r in resultados}
    frequencias=[f for f in base['frequencias'] if f['va']==va and
                 (disciplina is None or f['disciplina_id']==int(disciplina)) and f['aluno_id'] in ids]
    resumos=[]
    for a in base['alunos']:
        if a['id'] not in ids:continue
        fs=[f for f in frequencias if f['aluno_id']==a['id']]
        resumos.append({'id':a['id'],'nome':a['nome'],'matricula':a['matricula'],'turma':a['turma'],
            'turmaId':a['turma_id'],'media':mean(por_aluno[a['id']]) if por_aluno[a['id']] else None,
            'frequencia':frequencia_global(fs),'pendencias':pendencias[a['id']],
            'situacao':'Critério de aprovação pendente'})
    valores=[n['nota'] for n in notas if n['nota'] is not None]
    pares=[r for r in resumos if r['media'] is not None and r['frequencia'] is not None]
    pearson=Correlacao.calcular_correlacao_frequencia_nota([r['frequencia'] for r in pares],[r['media'] for r in pares])
    previsoes=[]
    for r in resultados:
        concluidas=[v for v in r['vas'] if v['fechada']]
        p=Regressao.prever_proxima_nota([v['nota'] for v in concluidas],[v['va'] for v in concluidas],nota_maxima=100)
        previsoes.append({'aluno_id':r['aluno_id'],'turma_id':r['turma_id'],'disciplina_id':r['disciplina_id'],**p})
    return {'va':va,'escala':100,'indicadores':{'totalAlunos':len(resumos),
        'mediaGeral':mean(valores) if valores else None,'frequenciaMedia':frequencia_global(frequencias),
        'pendencias':sum(pendencias.values()),'notasLancadas':len(valores)},
        'estatisticas':Estatistica.calcular_estatisticas_lista(valores),
        'resumos':resumos,'resultados':resultados,'recorte':{'notas':notas,'va':va},
        'correlacao':{'coeficiente_correlacao_r':pearson,'total_amostras':len(pares),
                      'interpretacao':Correlacao.interpretar_coeficiente(pearson)},
        'previsoes':previsoes,'criterio_aprovacao':None,
        'observacao':'Composição provisória. Pontos parciais não são notas finais; a média final exige VA1, VA2 e VA3 encerradas.'}
