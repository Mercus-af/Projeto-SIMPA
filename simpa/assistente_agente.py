"""Assistente com consultas limitadas, conversa por conta e resposta em Markdown."""
from collections import OrderedDict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from threading import Lock
import time
import unicodedata
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langsmith import tracing_context
from pydantic import ValidationError

from simpa.academico import inteiro
from simpa.analise_historica import analisar_historico
from simpa.dataset_professor import RepositorioDatasetProfessor
from simpa.importacao.validacoes import DadosInvalidos
from simpa.repositorio import PermissaoNegada, RepositorioAcademico, numeros
from simpa.servico_analitico import analisar

PROMPT = Path(__file__).resolve().parents[1] / 'prompts/assistente_academico.md'
_conversas = OrderedDict()
_trava = Lock()
TTL = 1800


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.casefold()) if not unicodedata.combining(c))


def pede_consulta(pergunta):
    q=normalizar(pergunta)
    if re.search(r'(o que|como|quais).{0,35}(pode|consegue|ajuda|funciona)',q):return False
    return bool(re.search(r'nota|frequencia|pendencia|media|previs|aps|daily|a360|vrau|afe|aluno|turma|disciplina',q))


def validar_escopo(usuario, entrada):
    if entrada.get('base', 'curso') not in ('curso', 'dataset'):
        raise DadosInvalidos('Base inválida.')
    if entrada.get('base') == 'dataset' and usuario['perfil'] != 'professor':
        raise PermissaoNegada('O dataset do professor não está disponível para alunos.')
    r = RepositorioAcademico(usuario)
    if entrada.get('base', 'curso') == 'curso':
        for campo in ('turma_id', 'disciplina_id', 'aluno_id'):
            if entrada.get(campo) in (None, ''): continue
            valor = inteiro(entrada[campo], campo)
            if campo == 'aluno_id': r.exigir_aluno(valor)
            elif campo == 'turma_id' and valor not in {o['turma_id'] for o in r.listar_ofertas()}:
                raise PermissaoNegada('Turma fora do seu acesso.')
            elif campo == 'disciplina_id' and valor not in {o['disciplina_id'] for o in r.listar_ofertas()}:
                raise PermissaoNegada('Disciplina fora do seu acesso.')


def dono_conversa(usuario, entrada, sessao):
    filtros = {k: entrada.get(k) for k in ('base', 'va', 'turma_id', 'disciplina_id', 'aluno_id', 'semestre')}
    dados = [usuario['id'], usuario['perfil'], usuario.get('aluno_id'), sessao, filtros]
    return sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()


def recuperar_conversa(usuario, entrada, sessao):
    dono = dono_conversa(usuario, entrada, sessao)
    cid = entrada.get('conversa_id')
    if cid is not None and (not isinstance(cid, str) or len(cid) > 64):
        raise DadosInvalidos('Conversa inválida.')
    with _trava:
        agora = time.monotonic()
        for chave in list(_conversas):
            if agora - _conversas[chave]['tempo'] > TTL: del _conversas[chave]
        if cid in _conversas:
            conversa = _conversas[cid]
            if conversa['dono'] != dono:
                raise PermissaoNegada('Esta conversa não pertence à conta e aos filtros atuais.')
            return cid, dono, list(conversa['mensagens'])
    return uuid4().hex, dono, []


def guardar_conversa(cid, dono, mensagens, selecao=None):
    with _trava:
        _conversas[cid] = {'dono': dono, 'tempo': time.monotonic(), 'mensagens': mensagens[-8:], 'selecao':selecao or {}}
        _conversas.move_to_end(cid)
        while len(_conversas) > 128: _conversas.popitem(last=False)


class Consultas:
    def __init__(self, usuario, entrada):
        self.usuario, self.entrada = usuario, entrada
        self.fontes, self.resultados = [], []
        self.chamadas = 0
        self.tentativas = 0
        self.ultima_selecao={}

    def fonte(self, nome, url, dados):
        self.chamadas += 1
        if self.chamadas > 6: raise DadosInvalidos('Limite de consultas desta pergunta atingido.')
        sid = f'S{len(self.fontes)+1}'
        self.fontes.append({'id': sid, 'nome': nome, 'url': url})
        def apresentar(v,campo=''):
            if isinstance(v,float):return round(v,4 if campo in ('r_quadrado','inclinacao','coeficiente','coeficiente_correlacao_r') else 2)
            if isinstance(v,dict):return {k:apresentar(x,k) for k,x in v.items()}
            if isinstance(v,list):return [apresentar(x,campo) for x in v]
            return v
        dados=json.loads(json.dumps(apresentar(numeros(dados)),ensure_ascii=False,default=str))
        self.resultados.append(dados)
        return {'fonte': sid, 'dados': dados}

    def vinculos(self, busca='', base='curso', pagina=1):
        pagina = inteiro(pagina, 'pagina', 1, 20)
        busca = normalizar(str(busca)[:150])
        if base == 'dataset':
            if self.usuario['perfil'] != 'professor': raise PermissaoNegada('Área exclusiva de professores.')
            base_dados = RepositorioDatasetProfessor(self.usuario).dados()
            if base_dados is None: raise DadosInvalidos('Dataset ainda não importado.')
            itens = [{'tipo': 'aluno_sintetico', 'aluno_id': a['aluno_id'], 'nome': a['nome_sintetico']}
                     for a in base_dados['alunos']]
        elif base == 'curso':
            r = RepositorioAcademico(self.usuario)
            itens = [{'tipo': 'oferta', **{k: o[k] for k in ('turma_id', 'turma', 'disciplina_id', 'disciplina', 'codigo')}}
                     for o in r.listar_ofertas()]
            itens += [{'tipo': 'aluno', **{k: a[k] for k in ('aluno_id', 'nome', 'turma_id', 'turma')}}
                      for a in r.listar_matriculas()]
        else: raise DadosInvalidos('Base inválida.')
        itens = [i for i in itens if busca in normalizar(' '.join(str(v) for v in i.values()))]
        inicio = (pagina-1)*20
        return self.fonte('Vínculos autorizados', '/turmas' if self.usuario['perfil'] == 'professor' else '/minhas-notas',
                          {'resultados': itens[inicio:inicio+20], 'total': len(itens), 'pagina': pagina, 'por_pagina': 20})

    def academico(self, aluno_id=None, disciplina_id=None, turma_id=None, va=None, pagina=1):
        from simpa.assistente import previsao_va
        r = RepositorioAcademico(self.usuario)
        valores = {'aluno_id': aluno_id, 'disciplina_id': disciplina_id, 'turma_id': turma_id, 'va': va}
        for k, v in valores.items():
            if v is None: valores[k] = self.entrada.get(k) if self.entrada.get('base','curso')=='curso' else None
        aluno_id, disciplina_id, turma_id = (valores[k] for k in ('aluno_id', 'disciplina_id', 'turma_id'))
        valor_va=valores['va'] or 2
        if isinstance(valor_va,str):valor_va=valor_va.strip().upper().removeprefix('VA').strip()
        va = inteiro(valor_va, 'va', 1, 3)
        if self.usuario['perfil'] == 'aluno':
            if aluno_id is not None and inteiro(aluno_id, 'aluno_id') != self.usuario['aluno_id']:
                raise PermissaoNegada('Você só pode consultar o próprio boletim.')
            aluno_id = self.usuario['aluno_id']
        if disciplina_id is not None and inteiro(disciplina_id, 'disciplina_id') not in {d['id'] for d in r.listar_disciplinas()}:
            raise PermissaoNegada('Disciplina fora do seu acesso.')
        base = r.dados_dashboard(turma_id=turma_id, aluno_id=aluno_id)
        a = analisar(base, disciplina=disciplina_id, va=va)
        self.ultima_selecao={'base':'curso','aluno_id':aluno_id,'disciplina_id':disciplina_id,'turma_id':turma_id,'va':va}
        pagina = inteiro(pagina, 'pagina', 1, 50)
        alunos = a['resumos'][(pagina-1)*20:pagina*20]
        dados = {'va': va, 'escala': 100, 'indicadores': a['indicadores'], 'estatisticas': a['estatisticas'],
                 'alunos': [{k: x[k] for k in ('id','nome','media','frequencia','pendencias')} for x in alunos],
                 'total_alunos': len(a['resumos']), 'pagina': pagina, 'por_pagina': 20,
                 'criterio_aprovacao': 'não informado; não é possível classificar aprovação ou risco',
                 'observacao': 'Pontos parciais não são nota final. Ausência não é zero. Pendência não comprova falta de entrega.'}
        dados['disciplinas'] = []
        for did in sorted({x['disciplina_id'] for x in a['resultados']}):
            resultados = [x for x in a['resultados'] if x['disciplina_id'] == did]
            ns = [v['parcial'] for x in resultados for v in x['vas'] if v['va'] == va and v['parcial'] is not None]
            dados['disciplinas'].append({'id':did,'nome':resultados[0]['disciplina'],
                'media_pontos_lancados':sum(ns)/len(ns) if ns else None,'resultados_com_nota':len(ns)})
        if aluno_id is not None:
            dados['boletim'] = []
            for x in a['resultados'][:15]:
                vas = [{k:v[k] for k in ('va','parcial','nota','status','fechada','pendencias','componentes')}
                       for v in x['vas']]
                atividades = [{k: at.get(k) for k in ('titulo','tipo','nota','maximo','data_atividade')}
                              for v in x['vas'] if v['va'] == va for at in v['atividades'][:40]]
                dados['boletim'].append({'aluno':x['nome'],'disciplina':x['disciplina'],'turma':x['turma'],
                    'vas':vas,'media_final':x['media_final'],'previsao':previsao_va(x['vas'],va),
                    'atividades_va_consultada':atividades})
            dados['total_ofertas'] = len(a['resultados'])
        url = f'/alunos/{aluno_id}' if self.usuario['perfil']=='professor' and aluno_id else '/dashboard'
        if self.usuario['perfil']=='aluno': url='/minhas-notas'
        return self.fonte(f'Curso de IA · VA{va}', url, dados)

    def dataset(self, aluno_id=None, semestre=None):
        if self.usuario['perfil']!='professor': raise PermissaoNegada('O dataset é exclusivo de professores.')
        base = RepositorioDatasetProfessor(self.usuario).dados()
        if base is None: raise DadosInvalidos('Dataset ainda não importado.')
        if aluno_id is None and self.entrada.get('base')=='dataset':aluno_id=self.entrada.get('aluno_id')
        a = analisar_historico(base, semestre or self.entrada.get('semestre'), aluno_id)
        self.ultima_selecao={'base':'dataset','aluno_id':a['filtros']['aluno_id'],'semestre':a['filtros']['semestre']}
        dados = {k:v for k,v in a.items() if k not in ('opcoes','alunos')}
        dados['alunos'] = a['alunos'][:20]
        dados['alunos_mostrados'] = min(20,len(a['alunos']))
        dados['total_alunos'] = len(a['alunos'])
        return self.fonte('Dataset fictício do professor', '/dashboard/dataset-professor', dados)

    def regras(self):
        base = RepositorioAcademico(self.usuario).dados_dashboard()
        regras = []
        vistos = set()
        for r in base['regras']:
            campos = ('va','max_atividades','max_a360','max_vrau','max_afe','max_aps','max_daily','provisoria')
            valores = numeros({k:r[k] for k in campos})
            chave = json.dumps(valores,sort_keys=True)
            if chave not in vistos: regras.append(valores); vistos.add(chave)
        return self.fonte('Composição e regras do curso', '/avaliacoes' if self.usuario['perfil']=='professor' else '/minhas-notas',
            {'composicoes_nos_vinculos':regras,'media_final':'(VA1 + VA2 + VA3) / 3; exige três VAs completas e encerradas',
             'aprovacao':'critério ainda não informado','pendencia':'ausência de nota, não significa zero ou falta de entrega',
             'previsao':'mínimo de duas VAs encerradas até a VA consultada; não existe VA4'})

    def ferramentas(self):
        @tool
        def listar_vinculos(busca: str = '', base: str = 'curso', pagina: int = 1) -> dict:
            """Localize pelo nome alunos, turmas e disciplinas autorizados. Busca ignora acentos. Páginas de 20 itens. base=dataset só professor."""
            return self.vinculos(busca,base,pagina)
        @tool
        def consultar_academico(aluno_id: int | None = None, disciplina_id: int | None = None,
                               turma_id: int | None = None, va: int | str | None = None, pagina: int = 1) -> dict:
            """Consulte notas, componentes, atividades, frequência, pendências, estatísticas e previsão. Aluno só acessa seu boletim. IDs devem vir da busca ou da pergunta; filtros omitidos usam seleção atual."""
            return self.academico(aluno_id,disciplina_id,turma_id,va,pagina)
        @tool
        def consultar_dataset(aluno_id: int | None = None, semestre: str | None = None) -> dict:
            """Professor: histórico sintético e previsão por semestre. Exemplo de semestre: 2026-2. IDs são exclusivos desta base."""
            return self.dataset(aluno_id,semestre)
        @tool
        def consultar_regras() -> dict:
            """Consulte no sistema as composições das VAs, valores de APS/Daily/atividades personalizadas/A360/VRAU/AFE e regras de média final e previsão."""
            return self.regras()
        fs = [listar_vinculos,consultar_academico,consultar_regras]
        if self.usuario['perfil']=='professor':fs.append(consultar_dataset)
        return {f.name:f for f in fs}


def modelo(timeout=40):
    from simpa.assistente import configuracao
    url, nome, chave = configuracao()
    return ChatOllama(model=nome,base_url=url,temperature=0.2,num_predict=1800,
        client_kwargs={'timeout':timeout,'trust_env':False,'follow_redirects':False,
                       'headers':{'Authorization':'Bearer '+chave}})


def validar_resposta(texto, consultas):
    from simpa.assistente import AssistenteIndisponivel
    if not texto or len(texto)>16000:raise AssistenteIndisponivel('Não consegui concluir a resposta. Tente uma pergunta mais específica.')
    ids = set(re.findall(r'\[(S\d+)\]',texto))
    if not ids <= {s['id'] for s in consultas.fontes}:
        raise AssistenteIndisponivel('A resposta citou uma fonte inexistente e foi bloqueada.')
    if consultas.fontes and not ids:
        raise AssistenteIndisponivel('A resposta não identificou a consulta usada. Reformule a pergunta.')
    t=normalizar(texto)
    if re.search(r'(confiabilidade|precisao).{0,80}(baixa|alta).{0,100}r(?:2|\^2)',t,re.S):
        raise AssistenteIndisponivel('R² descreve ajuste ao histórico, não comprova confiabilidade futura. Explique apenas o ajuste e as limitações retornadas.')
    # Números devem existir nos resultados, inclusive suas formas de apresentação arredondadas.
    permitidos=set()
    def coletar(v):
        if isinstance(v,bool) or v is None:return
        if isinstance(v,(int,float)):
            permitidos.add(str(v).replace(',','.'))
            for casas in (0,1,2,3,4):permitidos.add(f'{v:.{casas}f}')
        elif isinstance(v,str):permitidos.update(x.replace(',','.') for x in re.findall(r'(?<![\w])\d+(?:[.,]\d+)?',v))
        elif isinstance(v,dict):
            for x in v.values():coletar(x)
        elif isinstance(v,list):
            for x in v:coletar(x)
    coletar(consultas.resultados)
    sem_refs=re.sub(r'\[S\d+\]','',texto)
    sem_listas=re.sub(r'(?m)^\s*\d+[.)]\s+','',sem_refs)
    numeros_texto=set(x.replace(',','.') for x in re.findall(r'(?<![\w])\d+(?:[.,]\d+)?',sem_listas))
    if not numeros_texto <= permitidos:
        raise AssistenteIndisponivel('A resposta trouxe um número que não consegui conferir nos resultados. Tente reformular a pergunta.')
    return texto


def renderizar_markdown(texto):
    from markdown_it import MarkdownIt
    import bleach
    html=MarkdownIt('commonmark',{'html':False}).enable('table').render(texto)
    return bleach.clean(html,tags={'p','br','strong','em','ul','ol','li','h2','h3','h4','blockquote','pre','code',
        'table','thead','tbody','tr','th','td','a','hr'},attributes={'a':['href','title']},protocols=['https','http'],strip=True)


def conversar(usuario, entrada, sessao='', persistir=False):
    from simpa.assistente import AssistenteIndisponivel
    validar_escopo(usuario,entrada)
    if persistir:
        from simpa.chats import RepositorioChats,filtros_chat
        armazenamento=RepositorioChats(usuario)
        chat=armazenamento.obter(entrada['conversa_id']) if entrada.get('conversa_id') else armazenamento.criar(entrada)
        if chat['filtros']!=filtros_chat(entrada):raise DadosInvalidos('Abra um novo chat ao mudar os filtros.')
        cid=str(chat['id']);dono=None
        historico=[(m['papel'],m['texto']) for m in armazenamento.mensagens(cid,8)]
        ultima=chat['selecao']
        validar_escopo(usuario,ultima)
    else:
        cid,dono,historico=recuperar_conversa(usuario,entrada,sessao)
        with _trava:
            ultima=dict(_conversas.get(cid,{}).get('selecao',{}))
    selecao={**entrada,**ultima}
    consultas=Consultas(usuario,selecao)
    ferramentas=consultas.ferramentas()
    filtros={k:selecao.get(k) for k in ('base','va','turma_id','disciplina_id','aluno_id','semestre') if selecao.get(k) is not None}
    sistema=PROMPT.read_text(encoding='utf-8')+'\n\nPerfil confirmado pelo servidor: '+usuario['perfil']+'\nSeleção atual: '+json.dumps(filtros,ensure_ascii=False)
    mensagens=[SystemMessage(sistema)]
    for papel,texto in historico:
        mensagens.append(HumanMessage(texto) if papel=='user' else AIMessage(re.sub(r'\[S\d+\]','',texto)))
    pergunta=entrada['pergunta'].strip()
    mensagens.append(HumanMessage(pergunta))
    # Continuação retoma os identificadores conferidos, mas os valores são lidos de novo.
    if historico and ultima and re.search(r'nota|frequencia|media|previs|pendencia|daily|aps|afe|vrau|a360|nessa|mesma|dele|dela',normalizar(pergunta)):
        nome='consultar_dataset' if ultima.get('base')=='dataset' else 'consultar_academico'
        resultado=consultas.dataset() if nome=='consultar_dataset' else consultas.academico()
        tid=uuid4().hex
        mensagens.append(AIMessage('',tool_calls=[{'name':nome,'args':{},'id':tid,'type':'tool_call'}]))
        mensagens.append(ToolMessage(json.dumps(resultado,ensure_ascii=False,default=str),tool_call_id=tid,name=nome))
    limite=time.monotonic()+100
    texto=''
    with tracing_context(enabled=False):
        for rodada in range(4):
            restante=limite-time.monotonic()
            if restante<=0:raise AssistenteIndisponivel('A consulta demorou demais. Faça uma pergunta mais específica.')
            llm=modelo(min(40,restante)).bind_tools(list(ferramentas.values())).bind(stream=False)
            resposta=llm.invoke(mensagens)
            if not resposta.tool_calls:
                texto=resposta.content if isinstance(resposta.content,str) else ''
                try:
                    recusa=bool(re.search(r'nao (tenho (permissao|acesso)|posso (acessar|exibir|consultar))|(?:apenas|somente).{0,30}(suas proprias|seus proprios|seu proprio)',normalizar(texto)))
                    if pede_consulta(pergunta) and not consultas.fontes and not consultas.tentativas and not recusa and not (texto.rstrip().endswith('?') and len(texto)<450):
                        raise AssistenteIndisponivel('Ainda não foi executada uma consulta para responder sobre esses dados.')
                    validar_resposta(texto,consultas)
                    break
                except AssistenteIndisponivel as exc:
                    if rodada>=3:raise
                    mensagens.append(resposta)
                    mensagens.append(HumanMessage('A verificação do servidor encontrou um problema: '+str(exc)+
                        ' Consulte os dados necessários e corrija a resposta, usando somente os valores e fontes retornados.'))
                    texto=''
                    continue
            mensagens.append(resposta)
            for chamada in resposta.tool_calls:
                nome=chamada['name']
                if nome not in ferramentas:raise PermissaoNegada('Consulta não permitida para esta conta.')
                if consultas.chamadas>=6 or consultas.tentativas>=6:raise AssistenteIndisponivel('Limite de consultas atingido. Especifique aluno e disciplina.')
                consultas.tentativas+=1
                try:
                    resultado=ferramentas[nome].invoke(chamada['args'])
                except ValidationError as exc:
                    resultado={'erro':'Argumentos inválidos para a consulta.',
                        'campos':[{'campo':'.'.join(str(p) for p in e['loc']),'tipo':e['type']}
                                  for e in exc.errors(include_input=False,include_url=False)],
                        'orientacao':'Localize os IDs com listar_vinculos e envie valores nos tipos definidos pela ferramenta.'}
                except (PermissaoNegada,DadosInvalidos) as exc:
                    resultado={'erro':str(exc),'orientacao':'Não invente resultados; respeite a restrição ou peça esclarecimento.'}
                mensagens.append(ToolMessage(json.dumps(resultado,ensure_ascii=False,default=str),tool_call_id=chamada['id'],name=nome))
    texto=validar_resposta(texto,consultas)
    if persistir:
        armazenamento.salvar_turno(cid,pergunta,texto,consultas.fontes,consultas.ultima_selecao or ultima)
    else:
        guardar_conversa(cid,dono,historico+[('user',pergunta),('assistant',texto[:6000])],consultas.ultima_selecao or ultima)
    return {'conversa_id':cid,'mensagem':texto,'resposta_markdown':texto,'resposta_html':renderizar_markdown(texto),
            'fontes':consultas.fontes,'fatos':[],'acoes':[],
            'consultado_em':datetime.now(timezone.utc).isoformat(),
            'recorte':' · '.join(s['nome'] for s in consultas.fontes) or 'Conversa sem consulta de registros',
            'modo':'Gemma com ferramentas de consulta autorizadas'}
