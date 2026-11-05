import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
from langchain_core.messages import AIMessage

from simpa.assistente import AssistenteIndisponivel
from simpa.assistente_agente import (Consultas,conversar,guardar_conversa,recuperar_conversa,pede_consulta,
    renderizar_markdown,validar_resposta,validar_escopo,_conversas)
from simpa.repositorio import PermissaoNegada


class AgenteAcademico(unittest.TestCase):
    def setUp(self):
        _conversas.clear()
        self.aluno={'id':1,'perfil':'aluno','aluno_id':7}

    def test_markdown_renderiza_e_bloqueia_html_e_javascript(self):
        html=renderizar_markdown('**Nota**\n\n- Revisar\n\n<script>alert(1)</script>\n\n[abrir](javascript:alert(1))')
        self.assertIn('<strong>Nota</strong>',html)
        self.assertIn('<li>Revisar</li>',html)
        self.assertNotIn('<script>',html)
        self.assertNotIn('href="javascript:',html)

    def test_tabela_markdown(self):
        self.assertIn('<table>',renderizar_markdown('| VA | Nota |\n| --- | --- |\n| VA1 | 70 |'))

    def test_consulta_de_dados_diferente_de_capacidades(self):
        self.assertFalse(pede_consulta('O que você pode me responder sobre notas?'))
        self.assertTrue(pede_consulta('Qual é minha nota em Álgebra?'))

    def test_apresentacao_de_valores_arredondados(self):
        c=Consultas(self.aluno,{})
        r=c.fonte('Frequência','/minhas-notas',{'frequencia':100*2/3,'r_quadrado':0.001})
        self.assertEqual(r['dados']['frequencia'],66.67)
        self.assertEqual(r['dados']['r_quadrado'],0.001)

    def test_r2_nao_vira_medida_de_confiabilidade_futura(self):
        c=Consultas(self.aluno,{})
        c.fonte('Previsão','/minhas-notas',{'r_quadrado':0.001})
        with self.assertRaises(AssistenteIndisponivel):
            validar_resposta('A confiabilidade é baixa, pois o R² é 0,001. [S1]',c)
        validar_resposta('O R² é 0,001: descreve ajuste ao histórico, não precisão futura. [S1]',c)

    def test_historia_isolada_por_conta_sessao_e_filtros(self):
        cid,dono,_=recuperar_conversa(self.aluno,{},'sessao1')
        guardar_conversa(cid,dono,[('user','Álgebra'),('assistant','Vamos consultar.')])
        _,_,h=recuperar_conversa(self.aluno,{'conversa_id':cid},'sessao1')
        self.assertEqual(h[0][1],'Álgebra')
        for u,e,s in [({'id':2,'perfil':'aluno','aluno_id':8},{},'sessao1'),(self.aluno,{},'sessao2'),(self.aluno,{'va':1},'sessao1')]:
            with self.assertRaises(PermissaoNegada):recuperar_conversa(u,{**e,'conversa_id':cid},s)

    def test_aluno_nao_tem_ferramenta_dataset(self):
        c=Consultas(self.aluno,{})
        self.assertNotIn('consultar_dataset',c.ferramentas())
        with self.assertRaises(PermissaoNegada):c.dataset()

    def test_bloqueia_dados_e_fontes_inventados(self):
        c=Consultas(self.aluno,{})
        c.fonte('Boletim','/minhas-notas',{'nota':13.97,'escala':100})
        self.assertEqual(validar_resposta('Sua nota parcial é **13,97** de 100. [S1]',c),'Sua nota parcial é **13,97** de 100. [S1]')
        for t in ['Sua nota é 99,99. [S1]','Nota 13,97. [S9]','Nota 13,97 sem fonte.']:
            with self.assertRaises(AssistenteIndisponivel):validar_resposta(t,c)

    def test_capacidades_sem_consulta_nao_recebe_boletim(self):
        llm=unittest.mock.MagicMock()
        llm.bind_tools.return_value.bind.return_value.invoke.return_value=AIMessage('Posso consultar **notas**, frequência e pendências. Qual disciplina você quer ver?')
        with patch('simpa.assistente_agente.validar_escopo'),patch('simpa.assistente_agente.modelo',return_value=llm):
            r=conversar(self.aluno,{'pergunta':'O que você pode me responder?'},'s1')
        self.assertEqual(r['fontes'],[])
        self.assertIn('<strong>notas</strong>',r['resposta_html'])
        prompt=llm.bind_tools.return_value.bind.return_value.invoke.call_args.args[0][0].content
        self.assertIn('Não consulte nem apresente notas',prompt)

    def test_execucao_de_ferramenta_e_uso_do_resultado(self):
        c=Consultas(self.aluno,{})
        primeira=AIMessage('',tool_calls=[{'name':'consultar_regras','args':{},'id':'t1','type':'tool_call'}])
        segunda=AIMessage('A média final exige as três VAs encerradas. [S1]')
        llm=unittest.mock.MagicMock()
        llm.bind_tools.return_value.bind.return_value.invoke.side_effect=[primeira,segunda]
        def regras():return c.fonte('Regras','/minhas-notas',{'regra':'exige as três VAs encerradas'})
        with patch('simpa.assistente_agente.validar_escopo'),patch('simpa.assistente_agente.modelo',return_value=llm),patch.object(Consultas,'regras',side_effect=regras):
            # Compartilha somente os resultados fictícios desta instância para esta verificação.
            with patch('simpa.assistente_agente.Consultas',return_value=c):
                r=conversar(self.aluno,{'pergunta':'Como calculo a média final?'},'s1')
        self.assertEqual(r['fontes'][0]['nome'],'Regras')
        mensagens=llm.bind_tools.return_value.bind.return_value.invoke.call_args.args[0]
        self.assertTrue(any(m.type=='tool' for m in mensagens))

    def test_ferramenta_desconhecida_nao_e_executada(self):
        llm=unittest.mock.MagicMock()
        llm.bind_tools.return_value.bind.return_value.invoke.return_value=AIMessage('',tool_calls=[
            {'name':'executar_sql','args':{'sql':'DELETE FROM alunos'},'id':'x','type':'tool_call'}])
        with patch('simpa.assistente_agente.validar_escopo'),patch('simpa.assistente_agente.modelo',return_value=llm):
            with self.assertRaises(PermissaoNegada):conversar(self.aluno,{'pergunta':'oi'},'s1')

    def test_prompt_md_editado_e_lido_na_proxima_pergunta(self):
        llm=unittest.mock.MagicMock()
        llm.bind_tools.return_value.bind.return_value.invoke.return_value=AIMessage('Olá! Como posso ajudar?')
        with TemporaryDirectory() as d:
            p=Path(d)/'estilo.md';p.write_text('Estilo curto de teste',encoding='utf-8')
            with patch('simpa.assistente_agente.PROMPT',p),patch('simpa.assistente_agente.validar_escopo'),patch('simpa.assistente_agente.modelo',return_value=llm):
                conversar(self.aluno,{'pergunta':'oi'},'s1')
                self.assertIn('Estilo curto de teste',llm.bind_tools.return_value.bind.return_value.invoke.call_args.args[0][0].content)
                p.write_text('Novo estilo de teste',encoding='utf-8')
                conversar(self.aluno,{'pergunta':'olá'},'s1')
                self.assertIn('Novo estilo de teste',llm.bind_tools.return_value.bind.return_value.invoke.call_args.args[0][0].content)

    def test_continuacao_atualiza_consulta_mantendo_disciplina_e_va(self):
        cid,dono,_=recuperar_conversa(self.aluno,{},'s1')
        guardar_conversa(cid,dono,[('user','Álgebra'),('assistant','Nota anterior.')],
                         {'base':'curso','disciplina_id':5,'va':1,'aluno_id':7})
        c=Consultas(self.aluno,{})
        def construir(u,e):c.entrada=e;return c
        def consultar():return c.fonte('Frequência atual','/minhas-notas',{'frequencia':80})
        llm=unittest.mock.MagicMock()
        llm.bind_tools.return_value.bind.return_value.invoke.return_value=AIMessage('Sua frequência é **80,00%**. [S1]')
        with patch('simpa.assistente_agente.validar_escopo'),patch('simpa.assistente_agente.modelo',return_value=llm),patch('simpa.assistente_agente.Consultas',side_effect=construir),patch.object(c,'academico',side_effect=consultar) as atualiza:
            r=conversar(self.aluno,{'pergunta':'E minha frequência?','conversa_id':cid},'s1')
        atualiza.assert_called_once()
        self.assertEqual(c.entrada['disciplina_id'],5)
        self.assertEqual(c.entrada['va'],1)
        self.assertIn('80,00%',r['mensagem'])


if __name__=='__main__':unittest.main()
