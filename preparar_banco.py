"""Migrações aditivas e preparação do curso de Inteligência Artificial."""
import argparse
import json
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from random import Random

import psycopg2
import db
from academico import DISCIPLINAS_IA

PASTA=Path(__file__).resolve().parent


def preparar():
    with closing(db.conectar()) as con,con.cursor() as cur:
        cur.execute("SELECT to_regclass('simpa.usuarios') AS tabela")
        existe=cur.fetchone()['tabela'] is not None
        con.rollback()
        if not existe:cur.execute((PASTA/'sql'/'001_base_original.sql').read_text(encoding='utf-8-sig'))
        for nome in ['002_modulo_analitico.sql','003_perfis_e_vas.sql']:
            cur.execute((PASTA/'sql'/nome).read_text(encoding='utf-8-sig'))
        con.commit()
    preparar_curso()


def preparar_curso():
    with closing(db.conectar()) as con,con,con.cursor() as cur:
        cur.execute('''INSERT INTO simpa.turmas(identificador,nome,ano_letivo,semestre,serie)
            VALUES ('IA-2-2026','Inteligência Artificial — 2º período',2026,2,'2º período')
            ON CONFLICT(identificador,ano_letivo,semestre) DO NOTHING''')
        cur.execute("SELECT id FROM simpa.turmas WHERE identificador='IA-2-2026' AND ano_letivo=2026 AND semestre=2")
        turma=cur.fetchone()['id']
        disciplinas=[]
        for codigo,nome in DISCIPLINAS_IA:
            cur.execute('''INSERT INTO simpa.disciplinas(codigo,nome,area)
                VALUES (%s,%s,'Inteligência Artificial') ON CONFLICT(codigo) DO NOTHING''',('IA-'+codigo,nome))
            cur.execute('SELECT id FROM simpa.disciplinas WHERE codigo=%s',('IA-'+codigo,))
            did=cur.fetchone()['id'];disciplinas.append(did)
            cur.execute('INSERT INTO simpa.turma_disciplinas(turma_id,disciplina_id) VALUES (%s,%s) ON CONFLICT DO NOTHING',(turma,did))
            for va in (1,2,3):
                cur.execute('INSERT INTO simpa.regras_va(turma_id,disciplina_id,va) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',(turma,did,va))
                for tipo,campo in [('A360','max_a360'),('VRAU','max_vrau'),('AFE','max_afe')]:
                    cur.execute(f'''INSERT INTO simpa.atividades_va(turma_id,disciplina_id,va,tipo,titulo,maximo)
                        SELECT turma_id,disciplina_id,va,%s,%s,{campo} FROM simpa.regras_va
                        WHERE turma_id=%s AND disciplina_id=%s AND va=%s ON CONFLICT DO NOTHING''',
                        (tipo,tipo,turma,did,va))
        # Compatibilidade com a conta inicial, que antes administrava toda a demonstração.
        cur.execute("SELECT id FROM simpa.usuarios WHERE ativo AND perfil='professor' ORDER BY id")
        professores=cur.fetchall()
        cur.execute('SELECT count(*) AS total FROM simpa.professor_disciplinas')
        if len(professores)==1 and cur.fetchone()['total']==0:
            for did in disciplinas:
                cur.execute('INSERT INTO simpa.professor_disciplinas(usuario_id,turma_id,disciplina_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                            (professores[0]['id'],turma,did))
    return turma,disciplinas


def carregar_demonstracao():
    """Exemplo fictício: VA1 concluída, VA2 em andamento, VA3 pendente."""
    turma,disciplinas=preparar_curso()
    alunos=json.loads((PASTA/'data'/'exemplos'/'alunos.json').read_text(encoding='utf-8'))
    rng=Random(2026)
    with closing(db.conectar()) as con,con,con.cursor() as cur:
        cur.execute("SELECT 1 FROM simpa.cargas_demo WHERE chave='ia_vas_2026'")
        if cur.fetchone():return False
        ids=[]
        for a in alunos:
            matricula='IADEMO-'+a['matricula']
            cur.execute('''INSERT INTO simpa.alunos(matricula,nome_completo,email_institucional)
                VALUES (%s,%s,%s) ON CONFLICT(matricula) DO NOTHING''',
                (matricula,a['nome'],a['id'].lower()+'@exemplo.edu.br'))
            cur.execute('SELECT id FROM simpa.alunos WHERE matricula=%s',(matricula,))
            aid=cur.fetchone()['id'];ids.append(aid)
            cur.execute('INSERT INTO simpa.matriculas(aluno_id,turma_id) VALUES (%s,%s) ON CONFLICT DO NOTHING',(aid,turma))
        for did in disciplinas:
            # Seis encontros apenas neste exemplo de VA1; o sistema não fixa essa quantidade.
            for va,encontros in [(1,6),(2,3)]:
                for encontro in range(1,encontros+1):
                    for tipo,maximo in [('APS',2),('DAILY',3)]:
                        cur.execute('''INSERT INTO simpa.atividades_va(turma_id,disciplina_id,va,tipo,titulo,maximo)
                            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
                            (turma,did,va,tipo,f'{tipo} — encontro {encontro} (exemplo)',maximo))
                cur.execute('SELECT * FROM simpa.atividades_va WHERE turma_id=%s AND disciplina_id=%s AND va=%s ORDER BY id',(turma,did,va))
                atividades=cur.fetchall()
                for i,aid in enumerate(ids):
                    for a in atividades:
                        if va==2 and (a['tipo'] in ('VRAU','AFE') or (i+a['id'])%7==0):continue
                        ratio=Decimal(str(round(rng.uniform(.45,.98),2)))
                        if i==0 and va==1:
                            valor={'A360':Decimal(8),'VRAU':Decimal(22),'AFE':Decimal(26)}.get(a['tipo'],a['maximo']*Decimal('.8'))
                        else:valor=(a['maximo']*ratio).quantize(Decimal('.01'))
                        cur.execute('''INSERT INTO simpa.notas_atividades(atividade_id,aluno_id,nota)
                            VALUES (%s,%s,%s) ON CONFLICT DO NOTHING''',(a['id'],aid,valor))
                    aulas=12 if va==1 else 6
                    presencas=max(0,aulas-rng.randrange(0,3))
                    cur.execute('''INSERT INTO simpa.frequencias_va(aluno_id,turma_id,disciplina_id,va,aulas,presencas)
                        VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',(aid,turma,did,va,aulas,presencas))
            cur.execute('UPDATE simpa.regras_va SET fechada=TRUE,fechada_em=CURRENT_TIMESTAMP WHERE turma_id=%s AND disciplina_id=%s AND va=1',(turma,did))
        cur.execute("INSERT INTO simpa.cargas_demo(chave) VALUES ('ia_vas_2026')")
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true',help='Acrescentar demonstração fictícia do curso de IA')
    args=parser.parse_args()
    try:
        preparar()
        if args.demo:carregar_demonstracao()
    except psycopg2.Error as erro:
        print('Não foi possível preparar o banco. Confira o .env e o banco simpa.')
        print('Tipo do erro:',type(erro).__name__)
        raise SystemExit(1)
    print('Estrutura atualizada: perfis, cinco disciplinas do curso e VA1/VA2/VA3. Dados antigos preservados.')
    if args.demo:print('Demonstração de IA disponível: 35 alunos fictícios; VA1 concluída, VA2 parcial e VA3 pendente.')
