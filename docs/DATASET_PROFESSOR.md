# Dataset do professor no SIMPA

## Origem e separação

Material fornecido pelo professor ao grupo em `Arquivos Dataset-20261030`. Curso de Engenharia de Software, dados inteiramente sintéticos, escala de 0 a 100. Foram preservados os 15 CSVs normalizados, o dicionário de dados e a descrição original. O manifesto registra contagens, campos, tipos, nulidade e SHA-256 de cada CSV. Não foram convertidas N1, N2 ou notas de projeto para APS/Daily/A360/VRAU/AFE.

O schema `simpa_dataset` possui suas próprias entidades e identificadores. Não há vinculação dos alunos fictícios a contas de acesso, nem concessão de novas permissões de lançamento no curso de IA. Somente professores podem consultar esta demonstração. As tabelas `indicadores_risco` e `desfechos_alunos` são referências recebidas, não resultados produzidos pelo SIMPA e não entradas de previsão.

## Fluxo

1. `importar_dataset_professor.py` verifica os arquivos da edição incluída e carrega uma única transação usando `sql/004_dataset_professor.sql`.
2. `RepositorioDatasetProfessor` consulta registros, matrículas, turmas, disciplinas e períodos por junções PostgreSQL.
3. `analise_historica.py` seleciona semestre e aluno, preserva nulos e usa os módulos estatísticos do grupo.
4. `GET /api/dataset-professor` entrega os cálculos e a cobertura.
5. O dashboard permite alternar a base. Um gráfico mostra a comparação geral ou, ao escolher aluno, o histórico individual. A frequência permanece em um segundo gráfico.

O script não executa o `schema_sqlite.sql` recebido. A adaptação PostgreSQL contém chaves estrangeiras, unicidade e limites de notas/frequência. A carga aceita somente a edição de referência; outra edição requer revisão explícita. Repetir a mesma carga é seguro e não sobrescreve dados.

## O que significa cada indicador

- Unidade de análise: um registro acadêmico, correspondente a uma tentativa de matrícula em turma. Tentativas distintas são preservadas e participam como registros separados.
- Média, mediana, variância e desvio-padrão: calculados sobre as notas disponíveis do campo selecionado. Semestre com registros em curso usa `nota_parcial`; demais semestres usam `nota_final`. Zero é incluído e campo vazio é excluído, com contagem exposta. Variância e desvio-padrão populacionais, divisor n.
- Frequência: média simples dos percentuais disponíveis por registro. Não se inventam presenças ou totais de aulas. Não é a mesma agregação do curso de IA.
- Gráfico geral: médias por período curricular da disciplina no semestre consultado. Não significa acompanhar a mesma turma entre períodos.
- Pearson: pares de frequência média e média de notas por aluno, ambos disponíveis no recorte. Informa n e retorna indefinido quando não há variação ou pares suficientes. Não comprova causalidade.
- Série individual: média de notas finais por semestre, somente até o semestre escolhido. As disciplinas e tentativas podem mudar; descreve desempenho global e não a mesma disciplina repetida.
- Regressão: reta por mínimos quadrados sobre a série individual, com ao menos dois semestres e limite de projeção 0–100. Informa o semestre projetado, inclinação, n e R² de ajuste. Valores próximos de zero de inclinação e R² não devem ser apresentados como evidência forte de tendência.
- Resultados parciais não podem ser usados isoladamente para afirmar piora diante de resultados finais. Os indicadores abaixo do gráfico referem-se ao recorte selecionado, não à série histórica inteira.

## Demonstração curta

Entre como professor, abra Dashboard e selecione Dataset do professor. Em 2026-2 há 120 alunos e 600 registros, com 597 notas parciais e 592 frequências disponíveis. Mostre os campos ausentes e explique por que não viram zero. Selecione um aluno dos últimos períodos para mostrar seu histórico e a projeção. Compare um semestre anterior e confirme que semestres futuros somem do histórico. Alunos do início do curso não possuem histórico final suficiente, e o sistema explica essa limitação.

No exemplo do aluno 120: sete semestres concluídos, projeção 2026-2 de 67,29 pontos. A inclinação é pequena e R² é aproximadamente 0,001; o exemplo comprova execução, não qualidade preditiva. Para discutir tendência, examine também séries com variação maior, sempre mostrando a reta como estimativa exploratória.

## Verificação em 30/10/2026

- 29 testes passaram: 7 cálculos do curso, 6 testes de cálculo/leitura do dataset, 4 integrações do dataset e 12 integrações do curso, em banco descartável PGlite/PostgreSQL.
- Casos: zero versus ausência, tentativa distinta, frequência por percentuais, filtro inválido, aluno sem histórico, regressão sem acesso ao futuro, carga de 15 arquivos, idempotência, isolamento entre bases e permissões de professor/aluno.
- Importação local PostgreSQL 18: 4.128 linhas distribuídas em 15 tabelas, incluindo 2.949 registros acadêmicos. Backup criado e verificado antes da carga. Contagens e hashes de conteúdo das 16 tabelas preexistentes do schema `simpa` permaneceram iguais.
- Consultas locais retornaram 200 para o dashboard de IA, seus dados e as novas rotas de página/API do dataset. A repetição do importador retornou `ja_importado`.
- Navegador com banco descartável: login de professor, seletor de base, visão geral e histórico do aluno 120 executados; sem erros de console no fluxo verificado. Captura em `capturas/dataset-historico.png`. Não representa a conta pessoal do usuário.

Não foi implementada classificação de risco do curso de IA, nem se confirmou sua nota mínima. O dataset não altera essas regras.
