"""ETL do grupo com permissão por professor e lançamento por atividade."""
import psycopg2
from simpa.academico import inteiro
from simpa.repositorio import PermissaoNegada
from .leitura import ArquivoInvalido,extrair_linhas
from .validacoes import DadosInvalidos


def importar_arquivo(repositorio,tipo,nome_arquivo,conteudo):
    repositorio.exigir_professor()
    if tipo not in {'alunos','registros'}:raise ArquivoInvalido('Tipo de importação inválido.')
    linhas=list(extrair_linhas(nome_arquivo,conteudo,tipo))
    resultado={'tipo':tipo,'arquivo':nome_arquivo,'total_lidos':len(linhas),'importados':0,'recusados':0,'erros':[]}
    permitidos={a['matricula']:a['id'] for a in repositorio.listar_alunos()}
    with repositorio.transacao() as cur:
        cur.execute('INSERT INTO simpa.importacoes(nome_arquivo,registros_lidos) VALUES (%s,%s) RETURNING id',(nome_arquivo,len(linhas)))
        carga=cur.fetchone()['id']
        for numero,entrada,erro in linhas:
            cur.execute('SAVEPOINT linha_importacao')
            try:
                if erro:raise DadosInvalidos(erro)
                if tipo=='alunos':repositorio.cadastrar_aluno(entrada,cur)
                else:
                    aid=permitidos.get(str(entrada.get('matricula','')).strip())
                    if aid is None:raise DadosInvalidos('Matrícula não disponível nas suas turmas.')
                    atividade=inteiro(entrada.get('atividade_id'),'atividade_id')
                    repositorio.atividade(atividade,cur)
                    # Importação não sobrescreve nota já preenchida; correções ficam na tela.
                    cur.execute('SELECT nota FROM simpa.notas_atividades WHERE atividade_id=%s AND aluno_id=%s',(atividade,aid))
                    anterior=cur.fetchone()
                    if anterior and anterior['nota'] is not None:raise DadosInvalidos('Nota já lançada; corrija pela tela de avaliações.')
                    repositorio.salvar_notas(atividade,[{'aluno_id':aid,'nota':entrada.get('nota')}],cur)
            except (DadosInvalidos,PermissaoNegada,psycopg2.IntegrityError) as exc:
                cur.execute('ROLLBACK TO SAVEPOINT linha_importacao')
                mensagem=str(exc) if isinstance(exc,(DadosInvalidos,PermissaoNegada)) else 'Registro duplicado ou vínculo inválido'
                resultado['recusados']+=1;resultado['erros'].append({'linha':numero,'motivo':mensagem})
                cur.execute('INSERT INTO simpa.erros_importacao(importacao_id,numero_linha,mensagem) VALUES (%s,%s,%s)',(carga,numero,mensagem))
            else:resultado['importados']+=1
            finally:cur.execute('RELEASE SAVEPOINT linha_importacao')
        cur.execute("UPDATE simpa.importacoes SET situacao='concluida',finalizada_em=CURRENT_TIMESTAMP,registros_aceitos=%s,registros_com_erro=%s WHERE id=%s",(resultado['importados'],resultado['recusados'],carga))
    return resultado
