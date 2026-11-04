"""Regras do curso: componentes em pontos, VAs e média final por disciplina."""
from decimal import Decimal,InvalidOperation

from importacao.validacoes import DadosInvalidos

TIPOS=('APS','DAILY','A360','VRAU','AFE')
DISCIPLINAS_IA=(
    ('ALG','Álgebra Linear e Aplicações'),
    ('DOO','Desenvolvimento Orientado a Objetos'),
    ('DSO','Design de Soluções'),
    ('ESTM','Estatística Aplicada e Modelagem de Soluções'),
    ('FRSI','Fundamentos de Redes e Segurança da Informação'),
)


def pontos(valor,campo='nota',maximo=100,permitir_vazio=False):
    if valor is None or str(valor).strip()=='':
        if permitir_vazio:return None
        raise DadosInvalidos(f'{campo}: preenchimento obrigatório')
    try:
        if isinstance(valor,bool):raise InvalidOperation
        numero=Decimal(str(valor).strip().replace(',','.'))
        if not numero.is_finite() or numero<0 or numero>Decimal(str(maximo)):
            raise InvalidOperation
        if numero!=numero.quantize(Decimal('0.01')):
            raise DadosInvalidos(f'{campo}: use no máximo duas casas decimais')
        return numero
    except (InvalidOperation,ValueError):
        raise DadosInvalidos(f'{campo}: informe um número entre 0 e {maximo}')


def inteiro(valor,campo,minimo=1,maximo=None):
    try:
        if isinstance(valor,bool):raise ValueError
        n=int(str(valor))
        if n<minimo or (maximo is not None and n>maximo):raise ValueError
        return n
    except (ValueError,TypeError):
        raise DadosInvalidos(f'{campo}: informe um inteiro válido')


class ResultadoVA:
    def __init__(self,regra,atividades,notas):
        self.regra=regra
        self.atividades=atividades
        self.notas=notas

    def calcular(self):
        componentes={tipo:{'obtido':None,'maximo':0,'pendentes':0} for tipo in TIPOS}
        valores=[]
        detalhes=[]
        for a in self.atividades:
            nota=self.notas.get(a['id'])
            maximo=Decimal(str(a['maximo']))
            c=componentes[a['tipo']]
            c['maximo']+=maximo
            if nota is None:c['pendentes']+=1
            else:
                nota=Decimal(str(nota))
                valores.append(nota)
                c['obtido']=(c['obtido'] or Decimal(0))+nota
            detalhes.append({**a,'nota':None if nota is None else float(nota)})
        distribuido=sum(Decimal(str(a['maximo'])) for a in self.atividades if a['tipo'] in ('APS','DAILY'))
        planejada=distribuido==Decimal(str(self.regra['max_atividades']))
        for tipo,campo in [('A360','max_a360'),('VRAU','max_vrau'),('AFE','max_afe')]:
            planejada=planejada and componentes[tipo]['maximo']==Decimal(str(self.regra[campo]))
        pendentes=sum(c['pendentes'] for c in componentes.values())
        completa=planejada and pendentes==0
        parcial=sum(valores) if valores else None
        fechada=bool(self.regra['fechada']) and completa
        return {'va':self.regra['va'],'parcial':None if parcial is None else float(parcial),
            'nota':float(parcial) if fechada else None,'fechada':fechada,
            'completa':completa,'planejada':planejada,'pendencias':pendentes,
            'status':'Concluída' if fechada else 'Parcial' if valores else 'Pendente',
            'maximo':100,'atividades_distribuidas':float(distribuido),
            'atividades_previstas':float(self.regra['max_atividades']),
            'componentes':{t:{k:float(v) if isinstance(v,Decimal) else v for k,v in c.items()} for t,c in componentes.items()},
            'atividades':detalhes,'provisoria':bool(self.regra['provisoria'])}


def calcular_media_final(resultados):
    por_va={r['va']:r for r in resultados}
    if set(por_va)!={1,2,3} or not all(r['fechada'] and r['nota'] is not None for r in por_va.values()):
        return None
    return sum(r['nota'] for r in por_va.values())/3
