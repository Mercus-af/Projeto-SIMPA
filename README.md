# SIMPA - Marco 1

O SIMPA (Sistema Inteligente de Monitoramento e Predição Acadêmica) organiza dados de alunos, turmas e disciplinas. Neste primeiro marco, o objetivo é apresentar as classes principais, a modelagem e uma API básica de cadastro e consulta.

Não há frontend implementado neste marco. Os arquivos da pasta `wireframe/` são apenas os protótipos das telas planejadas.

## O que está funcionando

- consulta de alunos, turmas e disciplinas;
- cadastro de aluno com validação dos campos;
- bloqueio de matrícula duplicada;
- consulta de aluno pela matrícula;
- armazenamento local em SQLite;
- documentação interativa da API pelo Swagger;
- validações de nota (0 a 10) e frequência (0% a 100%) nas classes acadêmicas.

## Organização

```text
api.py                       # rotas FastAPI e validação das entradas
sqlite_repositorio.py        # persistência local usada na demonstração
aluno_classe.py              # classe Aluno
RA_classe.py                 # classe RegistroAcademico
turma_classe.py              # classe Turma
disciplina_classe.py         # classe Disciplina
*_repositorio.py e conexao.py # arquivos existentes para PostgreSQL
data/                        # banco SQLite criado na primeira execução
documentos/modelagem_uml.md  # diagramas do Marco 1
wireframe/                   # protótipos, sem frontend implementado
```

## Banco usado no Marco 1

A demonstração local usa SQLite. O arquivo `data/simpa.db` é criado automaticamente e mantém os cadastros depois que a API é encerrada. Na primeira execução são inseridos dois alunos, duas turmas e três disciplinas para facilitar a apresentação.

A API acessa as tabelas por meio da classe `RepositorioSQLite`. As classes `Aluno`, `Turma`, `Disciplina` e `RegistroAcademico` representam a parte acadêmica e seus cálculos, mas ainda não são instanciadas pelas rotas da API.

Os módulos já existentes de PostgreSQL (`conexao.py` e os arquivos `*_repositorio.py`) foram mantidos no projeto, mas não são usados pela API deste marco. Eles representam uma possibilidade de integração futura. A conexão com o PostgreSQL remoto não foi validada nesta entrega.

## Instalação

É necessário ter Python 3.11 ou superior.

### Linux, WSL ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Se o comando de criação do ambiente não estiver disponível, também é possível usar `uv`:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Executar a API

Com o ambiente virtual ativado:

```bash
python -m uvicorn api:app --reload
```

A API ficará disponível em `http://127.0.0.1:8000` e o Swagger em:

- `http://127.0.0.1:8000/docs`

O caminho do banco pode ser alterado pela variável de ambiente `SIMPA_DB_PATH`. Sem essa variável, será usado `data/simpa.db`.

## Endpoints

| Método | Caminho | Função |
|---|---|---|
| GET | `/saude` | verifica se a API está respondendo |
| GET | `/alunos` | lista os alunos |
| POST | `/alunos` | cadastra um aluno |
| GET | `/alunos/{matricula}` | consulta um aluno pela matrícula |
| GET | `/turmas` | lista as turmas |
| GET | `/disciplinas` | lista as disciplinas |

Exemplo de cadastro:

```bash
curl -X POST http://127.0.0.1:8000/alunos \
  -H "Content-Type: application/json" \
  -d '{
    "matricula": "2026999",
    "nome": "Marina Souza",
    "email": "marina.souza@faculdade.edu.br",
    "turma_id": 1
  }'
```

A matrícula deve ser única, a turma precisa existir e os campos não podem ser vazios. Entradas inválidas retornam erro `422`; matrícula repetida retorna erro `409`.

## Roteiro de demonstração (3 a 5 minutos)

1. Mostrar rapidamente `documentos/modelagem_uml.md` e explicar Aluno, Turma, Disciplina, RegistroAcademico, API e repositório SQLite.
2. Iniciar a API e abrir `/docs` para mostrar que a documentação é gerada automaticamente.
3. Executar `GET /turmas`, `GET /disciplinas` e `GET /alunos` para apresentar os dados iniciais.
4. Executar `POST /alunos` com uma matrícula nova e depois `GET /alunos/{matricula}`.
5. Repetir o cadastro para mostrar o erro de matrícula duplicada.
6. Encerrar e iniciar a API novamente. Repetir o GET da matrícula criada para comprovar a persistência.

## Limites deste marco

O frontend, a autenticação, os indicadores estatísticos e as previsões não foram implementados. Eles pertencem aos próximos ciclos. Os wireframes registram a ideia das telas, mas não representam uma interface já disponível.
