import numpy as np


class ModuloCorrelacaoFrequenciaNota:
    """Pearson: associação linear observada, sem conclusão de causalidade."""
    @staticmethod
    def calcular_correlacao_frequencia_nota(frequencias,notas):
        if len(frequencias)!=len(notas):
            raise ValueError('As listas precisam ter o mesmo tamanho')
        pares=[(float(f),float(n)) for f,n in zip(frequencias,notas)
               if f is not None and n is not None and np.isfinite(float(f)) and np.isfinite(float(n))]
        if len(pares)<2:
            return None
        x,y=np.array(pares).T
        if np.std(x)==0 or np.std(y)==0:
            return None
        return float(np.corrcoef(x,y)[0,1])

    @classmethod
    def analisar_impacto_frequencia_turma(cls,turma):
        pares=[(a.calcular_frequencia_global(),a.calcular_cr()) for a in turma.alunos if a.notas]
        pares=[(f,n) for f,n in pares if f is not None and n is not None]
        r=cls.calcular_correlacao_frequencia_nota([p[0] for p in pares],[p[1] for p in pares])
        return {'id_turma':turma.id_turma,'nome_turma':turma.nome,'total_amostras':len(pares),
                'coeficiente_correlacao_r':r,'interpretacao':cls.interpretar_coeficiente(r)}

    @staticmethod
    def interpretar_coeficiente(r):
        if r is None:
            return 'Correlação indefinida: são necessários dois pares válidos e variação nas duas medidas.'
        intensidade='forte' if abs(r)>=0.7 else 'moderada' if abs(r)>=0.3 else 'fraca'
        sentido='positiva' if r>0 else 'negativa' if r<0 else 'nula'
        return f'Associação linear {intensidade}, {sentido}, neste recorte. Correlação não comprova causalidade.'
