# Modelagem do SIMPA - Marco 1

Esta modelagem mostra apenas o que existe neste marco. A API usa FastAPI e SQLite. As classes acadêmicas ficam separadas da API: elas representam alunos, turmas, disciplinas e registros acadêmicos, mas as rotas atuais leem e gravam os dados diretamente pelo `RepositorioSQLite`.

## Classes acadêmicas

```mermaid
classDiagram
    class Aluno {
        -id_aluno: int
        +nome: str
        +email: str
        +matricula: str
        +semestre: int
        +ano: int
        +disciplinas: list
        +notas: dict
        +faltas: dict
        +atualizar_email(novo_email)
        +get_disciplinas_em_risco() list
        +disciplinas_abaixo_media() list
        +get_aprovacao() bool
        +calcular_cr() float
        +get_disciplinas()
        +get_notas()
        +get_faltas()
        +to_dict() dict
    }

    class Turma {
        -id_turma: int
        +nome: str
        +semestre: int
        +ano: int
        +alunos: list
        +disciplinas: list
        +professores: list
        +matricular_aluno(aluno)
        +remover_aluno(aluno)
        +adicionar_disciplina(disciplina)
        +remover_disciplina(disciplina)
        +adicionar_professor(professor)
        +remover_professor(professor)
        +calcular_media_turma() float
        +calcular_taxa_aprovacao() float
        +get_total_alunos() int
        +get_total_disciplinas() int
        +get_total_professores() int
        +to_dict() dict
    }

    class Disciplina {
        -id_disciplina: int
        +nome: str
        +semestre: int
        +ano: int
        +carga_horaria: int
        +alunos: list
        +professores: list
        +adicionar_aluno(aluno)
        +remover_aluno(aluno)
        +adicionar_professor(professor)
        +remover_professor(professor)
        +get_total_alunos() int
        +get_total_professores() int
        +get_alunos()
        +get_professores()
        +to_dict() dict
    }

    class RegistroAcademico {
        -id_registro: int
        +aluno: Aluno
        +turma: Turma
        +disciplinas: list
        +notas: dict
        +faltas: dict
        +frequencias: dict
        +adicionar_disciplina(disciplina)
        +remover_disciplina(disciplina)
        +registrar_nota(disciplina, nota)
        +registrar_frequencia(disciplina, frequencia)
        +registrar_falta(disciplina, faltas)
        +calcular_cr() float
        +get_aprovacao() bool
        +disciplinas_abaixo_media() list
        +get_disciplinas_em_risco() list
        +get_total_disciplinas() int
        +get_disciplinas() list
        +get_notas() dict
        +get_faltas() dict
        +get_frequencias() dict
        +get_turma() Turma
        +alterar_turma(nova_turma)
        +to_dict() dict
    }

    Turma "1" o-- "0..*" Aluno
    Turma "0..*" o-- "0..*" Disciplina
    RegistroAcademico --> Aluno
    RegistroAcademico --> Turma
    RegistroAcademico --> Disciplina
```

## API e persistência

```mermaid
classDiagram
    class API_FastAPI {
        +GET /saude
        +GET /alunos
        +POST /alunos
        +GET /alunos/{matricula}
        +GET /turmas
        +GET /disciplinas
    }

    class RepositorioSQLite {
        +inicializar()
        +listar_alunos()
        +buscar_aluno_por_matricula(matricula)
        +cadastrar_aluno(matricula, nome, email, turma_id)
        +listar_turmas()
        +listar_disciplinas()
    }

    class SQLite {
        turmas
        alunos
        disciplinas
    }

    API_FastAPI --> RepositorioSQLite
    RepositorioSQLite --> SQLite
```

O SQLite guarda três tabelas. Cada aluno pertence a uma turma por `turma_id`. Neste marco ainda não existe uma tabela para ligar turmas e disciplinas.

```mermaid
erDiagram
    TURMAS ||--o{ ALUNOS : possui

    TURMAS {
        INTEGER id PK
        TEXT nome UK
        INTEGER semestre
        INTEGER ano
        TEXT situacao
    }

    ALUNOS {
        INTEGER id PK
        TEXT matricula UK
        TEXT nome
        TEXT email
        INTEGER turma_id FK
        TEXT situacao
    }

    DISCIPLINAS {
        INTEGER id PK
        TEXT codigo UK
        TEXT nome
        TEXT situacao
    }
```

## Casos de uso do Marco 1

```mermaid
flowchart LR
    U[Usuário da API]
    S[SIMPA - API FastAPI]
    DB[(SQLite local)]

    U -->|Verificar funcionamento| SAUDE[Consultar saúde]
    U -->|Visualizar dados| LA[Listar alunos]
    U -->|Informar matrícula, nome, e-mail e turma| CA[Cadastrar aluno]
    U -->|Informar matrícula| CO[Consultar aluno]
    U -->|Visualizar dados| LT[Listar turmas]
    U -->|Visualizar dados| LD[Listar disciplinas]

    SAUDE --> S
    LA --> S
    CA --> S
    CO --> S
    LT --> S
    LD --> S
    S --> DB
```

## Regras representadas

- A matrícula do aluno não pode se repetir.
- O aluno deve estar ligado a uma turma existente.
- Matrícula, nome, e-mail e turma são obrigatórios na API.
- A nota aceita pelas classes acadêmicas fica entre 0 e 10.
- A frequência aceita pelo registro acadêmico fica entre 0% e 100%.
- Turmas vazias e alunos sem notas não interrompem os cálculos.
- Os dados cadastrados pela API permanecem no arquivo SQLite após o reinício.
