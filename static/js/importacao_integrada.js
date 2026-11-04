const tipo=document.getElementById('tipo');
tipo.addEventListener('change',()=>document.getElementById('modelo-link').href=`/api/importacao/modelo/${tipo.value}`);
document.getElementById('importar-form').addEventListener('submit',async e=>{
  e.preventDefault();
  const status=document.getElementById('resultado-importacao');
  const erros=document.getElementById('erros-importacao');
  const botao=document.getElementById('enviar');
  botao.disabled=true; status.textContent='Importando…'; erros.replaceChildren();
  try {
    const form=new FormData(); form.append('arquivo',document.getElementById('arquivo').files[0]);
    const r=await fetch(`/api/importacao/${tipo.value}`,{method:'POST',body:form,
      headers:{'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content}});
    const dados=await r.json(); if(!r.ok) throw new Error(dados.erro||`Falha HTTP ${r.status}`);
    status.textContent=`Lidos: ${dados.total_lidos} · Importados: ${dados.importados} · Recusados: ${dados.recusados}`;
    for(const erro of dados.erros){const p=document.createElement('p');p.textContent=`Linha ${erro.linha}: ${erro.motivo}`;erros.append(p);}
  } catch(erro) {status.textContent=erro.message;}
  finally {botao.disabled=false;}
});
