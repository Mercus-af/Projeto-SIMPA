"""Referência do grupo na escala antiga. Não usado sem confirmar o critério do curso."""
import math


class MotorRiscoAcademico:

    """SIMPA — classificação explicável de risco acadêmico.

        Regras do Ciclo 2:
        - alto: média < 6 ou frequência < 75%;
        - médio: média < 7 ou frequência < 80%, desde que não seja alto;
        - baixo: média >= 7 e frequência >= 80%.
        Sem frequência, nunca a inventamos. Se a média < 6, alto risco é conclusivo;
        caso contrário, a classificação permanece indeterminada.
    """

    @staticmethod
    def classificar_risco(media, frequencia=None):
        if media is None:
            return {'nivel': 'indeterminado', 'classificacao': 'Indeterminado',
                    'justificativa': 'Média não informada.', 'media': None,
                    'frequencia': frequencia}
        media = float(media)
        if not math.isfinite(media) or not 0 <= media <= 10:
            raise ValueError('Média deve estar entre 0 e 10')
        if frequencia is not None:
            frequencia = float(frequencia)
            if not math.isfinite(frequencia) or not 0 <= frequencia <= 100:
                raise ValueError('Frequência deve estar entre 0 e 100%')
        motivos = []
        if media < 6:
            motivos.append(f'média {media:.2f} abaixo de 6,0')
        if frequencia is not None and frequencia < 75:
            motivos.append(f'frequência {frequencia:.1f}% abaixo de 75%')
        if motivos:
            nivel, rotulo = 'alto', 'Alto Risco'
        elif frequencia is None:
            nivel, rotulo = 'indeterminado', 'Indeterminado'
            motivos.append(
                'frequência não informada; não é possível descartar risco por faltas')
            if media < 7:
                motivos.insert(0, f'média {media:.2f} na faixa de risco médio')
        elif media < 7 or frequencia < 80:
            nivel, rotulo = 'medio', 'Médio Risco'
            if media < 7:
                motivos.append(f'média {media:.2f} entre 6,0 e 6,9')
            if frequencia < 80:
                motivos.append(f'frequência {frequencia:.1f}% entre 75% e 79%')
        else:
            nivel, rotulo = 'baixo', 'Baixo Risco'
            motivos.append(
                f'média {media:.2f} >= 7,0 e frequência {frequencia:.1f}% >= 80%')
        return {'nivel': nivel, 'classificacao': rotulo,
                'justificativa': f'{rotulo}: ' + '; '.join(motivos) + '.',
                'media': round(media, 2), 'frequencia': frequencia}

    @classmethod
    def classificar_aluno(cls, aluno):
        """Integra com Aluno do SIMPA (calcular_cr/calcular_frequencia_global)."""
        media = aluno.calcular_cr()
        frequencia = aluno.calcular_frequencia_global()
        resultado = cls.classificar_risco(media, frequencia)
        resultado['id_aluno'] = aluno.id_aluno
        return resultado


classificar_risco = MotorRiscoAcademico.classificar_risco
