/** Dashboard resumido do SIMPA, seguindo o wireframe do grupo. */
import { carregarDados, buscarAPI } from './dataService.js';

const $=id=>document.getElementById(id);
const formatar=(valor,casas=1)=>valor===null||valor===undefined?'—':valor.toLocaleString('pt-BR',{minimumFractionDigits:casas,maximumFractionDigits:casas});
const percentual=valor=>valor===null||valor===undefined?'—':`${formatar(valor)}%`;
const textoSeguro=texto=>String(texto).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let base=null;
let pedido=0;

function preencherFiltros(){
  for(const t of base.turmas){const o=new Option(t.nome,t.id);$('filtro-turma').add(o);}

}

function desenharNotas(analise){
  const notas=analise.recorte.notas;
  const medias=new Map();
  for(const n of notas){
    if(n.nota===null)continue;
    const grupo=medias.get(n.disciplinaId)||[];
    grupo.push(n.nota);medias.set(n.disciplinaId,grupo);
  }
  const disciplinas=base.disciplinas.filter(d=>medias.has(d.id));
  const el=$('grafico-notas');
  if(!disciplinas.length){
    if(el.data)Plotly.purge(el);
    el.replaceChildren();const mensagem=document.createElement('div');
    mensagem.className='dashboard-empty';mensagem.textContent='Nenhuma nota registrada neste período.';el.append(mensagem);
  }else{
    if(!el.data)el.replaceChildren();
    const estilo=getComputedStyle(document.documentElement);
    const cor=estilo.getPropertyValue('--slate').trim();
    const valores=disciplinas.map(d=>{const ns=medias.get(d.id);return ns.reduce((s,n)=>s+n,0)/ns.length;});
    Plotly.react(el,[{type:'bar',x:disciplinas.map(d=>textoSeguro(d.codigo.replace('IA-',''))),y:valores,customdata:disciplinas.map(d=>textoSeguro(d.nome)),
      text:valores.map(v=>formatar(v)),textposition:'outside',cliponaxis:false,
      marker:{color:cor,opacity:.9},hovertemplate:'%{customdata}<br>Pontos: %{y:.2f}/100<extra></extra>'}],{
      paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{t:18,r:8,b:55,l:26},
      font:{family:'Inter, system-ui, sans-serif',size:10,color:cor},bargap:.4,
      yaxis:{range:[0,108],tickvals:[0,50,100],gridcolor:'#efeeee',zeroline:false,fixedrange:true},
      xaxis:{tickfont:{size:9},fixedrange:true},showlegend:false,
    },{responsive:true,displayModeBar:false,displaylogo:false});
  }
  $('nota-mediana').textContent=formatar(analise.estatisticas.mediana,2);
  $('nota-desvio').textContent=formatar(analise.estatisticas.desvio_padrao,2);
  $('resumo-evolucao').textContent=`VA${analise.va}: ${analise.indicadores.pendencias} avaliações pendentes nas atividades cadastradas. Pontos parciais não são a média final.`;
}

function mostrarCadastros(analise){
  const corpo=$('alunos-recentes');corpo.replaceChildren();
  const lista=[...analise.resumos].sort((a,b)=>Number(b.id)-Number(a.id)).slice(0,5);
  if(!lista.length){const linha=corpo.insertRow();const celula=linha.insertCell();celula.colSpan=6;celula.className='empty-state';celula.textContent='Nenhum aluno cadastrado nesta turma.';}
  for(const aluno of lista){
    const linha=corpo.insertRow();
    const nome=linha.insertCell();const link=document.createElement('a');link.className='student-cell';link.href=`/alunos/${encodeURIComponent(aluno.id)}`;
    const avatar=document.createElement('span');avatar.className='avatar';avatar.textContent=aluno.nome[0];
    const rotulo=document.createElement('strong');rotulo.textContent=aluno.nome;link.append(avatar,rotulo);nome.append(link);
    for(const valor of [aluno.matricula,aluno.turma,formatar(aluno.media),percentual(aluno.frequencia)])linha.insertCell().textContent=valor;
    const abrir=document.createElement('a');abrir.href=link.href;abrir.className='row-action';abrir.textContent='↗';abrir.setAttribute('aria-label',`Abrir perfil de ${aluno.nome}`);linha.insertCell().append(abrir);
  }
  $('resumo-cadastros').textContent=`Mostrando ${lista.length} de ${analise.resumos.length} alunos.`;
}

async function atualizar(){
  const atual=++pedido;const turma=$('filtro-turma').value;const va=$('filtro-va').value;
  const parametros=new URLSearchParams();if(turma)parametros.set('turma_id',turma);parametros.set('va',va);
  $('dashboard-conteudo').setAttribute('aria-busy','true');
  try{
    const analise=await buscarAPI(`/api/analises?${parametros}`);
    if(atual!==pedido)return;
    const i=analise.indicadores;
    $('kpi-total').textContent=formatar(i.totalAlunos,0);
    $('kpi-media').textContent=formatar(i.mediaGeral);
    $('kpi-frequencia').textContent=percentual(i.frequenciaMedia);
    const turmas=base.turmas.filter(t=>(!turma||String(t.id)===turma)&&t.situacao==='ativa');
    $('kpi-turmas').textContent=formatar(turmas.length,0);
    const anos=[...new Set(turmas.map(t=>t.ano_letivo))];$('periodo-label').textContent=anos.length?`Ano letivo ${anos.join(', ')}`:'Base acadêmica';
    $('frequencia-centro').textContent=percentual(i.frequenciaMedia);
    $('grafico-frequencia').style.setProperty('--presenca',`${i.frequenciaMedia??0}%`);
    $('grafico-frequencia').setAttribute('aria-label',i.frequenciaMedia===null?'Sem frequência registrada':`Frequência média de ${percentual(i.frequenciaMedia)}`);
    $('grafico-frequencia').title='Presenças divididas pelo total de aulas registradas';
    $('va-label').textContent=`VA${analise.va}`;
    desenharNotas(analise);mostrarCadastros(analise);$('dashboard-aviso').hidden=true;
  }catch(erro){
    if(atual===pedido){$('dashboard-aviso').textContent=`Não foi possível atualizar o painel. ${erro.message}`;$('dashboard-aviso').hidden=false;}
  }finally{if(atual===pedido)$('dashboard-conteudo').setAttribute('aria-busy','false');}
}

async function iniciar(){
  try{
    base=await carregarDados();preencherFiltros();
    if(!window.Plotly)throw new Error('A biblioteca dos gráficos não carregou. Recarregue a página.');
    for(const id of ['filtro-turma','filtro-va'])$(id).addEventListener('change',atualizar);
    await atualizar();
  }catch(erro){$('dashboard-aviso').textContent=erro.message;$('dashboard-aviso').hidden=false;$('dashboard-conteudo').setAttribute('aria-busy','false');}
}
iniciar();
