"""Histórico sintético: cálculos puros e integração somente em banco descartável."""
import os
import unittest
from contextlib import closing
from statistics import mean, median, pvariance
from uuid import uuid4

import db
from analise_historica import analisar_historico
from app import criar_app
from importacao.validacoes import DadosInvalidos
from importar_dataset_professor import importar, ler_dataset
from preparar_banco import preparar


def exemplo():
    def registro(aluno, ano, semestre, final, parcial=None, frequencia=None):
        return dict(aluno_id=aluno, ano_letivo=ano, semestre_letivo=semestre, numero_periodo=1,
                    nota_final=final, nota_parcial=parcial, frequencia_percentual=frequencia,
                    situacao='EM_CURSO' if final is None else 'APROVADO')
    return {'fonte': {'curso': 'Exemplo', 'sintetico': True},
            'alunos': [{'aluno_id': i, 'nome_sintetico': f'Aluno {i}', 'codigo_academico': str(i)} for i in (1, 2)],
            'registros': [registro(1, 2025, 1, 60, frequencia=80), registro(1, 2025, 1, 80, frequencia=100),
                          registro(1, 2025, 2, 80), registro(1, 2026, 1, None, 0, 0),
                          registro(2, 2026, 1, None), registro(1, 2026, 2, 100)]}


class AnaliseDataset(unittest.TestCase):
    def test_zero_ausencia_e_frequencia(self):
        a = analisar_historico(exemplo(), '2026-1')
        self.assertEqual(a['indicadores']['media'], 0)
        self.assertEqual(a['indicadores']['frequencia_media'], 0)
        self.assertEqual(a['cobertura']['notas_ausentes'], 1)
        self.assertEqual(a['tipo_nota'], 'parcial')

    def test_regressao_sem_vazamento_de_semestres_futuros(self):
        a = analisar_historico(exemplo(), '2025-2', 1)
        self.assertEqual([r['media'] for r in a['serie']], [70, 80])
        self.assertEqual(a['previsao']['previsao'], 90)
        self.assertEqual(a['previsao']['semestre_estimado'], '2026-1')
        self.assertEqual(a['previsao']['tendencia'], 'melhora')

    def test_nao_inventa_historico_de_aluno_sem_registros(self):
        a = analisar_historico(exemplo(), '2025-1', 2)
        self.assertEqual(a['indicadores']['total_registros'], 0)
        self.assertIsNone(a['indicadores']['media'])
        self.assertEqual(a['previsao']['status'], 'dados_insuficientes')

    def test_recusa_filtros_inexistentes(self):
        for params in [('2027-1', None), ('2026-1', 999), ('2026-1', 'abc')]:
            with self.subTest(params=params), self.assertRaises(DadosInvalidos):
                analisar_historico(exemplo(), *params)

    def test_tentativas_sao_registros_distintos_e_frequencia_nao_e_inventada(self):
        a = analisar_historico(exemplo(), '2025-1')
        self.assertEqual(a['estatisticas']['media'], 70)
        self.assertEqual(a['estatisticas']['variancia'], 100)
        self.assertEqual(a['indicadores']['total_registros'], 2)
        self.assertEqual(a['indicadores']['frequencia_media'], 90)

    def test_copia_de_referencia_integral(self):
        manifesto, digest, tabelas = ler_dataset()
        contagens = {nome: len(linhas) for nome, campos, linhas in tabelas}
        self.assertTrue(manifesto['sintetico'])
        self.assertEqual(len(tabelas), 15)
        self.assertEqual(contagens['alunos'], 120)
        self.assertEqual(contagens['registros_academicos'], 2949)
        self.assertEqual(len(digest), 64)


@unittest.skipUnless(os.getenv('SIMPA_TEST_DSN'), 'Configure somente banco descartável em SIMPA_TEST_DSN')
class IntegracaoDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        preparar()
        cls.antes = cls.contagens_curso()
        cls.carga = importar()
        cls.app = criar_app({'TESTING': True, 'SECRET_KEY': 'dataset-testes-isolados'})
        with closing(db.conectar()) as con, con, con.cursor() as cur:
            cur.execute("INSERT INTO simpa.alunos(matricula,nome_completo) VALUES (%s,'Aluno isolado') RETURNING id", ('DS-' + uuid4().hex[:12],))
            aid = cur.fetchone()['id']
            cls.usuarios = {}
            for perfil in ('professor', 'aluno'):
                cur.execute('INSERT INTO simpa.usuarios(nome,matricula,senha_hash,perfil,aluno_id) VALUES (%s,%s,%s,%s,%s) RETURNING id',
                            ('Teste dataset', 'DS-' + uuid4().hex[:12], 'nao-usado-em-login', perfil, aid if perfil == 'aluno' else None))
                cls.usuarios[perfil] = cur.fetchone()['id']

    @classmethod
    def contagens_curso(cls):
        with closing(db.conectar()) as con, con.cursor() as cur:
            resultado = {}
            for nome in ('alunos', 'usuarios', 'notas_atividades', 'regras_va', 'avaliacoes'):
                cur.execute(f'SELECT count(*) AS total FROM simpa.{nome}')
                resultado[nome] = cur.fetchone()['total']
            return resultado

    def cliente(self, perfil=None):
        c = self.app.test_client()
        if perfil:
            with c.session_transaction() as s:
                s['usuario_id'] = self.usuarios[perfil]
        return c

    def test_idempotencia_sem_alterar_curso(self):
        antes = self.contagens_curso()
        self.assertEqual(importar()['status'], 'ja_importado')
        self.assertEqual(self.contagens_curso(), antes)
        self.assertEqual(antes['notas_atividades'], self.antes['notas_atividades'])
        self.assertEqual(antes['regras_va'], self.antes['regras_va'])

    def test_api_compara_calculo_independente_do_csv(self):
        c = self.cliente('professor')
        resposta = c.get('/api/dataset-professor?semestre=2026-2')
        self.assertEqual(resposta.status_code, 200)
        a = resposta.get_json()
        with closing(db.conectar()) as con, con.cursor() as cur:
            cur.execute('''SELECT r.nota_parcial FROM simpa_dataset.registros_academicos r
                JOIN simpa_dataset.turmas t USING(turma_id) WHERE t.ano_letivo=2026 AND t.semestre_letivo=2''')
            valores = [float(r['nota_parcial']) for r in cur.fetchall() if r['nota_parcial'] is not None]
        self.assertEqual(a['indicadores']['total_registros'], 600)
        self.assertEqual(a['indicadores']['total_alunos'], 120)
        self.assertAlmostEqual(a['estatisticas']['media'], mean(valores))
        self.assertAlmostEqual(a['estatisticas']['mediana'], median(valores))
        self.assertAlmostEqual(a['estatisticas']['variancia'], pvariance(valores))

    def test_perfis_e_filtros(self):
        self.assertEqual(self.cliente().get('/api/dataset-professor').status_code, 401)
        self.assertEqual(self.cliente('aluno').get('/api/dataset-professor').status_code, 403)
        self.assertEqual(self.cliente('aluno').get('/dashboard/dataset-professor').status_code, 403)
        c = self.cliente('professor')
        self.assertEqual(c.get('/dashboard/dataset-professor').status_code, 200)
        self.assertEqual(c.get('/api/dataset-professor?aluno_id=99999999').status_code, 422)
        self.assertEqual(c.get('/api/dataset-professor?semestre=VA2').status_code, 422)

    def test_historico_real_do_dataset_tem_previsao_executavel(self):
        c = self.cliente('professor')
        alunos = c.get('/api/dataset-professor').get_json()['opcoes']['alunos']
        encontrou = False
        for aluno in alunos:
            a = c.get(f'/api/dataset-professor?aluno_id={aluno["aluno_id"]}').get_json()
            if a['previsao']['status'] == 'ok':
                self.assertTrue(0 <= a['previsao']['previsao'] <= 100)
                self.assertGreaterEqual(len(a['serie']), 2)
                encontrou = True
                break
        self.assertTrue(encontrou)
