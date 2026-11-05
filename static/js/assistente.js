/* Sem HTML gerado pela IA, sem localStorage e sem chave de API no navegador. */
(() => {
  const $ = id => document.getElementById(id);
  const filtros = $('assistente-filtros'), form = $('ia-form'), enviar = $('ia-enviar');
  const erro = $('ia-erro'), mensagens = $('ia-mensagens'), pergunta = $('ia-pergunta');
  const professor = filtros.dataset.professor === 'sim';
  let opcoes = {}, carregando = false, configurado = false, pronto = false;
  let conversaId = null, filtrosSalvos = null, gerenciando = true, paginaChats = 1, excluirId = null, excluindo = false;
  const chatInicial = new URL(location.href).searchParams.get('chat');
  function guardarURL() { const url = new URL(location.href); if (conversaId) url.searchParams.set('chat',conversaId); else url.searchParams.delete('chat'); history.replaceState(null,'',url); }
  const base = () => $('ia-base')?.value || 'curso';
  function vazio() { conversaId = null; filtrosSalvos = null; guardarURL(); const p = document.createElement('p'); p.id = 'ia-vazio'; p.textContent = 'Como posso ajudar?'; mensagens.replaceChildren(p); }
  function rolar() { mensagens.scrollTop = mensagens.scrollHeight; }
  function aviso(texto = '') { erro.textContent = texto; erro.hidden = !texto; }
  function atualizarBotao() {
    enviar.disabled = carregando || gerenciando || !configurado || !pronto;
    document.querySelectorAll('#ia-chats button, #ia-novo-chat, #ia-chats-mais, #ia-limpar').forEach(b => { b.disabled = carregando || gerenciando; });
  }
  function option(select, valor, texto) { const o = document.createElement('option'); o.value = valor; o.textContent = texto; select.append(o); }
  function alunos() {
    if (!professor) return;
    const sel = $('ia-aluno'); sel.replaceChildren(); option(sel, '', 'Visão do grupo');
    const turma = $('ia-oferta').value.split(':')[0], vistos = new Set();
    for (const a of opcoes.alunos || []) {
      if (base() === 'curso' && turma && String(a.turma_id) !== turma) continue;
      if (!vistos.has(a.id)) { option(sel, a.id, a.nome); vistos.add(a.id); }
    }
  }
  async function json(url, init) {
    const r = await fetch(url, init);
    if (r.status === 401) { window.location.assign('/login'); throw new Error('Faça login novamente.'); }
    let dados; try { dados = await r.json(); } catch { throw new Error('O servidor não concluiu a consulta.'); }
    if (!r.ok) throw new Error(dados.erro || 'Não foi possível consultar o assistente.');
    return dados;
  }
  async function carregar(limpar = true) {
    pronto = false; atualizarBotao(); aviso(); if (limpar) vazio();
    filtros.querySelectorAll('select').forEach(el => { el.disabled = true; });
    try {
      opcoes = await json('/api/assistente/opcoes?base=' + base());
      const dataset = base() === 'dataset';
      $('ia-oferta-label').hidden = dataset; $('ia-va-label').hidden = dataset; $('ia-semestre-label').hidden = !dataset;
      $('ia-oferta').replaceChildren(); option($('ia-oferta'), '', 'Todos os meus vínculos');
      for (const o of opcoes.ofertas || []) option($('ia-oferta'), `${o.turma_id}:${o.disciplina_id}`, `${o.turma} · ${o.disciplina}`);
      $('ia-semestre').replaceChildren();
      for (const s of opcoes.semestres || []) option($('ia-semestre'), s, s);
      if (dataset) $('ia-semestre').value = opcoes.semestres.at(-1);
      alunos(); pronto = true;
    } catch (e) { aviso(e.message); }
    finally { filtros.querySelectorAll('select').forEach(el => { el.disabled = false; }); atualizarBotao(); }
  }
  function mensagem(titulo, texto) {
    $('ia-vazio')?.remove();
    const box = document.createElement('article'); box.className = 'ia-mensagem';
    if (titulo === 'Você') box.classList.add('ia-usuario');
    const h = document.createElement('h3'); h.textContent = titulo; box.append(h);
    if (texto) { const p = document.createElement('p'); p.textContent = texto; box.append(p); }
    mensagens.append(box); rolar(); return box;
  }
  function processando(box) {
    box.classList.add('ia-processando');
    const status = document.createElement('p'); status.className = 'ia-processamento'; status.setAttribute('role', 'status');
    const simbolo = document.createElement('span'); simbolo.className = 'ia-spinner'; simbolo.setAttribute('aria-hidden', 'true');
    status.append(simbolo, document.createTextNode('Processando…')); box.append(status); rolar();
    return status;
  }
  async function revelar(corpo) {
    // Anima somente o HTML que já foi validado e sanitizado pelo servidor.
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || document.hidden) return;
    const walker = document.createTreeWalker(corpo, NodeFilter.SHOW_TEXT), trechos = [];
    let node;
    while ((node = walker.nextNode())) {
      if (node.textContent.trim()) trechos.push({node, letras: Array.from(node.textContent)});
    }
    const total = trechos.reduce((n, t) => n + t.letras.length, 0);
    if (!total) return;
    const blocos = [...corpo.querySelectorAll('p,li,ul,ol,table,thead,tbody,tr,th,td,h2,h3,h4,blockquote,pre')];
    blocos.forEach(el => { el.hidden = true; });
    trechos.forEach(t => { t.node.textContent = ''; });
    corpo.setAttribute('aria-busy', 'true'); mensagens.classList.add('ia-revelando');
    const duracao = Math.min(6000, Math.max(500, total * 9));
    const inicio = performance.now();
    await new Promise(resolve => {
      let quadro, terminou = false;
      function terminar() {
        if (terminou) return;
        terminou = true; cancelAnimationFrame(quadro);
        trechos.forEach(t => { t.node.textContent = t.letras.join(''); });
        blocos.forEach(el => { el.hidden = false; });
        corpo.removeAttribute('aria-busy'); mensagens.classList.remove('ia-revelando');
        document.removeEventListener('visibilitychange', visibilidade); resolve();
      }
      function visibilidade() { if (document.hidden) terminar(); }
      function passo(agora) {
        const acompanha = mensagens.scrollHeight - mensagens.scrollTop - mensagens.clientHeight < 90;
        let restante = Math.floor(Math.min(1, (agora - inicio) / duracao) * total);
        for (const t of trechos) {
          const visivel = Math.min(t.letras.length, Math.max(0, restante));
          if (t.visivel !== visivel) {
            t.node.textContent = t.letras.slice(0, visivel).join(''); t.visivel = visivel;
            if (visivel) for (let el = t.node.parentElement; el && el !== corpo; el = el.parentElement) el.hidden = false;
          }
          restante -= t.letras.length;
        }
        if (acompanha) rolar();
        if (agora - inicio >= duracao) terminar(); else quadro = requestAnimationFrame(passo);
      }
      document.addEventListener('visibilitychange', visibilidade);
      quadro = requestAnimationFrame(passo);
    });
  }
  async function exibirResposta(dados, box = null, animar = false) {
    dados = {fatos: [], acoes: [], ...dados};
    box = box || mensagem('Assistente acadêmico', '');
      const corpo = document.createElement('div'); corpo.className = 'ia-markdown';
      if (dados.resposta_html) {
        // HTML produzido pelo MarkdownIt com HTML bruto desativado e sanitizado com Bleach no servidor.
        corpo.innerHTML = dados.resposta_html;
      } else { const p = document.createElement('p'); p.textContent = dados.mensagem; corpo.append(p); }
      box.append(corpo);
      const fontes = document.createElement('details'); fontes.className = 'ia-fontes';
      const resumo = document.createElement('summary'); resumo.textContent = 'Fontes e contexto'; fontes.append(resumo);
      for (const f of dados.fontes || []) {
        const a = document.createElement('a'); a.textContent = `${f.id} · ${f.nome}`;
        if (f.url.startsWith('/') && !f.url.startsWith('//')) a.href = f.url;
        fontes.append(a);
      }
      for (const f of dados.fatos) {
        const p = document.createElement('p'); p.textContent = f.texto; corpo.append(p);
        const a = document.createElement('a'); a.textContent = `Fonte ${f.id}`;
        // Somente rotas internas fornecidas pelo servidor.
        if (f.fonte.startsWith('/') && !f.fonte.startsWith('//')) a.href = f.fonte;
        fontes.append(a);
      }
      if (dados.acoes.length) {
        const h = document.createElement('h3'); h.textContent = 'Próximos passos sugeridos'; corpo.append(h);
        const lista = document.createElement('ul');
        for (const a of dados.acoes) { const li = document.createElement('li'); li.textContent = a.texto; lista.append(li); }
        corpo.append(lista);
      }
      if (animar) await revelar(corpo);
      const rodape = document.createElement('small'); rodape.className = 'ia-recorte';
      rodape.textContent = `${dados.recorte} · consultado em ${new Date(dados.consultado_em).toLocaleString('pt-BR')}`;
      fontes.append(rodape); if ((dados.fontes || []).length || dados.fatos.length) box.append(fontes);
      rolar();
  }
  form.addEventListener('submit', async e => {
    e.preventDefault(); if (enviar.disabled) return;
    const texto = pergunta.value.trim(); if (texto.length < 3) return;
    const entrada = {pergunta: texto, ...filtrosAtuais()};
    if (conversaId) entrada.conversa_id = conversaId;
    carregando = true; atualizarBotao(); enviar.textContent = 'Enviando…'; aviso();
    $('ia-contexto').open = false;
    filtros.querySelectorAll('select').forEach(el => { el.disabled = true; });
    $('ia-limpar').disabled = true; mensagem('Você', texto); pergunta.value = ''; form.setAttribute('aria-busy', 'true');
    const box = mensagem('Assistente acadêmico', '');
    const indicador = processando(box);
    try {
      const dados = await json('/api/assistente', {method: 'POST', headers: {'Content-Type': 'application/json',
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content}, body: JSON.stringify(entrada)});
      conversaId = dados.conversa_id || null;
      guardarURL();
      indicador.remove(); box.classList.remove('ia-processando'); enviar.textContent = 'Respondendo…';
      await exibirResposta(dados, box, true);
    } catch (e) { box.remove(); aviso(e.message); if (!pergunta.value) pergunta.value = texto; }
    finally {
      carregando = false; atualizarBotao(); enviar.textContent = 'Enviar ↑'; form.removeAttribute('aria-busy');
      filtros.querySelectorAll('select').forEach(el => { el.disabled = false; });
      await carregarHistorico(); atualizarBotao();
    }
  });
  filtros.addEventListener('change', e => {
    if (e.target.id === 'ia-base') carregar();
    else { vazio(); aviso(); if (e.target.id === 'ia-oferta') alunos(); }
    marcarAtivo();
  });
  $('ia-limpar').addEventListener('click', novoChat);
  pergunta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); if (!enviar.disabled) form.requestSubmit(); } });
  document.addEventListener('click', e => { if (!$('ia-contexto').contains(e.target)) $('ia-contexto').open = false; });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') $('ia-contexto').open = false; });

  function filtrosAtuais() {
    if (conversaId && filtrosSalvos) return {...filtrosSalvos};
    const f = {base: base()};
    if (base() === 'curso') {
      f.va = Number($('ia-va').value);
      if ($('ia-oferta').value) [f.turma_id, f.disciplina_id] = $('ia-oferta').value.split(':').map(Number);
    } else f.semestre = $('ia-semestre').value;
    if (professor && $('ia-aluno').value) f.aluno_id = Number($('ia-aluno').value);
    return f;
  }
  const csrf = () => ({'Content-Type':'application/json', 'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content});
  function marcarAtivo() {
    document.querySelectorAll('.ia-chat-item').forEach(li => {
      const ativo = li.dataset.id === conversaId;
      li.classList.toggle('ativo', ativo); li.querySelector('.ia-chat-abrir').setAttribute('aria-current', ativo ? 'true' : 'false');
    });
  }
  function fecharHistorico() { $('ia-historico').classList.remove('aberto'); $('ia-historico-toggle').setAttribute('aria-expanded','false'); }
  async function carregarHistorico(pagina = 1) {
    try {
      const d = await json('/api/assistente/chats?pagina=' + pagina);
      if (pagina === 1) $('ia-chats').replaceChildren();
      paginaChats = pagina;
      for (const chat of d.chats) {
        const li = document.createElement('li'); li.className = 'ia-chat-item'; li.dataset.id = chat.id;
        const abrir = document.createElement('button'); abrir.type = 'button'; abrir.className = 'ia-chat-abrir'; abrir.title = chat.titulo;
        const titulo = document.createElement('strong'); titulo.textContent = chat.titulo;
        const tempo = document.createElement('time'); tempo.dateTime = chat.atualizado_em;
        tempo.textContent = new Date(chat.atualizado_em).toLocaleString('pt-BR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
        abrir.append(titulo,tempo); abrir.addEventListener('click', () => abrirChat(chat.id));
        const apagar = document.createElement('button'); apagar.type = 'button'; apagar.className = 'ia-chat-apagar'; apagar.textContent = 'Apagar';
        apagar.setAttribute('aria-label','Apagar chat ' + chat.titulo);
        apagar.addEventListener('click', () => {
          if (carregando || gerenciando) return;
          excluirId = chat.id; $('ia-excluir-texto').textContent = chat.titulo;
          $('ia-excluir-erro').hidden = true; $('ia-excluir-dialog').showModal();
        });
        li.append(abrir,apagar); $('ia-chats').append(li);
      }
      $('ia-chats-mais').hidden = !d.tem_mais;
      $('ia-historico-aviso').textContent = $('ia-chats').children.length ? '' : 'Seus chats aparecerão aqui.';
      marcarAtivo(); atualizarBotao(); return d.chats;
    } catch (e) { $('ia-historico-aviso').textContent = e.message; return []; }
  }
  async function novoChat() {
    if (carregando || gerenciando) return;
    const f = filtrosAtuais(); gerenciando = true; atualizarBotao(); aviso();
    try {
      const d = await json('/api/assistente/chats', {method:'POST',headers:csrf(),body:JSON.stringify(f)});
      vazio(); conversaId = d.id; filtrosSalvos = d.filtros; guardarURL();
      pergunta.value = ''; fecharHistorico(); await carregarHistorico(); pergunta.focus();
    } catch(e) { aviso(e.message); }
    finally { gerenciando = false; atualizarBotao(); }
  }
  async function abrirChat(id) {
    if (carregando || gerenciando) return;
    gerenciando = true; atualizarBotao(); aviso();
    try {
      const d = await json('/api/assistente/chats/' + encodeURIComponent(id));
      const f = d.chat.filtros;
      if ($('ia-base')) $('ia-base').value = f.base || 'curso';
      await carregar(false);
      if (f.turma_id && f.disciplina_id) $('ia-oferta').value = `${f.turma_id}:${f.disciplina_id}`;
      $('ia-va').value = f.va || 2;
      if (f.semestre) $('ia-semestre').value = f.semestre;
      alunos(); if (professor && f.aluno_id) $('ia-aluno').value = f.aluno_id;
      mensagens.replaceChildren(); conversaId = d.chat.id; filtrosSalvos = f;
      if (!d.mensagens.length) { vazio(); conversaId = d.chat.id; filtrosSalvos = f; }
      for (const m of d.mensagens) {
        if (m.papel === 'user') mensagem('Você',m.texto);
        else await exibirResposta({mensagem:m.texto,resposta_html:m.resposta_html,fontes:m.fontes,
          consultado_em:m.criado_em,recorte:m.fontes.map(x => x.nome).join(' · ') || d.chat.titulo});
      }
      pergunta.value = ''; guardarURL(); marcarAtivo(); fecharHistorico(); rolar();
    } catch(e) { aviso(e.message); }
    finally { gerenciando = false; atualizarBotao(); }
  }
  $('ia-novo-chat').addEventListener('click',novoChat);
  $('ia-chats-mais').addEventListener('click', () => carregarHistorico(paginaChats + 1));
  $('ia-historico-toggle').addEventListener('click', () => {
    const aberto = $('ia-historico').classList.toggle('aberto'); $('ia-historico-toggle').setAttribute('aria-expanded',String(aberto));
  });
  $('ia-historico-fechar').addEventListener('click',fecharHistorico);
  $('ia-excluir-cancelar').addEventListener('click', () => $('ia-excluir-dialog').close());
  $('ia-excluir-dialog').addEventListener('cancel', e => { if (excluindo) e.preventDefault(); });
  $('ia-excluir-confirmar').addEventListener('click', async () => {
    if (!excluirId || excluindo || carregando || gerenciando) return;
    excluindo = true; $('ia-excluir-confirmar').disabled = true; $('ia-excluir-cancelar').disabled = true;
    try {
      const r = await fetch('/api/assistente/chats/' + encodeURIComponent(excluirId), {method:'DELETE',headers:csrf()});
      if (!r.ok) { const d = await r.json(); throw new Error(d.erro || 'Não foi possível apagar o chat.'); }
      if (conversaId === excluirId) { vazio(); pergunta.value = ''; }
      $('ia-excluir-dialog').close(); excluirId = null; await carregarHistorico();
    } catch(e) { $('ia-excluir-erro').textContent = e.message; $('ia-excluir-erro').hidden = false; }
    finally { excluindo = false; $('ia-excluir-confirmar').disabled = false; $('ia-excluir-cancelar').disabled = false; }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') fecharHistorico(); });

  json('/api/assistente/status').then(d => { configurado = d.configurado; })
    .catch(e => { $('ia-config').textContent = e.message; $('ia-config').hidden = false; }).finally(atualizarBotao);
  (async () => { await carregar(); const lista = await carregarHistorico(); gerenciando = false; atualizarBotao(); if (chatInicial) await abrirChat(chatInicial); else if (lista.length) await abrirChat(lista[0].id); })();
})();
