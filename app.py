"""SIMPA: acesso por perfil, avaliações por VA e API com o mesmo escopo das telas."""
import io
import os
import secrets
from datetime import timedelta,date

import psycopg2
from flask import Flask,abort,flash,g,jsonify,redirect,render_template,request,send_file,session,url_for

import db
from academico import inteiro
from autenticacao import autenticar,encerrar_sessao,iniciar_sessao
from importacao.leitura import ArquivoInvalido,MAX_ARQUIVO
from importacao.servico import importar_arquivo
from importacao.validacoes import DadosInvalidos
from repositorio import PermissaoNegada,RepositorioAcademico,numeros
from servico_analitico import analisar
from dataset_professor import RepositorioDatasetProfessor
from analise_historica import analisar_historico


def criar_app(config=None):
    app=Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=MAX_ARQUIVO+65536,SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',PERMANENT_SESSION_LIFETIME=timedelta(hours=4))
    if config:app.config.update(config)

    def repo():return RepositorioAcademico(g.usuario)
    def professor():
        if g.usuario['perfil']!='professor':raise PermissaoNegada('Área exclusiva de professores.')
    def csrf_token():
        if 'csrf' not in session:session['csrf']=secrets.token_hex(24)
        return session['csrf']
    def inteiro_filtro(nome,padrao=None,maximo=None):
        valor=request.args.get(nome)
        return padrao if valor in (None,'') else inteiro(valor,nome,1,maximo)
    def json_entrada():
        dados=request.get_json(silent=True)
        if not isinstance(dados,dict):raise DadosInvalidos('Envie um objeto JSON.')
        return dados
    def contexto_oferta():
        ofertas=repo().listar_ofertas()
        bruto=request.args.get('oferta')
        if bruto:
            partes=bruto.split(':')
            if len(partes)!=2:raise DadosInvalidos('Oferta inválida.')
            oferta=repo().exigir_oferta(*partes)
        else:oferta=ofertas[0] if ofertas else None
        return ofertas,oferta,inteiro_filtro('va',2,3)
    def volta_oferta(t,d,va):
        return redirect(url_for('avaliacoes',oferta=f'{t}:{d}',va=va))

    @app.context_processor
    def contexto():
        usuario=getattr(g,'usuario',None)
        return {'app_name':'SIMPA','usuario':usuario,'usuario_nome':usuario['nome'] if usuario else '',
                'eh_professor':bool(usuario and usuario['perfil']=='professor'),
                'csrf_token':csrf_token,'fmt':lambda v:'—' if v is None else f'{float(v):.2f}'.replace('.',',')}

    @app.before_request
    def proteger():
        g.usuario=None
        if request.endpoint=='static' or request.path=='/saude':return
        uid=session.get('usuario_id')
        if uid:
            g.usuario=db.usuario_por_id(uid)
            if not g.usuario or not g.usuario['ativo']:
                encerrar_sessao();g.usuario=None
        if request.endpoint!='login' and not g.usuario:
            return (jsonify(erro='Faça login para continuar.'),401) if request.path.startswith('/api/') else redirect(url_for('login'))
        if request.method in {'POST','PUT','PATCH','DELETE'} and not app.config.get('CSRF_DESATIVADO',False):
            recebido=request.headers.get('X-CSRF-Token') or request.form.get('csrf_token','')
            if not recebido or not secrets.compare_digest(recebido,session.get('csrf','')):
                abort(400,description='Sessão do formulário expirou. Recarregue a página.')

    @app.errorhandler(PermissaoNegada)
    def acesso_negado(erro):
        if request.path.startswith('/api/'):return jsonify(erro=str(erro)),403
        return render_template('erro.html',title='Acesso não permitido',mensagem=str(erro)),403

    @app.errorhandler(DadosInvalidos)
    @app.errorhandler(ArquivoInvalido)
    def dados_invalidos(erro):
        if request.path.startswith('/api/'):return jsonify(erro=str(erro)),422
        return render_template('erro.html',title='Verifique os dados',mensagem=str(erro)),422

    @app.errorhandler(psycopg2.IntegrityError)
    def conflito(erro):
        mensagem='Registro duplicado ou vínculo acadêmico inválido.'
        if request.path.startswith('/api/'):return jsonify(erro=mensagem),409
        return render_template('erro.html',title='Não foi possível salvar',mensagem=mensagem),409

    @app.errorhandler(psycopg2.Error)
    def banco_indisponivel(erro):
        app.logger.error('Falha PostgreSQL: %s',type(erro).__name__)
        mensagem='Não foi possível acessar o banco. Confira o .env e execute python preparar_banco.py --demo.'
        if request.path.startswith('/api/'):return jsonify(erro=mensagem),503
        return render_template('erro.html',title='Banco indisponível',mensagem=mensagem),503

    @app.errorhandler(413)
    def arquivo_grande(erro):return jsonify(erro='Arquivo muito grande. Limite de 2 MB.'),413

    @app.errorhandler(400)
    def requisicao_invalida(erro):
        if request.path.startswith('/api/'):return jsonify(erro=erro.description),400
        return render_template('erro.html',title='Recarregue a página',mensagem=erro.description),400

    @app.get('/saude')
    def saude():return {'status':'ok','versao':'2.3','periodos':['VA1','VA2','VA3']}

    @app.get('/')
    def index():return redirect(url_for('dashboard'))

    @app.route('/login',methods=['GET','POST'])
    def login():
        if g.usuario:return redirect(url_for('dashboard'))
        erro=None;status=200
        identificador=request.form.get('identificador','').strip()
        if request.method=='POST':
            senha=request.form.get('password','')
            if not identificador or not senha:erro,status='Preencha o identificador e a senha.',400
            else:
                usuario=autenticar(identificador,senha)
                if usuario:
                    iniciar_sessao(usuario);session.permanent=True
                    return redirect(url_for('dashboard'))
                erro,status='Matrícula, e-mail ou senha incorretos.',401
        return render_template('login.html',erro=erro,identificador=identificador),status

    @app.post('/logout')
    def logout():encerrar_sessao();return redirect(url_for('login'))

    @app.get('/dashboard')
    def dashboard():
        if g.usuario['perfil']=='aluno':
            base=repo().dados_dashboard()
            return render_template('dashboard_aluno.html',title='Meu painel',analise=analisar(base),aluno=base['alunos'][0] if base['alunos'] else None)
        return render_template('dashboard_integrado.html',title='Dashboard',page_class='dashboard-page')

    @app.get('/dashboard/dataset-professor')
    def dashboard_dataset():
        professor()
        return render_template('dashboard_dataset.html',title='Dashboard',page_class='dashboard-page',base_dataset=True)

    @app.get('/api/dataset-professor')
    def dataset_api():
        professor()
        base=RepositorioDatasetProfessor(g.usuario).dados()
        if base is None:
            return jsonify(erro='Dataset ainda não importado. No terminal, execute python importar_dataset_professor.py.'),503
        return jsonify(analisar_historico(base,request.args.get('semestre'),request.args.get('aluno_id')))

    @app.get('/minhas-notas')
    def minhas_notas():
        if g.usuario['perfil']!='aluno':raise PermissaoNegada('Esta página é o boletim individual de alunos.')
        base=repo().dados_dashboard()
        return render_template('boletim.html',title='Minhas notas',analise=analisar(base),aluno=base['alunos'][0] if base['alunos'] else None)

    @app.get('/alunos')
    def alunos():
        professor();q=request.args.get('q','').strip();base=repo().dados_dashboard()
        resumos=analisar(base)['resumos']
        lista=[r for r in resumos if q.casefold() in r['nome'].casefold() or q in r['matricula']]
        return render_template('alunos.html',title='Alunos',alunos=lista,query=q)

    @app.route('/alunos/novo',methods=['GET','POST'])
    def cadastro_aluno():
        professor()
        if request.method=='POST':
            repo().cadastrar_aluno(request.form);flash('Aluno cadastrado. As avaliações ficam pendentes até o lançamento.','sucesso')
            return redirect(url_for('alunos'))
        return render_template('cadastro_aluno.html',title='Cadastrar aluno',turmas=repo().listar_turmas())

    @app.get('/alunos/<int:aluno_id>')
    def perfil_aluno(aluno_id):
        repo().exigir_aluno(aluno_id)
        base=repo().dados_dashboard(aluno_id=aluno_id)
        return render_template('boletim.html',title='Perfil do aluno',analise=analisar(base),aluno=base['alunos'][0])

    @app.get('/turmas')
    def turmas():
        professor();r=repo();ofertas=r.listar_ofertas();matriculas=r.listar_matriculas()
        lista=[{**t,'alunos':sum(m['turma_id']==t['id'] for m in matriculas),
                      'disciplinas':sum(o['turma_id']==t['id'] for o in ofertas)} for t in r.listar_turmas()]
        return render_template('turmas.html',title='Turmas',turmas=lista)

    @app.route('/turmas/nova',methods=['GET','POST'])
    def cadastro_turma():
        professor();r=repo()
        disciplinas=[d for d in r.listar_disciplinas() if d['situacao']=='ativa']
        hoje=date.today()
        valores=request.form.to_dict() if request.method=='POST' else {
            'ano_letivo':hoje.year,'semestre':1 if hoje.month<=6 else 2,'situacao':'ativa'}
        selecionadas=request.form.getlist('disciplinas') if request.method=='POST' else [str(d['id']) for d in disciplinas]
        erro=None;status=200
        if request.method=='POST':
            try:
                r.cadastrar_turma({**valores,'disciplinas':selecionadas})
                flash('Turma cadastrada. As disciplinas já estão disponíveis em Avaliações e no cadastro de alunos.','sucesso')
                return redirect(url_for('turmas'))
            except DadosInvalidos as exc:
                erro=str(exc);status=422
            except psycopg2.IntegrityError as exc:
                if exc.diag.constraint_name!='uq_turma_contexto':raise
                erro='Já existe uma turma com esse identificador no mesmo ano e semestre.';status=409
        return render_template('cadastro_turma.html',title='Cadastrar turma',disciplinas=disciplinas,
                               valores=valores,selecionadas=selecionadas,erro=erro),status

    @app.get('/disciplinas')
    def disciplinas():
        professor();return render_template('disciplinas.html',title='Disciplinas',disciplinas=repo().listar_disciplinas())

    @app.get('/registro-academico')
    def registro_academico():professor();return redirect(url_for('avaliacoes'))

    @app.get('/avaliacoes')
    def avaliacoes():
        professor();ofertas,oferta,va=contexto_oferta();base=repo().dados_dashboard()
        regra=None;atividades=[];alunos=[]
        if oferta:
            t,d=oferta['turma_id'],oferta['disciplina_id']
            regra=next((r for r in base['regras'] if (r['turma_id'],r['disciplina_id'],r['va'])==(t,d,va)),None)
            atividades=[a for a in base['atividades'] if (a['turma_id'],a['disciplina_id'],a['va'])==(t,d,va)]
            alunos=[m for m in base['matriculas'] if m['turma_id']==t]
        return render_template('avaliacoes.html',title='Avaliações',ofertas=ofertas,oferta=oferta,va=va,regra=regra,atividades=atividades,alunos=alunos)

    @app.post('/avaliacoes/nova')
    def nova_atividade():
        professor();repo().criar_atividade(request.form);flash('Atividade cadastrada; as notas ainda estão pendentes.','sucesso')
        return volta_oferta(request.form['turma_id'],request.form['disciplina_id'],request.form['va'])

    @app.route('/avaliacoes/<int:atividade_id>/notas',methods=['GET','POST'])
    def notas_atividade(atividade_id):
        professor();r=repo();a=r.atividade(atividade_id)
        alunos=[m for m in r.listar_matriculas() if m['turma_id']==a['turma_id']]
        if request.method=='POST':
            linhas=[{'aluno_id':aid,'nota':valor} for chave,valor in request.form.items() if chave.startswith('nota_') for aid in [chave[5:]]]
            r.salvar_notas(atividade_id,linhas);flash('Notas salvas. Campo vazio permanece pendente.','sucesso')
            return volta_oferta(a['turma_id'],a['disciplina_id'],a['va'])
        base=r.dados_dashboard(turma_id=a['turma_id'])
        notas={n['aluno_id']:n['nota'] for n in base['notas_componentes'] if n['atividade_id']==atividade_id}
        regra=next(regra for regra in base['regras'] if (regra['turma_id'],regra['disciplina_id'],regra['va'])==(a['turma_id'],a['disciplina_id'],a['va']))
        return render_template('lancar_notas.html',title='Lançar notas',atividade=a,alunos=alunos,notas=notas,regra=regra)

    @app.post('/avaliacoes/composicao')
    def composicao_va():
        professor();repo().configurar_va(request.form);flash('Composição atualizada sem cortar ou redistribuir notas.','sucesso')
        return volta_oferta(request.form['turma_id'],request.form['disciplina_id'],request.form['va'])

    @app.post('/avaliacoes/encerrar')
    def encerrar_va():
        professor();dados=request.form
        repo().fechar_va(dados.get('turma_id'),dados.get('disciplina_id'),dados.get('va'),dados.get('acao')=='reabrir')
        flash('Situação da VA atualizada.','sucesso');return volta_oferta(dados['turma_id'],dados['disciplina_id'],dados['va'])

    @app.post('/avaliacoes/frequencia')
    def frequencia_va():
        professor();repo().salvar_frequencia(request.form);flash('Frequência salva.','sucesso')
        return volta_oferta(request.form['turma_id'],request.form['disciplina_id'],request.form['va'])

    @app.get('/importacao')
    def importacao():professor();return render_template('importacao_integrada.html',title='Importação')

    @app.get('/api/dados')
    def dados_api():return jsonify(repo().dados_dashboard(inteiro_filtro('turma_id')))

    @app.get('/api/analises')
    def analises_api():
        if 'bimestre' in request.args:raise DadosInvalidos('Use va=1, va=2 ou va=3; o curso não usa bimestres.')
        base=repo().dados_dashboard(inteiro_filtro('turma_id'));d=inteiro_filtro('disciplina_id')
        if d is not None and d not in {o['disciplina_id'] for o in base['ofertas']}:
            raise PermissaoNegada('Disciplina sem permissão de acesso.')
        return jsonify(analisar(base,d,inteiro_filtro('va',2,3)))

    @app.route('/api/alunos',methods=['GET','POST'])
    def alunos_api():
        professor()
        if request.method=='POST':return jsonify(repo().cadastrar_aluno(json_entrada())),201
        return jsonify(repo().listar_alunos())

    @app.route('/api/turmas',methods=['GET','POST'])
    def turmas_api():
        if request.method=='POST':
            professor();return jsonify(repo().cadastrar_turma(json_entrada())),201
        return jsonify(repo().listar_turmas())

    @app.get('/api/disciplinas')
    def disciplinas_api():return jsonify(repo().listar_disciplinas())

    @app.route('/api/atividades',methods=['GET','POST'])
    @app.route('/api/avaliacoes',methods=['GET','POST'])
    def atividades_api():
        if request.method=='POST':professor();return jsonify(repo().criar_atividade(json_entrada())),201
        return jsonify(repo().dados_dashboard()['atividades'])

    @app.route('/api/atividades/<int:atividade_id>/notas',methods=['GET','POST'])
    def notas_api(atividade_id):
        r=repo();a=r.atividade(atividade_id)
        if request.method=='POST':professor();return jsonify(r.salvar_notas(atividade_id,json_entrada().get('notas')))
        base=r.dados_dashboard(turma_id=a['turma_id'])
        return jsonify({'atividade':numeros(a),'notas':[n for n in base['notas_componentes'] if n['atividade_id']==atividade_id]})

    @app.post('/api/frequencias')
    def frequencias_api():professor();return jsonify(repo().salvar_frequencia(json_entrada()))

    @app.post('/api/vas/composicao')
    def composicao_api():professor();return jsonify(repo().configurar_va(json_entrada()))

    @app.post('/api/vas/encerrar')
    def encerrar_api():
        professor();dados=json_entrada()
        return jsonify(repo().fechar_va(dados.get('turma_id'),dados.get('disciplina_id'),dados.get('va'),dados.get('acao')=='reabrir'))

    @app.get('/api/meu-boletim')
    def boletim_api():
        if g.usuario['perfil']!='aluno':raise PermissaoNegada('Rota individual do aluno.')
        return jsonify(analisar(repo().dados_dashboard()))

    @app.post('/api/importacao/<tipo>')
    def upload(tipo):
        professor();arquivo=request.files.get('arquivo')
        if not arquivo or not arquivo.filename:return jsonify(erro='Selecione CSV ou XLSX.'),400
        return jsonify(importar_arquivo(repo(),tipo,arquivo.filename,arquivo.stream.read(MAX_ARQUIVO+1)))

    @app.get('/api/importacao/modelo/<tipo>')
    def modelo(tipo):
        professor();modelos={'alunos':'matricula;nome;email;turma_id\n','registros':'matricula;atividade_id;nota\n'}
        if tipo not in modelos:abort(404)
        return send_file(io.BytesIO(('\ufeff'+modelos[tipo]).encode('utf-8')),mimetype='text/csv',as_attachment=True,download_name=f'modelo_{tipo}.csv')

    @app.get('/api/importacao/resumo')
    def resumo_api():
        professor();base=repo().dados_dashboard()
        return {k:len(base[k]) for k in ['alunos','turmas','disciplinas']}|{'registros':sum(n['nota'] is not None for n in base['notas_componentes'])}

    @app.get('/api/docs')
    def docs_api():professor();return render_template('api_docs.html',title='API')
    return app


app=criar_app()
if __name__=='__main__':app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
