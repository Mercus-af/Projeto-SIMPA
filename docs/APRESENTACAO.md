# Roteiro — perfis, VAs e análise do Marco 2

1. Explicar a evolução: cadastro/consulta do Marco 1 agora alimentam resultados, estatísticas e duas visões de acesso.
2. Mostrar o professor: suas disciplinas, turma e seleção de VA1/VA2/VA3. Explicar os componentes de 100 pontos, ainda provisórios.
3. Abrir Avaliações, cadastrar uma APS de até 2 pontos e lançar uma nota zero. Explicar a diferença entre zero e pendente.
4. Voltar ao dashboard e observar os indicadores recalculados. Explicar média, mediana e desvio-padrão, com o exemplo `[0,50,100]` se necessário.
5. Comparar VA1 concluída e VA2 parcial sem chamar os pontos parciais de média final. Mostrar o total de pendências.
6. Entrar como aluno e consultar o boletim individual: componentes, atividades e VAs. Demonstrar que não há acesso aos colegas nem à tela de lançamento.
7. Explicar o encerramento: planejamento completo + todas as notas lançadas; reabertura para correção. Mostrar que a média final aguarda as três VAs.
8. Apresentar `/api/analises?va=2` como professor e explicar o caminho: permissão → repositório → ResultadoVA → módulos estatísticos → JSON → gráfico.
9. Se apresentar Pearson e regressão, explicar seus limites. A regressão exige duas VAs encerradas; com uma só, o resultado correto é dados insuficientes.
10. Demonstrar importação de notas com uma linha inválida, preservando as demais, e explicar o relatório.

Ensaiem com contas separadas e no computador da apresentação. Cada integrante deve saber explicar a parte que produziu e o fluxo completo. A nota mínima de aprovação não foi confirmada e não deve ser inventada na fala ou no código.
# Demonstração adicional com o dataset do professor

No Dashboard, alterne Base de dados para Dataset do professor. Mostre 120 alunos e 600 registros em 2026-2, com notas parciais e frequências ausentes identificadas. Ao escolher um aluno com histórico, o mesmo gráfico passa a mostrar médias finais por semestre e projeção. Explique que são dados fictícios de Engenharia de Software, sem conversão para as VAs do curso de IA. Pearson e os detalhes do método aparecem na seção recolhida de interpretação. As regras e resultados de risco recebidos no material não são cálculos do SIMPA. Consulte `DATASET_PROFESSOR.md` para limites e roteiro.
