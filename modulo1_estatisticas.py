import math
import numpy as np


class ModuloEstatisticaAcademica:
    """Módulo 1 de Caio Fábio, com correções de zero e ausência de dados.

    Dispersão populacional (divisor n): descrevemos todo o recorte disponível.
    """
    @staticmethod
    def calcular_estatisticas_lista(valores):
        validos=[float(v) for v in valores if v is not None and math.isfinite(float(v))]
        if not validos:
            return dict.fromkeys(['media','mediana','variancia','desvio_padrao'],None) | {'total_registros':0}
        arr=np.array(validos)
        return {'media':float(np.mean(arr)), 'mediana':float(np.median(arr)),
                'variancia':float(np.var(arr)), 'desvio_padrao':float(np.std(arr)),
                'total_registros':len(validos)}

    @classmethod
    def analisar_desempenho_aluno(cls,aluno):
        e=cls.calcular_estatisticas_lista(list(aluno.notas.values()))
        return {'id_aluno':aluno.id_aluno,'nome':aluno.nome,'matricula':aluno.matricula,
                'cr':e['media'],'mediana_notas':e['mediana'],'desvio_padrao_notas':e['desvio_padrao'],
                'total_disciplinas':e['total_registros'],'frequencia':aluno.calcular_frequencia_global()}

    @classmethod
    def analisar_desempenho_turma(cls,turma):
        e=cls.calcular_estatisticas_lista([a.calcular_cr() for a in turma.alunos if a.notas])
        return {'id_turma':turma.id_turma,'nome_turma':turma.nome,'total_alunos':len(turma.alunos),
                'media_geral_turma':e['media'],'mediana_turma':e['mediana'],
                'desvio_padrao_turma':e['desvio_padrao'],'variancia_turma':e['variancia'],
                'outliers':cls.identificar_outliers_turma(turma)}

    @staticmethod
    def identificar_outliers_turma(turma):
        alunos=[a for a in turma.alunos if a.notas]
        medias=[a.calcular_cr() for a in alunos]
        resultado={'destaques_positivos':[],'alertas_desempenho':[]}
        if len(medias)<3 or np.std(medias)==0:
            return resultado
        centro,desvio=np.mean(medias),np.std(medias)
        for a in alunos:
            cr=a.calcular_cr()
            if cr>centro+1.5*desvio:
                resultado['destaques_positivos'].append({'nome':a.nome,'cr':cr})
            elif cr<centro-1.5*desvio:
                resultado['alertas_desempenho'].append({'nome':a.nome,'cr':cr})
        return resultado
