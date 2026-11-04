import { buscarAPI } from './dataService.js';

const $ = id => document.getElementById(id);
const numero = (v, casas = 2) => v === null || v === undefined ? '—' : Number(v).toLocaleString('pt-BR', {minimumFractionDigits: casas, maximumFractionDigits: casas});
const percentual = v => v === null || v === undefined ? '—' : `${numero(v, 1)}%`;
let pedido = 0;
let iniciado = false;

function grafico(a) {
  const individual = a.filtros.aluno_id !== null;
  const fonte = individual ? a.serie : a.comparacao;
  $('dataset-grafico-titulo').textContent = individual ? 'Histórico de médias finais' : 'Notas por período da disciplina';
  $('dataset-grafico-subtitulo').textContent = individual ? 'Semestres com notas finais até o recorte selecionado.' : `Médias ${a.tipo_nota === 'parcial' ? 'parciais' : 'finais'} por período curricular.`;
  const el = $('dataset-grafico');
  if (!fonte.length) {
    if (el.data) window.Plotly.purge(el);
    el.replaceChildren();
    const vazio = document.createElement('div'); vazio.className = 'dashboard-empty';
    vazio.textContent = individual ? 'Não há notas finais anteriores para este aluno.' : 'Não há notas disponíveis neste recorte.';
    el.append(vazio);
  } else {
    if (!el.data) el.replaceChildren();
    const cor = getComputedStyle(document.documentElement).getPropertyValue('--slate').trim();
    const x = fonte.map(r => individual ? r.semestre : `${r.periodo}º`);
    const y = fonte.map(r => r.media);
    const traces = [{type: individual ? 'scatter' : 'bar', mode: 'lines+markers', x, y,
      marker: {color: cor}, line: {color: cor}, name: individual ? 'Média final' : 'Média',
      hovertemplate: '%{x}<br>%{y:.2f} pontos<extra></extra>'}];
    if (individual && a.previsao?.status === 'ok') {
      const ultimo = fonte[fonte.length - 1];
      traces.push({type: 'scatter', mode: 'lines+markers', x: [ultimo.semestre, a.previsao.semestre_estimado],
        y: [ultimo.media, a.previsao.previsao], name: 'Projeção', line: {color: cor, dash: 'dot'},
        marker: {color: cor, symbol: 'diamond-open'}, hovertemplate: 'Projeção %{x}<br>%{y:.2f} pontos<extra></extra>'});
    }
    window.Plotly.react(el, traces, {paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      margin: {t: 12, r: 12, b: 40, l: 30}, showlegend: false,
      font: {family: 'Inter, system-ui, sans-serif', size: 10, color: cor},
      yaxis: {range: [0, 105], tickvals: [0, 50, 100], fixedrange: true, gridcolor: '#efeeee'},
      xaxis: {type: 'category', fixedrange: true}}, {responsive: true, displayModeBar: false, displaylogo: false});
  }
  const p = a.previsao;
  $('dataset-tendencia').textContent = !individual ? 'Selecione um aluno para consultar sua evolução por semestre.' :
    p?.status === 'ok' ? `Variação ajustada: ${p.inclinacao > 0 ? '+' : ''}${numero(p.inclinacao)} ponto(s)/semestre. Projeção ${p.semestre_estimado}: ${numero(p.previsao)} pontos, com ${p.total_avaliacoes} semestres. Estimativa exploratória.` : 'Histórico insuficiente para estimar tendência: são necessários ao menos dois semestres com notas finais.';
  $('dataset-ajuste').textContent = p?.status === 'ok' ? `Ajuste da regressão: R² = ${numero(p.r_quadrado, 3)}. Esse valor descreve o ajuste ao histórico e não mede a precisão da previsão futura.` : 'A regressão fica indisponível quando há menos de dois semestres com notas finais.';
  el.setAttribute('aria-label', individual ? 'Histórico de notas finais por semestre e projeção exploratória' : 'Médias de notas por período curricular');
}

function tabela(a) {
  const corpo = $('dataset-alunos'); corpo.replaceChildren();
  for (const aluno of a.alunos.slice(0, 5)) {
    const tr = corpo.insertRow();
    for (const v of [aluno.nome_sintetico, aluno.codigo_academico, numero(aluno.media), percentual(aluno.frequencia)]) tr.insertCell().textContent = v;
    const link = document.createElement('button'); link.className = 'button button-ghost'; link.type = 'button';
    link.textContent = 'Ver histórico'; link.setAttribute('aria-label', `Ver histórico de ${aluno.nome_sintetico}`);
    link.addEventListener('click', () => {$('filtro-aluno-dataset').value = String(aluno.aluno_id); atualizar();});
    tr.insertCell().append(link);
  }
  if (!a.alunos.length) {const td = corpo.insertRow().insertCell(); td.colSpan = 5; td.className = 'empty-state'; td.textContent = 'Nenhum registro no recorte selecionado.';}
  $('dataset-tabela-resumo').textContent = `Mostrando ${Math.min(5, a.alunos.length)} de ${a.alunos.length}`;
}

async function atualizar() {
  const atual = ++pedido;
  const params = iniciado ? new URLSearchParams({semestre: $('filtro-semestre').value}) : new URLSearchParams(window.location.search);
  if (iniciado && $('filtro-aluno-dataset').value) params.set('aluno_id', $('filtro-aluno-dataset').value);
  $('dataset-conteudo').setAttribute('aria-busy', 'true');
  try {
    const a = await buscarAPI(`/api/dataset-professor?${params}`);
    if (atual !== pedido) return;
    if (!iniciado) {
      $('filtro-semestre').replaceChildren(...a.opcoes.semestres.map(s => new Option(s, s)));
      for (const aluno of a.opcoes.alunos) $('filtro-aluno-dataset').add(new Option(aluno.nome_sintetico, aluno.aluno_id));
      $('filtro-semestre').value = a.filtros.semestre;
      $('filtro-aluno-dataset').value = a.filtros.aluno_id === null ? '' : String(a.filtros.aluno_id);
      for (const id of ['filtro-semestre', 'filtro-aluno-dataset']) {$(id).disabled = false; $(id).addEventListener('change', atualizar);}
      iniciado = true;
    }
    if (!window.Plotly) throw new Error('A biblioteca de gráficos não carregou. Recarregue a página.');
    const i = a.indicadores;
    $('dataset-total').textContent = numero(i.total_alunos, 0);
    $('dataset-media').textContent = numero(i.media, 1);
    $('dataset-media-titulo').textContent = `Média ${a.tipo_nota === 'parcial' ? 'parcial' : 'final'}`;
    $('dataset-cobertura').textContent = `${a.cobertura.notas_disponiveis} notas disponíveis de ${i.total_registros}`;
    $('dataset-registros').textContent = numero(i.total_registros, 0);
    $('dataset-frequencia').textContent = percentual(i.frequencia_media);
    $('dataset-frequencia-centro').textContent = percentual(i.frequencia_media);
    $('dataset-donut').style.setProperty('--presenca', `${i.frequencia_media ?? 0}%`);
    $('dataset-donut').setAttribute('aria-label', i.frequencia_media === null ? 'Sem frequência registrada' : `Frequência média de ${percentual(i.frequencia_media)}`);
    $('dataset-frequencia-cobertura').textContent = `${a.cobertura.frequencias_disponiveis} de ${i.total_registros} registros com frequência`;
    $('dataset-semestre-label').textContent = a.filtros.semestre;
    $('dataset-mediana').textContent = numero(a.estatisticas.mediana);
    $('dataset-desvio').textContent = numero(a.estatisticas.desvio_padrao);
    $('dataset-variancia').textContent = numero(a.estatisticas.variancia);
    $('dataset-interpretacao').textContent = a.interpretacao;
    $('dataset-metodo').textContent = a.metodo;
    $('dataset-correlacao').textContent = `Frequência e média por aluno: r = ${numero(a.correlacao.coeficiente, 3)}, n = ${a.correlacao.amostras}. ${a.correlacao.interpretacao}`;
    $('dataset-conteudo').hidden = false; grafico(a); tabela(a); $('dataset-aviso').hidden = true;
    const url = new URL(window.location.href); url.search = '';
    url.searchParams.set('semestre', a.filtros.semestre);
    if (a.filtros.aluno_id !== null) url.searchParams.set('aluno_id', a.filtros.aluno_id);
    window.history.replaceState({}, '', url);
  } catch (erro) {
    if (atual === pedido) {$('dataset-conteudo').hidden = true; $('dataset-aviso').textContent = `Não foi possível consultar o dataset. ${erro.message}`; $('dataset-aviso').hidden = false;}
  } finally {if (atual === pedido) $('dataset-conteudo').setAttribute('aria-busy', 'false');}
}

atualizar();
