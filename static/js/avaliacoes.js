(() => {
  const tipo = document.getElementById('tipo');
  const campo = document.getElementById('campo-maximo');
  const maximo = document.getElementById('maximo');
  if (!tipo || !campo || !maximo) return;
  function atualizar() {
    const personalizado = tipo.value === 'PERSONALIZADA';
    campo.hidden = !personalizado;
    maximo.disabled = !personalizado;
    maximo.required = personalizado;
  }
  tipo.addEventListener('change', atualizar);
  atualizar();
})();
