/** A mesma sessão do login acessa a API Flask; não há mais leitura de JSON estático. */
export async function buscarAPI(url){
  const resposta=await fetch(url,{cache:'no-store'});
  if(resposta.status===401){window.location.assign('/login');throw new Error('Sessão encerrada.');}
  const dados=await resposta.json();
  if(!resposta.ok) throw new Error(dados.erro||`Falha HTTP ${resposta.status}`);
  return dados;
}
export async function carregarDados(){
  const base=await buscarAPI('/api/dados');
  return {...base,avisos:[],fonte:'api',carregadoEm:new Date()};
}
