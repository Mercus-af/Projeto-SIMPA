import unittest
from decimal import Decimal
from simpa.academico import ResultadoVA,calcular_media_final,pontos
from simpa.importacao.validacoes import DadosInvalidos
from simpa.modulo1_estatisticas import ModuloEstatisticaAcademica as E
from simpa.modulo2_parte1 import ModuloCorrelacaoFrequenciaNota as C
from simpa.modulo2_regressao import ModuloRegressao as P


class RegrasVA(unittest.TestCase):
    def cenario(self):
        regra={'va':1,'max_atividades':30,'max_a360':10,'max_vrau':30,'max_afe':30,'fechada':True,'provisoria':True}
        atividades=[];notas={}
        for i in range(6):
            for tipo,maximo in [('APS',2),('DAILY',3)]:
                aid=len(atividades)+1
                atividades.append({'id':aid,'tipo':tipo,'maximo':maximo})
                notas[aid]=Decimal(str(maximo))*Decimal('.8')
        for tipo,maximo,nota in [('A360',10,8),('VRAU',30,22),('AFE',30,26)]:
            aid=len(atividades)+1;atividades.append({'id':aid,'tipo':tipo,'maximo':maximo});notas[aid]=nota
        return regra,atividades,notas

    def test_exemplo_80_pontos(self):
        r,a,n=self.cenario();v=ResultadoVA(r,a,n).calcular()
        self.assertEqual(v['nota'],80)
        self.assertEqual(v['componentes']['APS']['obtido']+v['componentes']['DAILY']['obtido'],24)
        self.assertTrue(v['fechada'])

    def test_zero_nao_e_pendente(self):
        r,a,n=self.cenario();n[1]=0;n[2]=None
        v=ResultadoVA(r,a,n).calcular()
        self.assertEqual(v['pendencias'],1);self.assertEqual(v['atividades'][0]['nota'],0)
        self.assertIsNone(v['nota']);self.assertIsNotNone(v['parcial'])

    def test_sem_lancamentos_nao_vira_zero(self):
        r,a,n=self.cenario();v=ResultadoVA(r,a,{}).calcular()
        self.assertIsNone(v['parcial']);self.assertEqual(v['status'],'Pendente')

    def test_planejamento_incompleto_nao_fecha(self):
        r,a,n=self.cenario();v=ResultadoVA(r,a[2:],n).calcular()
        self.assertFalse(v['planejada']);self.assertFalse(v['fechada'])

    def test_final_exige_tres_vas_encerradas(self):
        valores=[{'va':1,'nota':80,'fechada':True},{'va':2,'nota':70,'fechada':True},{'va':3,'nota':90,'fechada':True}]
        self.assertEqual(calcular_media_final(valores),80)
        self.assertIsNone(calcular_media_final(valores[:2]))
        valores[2]={'va':3,'nota':None,'fechada':False}
        self.assertIsNone(calcular_media_final(valores))

    def test_limites_e_numeros_invalidos(self):
        self.assertEqual(pontos('2,00',maximo=2),2)
        for valor in ['NaN','Infinity',-1,2.01,True,'0.001']:
            with self.subTest(valor=valor),self.assertRaises(DadosInvalidos):pontos(valor,maximo=2)

    def test_dispersao_e_regressao_na_escala_100(self):
        e=E.calcular_estatisticas_lista([0,50,100])
        self.assertEqual(e['media'],50);self.assertAlmostEqual(e['variancia'],5000/3)
        self.assertAlmostEqual(C.calcular_correlacao_frequencia_nota([70,80,90],[40,60,80]),1)
        self.assertEqual(P.prever_proxima_nota([60,70],[1,2],nota_maxima=100)['previsao'],80)


if __name__=='__main__':unittest.main()
