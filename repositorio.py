"""Persistência e permissões por professor, turma, disciplina e aluno."""
from contextlib import closing,contextmanager
from decimal import Decimal

import db
from academico import inteiro,pontos
from importacao.validacoes import DadosInvalidos,validar_aluno,obrigatorio


class PermissaoNegada(Exception):
    pass


def numeros(valor):
    if isinstance(valor,Decimal):return float(valor)
    if isinstance(valor,dict):return {k:numeros(v) for k,v in valor.items()}
    if isinstance(valor,list):return [numeros(v) for v in valor]
    return valor


class RepositorioAcademico:
    def __init__(self,usuario=None):
        self.usuario=usuario

    @contextmanager
    def transacao(self):
        with closing(db.conectar()) as con,con,con.cursor() as cur:
            yield cur

    def consultar(self,sql,parametros=()):
        with self.transacao() as cur:
            cur.execute(sql,parametros)
            return [dict(l) for l in cur.fetchall()]

    def exigir_professor(self):
        if not self.usuario or self.usuario['perfil']!='professor':
            raise PermissaoNegada('Esta operação é exclusiva de professores.')

    def listar_ofertas(self):
        if not self.usuario:raise PermissaoNegada('Identificação de acesso ausente.')
        if hasattr(self,'_ofertas'):return self._ofertas
        if self.usuario['perfil']=='professor':
            origem='simpa.professor_disciplinas p'
            filtro='p.usuario_id=%s';param=self.usuario['id']
        else:
            origem='simpa.matriculas m JOIN simpa.turma_disciplinas p ON p.turma_id=m.turma_id'
            filtro='m.aluno_id=%s';param=self.usuario['aluno_id']
        self._ofertas=self.consultar(f'''SELECT p.turma_id,p.disciplina_id,t.nome AS turma,
            d.nome AS disciplina,d.codigo,t.ano_letivo,t.semestre,t.situacao
            FROM {origem} JOIN simpa.turmas t ON t.id=p.turma_id
            JOIN simpa.disciplinas d ON d.id=p.disciplina_id
            WHERE {filtro} ORDER BY t.nome,d.nome''',(param,))
        return self._ofertas

    def exigir_oferta(self,turma_id,disciplina_id):
        t=inteiro(turma_id,'turma_id');d=inteiro(disciplina_id,'disciplina_id')
        oferta=next((o for o in self.listar_ofertas() if (o['turma_id'],o['disciplina_id'])==(t,d)),None)
        if oferta is None:raise PermissaoNegada('Você não possui acesso a esta turma e disciplina.')
        return oferta

    @staticmethod
    def condicao_ofertas(ofertas,alias=''):
        prefixo=alias+'.' if alias else ''
        if not ofertas:return 'FALSE',[]
        sql=' OR '.join(f'({prefixo}turma_id=%s AND {prefixo}disciplina_id=%s)' for o in ofertas)
        params=[v for o in ofertas for v in (o['turma_id'],o['disciplina_id'])]
        return sql,params

    def listar_turmas(self):
        ofertas=self.listar_ofertas();ids=sorted({o['turma_id'] for o in ofertas})
        if not ids:return []
        return self.consultar('''SELECT t.*,t.identificador AS codigo,
            t.ano_letivo::text || '/' || t.semestre::text AS periodo
            FROM simpa.turmas t WHERE t.id=ANY(%s) ORDER BY nome''',(ids,))

    def listar_disciplinas(self):
        ids=sorted({o['disciplina_id'] for o in self.listar_ofertas()})
        return self.consultar('SELECT * FROM simpa.disciplinas WHERE id=ANY(%s) ORDER BY nome',(ids,)) if ids else []

    def cadastrar_turma(self,entrada):
        self.exigir_professor()
        identificador=obrigatorio(entrada,'identificador',1,50)
        nome=obrigatorio(entrada,'nome',1,150)
        ano=inteiro(entrada.get('ano_letivo'),'ano_letivo',1,32767)
        semestre=inteiro(entrada.get('semestre'),'semestre',1,2)
        situacao=entrada.get('situacao','ativa')
        if situacao not in ('ativa','inativa','concluida'):
            raise DadosInvalidos('Situação da turma inválida.')
        disciplinas=entrada.get('disciplinas')
        if not isinstance(disciplinas,list) or not disciplinas:
            raise DadosInvalidos('Selecione pelo menos uma disciplina para a turma.')
        ids=sorted({inteiro(d,'disciplina') for d in disciplinas})
        permitidas={d['id'] for d in self.listar_disciplinas() if d['situacao']=='ativa'}
        if not set(ids)<=permitidas:
            raise PermissaoNegada('Selecione somente disciplinas ativas vinculadas à sua conta.')
        with self.transacao() as cur:
            cur.execute('''INSERT INTO simpa.turmas(identificador,nome,ano_letivo,semestre,situacao)
                VALUES (%s,%s,%s,%s,%s) RETURNING id''',(identificador,nome,ano,semestre,situacao))
            tid=cur.fetchone()['id']
            for did in ids:
                cur.execute('INSERT INTO simpa.turma_disciplinas(turma_id,disciplina_id) VALUES (%s,%s)',(tid,did))
                cur.execute('INSERT INTO simpa.professor_disciplinas(usuario_id,turma_id,disciplina_id) VALUES (%s,%s,%s)',
                            (self.usuario['id'],tid,did))
                for va in (1,2,3):
                    cur.execute('''INSERT INTO simpa.regras_va(turma_id,disciplina_id,va)
                        VALUES (%s,%s,%s) RETURNING max_a360,max_vrau,max_afe''',(tid,did,va))
                    regra=cur.fetchone()
                    for tipo,campo in [('A360','max_a360'),('VRAU','max_vrau'),('AFE','max_afe')]:
                        cur.execute('''INSERT INTO simpa.atividades_va(turma_id,disciplina_id,va,tipo,titulo,maximo,criado_por)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)''',(tid,did,va,tipo,tipo,regra[campo],self.usuario['id']))
        for atributo in ('_ofertas','_matriculas'):
            self.__dict__.pop(atributo,None)
        return {'id':tid,'identificador':identificador,'nome':nome,'ano_letivo':ano,
                'semestre':semestre,'situacao':situacao,'disciplinas':ids}

    def listar_matriculas(self):
        if hasattr(self,'_matriculas'):return self._matriculas
        ids=sorted({o['turma_id'] for o in self.listar_ofertas()})
        if not ids:return []
        cond='m.turma_id=ANY(%s)';params=[ids]
        if self.usuario['perfil']=='aluno':cond+=' AND m.aluno_id=%s';params.append(self.usuario['aluno_id'])
        self._matriculas=self.consultar(f'''SELECT m.aluno_id,m.turma_id,t.nome AS turma,
            a.nome_completo AS nome,a.matricula,a.email_institucional AS email,
            a.situacao_academica AS situacao FROM simpa.matriculas m
            JOIN simpa.alunos a ON a.id=m.aluno_id JOIN simpa.turmas t ON t.id=m.turma_id
            WHERE {cond} ORDER BY a.nome_completo,t.nome''',params)
        return self._matriculas

    def listar_alunos(self):
        alunos={}
        for m in self.listar_matriculas():
            alunos.setdefault(m['aluno_id'],{'id':m['aluno_id'],**m})
        return list(alunos.values())

    def exigir_aluno(self,aluno_id,turma_id=None):
        aluno_id=inteiro(aluno_id,'aluno_id')
        matricula=next((m for m in self.listar_matriculas() if m['aluno_id']==aluno_id
                        and (turma_id is None or m['turma_id']==int(turma_id))),None)
        if not matricula:raise PermissaoNegada('Aluno fora do seu vínculo acadêmico.')
        return matricula

    def cadastrar_aluno(self,entrada,cur=None):
        self.exigir_professor();dados=validar_aluno(entrada)
        if dados['turma_id'] not in {o['turma_id'] for o in self.listar_ofertas()}:
            raise PermissaoNegada('Você não possui vínculo com esta turma.')
        if cur is None:
            with self.transacao() as cursor:return self.cadastrar_aluno(dados,cursor)
        cur.execute('''INSERT INTO simpa.alunos(matricula,nome_completo,email_institucional)
            VALUES (%s,%s,%s) RETURNING id''',(dados['matricula'],dados['nome'],dados['email']))
        aid=cur.fetchone()['id']
        cur.execute('INSERT INTO simpa.matriculas(aluno_id,turma_id) VALUES (%s,%s)',(aid,dados['turma_id']))
        # Matrícula nova não cria notas nem reabre VAs de outras disciplinas.
        return {'id':aid,**dados}

    def regra(self,cur,t,d,va,editar=False):
        self.exigir_oferta(t,d)
        if editar:self.exigir_professor()
        va=inteiro(va,'va',1,3)
        cur.execute('SELECT * FROM simpa.regras_va WHERE turma_id=%s AND disciplina_id=%s AND va=%s FOR UPDATE',(t,d,va))
        regra=cur.fetchone()
        if not regra:raise DadosInvalidos('A composição desta VA ainda não foi preparada.')
        if editar and regra['fechada']:raise DadosInvalidos('VA encerrada. Reabra antes de alterar notas ou atividades.')
        return regra

    def criar_atividade(self,entrada):
        self.exigir_professor()
        t=inteiro(entrada.get('turma_id'),'turma_id');d=inteiro(entrada.get('disciplina_id'),'disciplina_id')
        va=inteiro(entrada.get('va'),'va',1,3)
        tipo=str(entrada.get('tipo','')).upper()
        if tipo not in ('APS','DAILY'):raise DadosInvalidos('Cadastre uma APS ou Daily. Os outros componentes já são preparados na VA.')
        titulo=str(entrada.get('titulo','')).strip()
        if not 3<=len(titulo)<=150:raise DadosInvalidos('Título: informe de 3 a 150 caracteres.')
        data=entrada.get('data_atividade') or None
        if data:
            from datetime import date
            try:date.fromisoformat(data)
            except (ValueError,TypeError):raise DadosInvalidos('Data inválida.')
        with self.transacao() as cur:
            r=self.regra(cur,t,d,va,True)
            maximo=r['max_aps'] if tipo=='APS' else r['max_daily']
            cur.execute("SELECT coalesce(sum(maximo),0) AS total FROM simpa.atividades_va WHERE turma_id=%s AND disciplina_id=%s AND va=%s AND tipo IN ('APS','DAILY')",(t,d,va))
            if cur.fetchone()['total']+maximo>r['max_atividades']:
                raise DadosInvalidos('A atividade ultrapassa o limite do bloco APS + Dailys. Nenhum ponto foi cortado ou redistribuído.')
            cur.execute('''INSERT INTO simpa.atividades_va(turma_id,disciplina_id,va,tipo,titulo,data_atividade,maximo,criado_por)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',(t,d,va,tipo,titulo,data,maximo,self.usuario['id']))
            return {'id':cur.fetchone()['id'],'maximo':float(maximo)}

    def atividade(self,atividade_id,cur=None):
        parametros=(inteiro(atividade_id,'atividade_id'),)
        if cur is None:linhas=self.consultar('SELECT * FROM simpa.atividades_va WHERE id=%s',parametros)
        else:
            cur.execute('SELECT * FROM simpa.atividades_va WHERE id=%s',parametros)
            linha=cur.fetchone();linhas=[dict(linha)] if linha else []
        if not linhas:raise DadosInvalidos('Atividade não encontrada.')
        a=linhas[0];self.exigir_oferta(a['turma_id'],a['disciplina_id'])
        return a

    def salvar_notas(self,atividade_id,lancamentos,cur=None):
        self.exigir_professor();a=self.atividade(atividade_id,cur)
        if not isinstance(lancamentos,list) or not lancamentos:raise DadosInvalidos('Informe a lista de notas.')
        matriculados={m['aluno_id'] for m in self.listar_matriculas() if m['turma_id']==a['turma_id']}
        validados={}
        for linha in lancamentos:
            if not isinstance(linha,dict):raise DadosInvalidos('Lançamento inválido.')
            aid=inteiro(linha.get('aluno_id'),'aluno_id')
            if aid not in matriculados:raise PermissaoNegada('Aluno fora da turma desta atividade.')
            if aid in validados:raise DadosInvalidos('Aluno repetido no mesmo lote.')
            validados[aid]=pontos(linha.get('nota'),maximo=a['maximo'],permitir_vazio=True)
        if cur is None:
            with self.transacao() as cursor:return self.salvar_notas(atividade_id,lancamentos,cursor)
        self.regra(cur,a['turma_id'],a['disciplina_id'],a['va'],True)
        cur.execute('SELECT maximo FROM simpa.atividades_va WHERE id=%s',(a['id'],))
        limite_atual=cur.fetchone()['maximo']
        if any(n is not None and n>limite_atual for n in validados.values()):
            raise DadosInvalidos('Uma nota ultrapassa o limite atual da atividade. Recarregue a página.')
        for aid,nota in validados.items():
            cur.execute('''INSERT INTO simpa.notas_atividades(atividade_id,aluno_id,nota,lancado_por)
                VALUES (%s,%s,%s,%s) ON CONFLICT(atividade_id,aluno_id) DO UPDATE SET
                nota=excluded.nota,lancado_por=excluded.lancado_por,atualizado_em=CURRENT_TIMESTAMP''',
                (a['id'],aid,nota,self.usuario['id']))
        return {'atualizados':len(validados)}

    def salvar_frequencia(self,entrada):
        self.exigir_professor()
        t=inteiro(entrada.get('turma_id'),'turma_id');d=inteiro(entrada.get('disciplina_id'),'disciplina_id')
        va=inteiro(entrada.get('va'),'va',1,3);aid=inteiro(entrada.get('aluno_id'),'aluno_id')
        self.exigir_aluno(aid,t)
        aulas=inteiro(entrada.get('aulas'),'aulas');presencas=inteiro(entrada.get('presencas'),'presencas',0,aulas)
        with self.transacao() as cur:
            self.regra(cur,t,d,va,True)
            cur.execute('''INSERT INTO simpa.frequencias_va(aluno_id,turma_id,disciplina_id,va,aulas,presencas)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(aluno_id,turma_id,disciplina_id,va)
                DO UPDATE SET aulas=excluded.aulas,presencas=excluded.presencas''',(aid,t,d,va,aulas,presencas))
        return {'status':'ok'}

    def configurar_va(self,entrada):
        self.exigir_professor()
        t=inteiro(entrada.get('turma_id'),'turma_id');d=inteiro(entrada.get('disciplina_id'),'disciplina_id')
        va=inteiro(entrada.get('va'),'va',1,3)
        campos=['max_atividades','max_a360','max_vrau','max_afe','max_aps','max_daily']
        valores={c:pontos(entrada.get(c),c) for c in campos}
        if sum(valores[c] for c in campos[:4])!=100:raise DadosInvalidos('A composição da VA precisa somar 100 pontos.')
        if any(valores[c]<=0 for c in campos):raise DadosInvalidos('Os limites devem ser maiores que zero.')
        with self.transacao() as cur:
            self.regra(cur,t,d,va,True)
            cur.execute('SELECT * FROM simpa.atividades_va WHERE turma_id=%s AND disciplina_id=%s AND va=%s',(t,d,va))
            atividades=cur.fetchall()
            for tipo,campo in [('APS','max_aps'),('DAILY','max_daily')]:
                if any(a['tipo']==tipo and a['maximo']!=valores[campo] for a in atividades):
                    raise DadosInvalidos('O valor unitário não pode mudar depois de cadastrar atividades desse tipo.')
            if sum(a['maximo'] for a in atividades if a['tipo'] in ('APS','DAILY'))>valores['max_atividades']:
                raise DadosInvalidos('O novo limite é menor que os pontos já distribuídos em APS e Dailys.')
            for tipo,campo in [('A360','max_a360'),('VRAU','max_vrau'),('AFE','max_afe')]:
                cur.execute('''SELECT max(n.nota) AS maior FROM simpa.notas_atividades n
                    JOIN simpa.atividades_va a ON a.id=n.atividade_id
                    WHERE a.turma_id=%s AND a.disciplina_id=%s AND a.va=%s AND a.tipo=%s''',(t,d,va,tipo))
                maior=cur.fetchone()['maior']
                if maior is not None and maior>valores[campo]:raise DadosInvalidos('O limite é menor que uma nota já lançada.')
                cur.execute('UPDATE simpa.atividades_va SET maximo=%s WHERE turma_id=%s AND disciplina_id=%s AND va=%s AND tipo=%s',
                            (valores[campo],t,d,va,tipo))
            cur.execute('''UPDATE simpa.regras_va SET max_atividades=%s,max_a360=%s,max_vrau=%s,max_afe=%s,max_aps=%s,max_daily=%s
                WHERE turma_id=%s AND disciplina_id=%s AND va=%s''',tuple(valores[c] for c in campos)+(t,d,va))
        return {'status':'ok'}

    def fechar_va(self,t,d,va,reabrir=False):
        self.exigir_professor();t=inteiro(t,'turma_id');d=inteiro(d,'disciplina_id');va=inteiro(va,'va',1,3)
        with self.transacao() as cur:
            r=self.regra(cur,t,d,va)
            if not reabrir:
                cur.execute("SELECT coalesce(sum(maximo),0) AS total FROM simpa.atividades_va WHERE turma_id=%s AND disciplina_id=%s AND va=%s AND tipo IN ('APS','DAILY')",(t,d,va))
                if cur.fetchone()['total']!=r['max_atividades']:
                    raise DadosInvalidos('Distribua todo o bloco de APS + Dailys antes de encerrar a VA.')
                cur.execute('''SELECT count(*) AS pendentes FROM simpa.matriculas m CROSS JOIN simpa.atividades_va a
                    LEFT JOIN simpa.notas_atividades n ON n.atividade_id=a.id AND n.aluno_id=m.aluno_id
                    WHERE m.turma_id=%s AND a.turma_id=m.turma_id AND a.disciplina_id=%s AND a.va=%s AND n.nota IS NULL''',(t,d,va))
                if cur.fetchone()['pendentes']:raise DadosInvalidos('Há avaliações pendentes. Lance as notas antes de encerrar.')
                cur.execute('SELECT count(*) AS total FROM simpa.matriculas WHERE turma_id=%s',(t,))
                if not cur.fetchone()['total']:raise DadosInvalidos('Turma sem alunos.')
            cur.execute('UPDATE simpa.regras_va SET fechada=%s,fechada_em=CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END WHERE turma_id=%s AND disciplina_id=%s AND va=%s',
                        (not reabrir,not reabrir,t,d,va))
        return {'status':'reaberta' if reabrir else 'encerrada'}

    def dados_dashboard(self,turma_id=None,aluno_id=None):
        ofertas=self.listar_ofertas()
        if turma_id is not None:
            if int(turma_id) not in {o['turma_id'] for o in ofertas}:raise PermissaoNegada('Turma sem permissão de acesso.')
            ofertas=[o for o in ofertas if o['turma_id']==int(turma_id)]
        if aluno_id is not None:self.exigir_aluno(aluno_id)
        cond,params=self.condicao_ofertas(ofertas,'a')
        atividades=self.consultar(f'SELECT a.* FROM simpa.atividades_va a WHERE {cond} ORDER BY a.va,a.data_atividade NULLS LAST,a.id',params)
        regra_cond,regra_params=self.condicao_ofertas(ofertas)
        regras=self.consultar(f'SELECT * FROM simpa.regras_va WHERE {regra_cond}',regra_params)
        ids_turma={o['turma_id'] for o in ofertas}
        matriculas=[m for m in self.listar_matriculas() if m['turma_id'] in ids_turma and (aluno_id is None or m['aluno_id']==int(aluno_id))]
        alunos={m['aluno_id']:{'id':m['aluno_id'],**m} for m in matriculas}
        ids_ativ=[a['id'] for a in atividades];ids_alunos=list(alunos)
        notas=self.consultar('SELECT * FROM simpa.notas_atividades WHERE atividade_id=ANY(%s) AND aluno_id=ANY(%s)',(ids_ativ,ids_alunos)) if ids_ativ and ids_alunos else []
        fcond,fparams=self.condicao_ofertas(ofertas)
        frequencias=self.consultar(f'SELECT * FROM simpa.frequencias_va WHERE ({fcond}) AND aluno_id=ANY(%s)',fparams+[ids_alunos]) if ids_alunos else []
        ids_disc={o['disciplina_id'] for o in ofertas}
        return numeros({'usuario':{k:self.usuario.get(k) for k in ['id','nome','perfil','aluno_id']},
            'turmas':[t for t in self.listar_turmas() if t['id'] in ids_turma],
            'disciplinas':[d for d in self.listar_disciplinas() if d['id'] in ids_disc],
            'alunos':list(alunos.values()),'matriculas':matriculas,'ofertas':ofertas,
            'atividades':atividades,'notas_componentes':notas,'regras':regras,'frequencias':frequencias})
