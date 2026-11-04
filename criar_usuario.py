"""Provisionamento local: contas não escolhem o próprio perfil no navegador."""
import getpass
from contextlib import closing
from werkzeug.security import generate_password_hash
import db


def main():
    print('SIMPA — criar conta de acesso\n1. Professor\n2. Aluno')
    escolha=input('Perfil [1/2]: ').strip()
    if escolha not in ('1','2'):print('Escolha 1 para professor ou 2 para aluno.');return
    perfil='aluno' if escolha=='2' else 'professor'
    aluno_id=None
    if perfil=='aluno':
        matricula=input('Matrícula do aluno já cadastrado: ').strip()
        with closing(db.conectar()) as con,con.cursor() as cur:
            cur.execute('SELECT id,nome_completo,email_institucional FROM simpa.alunos WHERE matricula=%s',(matricula,))
            aluno=cur.fetchone()
        if not aluno:print('Aluno não encontrado. Cadastre a matrícula antes de criar a conta.');return
        aluno_id=aluno['id'];nome=aluno['nome_completo'];email=aluno['email_institucional']
        print('Conta vinculada a:',nome)
    else:
        nome=input('Nome completo: ').strip()
        matricula=input('Identificador/matrícula: ').strip() or None
        email=input('E-mail institucional: ').strip() or None
    if not nome or not (matricula or email):print('Preencha nome e matrícula ou e-mail.');return
    senha=getpass.getpass('Senha (mínimo 6 caracteres): ')
    if len(senha)<6 or senha!=getpass.getpass('Repita a senha: '):print('Senha curta ou confirmação diferente.');return
    try:
        uid=db.inserir_usuario(nome,matricula,email,generate_password_hash(senha),perfil,aluno_id)
        if perfil=='professor':
            from preparar_banco import preparar_curso
            preparar_curso()
            with closing(db.conectar()) as con,con.cursor() as cur:
                cur.execute('''SELECT td.turma_id,td.disciplina_id,t.nome AS turma,d.nome AS disciplina
                    FROM simpa.turma_disciplinas td JOIN simpa.turmas t ON t.id=td.turma_id
                    JOIN simpa.disciplinas d ON d.id=td.disciplina_id WHERE d.codigo LIKE 'IA-%%' ORDER BY d.nome''')
                ofertas=cur.fetchall()
            for i,o in enumerate(ofertas,1):print(f"{i}. {o['turma']} — {o['disciplina']}")
            selecao=input('Números das disciplinas deste professor, separados por vírgula (ou todas): ').strip()
            indices=set(range(1,len(ofertas)+1)) if selecao.casefold()=='todas' else {int(x.strip()) for x in selecao.split(',') if x.strip().isdigit()}
            with closing(db.conectar()) as con,con,con.cursor() as cur:
                # O vínculo inicial automático é substituído pelas escolhas deste cadastro.
                cur.execute('DELETE FROM simpa.professor_disciplinas WHERE usuario_id=%s',(uid,))
                for i,o in enumerate(ofertas,1):
                    if i in indices:cur.execute('INSERT INTO simpa.professor_disciplinas(usuario_id,turma_id,disciplina_id) VALUES (%s,%s,%s)',(uid,o['turma_id'],o['disciplina_id']))
        print(f'Conta criada: {perfil}. Use matrícula ou e-mail e a senha cadastrada.')
    except Exception as erro:
        print('Não foi possível concluir o cadastro. Verifique duplicidade e a preparação do banco.')
        print('Tipo do erro:',type(erro).__name__)


if __name__=='__main__':main()
