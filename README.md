# SIMPA — Sistema Inteligente de Monitoramento e Predição Acadêmica

Projeto do segundo período do curso de Inteligência Artificial. O SIMPA organiza dados acadêmicos, calcula indicadores estatísticos e permite acompanhar notas, frequência e pendências por aluno, turma e disciplina.

No **Marco 2**, o foco é transformar os registros em informações interpretáveis: estatística descritiva, gráficos, análise de histórico e estimativas de desempenho. O sistema também possui um assistente acadêmico com **Gemma 4 via Ollama Cloud e LangChain**, conectado às consultas autorizadas da plataforma.

## Tecnologias

| Parte | Tecnologia |
| --- | --- |
| Aplicação e API | Python e Flask |
| Banco de dados | PostgreSQL e psycopg2 |
| Interface | HTML/Jinja, CSS e JavaScript |
| Gráfico de notas e histórico | Plotly |
| Estatística | NumPy e módulos Python do grupo |
| Assistente acadêmico | LangChain, ChatOllama e Gemma 4 no Ollama Cloud |
| Importação | CSV e XLSX, com openpyxl |
| Formatação das respostas | MarkdownIt e Bleach |

## Funcionalidades e perfis

| Área | Funcionamento |
| --- | --- |
| Login | Acesso por matrícula ou e-mail institucional e senha |
| Cadastrar-se | Conta de aluno vinculada à matrícula existente, mediante código do professor |
| Dashboard do professor | Indicadores, médias por disciplina, frequência, filtros de turma/VA e últimos cadastros |
| Meu painel / Minhas notas | Visão individual, componentes das VAs, pendências e média final |
| Assistente acadêmico | Consultas em linguagem natural, respostas em Markdown e histórico privado de chats |
| Alunos | Cadastro acadêmico, busca, boletim individual e código de primeiro acesso |
| Turmas | Consulta e cadastro de turmas com disciplinas vinculadas ao professor |
| Disciplinas | Catálogo das disciplinas disponíveis à conta |
| Avaliações | APS, Daily ou atividade personalizada, notas, frequência e encerramento/reabertura da VA |
| Importação | Alunos e notas por atividade a partir dos modelos do SIMPA |
| Dataset do professor | Dados fictícios separados, com histórico por semestre e projeção |

O professor acessa suas ofertas de turma/disciplina. O aluno consulta somente os próprios dados e não possui permissão de lançamento. Os controles também são aplicados na API.

## Organização das pastas

```text
Projeto-SIMPA/
├── app.py                    # Entrada para iniciar o servidor
├── simpa/                    # Código Python da aplicação
│   ├── app.py                # Rotas, API e criação do aplicativo Flask
│   ├── repositorio.py        # Consultas e permissões acadêmicas
│   ├── academico.py          # Componentes, VAs e média final
│   ├── servico_analitico.py  # Indicadores e integração dos cálculos
│   ├── assistente_agente.py  # Ferramentas LangChain e conversa com o Gemma
│   ├── chats.py              # Histórico privado em PostgreSQL
│   ├── cadastro_contas.py    # Primeiro acesso por código de uso único
│   ├── importacao/           # Leitura, validação e processamento de arquivos
│   └── ...                   # Autenticação, dataset, estatística e classes
├── scripts/                  # Preparação e administração local
├── templates/                # Páginas HTML/Jinja
├── static/                   # CSS, JavaScript e biblioteca Plotly
├── prompts/                  # Instruções editáveis do assistente
├── sql/                      # Estrutura e migrações do banco
├── data/                     # Exemplos e dataset sintético
├── tests/                    # Testes automatizados
├── docs/                     # Guias, PDF de requisitos e evidências
│   ├── capturas/             # Demonstração e verificação
│   ├── originais/            # Documentos originais do projeto
│   └── wireframes/           # Wireframes do grupo
├── referencias/marco_1/      # Código anterior preservado para consulta
├── .env.example              # Modelo de configuração, sem credenciais
├── requirements.txt          # Dependências Python
└── iniciar_windows.bat       # Atalho para iniciar no Windows
```

A aplicação atual é a de `simpa/`. O código anterior permanece em `referencias/marco_1/` e no histórico Git. Os documentos e o PDF existente foram preservados.

## Instalação no Windows

Pré-requisitos: **Python 3.11 ou superior** e o **servidor PostgreSQL** instalado e em execução. O pgAdmin é uma interface de administração; instalar apenas o pgAdmin não instala necessariamente o servidor.

1. Clone o repositório e abra o PowerShell na pasta do projeto:

   ```powershell
   git clone https://github.com/Mercus-af/Projeto-SIMPA.git
   cd Projeto-SIMPA
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m scripts.configurar_env
   ```

2. No PostgreSQL, crie um banco vazio chamado `simpa`, pelo pgAdmin ou por SQL:

   ```sql
   CREATE DATABASE simpa;
   ```

3. Edite o `.env` criado na raiz e informe a conexão local:

   ```dotenv
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=simpa
   DB_USER=postgres
   DB_PASSWORD=sua_senha_local
   ```

   O script gera `SECRET_KEY` ao criar o arquivo. Um `.env` existente é preservado. Não publique nem compartilhe esse arquivo.

4. Prepare as tabelas, crie sua conta e inicie:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.preparar_banco --demo
   .\.venv\Scripts\python.exe -m scripts.criar_usuario
   .\.venv\Scripts\python.exe app.py
   ```

Abra **http://127.0.0.1:5000**. Para o primeiro acesso, crie uma conta de professor e selecione as ofertas de turma/disciplina no comando de criação de usuários. Não existe senha padrão.

`--demo` é opcional: acrescenta 35 alunos fictícios com prefixo `IADEMO-`, VA1 concluída, VA2 parcial e VA3 pendente. Para preparar a estrutura sem esses alunos, execute sem `--demo`.

O preparador aplica as migrações e configura as cinco disciplinas iniciais do curso. Não é necessário executar manualmente cada SQL. `sql/base_original_manual.sql` é uma referência da estrutura original, não um comando de atualização para banco já preenchido.

### Atualizar uma instalação existente

Faça backup do banco, encerre o servidor com `Ctrl+C` e execute na raiz:

```powershell
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.preparar_banco
.\.venv\Scripts\python.exe app.py
```

Atualize o navegador com `Ctrl+F5`. Os comandos de preparação agora ficam em `scripts/` e são executados com `-m scripts.nome_do_comando`. O `.env` e a `.venv` continuam na raiz. O comando para iniciar permanece `python app.py`.

## Contas e primeiro acesso

**Professor:** conta criada pelo responsável usando `scripts.criar_usuario`, com atribuição das disciplinas e turmas. Não há cadastro público de professor.

**Aluno pelo site:** primeiro, o professor cadastra a ficha acadêmica em **Alunos**. Depois abre o perfil e usa **Gerar código de cadastro**. O aluno recebe esse código diretamente do professor e acessa **Cadastrar-se no SIMPA**, no login, informando matrícula, e-mail institucional, código, senha e confirmação.

O código vale **48 horas**, tem uso único e é armazenado como hash. Gerar outro invalida o anterior. A conta usa a matrícula existente e define o perfil de aluno no servidor. Não cria outra ficha acadêmica. O comando local também permite criar contas de aluno vinculadas às matrículas.

## Regras acadêmicas

O curso trabalha com **VA1, VA2 e VA3**, cada uma na escala de 0 a 100 pontos. A composição adotada ainda é **provisória**, pois depende de confirmação das regras institucionais.

| Componente | Máximo inicial por VA |
| --- | ---: |
| Bloco de APS, Dailys e atividades personalizadas | 30 |
| A360 | 10 |
| VRAU | 30 |
| AFE | 30 |
| **Total** | **100** |

- APS vale inicialmente até 2 pontos; Daily, até 3. A quantidade de atividades é cadastrada pelo professor.
- **Personalizado** permite outro valor máximo, com até duas casas decimais. Usa o mesmo bloco das atividades; não é bônus acima dos 100 pontos.
- Nenhuma nota pode ultrapassar o máximo da atividade. O sistema não corta nem redistribui pontos automaticamente.
- Campo vazio é pendência; zero é nota válida. Pendência pode indicar falta de lançamento e não comprova falta de entrega.
- Encerrar a VA exige distribuição completa do bloco e todas as notas dos matriculados. A VA encerrada fica bloqueada; o professor responsável pode reabri-la.
- Média final por disciplina: **(VA1 + VA2 + VA3) ÷ 3**, após as três VAs completas e encerradas.
- O critério de aprovação ainda não foi informado. O sistema não declara aprovação/reprovação nem inventa um corte de risco.

A seção de edição da composição foi retirada de Avaliações. As validações e a configuração das regras permanecem no backend. Dados antigos por bimestre são preservados, sem conversão automática para as VAs.

## Estatística e predição

Os módulos Python calculam média, mediana, variância e desvio-padrão populacionais (divisor `n`). Valores ausentes são excluídos; zeros participam dos cálculos. No curso de IA, frequência agregada é **soma das presenças ÷ soma das aulas registradas × 100**.

Também há correlação de Pearson e regressão linear simples. Correlação descreve associação, não prova causa. As previsões exigem histórico suficiente e são estimativas exploratórias; **R² descreve ajuste ao histórico, não precisão futura**. No curso, usam VAs encerradas até o período consultado e não criam VA4.

Os cálculos são executados em Python e expostos pela API Flask. O navegador apresenta os resultados em indicadores e gráficos. O modelo de linguagem usa esses resultados para explicar e sugerir acompanhamento.

## Assistente acadêmico

O assistente usa **Gemma 4 pela API do Ollama Cloud**, conectado pelo LangChain. Para habilitá-lo, configure no `.env`:

```dotenv
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=gemma4
OLLAMA_API_KEY=sua_chave_do_ollama
```

Reinicie após alterar a chave. Essa configuração usa o serviço Cloud; não exige baixar o modelo localmente. Sem chave, as outras áreas continuam disponíveis.

O Gemma solicita ferramentas de busca e consulta. O código valida argumentos e permissões, consulta o PostgreSQL e calcula os indicadores. O modelo recebe os resultados e redige a resposta em Markdown. Não há ferramenta de SQL livre, execução de comandos ou alteração de notas.

Fontes e números são verificados antes da exibição. Isso ajuda a bloquear valores inventados, mas não garante que toda interpretação textual esteja correta. Pergunta, trecho de conversa e resultados autorizados necessários são enviados ao Ollama Cloud.

O histórico lateral permite criar, reabrir e apagar chats com confirmação. As mensagens ficam no PostgreSQL, privadas por conta, perfil e vínculo. O modelo recebe as **últimas oito mensagens anteriores** — quatro perguntas e quatro respostas — além da pergunta atual, instruções e seleção acadêmica. As consultas podem ser refeitas para obter valores atuais.

Para estudar ou personalizar:

- [Prompt editável](prompts/assistente_academico.md): tom e instruções, relidos a cada pergunta.
- [Ferramentas e execução](simpa/assistente_agente.py): `@tool`, `bind_tools`, chamadas ao Gemma e validação.
- [Consultas e permissões](simpa/repositorio.py): SQL e escopo acadêmico.
- [Histórico persistente](simpa/chats.py): leitura e gravação das conversas.
- [Guia do assistente](docs/ASSISTENTE_ACADEMICO.md): arquitetura e limites.

## Dataset do professor

São **15 CSVs normalizados**, com manifesto e hashes, de uma base **inteiramente sintética de Engenharia de Software**: 120 alunos, 40 disciplinas e 2.949 registros acadêmicos. Essa base é separada das VAs de IA e não cria contas.

Após preparar o banco, carregue com:

```powershell
.\.venv\Scripts\python.exe -m scripts.importar_dataset_professor
```

A carga usa uma transação no schema `simpa_dataset`. Repetir a mesma carga não duplica registros. No Dashboard, use **Base de dados → Dataset do professor**. Selecione semestre e aluno; o histórico individual usa médias finais por semestre e pode apresentar projeção quando há ao menos dois semestres concluídos.

Semestre em andamento usa notas parciais. A frequência dessa base é a média dos percentuais disponíveis, pois não há contagem de aulas/presenças para esse cálculo. Indicadores de risco e desfechos fornecidos no material são referências recebidas, não previsões produzidas pelo SIMPA. Veja o [guia do dataset](docs/DATASET_PROFESSOR.md).

## Importação pela interface

CSV UTF-8 e XLSX, até **2 MB e 10.000 linhas**, usando os modelos para download na tela:

| Tipo | Colunas obrigatórias |
| --- | --- |
| Alunos | `matricula`, `nome`, `email`, `turma_id` |
| Notas por atividade | `matricula`, `atividade_id`, `nota` |

A atividade deve existir e o aluno precisa pertencer à turma autorizada. Notas preenchidas são recusadas; correções são feitas em Avaliações. Erros são informados por linha; arquivo com falha estrutural não é importado. A carga dos CSVs normalizados do professor usa o comando específico acima, não esse formulário.

## API e testes

As rotas usam a mesma autenticação e permissões das telas. Alterações exigem token CSRF. A referência de endpoints está em **`/api/docs`**, após entrar como professor. **`/saude`** informa o estado básico e a versão.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Em 05/11/2026, os **81 testes passaram** após a reorganização, em um banco PostgreSQL descartável novo. A verificação está em [docs/verificacao_organizacao.json](docs/verificacao_organizacao.json).

Os testes de integração só executam quando `SIMPA_TEST_DSN` aponta para um **banco descartável**, pois criam usuários, turmas, atividades e notas. Sem a variável, esses casos são pulados. Para a suíte completa, crie um banco separado e configure somente no terminal de testes:

```powershell
$env:SIMPA_TEST_DSN='postgresql://usuario:senha@localhost:5432/simpa_teste'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SIMPA_TEST_DSN
```

**Não use o banco da apresentação ou de uso real.** O provedor é simulado nos testes automatizados. Registros de verificações anteriores com o Gemma real, usando dados fictícios, estão em `docs/`.

## Documentação

- [Requisitos por aba — PDF](docs/SIMPA_Marco_2_Requisitos_Por_Aba.pdf)
- [Descrição do Marco 2](docs/MARCO_2.md)
- [Integração e autoria](docs/INTEGRACAO_E_AUTORIA.md)
- [Roteiro técnico da apresentação](docs/APRESENTACAO.md)
- [Capturas de verificação](docs/capturas/)
- [Wireframes originais](docs/wireframes/)

O projeto está em desenvolvimento para fins acadêmicos. A execução padrão é local; o servidor de desenvolvimento do Flask não representa uma implantação pública de produção.
