# Verificação — perfis e VAs

Revisão de 30/10/2026. Foram executados **19 testes: sete de cálculo e doze de integração**, todos aprovados.

## Cálculos

- Exemplo de VA com 80 pontos, incluindo APS/Dailys 24, A360 8, VRAU 22 e AFE 26.
- Zero distinto de ausência; nenhum lançamento não vira zero.
- Planejamento incompleto mantém a VA parcial.
- Média final exige as três VAs encerradas; médias 80, 70 e 90 resultam em 80.
- Limites, números não finitos e precisão decimal validados.
- Estatística e regressão na escala de 0 a 100.

## Permissões e persistência

- Login e perfil conferidos no banco, sem confiar em perfil enviado pela sessão/cliente.
- Aluno vê apenas a própria matrícula e suas notas, inclusive na consulta direta de uma atividade.
- Aluno não acessa áreas de professor, importação nem escrita de notas.
- Professor não lê nem altera notas de disciplina sem vínculo.
- Conta inativada perde acesso com sessão já existente.
- O bloco de 30 pontos é respeitado sem fixar seis encontros: o teste também usa quinze APS.
- Encerramento exige planejamento e todas as notas. VA encerrada bloqueia edição; reabertura permite corrigir.
- Alteração de composição não corta nota já lançada.
- Importação usa a mesma transação e as mesmas permissões, aceita linhas válidas e rejeita CSV estruturalmente inválido sem carga parcial.
- Páginas dos dois perfis renderizam, VA4 é rejeitada e filtro por bimestre não é aceito.

## Navegador Edge

Foi verificado o fluxo professor → criar APS → lançar zero → aluno consultar o próprio boletim. O painel do professor mostrou cinco disciplinas, quatro cartões e o gráfico compacto. Os filtros VA1/VA2 alteraram os indicadores.

O aluno apresentou somente a própria matrícula na resposta da API e recebeu HTTP 403 ao tentar criar atividade. As cinco disciplinas apareceram no seu painel e a média final permaneceu ausente com VAs pendentes. Não houve erros JavaScript ou respostas HTTP 5xx.

Em 390 pixels, a largura do documento também foi 390 pixels. As capturas usam somente alunos fictícios e contas do ambiente isolado.

## Ambiente e banco local

Os testes foram executados com Python, Flask, psycopg2 e PostgreSQL/PGlite isolado. Depois foi gerado e validado um backup completo do PostgreSQL 18 local antes da migração. A conta existente e os 1.120 registros antigos foram preservados; as cinco disciplinas e as tabelas de VAs foram acrescentadas. Não foram criadas senhas padrão no banco local.

Na instalação local, dashboard, alunos, disciplinas, turmas, avaliações, dados, análises e documentação retornaram HTTP 200 com a conta existente de professor. Foram confirmados 35 alunos novos de demonstração, cinco disciplinas, escala 100, VA2 padrão e critério de aprovação ausente. O servidor local foi reiniciado e confirmou a versão 2.1 em `/saude`.
