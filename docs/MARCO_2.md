# SIMPA — módulo analítico com perfis e avaliações por VA

Curso de Inteligência Artificial, 2º período. Revisão de 30/10/2026.

## Objetivo e organização

O SIMPA transforma dados acadêmicos em indicadores e permite acompanhamento por dois perfis. O professor trabalha com os alunos das ofertas de turma/disciplina que lhe foram atribuídas. O aluno acompanha somente suas próprias notas, atividades e frequência.

O curso possui cinco disciplinas: Álgebra Linear e Aplicações; Desenvolvimento Orientado a Objetos; Design de Soluções; Estatística Aplicada e Modelagem de Soluções; Fundamentos de Redes e Segurança da Informação. Cada uma possui VA1, VA2 e VA3. A VA atual informada pelo grupo é a VA2.

## Regras de negócio discutidas com o grupo

A composição provisória de uma VA é de 100 pontos: APS + Dailys até 30, A360 até 10, VRAU até 30 e AFE até 30. Uma APS vale inicialmente até 2 e uma Daily até 3. A quantidade de atividades não é fixa. VRAU é a prova de 15 questões informada pelo grupo; a aplicação recebe sua pontuação total, sem presumir regras de correção por questão.

O professor cria as atividades e lança notas por aluno. Os máximos são validados antes de salvar. O bloco de APS + Dailys não pode ultrapassar a pontuação configurada. Não se corta um excedente nem se normaliza uma nota silenciosamente. A configuração da VA precisa continuar somando 100 pontos e preservar lançamentos existentes.

Nota ausente é `null`, exibida como Pendente. Nota zero é válida. O total parcial soma somente os pontos já lançados e não substitui a nota final. Se ainda não há nenhum lançamento, o total é ausente, em vez de zero.

Uma VA só pode ser encerrada após distribuir todo o bloco de atividades e preencher todas as notas dos alunos matriculados. Encerramento bloqueia edição; reabertura exige o professor responsável. Uma matrícula acrescentada posteriormente não inventa notas anteriores nem reabre as disciplinas dos outros professores.

A média final de uma disciplina é `(VA1 + VA2 + VA3) / 3`, na escala de 0 a 100. Só é apresentada após as três VAs estarem encerradas e completas. A aplicação não preenche uma VA futura com zero para antecipar a média. A nota mínima de aprovação não foi confirmada: por isso, o sistema não emite resultado oficial de aprovação ou classificação de risco pelos critérios antigos.

## Entidades e arquitetura

Fluxo: **conta autenticada → permissão por vínculo → PostgreSQL → ResultadoVA e módulos estatísticos → API → tela apropriada ao perfil**.

As entidades principais são Usuário, Aluno, Turma, Disciplina, Oferta de disciplina, Regra da VA, Atividade, Nota e Frequência. `ResultadoVA` reúne a composição e o estado de conclusão sem acessar o banco. `RepositorioAcademico` concentra SQL e conferência de vínculos. As rotas não confiam em perfil ou aluno informados no navegador para definir a identidade de quem acessa.

Tabelas novas:

- `usuarios.perfil` e `usuarios.aluno_id`: tipo de conta e vínculo individual.
- `professor_disciplinas`: permissões por oferta.
- `regras_va`: limites e encerramento por disciplina/turma/VA.
- `atividades_va`: APS, Daily, A360, VRAU e AFE, com máximo e data opcional.
- `notas_atividades`: valor individual, autor e data de atualização.
- `frequencias_va`: aulas e presenças por aluno/disciplina/VA.

As tabelas anteriores permanecem no banco. As notas de bimestres não são convertidas automaticamente porque não informam os componentes das VAs.

## Estatística e interpretação

Os indicadores do professor descrevem o recorte de VA e turma em suas disciplinas. Quando os resultados estão incompletos, a tela diz explicitamente pontos parciais. Esses subtotais não devem ser interpretados como médias finais nem usados para comparar alunos sem considerar as pendências.

| Indicador | Cálculo | Interpretação |
|---|---|---|
| Total parcial da VA | soma das notas já lançadas | pontos acumulados até a consulta |
| Média do recorte | soma dos totais disponíveis / quantidade disponível | nível de pontos registrados no recorte |
| Mediana | centro dos totais ordenados | posição central do grupo |
| Variância populacional | soma de `(valor − média)²` / n | dispersão em pontos ao quadrado |
| Desvio-padrão populacional | raiz da variância | dispersão na mesma unidade das notas |
| Frequência | soma das presenças / soma das aulas × 100 | participação ponderada pelo total de aulas |
| Pendências | notas ausentes nas atividades cadastradas | avaliações que ainda não foram lançadas |

O divisor da dispersão é n porque o indicador descreve todo o recorte disponível. Dados ausentes são excluídos dos cálculos, sem virar zero. Exemplo: os totais `[0,50,100]` têm média 50, mediana 50, variância 1.666,6667 e desvio-padrão aproximadamente 40,8248.

O módulo de Pearson continua disponível na API e relaciona pontos médios disponíveis e frequência por aluno. Ele exige dois pares válidos e variação nas medidas; caso contrário, devolve resultado indefinido. Associação não comprova causalidade, e pontuações parciais exigem cuidado na interpretação.

O módulo de regressão usa apenas VAs encerradas da mesma disciplina, turma e aluno, com escala máxima 100. Não trata atividades de disciplinas diferentes como sequência temporal nem usa VA pendente como zero. Com menos de duas VAs encerradas, retorna dados insuficientes. Uma extrapolação depois da VA3 é apenas matemática, não uma VA4 existente no curso.

## Visualizações e uso

O dashboard do professor mantém a composição enxuta do wireframe: quatro cartões, barras de pontos por disciplina, anel de frequência e cinco cadastros recentes. Os filtros são turma e VA. Não há rankings, boxplots ou blocos extensos na visão geral.

O painel do aluno apresenta suas disciplinas, VA1/VA2/VA3 e média final quando disponível. O boletim detalha os componentes e atividades de cada VA. O professor possui uma tela de avaliações para escolher a oferta, cadastrar APS/Daily, abrir a planilha de notas, configurar a composição e encerrar ou reabrir a VA.

## Segurança e integração verificável

Há hash de senha, sessão assinada e token CSRF. A conta é conferida no banco a cada requisição; conta inativa perde acesso. O aluno não recebe notas de colegas nem pode escrever na API. O professor não lança notas em oferta sem vínculo. Alunos podem criar a conta pelo link Cadastrar-se no SIMPA usando matrícula, e-mail e código de uso único gerado pelo professor da turma. O código vale 48 horas. A conta é vinculada à ficha acadêmica existente, com perfil de aluno definido pelo servidor. Contas de professor e seus vínculos continuam sendo criados pelo responsável no script local.

A API `/api/analises?va=2` devolve os indicadores, a dispersão, os resultados de VAs, resumos, correlação e previsões dentro do escopo do usuário. `/api/meu-boletim` é exclusivo do aluno. A importação valida atividade, matrícula, máximo, vínculo e duplicidade de nota preenchida, usando transação e relatório de erros.

## Demonstração e limites

A carga nova contém 35 alunos fictícios de IA. VA1 aparece concluída, VA2 em andamento e VA3 pendente. Os seis encontros usados no exemplo da VA1 apenas demonstram uma distribuição possível para o bloco de 30 pontos; o sistema também aceita outras quantidades que respeitem os limites.

A composição e a regra de aprovação precisam de confirmação do curso. A aplicação é destinada à apresentação local. Recuperação de senha, bloqueio por tentativas, auditoria completa de acessos e distribuição institucional de contas continuam como melhorias para a etapa de consolidação.
