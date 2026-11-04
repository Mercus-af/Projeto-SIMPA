# SIMPA — Marco 2: professores, alunos e VAs

Aplicação Flask com PostgreSQL, login, notas por atividade, estatística e dashboard enxuto baseado no wireframe. O curso usa **VA1, VA2 e VA3**, com escala de **0 a 100**. A composição continua identificada como provisória.

## Dataset do professor — versão 2.2

O seletor **Base de dados** do dashboard do professor permite alternar entre **Curso de IA · VAs** e **Dataset do professor**. A segunda opção usa o material sintético de Engenharia de Software: 120 alunos, 40 disciplinas e 2.949 registros acadêmicos. Não modifica as contas, disciplinas nem notas do curso de IA e não transforma N1/N2/projeto em VAs.

Para carregar em outra instalação, execute uma vez após preparar o banco:

```powershell
.venv\Scripts\python.exe importar_dataset_professor.py
```

Os 15 CSVs normalizados estão incluídos em `data/dataset_professor/`, com manifesto de origem e hashes SHA-256. O importador usa uma transação, valida a edição recebida e grava no schema separado `simpa_dataset`. Repetir a mesma carga não duplica registros. Não é necessário executar o SQL SQLite fornecido no material.

No dashboard, escolha o semestre. Com todos os alunos, o gráfico compara médias por período curricular da disciplina. Ao selecionar um aluno, o mesmo gráfico mostra médias finais por semestre e uma projeção linear, quando houver ao menos dois semestres concluídos. A análise respeita o semestre consultado: não utiliza notas finais de semestres posteriores. O gráfico de frequência permanece ao lado; não foram adicionados histogramas ou rankings.

O semestre em andamento usa notas parciais e informa quantos registros têm nota/frequência. Ausência não vira zero. A frequência desta base é a média dos percentuais disponíveis por registro, diferente da razão presenças/aulas do curso de IA. A série temporal descreve desempenho global, com disciplinas que podem mudar entre semestres. R² mede ajuste ao histórico, não precisão futura. Indicadores prontos de risco e desfechos são preservados como referência, sem alimentar os cálculos ou previsões.

API exclusiva de professores: `/api/dataset-professor?semestre=2026-2&aluno_id=120`. O filtro de aluno é opcional. Alunos autenticados continuam restritos ao próprio boletim de IA.

Veja `docs/DATASET_PROFESSOR.md` para arquitetura, critérios de interpretação e demonstração.

## Para quem já estava usando esta pasta

Pare o servidor com `Ctrl+C`. As tabelas novas devem ser preparadas sem apagar as antigas:

```powershell
.venv\Scripts\python.exe preparar_banco.py --demo
.venv\Scripts\python.exe app.py
```

Atualize o navegador com `Ctrl+F5`. As contas antigas permanecem como professor. Se houver apenas um professor e nenhum vínculo configurado, a preparação vincula essa conta às cinco disciplinas da turma inicial de IA. As contas seguintes recebem as disciplinas escolhidas no cadastro local.

Nesta instalação local, a atualização já foi executada com backup prévio em `../backups/`; as contas e os 1.120 registros antigos por bimestre foram preservados. O backup contém dados privados e não faz parte do ZIP.

## Primeira instalação no Windows

Pré-requisitos: Python 3.11+ e PostgreSQL. Crie o banco `simpa` no pgAdmin. No PowerShell **nesta pasta**:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe configurar_env.py
```

Preencha `DB_PASSWORD` no `.env` com a senha do PostgreSQL e confira `DB_HOST`, `DB_PORT`, `DB_NAME` e `DB_USER`. O `.env` não deve ser compartilhado nem enviado ao Git. O script gera `SECRET_KEY` sem sobrescrever um `.env` existente.

```powershell
.venv\Scripts\python.exe preparar_banco.py --demo
.venv\Scripts\python.exe criar_usuario.py
.venv\Scripts\python.exe app.py
```

Abra **http://127.0.0.1:5000**. O servidor usa somente o endereço local. Não há senha padrão.

## Criar contas

Execute `criar_usuario.py` no terminal:

- **1 — Professor:** informe os dados e escolha as ofertas de turma/disciplina, pelos números apresentados ou `todas`.
- **2 — Aluno:** informe uma matrícula já cadastrada. A conta fica vinculada a esse aluno; nomes e notas de colegas não são disponibilizados.

Na demonstração, as matrículas começam com `IADEMO-`, por exemplo `IADEMO-20260001`. Cada pessoa define sua própria senha. Não existe escolha de perfil nem criação de conta de professor pelo navegador.

## Cadastrar turma — versão 2.3

Entre como professor e abra **Turmas → Cadastrar turma**. Informe nome, identificador, ano letivo, semestre e situação. Selecione ao menos uma das disciplinas ativas já vinculadas à sua conta. O mesmo identificador pode ser reutilizado em outro ano/semestre, mas não no mesmo contexto acadêmico.

A criação é feita em uma transação: turma, ofertas, vínculo do professor e composição inicial de VA1/VA2/VA3. A360, VRAU e AFE ficam preparados para cada disciplina; APS e Dailys serão cadastradas pelo professor. Não são criados alunos, notas ou credenciais. A nova turma já aparece no cadastro de alunos e suas disciplinas aparecem em Avaliações. Outro professor precisa receber seu próprio vínculo para acessá-la.

O formulário mantém os dados preenchidos quando há erro de validação ou duplicidade. Também existe `POST /api/turmas`; formato em `/api/docs`. Usa as tabelas existentes: não é necessário executar migrações para esta funcionalidade. Após atualizar o código, reinicie o servidor se ele ainda estiver executando uma versão anterior.

## Regras implementadas

| Componente | Máximo inicial por VA |
|---|---:|
| APS + Dailys | 30 |
| A360 | 10 |
| VRAU | 30 |
| AFE | 30 |
| **VA** | **100** |

- Cada APS vale inicialmente até 2 pontos; cada Daily, até 3. O professor cadastra a quantidade necessária, sem fixar seis encontros no sistema.
- APS e Dailys não podem distribuir mais que o limite do bloco. O sistema não corta notas nem redistribui pontos automaticamente.
- A360, VRAU e AFE são preparados uma vez em cada VA. VRAU corresponde à prova de até 30 pontos informada pelo grupo; o professor lança o resultado, sem correção automática das 15 questões.
- Campo vazio é **pendente**. Zero é uma nota válida e participa dos totais.
- O resultado da VA permanece **parcial** enquanto faltarem notas, distribuição do bloco ou encerramento pelo professor.
- Para encerrar uma VA, o bloco de APS + Dailys deve estar todo distribuído e todas as notas dos matriculados devem estar lançadas.
- VA encerrada fica bloqueada para edição. O professor responsável pode reabri-la para corrigir e depois encerrá-la novamente.
- A média final é `(VA1 + VA2 + VA3) / 3`, somente após as três estarem encerradas. VA pendente não entra como zero.
- O professor pode ajustar os limites na seção de composição. O total permanece em 100; não é permitido reduzir um limite abaixo de nota já lançada nem mudar o valor unitário de APS/Daily já cadastrada.
- A média mínima de aprovação permanece **não definida**. A aplicação não classifica aprovado/reprovado nem calcula risco usando os limites antigos de 0–10.

## O que cada perfil vê

**Professor:** dashboard, alunos, turmas, disciplinas, avaliações e importação, sempre limitados às suas ofertas. Em Avaliações, escolhe turma/disciplina e VA, cria APS/Daily e abre a planilha de notas de cada atividade.

**Aluno:** Meu painel e Minhas notas. Consulta as cinco disciplinas em que estiver matriculado, os resultados de cada VA, os componentes, as atividades pendentes e a média final quando disponível.

Permissões são conferidas novamente no servidor a cada requisição. Esconder os links do menu é apenas parte da interface: a API também bloqueia acessos e alterações sem vínculo. Uma conta inativada perde acesso mesmo que ainda tenha cookie de sessão.

## Dados de demonstração e preservação

As disciplinas do curso são Álgebra Linear e Aplicações; Desenvolvimento Orientado a Objetos; Design de Soluções; Estatística Aplicada e Modelagem de Soluções; Fundamentos de Redes e Segurança da Informação.

`--demo` acrescenta 35 alunos fictícios na turma de IA: VA1 concluída, VA2 parcial e VA3 pendente. A quantidade de seis encontros usada no exemplo da VA1 é somente uma demonstração possível. Os cadastros usam prefixo `IADEMO-`. Nenhuma conta de aluno ou senha compartilhada é criada automaticamente.

As tabelas antigas de resultados por bimestre são preservadas. Não há conversão automática de notas antigas em VAs ou de 0–10 para componentes de 100 pontos, pois isso inventaria uma composição que não foi informada. A nova demonstração é separada dos dados anteriores e não os sobrescreve.

## Importação

CSV UTF-8 e XLSX, até 2 MB e 10.000 linhas. Baixe o modelo na tela:

- Alunos: `matricula;nome;email;turma_id`.
- Notas: `matricula;atividade_id;nota`.

A atividade deve existir e pertencer à disciplina do professor. O aluno precisa estar matriculado na turma. A nota não pode ultrapassar o máximo da atividade. A importação recusa notas já preenchidas; faça correções na tela Avaliações. Erros por linha são relatados; falha estrutural impede a carga inteira.

## Organização e verificação

`app.py` controla páginas e API; `repositorio.py` reúne SQL e permissões; `academico.py` define pontos e `ResultadoVA`; `servico_analitico.py` integra VAs e os módulos estatísticos do grupo. Os três arquivos em `sql/` fazem migrações aditivas. `autenticacao.py` e `db.py` mantêm a base de login do grupo.

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

São 34 testes: 13 de cálculo/leitura e 21 de integração. Integração exige `SIMPA_TEST_DSN` apontando **somente para banco descartável**, porque cria contas, turmas e notas de teste. Não use essa variável na base da apresentação.

Os 19 testes passaram em PostgreSQL isolado/PGlite. No Edge, foram verificados ambos os perfis, filtros de VA, lançamento de nota zero, privacidade das notas, bloqueio de escrita pelo aluno e layout de 390 px sem transbordamento da página. A migração local também foi aplicada no PostgreSQL 18 instalado, após backup.

Após a integração do dataset, os 29 testes passaram em banco PGlite/PostgreSQL isolado. A API foi conferida no PostgreSQL 18 local e o fluxo seletor → API → gráfico foi verificado no navegador. O registro em `docs/DATASET_PROFESSOR.md` distingue essa verificação das verificações anteriores do curso de IA.

Em 01/11/2026, após o cadastro de turmas, os 34 testes passaram no banco descartável. Os novos casos verificam duplicidade por contexto, campos obrigatórios, vínculo às disciplinas, preparação das VAs, ausência de notas inventadas, integração ao cadastro de alunos, perfis e CSRF. No navegador foi executado o fluxo Turmas → Cadastrar turma → salvar → consultar na lista, somente no banco de testes.

Veja `docs/MARCO_2.md`, `docs/APRESENTACAO.md` e `/api/docs` após entrar como professor.
