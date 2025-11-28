let currentConnections = [];

// Preview page functionality + interactive UX
(function(){
  const previewBtn = document.getElementById('previewBtn');
  const traceBtn = document.getElementById('traceBtn');
  const statusEl = document.getElementById('status');
  const previewCard = document.getElementById('previewCard');
  const previewImage = document.getElementById('previewImage');
  const connCount = document.getElementById('connCount');
  const resultsBody = document.getElementById('resultsBody');
  const resultsFilter = document.getElementById('resultsFilter');
  const exportBtn = document.getElementById('exportBtn');
  const copyBtn = document.getElementById('copyBtn');
  const fileDrop = document.getElementById('fileDrop');
  const pdfPathInput = document.getElementById('pdfPath');

  let currentConnections = [];
  let zoom = 1;

  function setStatus(state, text){
    statusEl.className = 'status ' + (state||'');
    if(statusEl.querySelector('.muted')) statusEl.querySelector('.muted').textContent = text;
    else statusEl.innerHTML = '<div class="muted">'+text+'</div>';
  }

  // drag/drop for path box (nice-to-have UX for local dev)
  ['dragenter','dragover'].forEach(ev=>{
    fileDrop.addEventListener(ev,e=>{e.preventDefault();fileDrop.classList.add('drag')});
  });
  ['dragleave','drop'].forEach(ev=>{
    fileDrop.addEventListener(ev,e=>{e.preventDefault();fileDrop.classList.remove('drag')});
  });
  fileDrop.addEventListener('drop',e=>{
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if(f) pdfPathInput.value = f.path || f.name || ''; // path works in electron/local env
  });

  // preview
  previewBtn.addEventListener('click', async ()=>{
    const pdfPath = pdfPathInput.value.trim();
    const page = document.getElementById('page').value || 1;
    if(!pdfPath){ setStatus('error', 'Enter a PDF path or drop a file'); return; }
    previewBtn.disabled = true; setStatus('loading','Loading page preview...');
    try{
      const res = await fetch('/api/preview', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pdf_path:pdfPath,page})});
      const json = await res.json();
      if(res.ok && json.success){
        previewImage.src = 'data:image/png;base64,' + json.image;
        previewCard.style.display = 'block';
        setStatus('ok','Preview loaded');
      } else {
        setStatus('error', json.error || 'Preview failed');
      }
    }catch(err){ setStatus('error','Network error: '+err.message); }
    previewBtn.disabled = false;
  });

  // trace
  document.getElementById('traceForm').addEventListener('submit',async e=>{
    e.preventDefault();
    const pdfPath = pdfPathInput.value.trim();
    const apiKey = document.getElementById('apiKey').value.trim();
    const page = document.getElementById('page').value || 1;
    const model = document.getElementById('model').value;
    const from_token = document.getElementById('fromToken').value.trim();
    const to_token = document.getElementById('toToken').value.trim();
    if(!pdfPath || !from_token || !to_token){ setStatus('error','PDF path, from and to tokens are required'); return; }
    traceBtn.disabled = true; setStatus('loading','Processing...');
    try{
      const resp = await fetch('/api/trace', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pdf_path:pdfPath,api_key:apiKey,page,model,from_token,to_token})});
      const json = await resp.json();
      if(resp.ok && json.success){
        currentConnections = json.connections || [];
        renderResults(currentConnections);
        setStatus('ok','Found '+ (currentConnections.length) +' connection(s)');
      } else {
        setStatus('error', json.error||'Trace failed');
        currentConnections = [];
        renderResults([]);
      }
    }catch(err){ setStatus('error','Network error: '+err.message); }
    traceBtn.disabled = false;
  });

  function renderResults(list){
    resultsBody.innerHTML = '';
    connCount.textContent = list.length;
    list.forEach((c,i)=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${escapeHtml(c.from)}</td><td>${escapeHtml(c.to)}</td><td>${escapeHtml(c.description)}</td>`;
      tr.addEventListener('mouseenter',()=>{tr.classList.add('highlight')});
      tr.addEventListener('mouseleave',()=>{tr.classList.remove('highlight')});
      resultsBody.appendChild(tr);
    });
  }

  function escapeHtml(s){ if(s==null) return ''; return String(s).replace(/[&<>"']/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]}); }

  resultsFilter.addEventListener('input',()=>{\n    const q = resultsFilter.value.trim().toLowerCase();
    const filtered = currentConnections.filter(r=> (r.from||'').toLowerCase().includes(q) || (r.to||'').toLowerCase().includes(q) || (r.description||'').toLowerCase().includes(q));
    renderResults(filtered);
  });

  exportBtn.addEventListener('click',()=>{\n    if(!currentConnections || !currentConnections.length){ alert('No connections to export'); return; }
    const csv = toCSV(currentConnections);
    const blob = new Blob([csv],{type:'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'wire_connections.csv'; a.click();
    URL.revokeObjectURL(url);
  });

  copyBtn.addEventListener('click',()=>{\n    if(!currentConnections || !currentConnections.length){ alert('Nothing to copy'); return; }
    const tsv = currentConnections.map(r=>`${r.from}\t${r.to}\t${r.description}`).join('\n');
    navigator.clipboard.writeText(tsv).then(()=>{ alert('Copied to clipboard') }).catch(()=>{ alert('Copy failed') });
  });

  function toCSV(arr){
    const rows = [['From','To','Description']].concat(arr.map(r=>[r.from,r.to,r.description]));
    return rows.map(r=>r.map(cell=>`"${String(cell||'').replace(/"/g,'""')}"`).join(',')).join('\n');
  }

  // small UX helpers
  document.getElementById('clearBtn').addEventListener('click',()=>{\n    pdfPathInput.value=''; document.getElementById('apiKey').value=''; document.getElementById('fromToken').value=''; document.getElementById('toToken').value=''; currentConnections=[]; renderResults([]); setStatus('','Idle'); previewCard.style.display='none';
  });

  // zoom controls only affect CSS transform for now
  document.getElementById('zoomIn').addEventListener('click',()=>{ zoom = Math.min(2,zoom+0.1); previewImage.style.transform = `scale(${zoom})`; });
  document.getElementById('zoomOut').addEventListener('click',()=>{ zoom = Math.max(0.5,zoom-0.1); previewImage.style.transform = `scale(${zoom})`; });

  // initial status
  setStatus('','Idle');

})();
