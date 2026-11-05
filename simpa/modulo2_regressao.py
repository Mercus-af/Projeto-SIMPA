import math
from statistics import mean


class ModuloRegressao:

    """SIMPA — regressão linear simples para estimar a próxima nota.

        Use notas de avaliações ordenadas cronologicamente (não notas de alunos distintos).
        A previsão é uma estimativa estatística, não uma garantia de desempenho.
    """

    @staticmethod
    def prever_proxima_nota(notas, periodos=None, nota_minima=0.0, nota_maxima=100.0):
        """Ajusta y = a*x+b por mínimos quadrados e prevê o período seguinte.

        Retorna dicionário JSON-serializável. Exige >=2 observações e períodos
        distintos. Sem `periodos`, assume avaliações sequenciais 1, 2, 3, ...
        """
        notas = list(notas)
        if periodos is None:
            periodos = list(range(1, len(notas) + 1))
        else:
            periodos = list(periodos)
        if len(notas) != len(periodos):
            raise ValueError('notas e periodos precisam ter o mesmo tamanho')
        if nota_minima >= nota_maxima:
            raise ValueError('Intervalo de notas inválido')
        pares = []
        for x, y in zip(periodos, notas):
            if x is None or y is None:
                continue
            x, y = float(x), float(y)
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError('Valores devem ser finitos')
            if not nota_minima <= y <= nota_maxima:
                raise ValueError('Nota fora do intervalo permitido')
            pares.append((x, y))
        if len(pares) < 2:
            return {'status': 'dados_insuficientes', 'previsao': None,
                    'justificativa': 'São necessárias pelo menos duas avaliações.'}
        pares.sort(key=lambda p: p[0])
        xs, ys = zip(*pares)
        if len(set(xs)) != len(xs):
            raise ValueError('Os períodos não podem se repetir')
        media_x, media_y = mean(xs), mean(ys)
        sxx = sum((x-media_x)**2 for x in xs)
        sxy = sum((x-media_x)*(y-media_y) for x, y in pares)
        inclinacao = sxy/sxx
        intercepto = media_y-inclinacao*media_x
        passo = xs[-1]-xs[-2]
        proximo_periodo = xs[-1]+passo
        previsao_bruta = inclinacao*proximo_periodo+intercepto
        previsao = min(nota_maxima, max(nota_minima, previsao_bruta))
        sq_total = sum((y-media_y)**2 for y in ys)
        sq_residuos = sum((y-(inclinacao*x+intercepto))**2 for x, y in pares)
        r2 = None if sq_total == 0 else max(0.0, 1-sq_residuos/sq_total)
        tendencia = 'melhora' if inclinacao > 1e-9 else 'queda' if inclinacao < -1e-9 else 'estável'
        return {
            'status': 'ok', 'total_avaliacoes': len(pares),
            'proximo_periodo': proximo_periodo,
            'previsao': round(previsao, 2),
            'previsao_sem_limite': round(previsao_bruta, 2),
            'inclinacao': round(inclinacao, 4),
            'intercepto': round(intercepto, 4),
            'r_quadrado': None if r2 is None else round(r2, 4),
            'tendencia': tendencia,
            'justificativa': f'Tendência de {tendencia} ({inclinacao:+.2f} ponto(s) por unidade de período).',
            'observacao': 'Projeção linear indicativa; dados escassos e mudanças no desempenho reduzem sua confiabilidade.'
        }

    @classmethod
    def prever_nota_aluno(cls, aluno, notas_historicas=None, periodos=None):
        """Recebe histórico explícito; não trata notas de disciplinas como sequência temporal."""
        if notas_historicas is None:
            notas_historicas = getattr(aluno, 'historico_notas', None)
        if notas_historicas is None:
            return {'status': 'dados_insuficientes', 'previsao': None,
                    'justificativa': 'Histórico cronológico de avaliações não informado.'}
        return cls.prever_proxima_nota(notas_historicas, periodos)


# Alias útil para uso direto
prever_proxima_nota = ModuloRegressao.prever_proxima_nota
