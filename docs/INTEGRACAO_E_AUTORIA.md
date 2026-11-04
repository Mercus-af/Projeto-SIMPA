# Integração do trabalho do grupo

Esta versão aproveita o material entregue pelo grupo e registra as adaptações para que todos consigam explicá-las. Autoria individual só é atribuída quando identificada no próprio arquivo; os demais nomes devem ser preenchidos pelo grupo conforme a divisão real de trabalho.

| Origem recebida | Aproveitamento e adaptação |
|---|---|
| Marco 1 no GitHub `Mercus-af/Projeto-SIMPA` | Classes Aluno e Turma e conceitos de persistência preservados como referência; o resultado atual usa ResultadoVA para os componentes de 100 pontos |
| `modulo1_estatisticas.py` (identificado como Caio Fábio) | Mantido o módulo estatístico, corrigidos exclusão de zero, ausência de dados e falsos destaques com desvio zero |
| `modulo2_parte1.py` | Pearson sem inventar frequência e com resultado indefinido para casos sem variação; interpretação sem causalidade |
| `modulo2_regressao.py` | Reaproveitado para VAs encerradas da mesma disciplina/turma/aluno, na escala 0–100 |
| `modulo3_risco.py` | Preservado como referência do grupo, sem uso na versão atual: a nota mínima de aprovação ainda não foi confirmada |
| `Login/` e `simpa_frontend_inicial/` | Interface, hash, sessão e consultas de usuário reaproveitados; formulários passam a persistir dados e possuem token CSRF |
| `dashboard-academico/` | Base das visualizações, depois simplificadas conforme o wireframe; dados e indicadores obtidos pela API com escopo do usuário |
| Parte 7 de importação | Leitura CSV/XLSX e validações reaproveitadas; PostgreSQL, permissões por oferta e savepoints por linha, com notas por atividade |
| `SIMPA_PostgreSQL.sql` | Preservado em `sql/001_base_original.sql`; complementos aditivos em `002_modulo_analitico.sql` e `003_perfis_e_vas.sql` |

Decisão de integração: uma aplicação Flask concentra interface e API. Essa decisão reúne os componentes novos na mesma origem e permite usar a sessão do login sem administrar dois servidores. O FastAPI do Marco 1 não é necessário para executar esta versão. O banco principal é PostgreSQL, conforme a escolha do grupo.

Mudança no cálculo de dispersão do dashboard: o desvio amostral original foi substituído pelo populacional para coincidir com o módulo Python e com a proposta de descrever a totalidade do recorte disponível. O dashboard não mantém regras de risco paralelas ao backend.

Mudança no modelo: o registro consolidado original não tinha dimensão temporal. A primeira integração acrescentou `avaliacoes` por bimestre. Após esclarecer as regras do curso, foram acrescentadas regras de VA, atividades e notas individuais, sem apagar as tabelas anteriores nem converter notas antigas por suposição.

Documentos antigos do Marco 1 e os arquivos originais de Downloads foram preservados. A exceção autorizada foi criar o `.env` local pedido pelo usuário, com a senha PostgreSQL em branco. A revisão integrada está em uma pasta separada.

## Revisão do dashboard conforme o wireframe

O painel foi simplificado e passou a herdar `base.html`, o mesmo menu e a paleta #0A0A0A / #536B7B / superfícies claras das demais telas. Mantidos quatro cartões, barras por disciplina, anel de frequência e cinco últimos cadastros. Foram retirados rankings, histograma, boxplot e tabelas de análise extensa da visão geral. Os módulos Python e endpoints analíticos continuam disponíveis. Filtros reduzidos a turma e período.

## Regras do curso e acesso por perfil

O período agora é VA1/VA2/VA3. APS/Dailys, A360, VRAU e AFE compõem até 100 pontos conforme a hipótese discutida com o grupo, identificada como provisória. A média final aguarda as três VAs encerradas. O modelo ResultadoVA distingue ponto lançado de nota pendente, sem preencher ausências com zero.

As contas de aluno são vinculadas à própria matrícula. Professores recebem ofertas específicas de turma/disciplina. Os vínculos são conferidos nas telas e APIs, e a conta é recarregada do banco a cada requisição. O código original de risco não participa da análise enquanto o critério de aprovação não for confirmado.


## Integração do dataset do professor

O material sintético de Engenharia de Software foi fornecido pelo professor ao grupo. Sua cópia está identificada em `data/dataset_professor/manifesto.json`. A adaptação PostgreSQL, o importador e a visão histórica são código de integração novo; reutilizam os módulos estatísticos do grupo. Os arquivos de indicadores de risco recebidos são referências, sem reapresentação como cálculos do SIMPA. O modelo de notas de IA e as atribuições de professores foram preservados.
