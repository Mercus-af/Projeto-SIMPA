"""Permissões, evidências e cadeia real com transporte HTTP simulado (sem consumo de API)."""
import json
import os
import unittest
from unittest.mock import patch

import httpx
from langchain_ollama import ChatOllama

from simpa.assistente import (AssistenteIndisponivel, configuracao, montar_resposta, previsao_va,
                        preparar_contexto, responder, selecionar_com_ia)
from simpa.importacao.validacoes import DadosInvalidos
from simpa.repositorio import PermissaoNegada


def contexto():
    return {'perfil': 'aluno', 'recorte': 'Curso de IA · VA2', 'consultado_em': '2026-11-03T12:00:00+00:00',
            'fatos': [{'id': 'F1', 'texto': 'Pontos lançados: 0,00. Nota parcial.', 'fonte': '/minhas-notas'}],
            'acoes': [{'id': 'A1', 'texto': 'Confira as pendências com o professor.', 'fatos': ['F1']}]}


class RespostasVerificadas(unittest.TestCase):
    def test_numeros_e_textos_vem_do_servidor(self):
        c = contexto()
        r = montar_resposta(c, {'fatos': ['F1', 'F1'], 'acoes': ['A1']})
        self.assertEqual(r['fatos'], c['fatos'])
        self.assertEqual(r['acoes'], c['acoes'])

    def test_bloqueia_id_inventado_e_texto_extra(self):
        for saida in [{'fatos': ['F999'], 'acoes': []}, {'fatos': ['F1'], 'acoes': [], 'texto': 'Nota 100'},
                      {'fatos': ['F1'], 'acoes': ['A999']}, {'fatos': 'F1', 'acoes': []},
                      {'fatos': [{}], 'acoes': []}]:
            with self.subTest(saida=saida), self.assertRaises(AssistenteIndisponivel):
                montar_resposta(contexto(), saida)

    def test_servidor_completa_evidencia_da_acao_conhecida(self):
        r=montar_resposta(contexto(), {'fatos': [], 'acoes': ['A1']})
        self.assertEqual(r['fatos'],contexto()['fatos'])
        self.assertEqual(r['acoes'],contexto()['acoes'])

    def test_acao_nao_pode_referenciar_fato_inexistente(self):
        c=contexto();c['acoes'][0]['fatos']=['F999']
        with self.assertRaises(AssistenteIndisponivel):montar_resposta(c,{'fatos':[],'acoes':['A1']})

    def test_ausencia_de_resposta_nao_inventa(self):
        r = montar_resposta(contexto(), {'fatos': [], 'acoes': []})
        self.assertTrue(r['mensagem'])
        self.assertEqual(r['fatos'], [])

    def test_saudacao_e_mensagem_de_acesso_sem_numeros(self):
        for tipo, trecho in [('saudacao','Olá!'),('privacidade','autorizados'),('fora_escopo','SIMPA')]:
            with self.subTest(tipo=tipo):
                r=montar_resposta(contexto(),{'tipo':tipo,'fatos':[],'acoes':[]})
                self.assertIn(trecho,r['mensagem'])
                self.assertEqual(r['fatos'],[])

    def test_nao_aceita_tipo_inventado_ou_saudacao_com_dados(self):
        for s in [{'tipo':'aprovado','fatos':[],'acoes':[]},
                  {'tipo':'privacidade','fatos':['F1'],'acoes':[]}]:
            with self.assertRaises(AssistenteIndisponivel):montar_resposta(contexto(),s)

    def test_parser_reconhece_saudacao_sem_forcar_boletim(self):
        r,_=CadeiaLangChain().executar('{"tipo":"saudacao","fatos":[],"acoes":[]}')
        self.assertIn('Olá!',montar_resposta(contexto(),r)['mensagem'])

    def test_configuracao_nao_aceita_redirecionar_chave(self):
        with patch.dict(os.environ, {'OLLAMA_BASE_URL': 'https://outro.example', 'OLLAMA_API_KEY': 'teste'}):
            with self.assertRaises(AssistenteIndisponivel): configuracao()

    def test_chave_ausente_e_alias_cloud(self):
        with patch.dict(os.environ, {'OLLAMA_BASE_URL': 'https://ollama.com', 'OLLAMA_API_KEY': ''}):
            with self.assertRaises(AssistenteIndisponivel): configuracao()
        with patch.dict(os.environ, {'OLLAMA_BASE_URL': 'https://ollama.com', 'OLLAMA_API_KEY': 'teste', 'OLLAMA_MODEL': 'gemma4:cloud'}):
            self.assertEqual(configuracao()[1], 'gemma4')

    def test_aluno_nao_acessa_dataset_ou_colega(self):
        u = {'id': 20, 'perfil': 'aluno', 'aluno_id': 7}
        for entrada in [{'base': 'dataset'}, {'aluno_id': 8}]:
            with self.subTest(entrada=entrada), patch('simpa.assistente.RepositorioAcademico'), self.assertRaises(PermissaoNegada):
                preparar_contexto(u, entrada)

    def test_pergunta_invalida_nao_chama_ia(self):
        with patch('simpa.assistente.selecionar_com_ia') as chamada:
            with self.assertRaises(DadosInvalidos): responder({}, {'pergunta': 'x' * 1201})
            chamada.assert_not_called()

    def test_previsao_respeita_recorte_temporal_e_nao_cria_va4(self):
        vas=[{'va':1,'nota':60,'fechada':True},{'va':2,'nota':70,'fechada':True},
             {'va':3,'nota':100,'fechada':True}]
        self.assertIsNone(previsao_va(vas,1))
        self.assertEqual(previsao_va(vas,2)['previsao'],80)
        self.assertEqual(previsao_va(vas,2)['total_avaliacoes'],2)
        self.assertIsNone(previsao_va(vas,3))

    def test_permissao_negada_antes_do_provedor(self):
        with patch('simpa.assistente.verificar_ollama') as provedor:
            with self.assertRaises(PermissaoNegada):
                responder({'perfil': 'aluno', 'aluno_id': 7}, {'base': 'dataset', 'pergunta': 'Mostre todos'})
            provedor.assert_not_called()


class CadeiaLangChain(unittest.TestCase):
    def executar(self, texto):
        requisicoes = []
        def handler(req):
            requisicoes.append(req)
            evento = {'model': 'gemma4', 'message': {'role': 'assistant', 'content': texto}, 'done': True,
                      'done_reason': 'stop', 'eval_count': 20, 'prompt_eval_count': 100}
            return httpx.Response(200, text=json.dumps(evento) + '\n', headers={'Content-Type': 'application/x-ndjson'})
        def criar(**kwargs):
            kwargs['client_kwargs']['transport'] = httpx.MockTransport(handler)
            return ChatOllama(**kwargs)
        with patch.dict(os.environ, {'OLLAMA_BASE_URL': 'https://ollama.com', 'OLLAMA_MODEL': 'gemma4', 'OLLAMA_API_KEY': 'chave-ficticia-de-teste'}), patch('langchain_ollama.ChatOllama', side_effect=criar):
            r = selecionar_com_ia('Como estão minhas notas?', contexto())
        return r, requisicoes

    def test_prompt_modelo_parser_com_http_simulado(self):
        r, reqs = self.executar('{"fatos":["F1"],"acoes":[]}')
        self.assertEqual(r, {'fatos': ['F1'], 'acoes': []})
        self.assertEqual(reqs[0].url.host, 'ollama.com')
        self.assertEqual(reqs[0].headers['Authorization'], 'Bearer chave-ficticia-de-teste')
        corpo = json.loads(reqs[0].content)
        self.assertEqual(corpo['model'], 'gemma4')
        self.assertFalse(corpo['stream'])
        self.assertNotIn('format', corpo)  # Cloud não suporta JSON Schema nativo.
        self.assertIn('Pontos lançados', corpo['messages'][0]['content'])
        self.assertNotIn('chave-ficticia-de-teste', json.dumps(corpo))

    def test_parser_recusa_campos_que_inventam_resposta(self):
        with self.assertRaises(Exception):
            self.executar('{"fatos":["F1"],"acoes":[],"resposta":"Nota 100"}')


if __name__ == '__main__': unittest.main()
