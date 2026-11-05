# Assistente acadêmico — consultas e Markdown e histórico (2.6)

## Onde mudar o jeito de responder

Edite **`prompts/assistente_academico.md`**. Esse é o arquivo de instruções do Gemma: tom, tamanho, formato, exemplos e uso das consultas. Ele é lido novamente a cada pergunta, sem necessidade de reiniciar o servidor. Não coloque senha ou chave nesse arquivo: seu conteúdo segue para o modelo no Ollama Cloud.

Você pode, por exemplo, pedir respostas mais curtas, listas de próximos passos ou tabelas em comparações. O Markdown do prompt organiza as instruções; o Markdown da resposta é apresentado com negrito, listas, parágrafos, código e tabelas no chat. A tela continua simples, com filtros no ⚙.

Ao enviar, aparece um símbolo girando com “Processando…”. Depois que a resposta completa passa pelas verificações, o navegador revela o texto gradualmente, preservando o Markdown. Não são mostrados tokens ainda não validados do modelo. A animação respeita a preferência de movimento reduzido; em caso de erro, o indicador desaparece e a pergunta pode ser reenviada.

Editar o prompt não muda permissões nem cria ferramentas. Essas restrições ficam no Python.

## O que mudou em relação à primeira versão

A primeira versão fazia o modelo selecionar IDs de frases prontas. Isso restringia a consulta e produzia respostas pouco pertinentes. A versão 2.5 usa **chamadas de ferramentas do LangChain com ChatOllama**: o modelo pode localizar os dados necessários e escrever sua própria explicação.

“O que você pode me responder?” recebe capacidades e exemplos, sem despejar o boletim. “Consulte minha nota em Álgebra” busca a disciplina e consulta o boletim. “E a frequência nessa mesma disciplina?” mantém a identificação consultada e lê os valores novamente.

## Caminho de uma pergunta

1. O navegador envia a pergunta, filtros e, se houver, um identificador de conversa. Não envia histórico editável, perfil nem chave de API.
2. `assistente.py` valida tamanho, limita concorrência e confere a configuração. A sessão determina o usuário.
3. `assistente_agente.py` confere o acesso, lê o `.md` e prepara as ferramentas daquele perfil.
4. O Gemma decide quais consultas precisa executar. O Python valida os argumentos e executa somente as funções permitidas, usando os repositórios e cálculos do SIMPA.
5. Os resultados retornam ao modelo com fontes. Ele redige a resposta em Markdown, citando `[S1]`, `[S2]` etc.
6. O servidor confere fontes e números contra os resultados daquela pergunta. Pode pedir uma correção ao modelo dentro do mesmo limite de execução.
7. MarkdownIt converte a resposta com HTML bruto desativado; Bleach sanitiza o HTML. Só então o navegador apresenta a resposta.

## Ferramentas e permissões

| Ferramenta | O que consulta |
| --- | --- |
| `listar_vinculos` | Localiza por nome alunos, turmas e disciplinas disponíveis à conta; páginas de 20 registros |
| `consultar_academico` | Notas, componentes, atividades, frequência, pendências, estatísticas e previsões por aluno/disciplina/VA |
| `consultar_regras` | Composição das VAs e valores de APS/Daily/A360/VRAU/AFE existentes nos vínculos da conta |
| `consultar_dataset` | Professor: histórico e previsão da base sintética de Engenharia de Software |

Aluno só consulta a própria matrícula, mesmo que tente passar outro ID. Professor só consulta suas ofertas de turma/disciplina. A ferramenta de dataset nem é oferecida ao aluno. Não há ferramenta de escrita, execução de comandos ou SQL livre. Busca por nome usa os registros já autorizados; as consultas SQL do repositório usam parâmetros.

Uma resposta de consulta traz as fontes em “Fontes e contexto”. Uma conversa geral, sem consulta, não exibe fontes fictícias.

## Conversa e atualização

O painel à direita lista os chats da conta, com título definido pela primeira pergunta e data da última resposta. **Novo chat** cria uma conversa separada. Ao abrir um chat, as mensagens, o Markdown, as fontes e os filtros são restaurados. A URL mantém o chat selecionado ao atualizar a página. Em telas menores, o botão **Chats** abre o histórico lateral.

As conversas ficam nas tabelas `simpa.chats_assistente` e `simpa.mensagens_assistente`, criadas pela migração aditiva `sql/005_historico_chats.sql` (também executada por `preparar_banco.py`). Permanecem após sair, entrar novamente ou reiniciar o servidor. Cada consulta exige o mesmo usuário, perfil e vínculo de aluno; as permissões acadêmicas são verificadas novamente. O modelo recebe somente as últimas quatro interações e a seleção anterior, enquanto a tela pode mostrar a conversa completa.

Uma continuação sobre notas/frequência atualiza a consulta da disciplina anterior. Números antigos não são uma fonte atual. Mudar os filtros inicia outra conversa. **Apagar** abre uma confirmação e exclui o chat e suas mensagens do banco, sem apagar dados acadêmicos. Uma resposta atrasada não recria um chat excluído. Não há recuperação de chats apagados pela interface.

As mensagens passam a ser salvas a partir desta versão. Conversas antigas que existiam apenas na memória do servidor não são recuperadas.

| Rota autenticada | Função |
| --- | --- |
| `GET /api/assistente/chats?pagina=1` | Lista 50 chats por página da conta |
| `POST /api/assistente/chats` | Cria chat com filtros autorizados e token CSRF |
| `GET /api/assistente/chats/<id>` | Abre chat próprio; sanitiza novamente o Markdown salvo |
| `DELETE /api/assistente/chats/<id>` | Exclui chat próprio e mensagens com token CSRF |

## Dados e limites

O Cloud recebe a pergunta, instruções, trecho de conversa e resultados necessários das consultas autorizadas. Em consultas nominais, nomes acadêmicos autorizados são enviados para permitir a resposta solicitada. Senhas, hashes, e-mails, datas de nascimento e a chave do banco não são incluídos pelas ferramentas. A chave Ollama fica no `.env` e segue apenas no cabeçalho HTTPS para `https://ollama.com`.

O controle de execução limita rodadas, consultas e tempo. Falhas de credencial, limite do provedor e rede têm mensagens controladas, sem exibir configuração privada. Resultados extensos são limitados e informam o total ou a paginação.

Números exibidos são conferidos com as consultas, inclusive arredondamentos. Isso ajuda a bloquear valores inventados, mas **não prova que toda interpretação textual esteja correta**: o Gemma continua sendo um modelo generativo. Uma fonte existente ou um número presente no resultado não garantem que a conclusão foi a melhor. As fontes permitem revisão, e os testes avaliam cenários concretos.

## Predição e recomendações

As previsões continuam sendo calculadas pelo Python. No curso de IA, usam VAs encerradas até a avaliação consultada, com pelo menos duas observações e sem criar VA4. No dataset, usam o histórico final até o semestre escolhido. R² descreve ajuste ao histórico, não garante acerto futuro.

O critério institucional de aprovação ainda não foi informado. O assistente não deve declarar aprovação/reprovação nem inventar um corte ou probabilidade de risco. Ausência é diferente de zero e uma pendência pode ser apenas falta de lançamento. As sugestões são orientações para avaliação humana, não alterações automáticas no sistema.

## Arquivos principais

- `prompts/assistente_academico.md`: comportamento editável.
- `assistente_agente.py`: ferramentas, consulta, memória, chamada ao Gemma e Markdown seguro.
- `assistente.py`: configuração, limite de concorrência, cálculo auxiliar e entrada `responder()`. Auxiliares da versão de catálogo foram mantidos para compatibilidade; não são o caminho atual de resposta.
- `chats.py`: consultas parametrizadas, isolamento do histórico e gravação atômica de pergunta/resposta.
- `static/js/assistente.js`: conversa, histórico lateral, confirmação de exclusão, envio de `conversa_id`, HTML sanitizado e fontes.
- `tests/test_chats.py`: seis testes de persistência, exclusão, autenticação e isolamento entre contas/perfis.
- `static/css/assistente.css`: layout do chat e apresentação de Markdown.
- `tests/test_assistente_agente.py`: permissões, fontes, números, histórico, edição do `.md`, ferramentas e sanitização.

## Configuração

Instale `requirements.txt`. No `.env`, configure `OLLAMA_BASE_URL=https://ollama.com`, `OLLAMA_MODEL=gemma4` e `OLLAMA_API_KEY`. Reinicie o aplicativo ao mudar a chave. Para mudar apenas o comportamento, edite o `.md` e envie outra pergunta.

## Verificação desta versão

A suíte automatizada passou com **72 testes**, incluindo seis testes do histórico. Na versão anterior, também foram verificados com o **Gemma real**, exclusivamente em dados fictícios: a pergunta do print, consulta de disciplina pelo nome, continuação sobre frequência, composição APS/Daily, busca de aluno pelo nome, privacidade e projeção do dataset. Os sete cenários passaram na execução final.

O histórico foi verificado no navegador com PostgreSQL descartável e resposta simulada, sem nova chamada ao Cloud: criar, alternar, recarregar o chat selecionado e cancelar a confirmação de exclusão. Sem erros de console. Captura em `capturas/assistente-historico.png`. A exclusão e sua cascata foram verificadas pela suíte de integração. No teste anterior foi reproduzida a pergunta do print, com resposta de capacidades em Markdown. Consulte `verificacao_assistente.json` e `capturas/assistente-markdown.png`. Os testes usam banco descartável. No banco configurado foi aplicada somente a migração aditiva 005 para criar as tabelas de histórico. Esses cenários são uma amostra de qualidade e segurança, não uma garantia sobre todas as perguntas futuras.

Fontes técnicas: [tool calling no Ollama](https://docs.ollama.com/capabilities/tool-calling) e [ChatOllama no LangChain](https://docs.langchain.com/oss/python/integrations/chat/ollama).
