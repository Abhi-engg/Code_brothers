// Minimal frontend to call backend /mindmap and render with MindElixir
const API = 'http://localhost:8000/mindmap';
const btn = document.getElementById('analyze');
const textEl = document.getElementById('text');
const titleEl = document.getElementById('title');
const textOutput = document.getElementById('text-output');
const tabs = document.querySelectorAll('.tab');
const textView = document.getElementById('text-view');
const mindmapWrap = document.getElementById('mindmap-wrap');
const mindmapDiv = document.getElementById('mindmap');

let ME = null; // MindElixir instance

function getMindElixirCtor(){
  if (typeof window === 'undefined') return null;
  if (window.MindElixir) return window.MindElixir;
  if (window.ME) return window.ME;
  if (window.default && (window.default.MindElixir || window.default.ME)) return window.default.MindElixir || window.default.ME;
  if (window.MindElixir && window.MindElixir.default) return window.MindElixir.default;
  return null;
}

function setActiveTab(name){
  tabs.forEach(t=> t.classList.toggle('active', t.dataset.tab===name));
  textView.style.display = name==='text' ? 'block' : 'none';
  mindmapWrap.style.display = name==='map' ? 'flex' : 'none';
}

tabs.forEach(t=> t.addEventListener('click', ()=> setActiveTab(t.dataset.tab)));
setActiveTab('text');

btn.addEventListener('click', async () => {
  const text = textEl.value.trim();
  if(!text){ alert('Enter text first'); return; }
  textOutput.textContent = 'Analyzing...';
  try{
    const res = await fetch(API, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ text, title: titleEl.value||undefined }) });
    if(!res.ok) throw new Error('Server error');
    const data = await res.json();
    textOutput.textContent = text;
    await renderMindMap(data);
    setActiveTab('map');
  }catch(err){
    textOutput.textContent = 'Error: '+err.message;
    console.error(err);
  }
});

function convertToMindElixirFormat(hier){
  // Convert hierarchical {topic, children[]} to MindElixir expected nodeData/rootId
  // We'll use a simple nodeData map where each node is { id: id, topic: topic, children: [] }
  let id = 1;
  const nodeData = {};
  function walk(node){
    const nid = String(id++);
    nodeData[nid] = { id: nid, topic: node.topic || '—', children: [] };
    if(node.children && node.children.length){
      for(const c of node.children){
        const cid = walk(c);
        nodeData[nid].children.push(cid);
      }
    }
    return nid;
  }
  const rootId = walk(hier);
  return { nodeData, rootId };
}

async function renderMindMap(hier){
  // hier: { topic, children }
  const conv = convertToMindElixirFormat(hier);
  // Prepare data for MindElixir
  const data = { "nodeData": conv.nodeData, "rootId": conv.rootId };

  // Destroy previous instance if exists
  if(ME){
    try{ ME.destroy(); }catch(e){}
    ME = null;
    mindmapDiv.innerHTML = '';
  }

  // Create MindElixir instance (defensive)
  let Ctor = getMindElixirCtor();
  if (!Ctor) {
    console.warn('MindElixir ctor not found — attempting dynamic import fallback...');
    // Try a dynamic import fallback (ESM) from unpkg
    try{
      const fallbackUrl = 'https://unpkg.com/mind-elixir@2.1.1/dist/index.js';
      const mod = await import(fallbackUrl);
      const maybeCtor = mod.MindElixir || mod.default || mod.ME || mod;
      if(maybeCtor){
        window.MindElixir = maybeCtor;
        Ctor = getMindElixirCtor();
        console.info('MindElixir loaded via dynamic import fallback');
      }
    }catch(e){
      console.warn('Dynamic import fallback failed:', e);
    }
  }

  if (!Ctor) {
    // Diagnostic output to help debugging in the browser console
    const keys = Object.keys(window).slice(0,200);
    console.error('MindElixir not available on window. window keys (truncated):', keys);
    mindmapDiv.innerHTML = '<div style="padding:16px;color:#b91c1c">MindElixir library not found. Check your CDN script. See console for diagnostics.</div>';
    return;
  }

  const options = {
    el: '#mindmap',
    data: data,
    direction: (Ctor.SIDE !== undefined ? Ctor.SIDE : (Ctor.directions && Ctor.directions.SIDE)) || 'right',
    draggable: true,
    contextMenu: true,
    editable: false,
  };

  try{
    ME = new Ctor(options);
  }catch(err){
    try{ ME = new Ctor(); ME.init(data); } catch(e){ console.error('Failed to init MindElixir ctor', err, e); mindmapDiv.innerHTML = '<div style="padding:16px;color:#b91c1c">Failed to initialize MindElixir.</div>'; return; }
  }
  if (typeof ME.init === 'function') ME.init(data);

  // basic controls: zoom via wheel (mind-elixir handles pan/zoom), expand/collapse handled by double-click
}
