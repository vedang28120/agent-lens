// AgentLens Mission Control Client Engine
document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const valFiles = document.getElementById('valFiles');
  const valSymbols = document.getElementById('valSymbols');
  const valHealth = document.getElementById('valHealth');
  const valHypo = document.getElementById('valHypo');
  const valPorts = document.getElementById('valPorts');
  const connStatus = document.getElementById('connStatus');
  const connBadge = document.getElementById('connBadge');
  const rescanBtn = document.getElementById('rescanBtn');
  const copyBriefBtn = document.getElementById('copyBriefBtn');
  const toast = document.getElementById('toast');

  // Tabs
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const countHypo = document.getElementById('countHypo');
  const countTasks = document.getElementById('countTasks');

  // Lists
  const hypoList = document.getElementById('hypoList');
  const taskList = document.getElementById('taskList');
  const decisionsList = document.getElementById('decisionsList');
  const scratchpadArea = document.getElementById('scratchpadArea');
  const saveScratchBtn = document.getElementById('saveScratchBtn');
  const radarDetailsList = document.getElementById('radarDetailsList');
  const radarScoreCircle = document.getElementById('radarScoreCircle');
  const radarStatusText = document.getElementById('radarStatusText');
  const portsList = document.getElementById('portsList');
  const refreshPortsBtn = document.getElementById('refreshPortsBtn');
  const activityList = document.getElementById('activityList');

  // Inputs
  const newHypoInput = document.getElementById('newHypoInput');
  const addHypoBtn = document.getElementById('addHypoBtn');
  const newTaskInput = document.getElementById('newTaskInput');
  const addTaskBtn = document.getElementById('addTaskBtn');

  // RepoMap
  const repoMapBudgetInput = document.getElementById('repoMapBudgetInput');
  const genRepoMapBtn = document.getElementById('genRepoMapBtn');
  const copyRepoMapBtn = document.getElementById('copyRepoMapBtn');
  const repoMapStats = document.getElementById('repoMapStats');
  const repoMapResult = document.getElementById('repoMapResult');

  // Dynamic Risk
  const dynamicRiskSymbolInput = document.getElementById('dynamicRiskSymbolInput');
  const runDynamicRiskBtn = document.getElementById('runDynamicRiskBtn');
  const dynamicRiskResultsList = document.getElementById('dynamicRiskResultsList');

  // Guard
  const guardFileInput = document.getElementById('guardFileInput');
  const runGuardBtn = document.getElementById('runGuardBtn');
  const guardResultsList = document.getElementById('guardResultsList');

  // Planner
  const planFileInput = document.getElementById('planFileInput');
  const planSymbolInput = document.getElementById('planSymbolInput');
  const planObjInput = document.getElementById('planObjInput');
  const runPlanBtn = document.getElementById('runPlanBtn');
  const planResultsList = document.getElementById('planResultsList');

  // Packer
  const packerQuery = document.getElementById('packerQuery');
  const packerBudget = document.getElementById('packerBudget');
  const packBtn = document.getElementById('packBtn');
  const packerResult = document.getElementById('packerResult');
  const packStats = document.getElementById('packStats');
  const copySliceBtn = document.getElementById('copySliceBtn');

  // Ghost Patch
  const ghostFile = document.getElementById('ghostFile');
  const ghostContent = document.getElementById('ghostContent');
  const ghostTestBtn = document.getElementById('ghostTestBtn');
  const ghostVerdict = document.getElementById('ghostVerdict');

  // Inspector & Search
  const graphSearchInput = document.getElementById('graphSearchInput');
  const inspectTitle = document.getElementById('inspectTitle');
  const inspectKind = document.getElementById('inspectKind');
  const inspectRisk = document.getElementById('inspectRisk');
  const inspectSig = document.getElementById('inspectSig');
  const inspectFile = document.getElementById('inspectFile');
  const inspectLines = document.getElementById('inspectLines');
  const inspectDoc = document.getElementById('inspectDoc');
  const inspectBlastCount = document.getElementById('inspectBlastCount');

  // Canvas
  const canvas = document.getElementById('graphCanvas');
  const ctx = canvas.getContext('2d');
  const resetZoomBtn = document.getElementById('resetZoomBtn');

  let memoryData = null;
  let graphData = { nodes: [], links: [] };
  let selectedNode = null;
  let highlightedNodes = new Set();
  let activities = [];

  // Graph Simulation State
  let width = canvas.clientWidth;
  let height = canvas.clientHeight;
  let transform = { x: 0, y: 0, k: 1 };
  let isDraggingCanvas = false;
  let dragStart = { x: 0, y: 0 };
  let draggedNode = null;

  function resizeCanvas() {
    width = canvas.parentElement.clientWidth;
    height = canvas.parentElement.clientHeight;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // --- API Calls ---

  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      valFiles.textContent = data.files_count || 0;
      valSymbols.textContent = data.symbols_count || 0;
      valHypo.textContent = data.hypotheses_count || 0;
    } catch (e) {
      console.error("Status fetch error", e);
    }
  }

  async function fetchMemory() {
    try {
      const res = await fetch('/api/memory');
      memoryData = await res.json();
      renderMemory();
    } catch (e) {
      console.error("Memory fetch error", e);
    }
  }

  async function fetchGraph() {
    try {
      const res = await fetch('/api/graph');
      const data = await res.json();
      initGraph(data);
    } catch (e) {
      console.error("Graph fetch error", e);
    }
  }

  async function fetchRadar() {
    try {
      const res = await fetch('/api/radar');
      const data = await res.json();
      valHealth.textContent = `${data.health_score}/100`;
      radarScoreCircle.textContent = data.health_score;
      radarScoreCircle.className = `score-circle ${data.status}`;
      radarStatusText.textContent = `Architecture Status: ${data.status}`;

      radarDetailsList.innerHTML = '';

      if (data.circular_dependencies && data.circular_dependencies.length > 0) {
        const cCard = document.createElement('div');
        cCard.className = 'item-card';
        cCard.innerHTML = `
          <div class="item-top">
            <span class="status-badge refuted">CIRCULAR DEPENDENCIES (${data.circular_count})</span>
          </div>
          <div style="font-size:0.75rem;color:var(--accent-red);margin-top:4px;">
            ${data.circular_dependencies.map(c => `• ${escapeHtml(c.join(' -> '))}`).join('<br>')}
          </div>
        `;
        radarDetailsList.appendChild(cCard);
      } else {
        const cCard = document.createElement('div');
        cCard.className = 'item-card';
        cCard.innerHTML = `<span style="color:var(--accent-green);font-size:0.8rem;">✓ No circular dependencies detected</span>`;
        radarDetailsList.appendChild(cCard);
      }

      if (data.god_nodes && data.god_nodes.length > 0) {
        const gCard = document.createElement('div');
        gCard.className = 'item-card';
        gCard.innerHTML = `
          <div class="item-top">
            <span class="status-badge exploring">HIGHLY COUPLED GOD NODES</span>
          </div>
          <div style="font-size:0.75rem;color:var(--text-main);margin-top:4px;">
            ${data.god_nodes.map(g => `• <strong>${escapeHtml(g.file)}</strong> (${g.in_degree} incoming deps, ${g.lines} lines, ${g.risk} risk)`).join('<br>')}
          </div>
        `;
        radarDetailsList.appendChild(gCard);
      }

      if (data.orphan_symbols && data.orphan_symbols.length > 0) {
        const oCard = document.createElement('div');
        oCard.className = 'item-card';
        oCard.innerHTML = `
          <div class="item-top">
            <span class="status-badge pending">ORPHAN / CANDIDATE DEAD CODE (${data.orphan_count})</span>
          </div>
          <div style="font-size:0.75rem;color:var(--text-dim);margin-top:4px;">
            ${data.orphan_symbols.slice(0, 6).map(o => `• <code>${escapeHtml(o.symbol)}</code> (${escapeHtml(o.file)}:${o.line})`).join('<br>')}
          </div>
        `;
        radarDetailsList.appendChild(oCard);
      }
    } catch (e) {
      console.error("Radar fetch error", e);
    }
  }

  async function fetchPorts() {
    try {
      const res = await fetch('/api/ports');
      const ports = await res.json();
      valPorts.textContent = `${ports.filter(p => p.is_dev_port).length} Active`;
      portsList.innerHTML = '';
      if (ports.length === 0) {
        portsList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">No active listening ports found.</div>';
        return;
      }
      ports.forEach(p => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span class="status-badge ${p.is_dev_port ? 'exploring' : 'pending'}">PORT ${p.port}</span>
            <span style="font-size:0.75rem;color:var(--text-muted)">PID ${p.pid}</span>
          </div>
          <div style="font-size:0.8rem;color:var(--accent-cyan);">${escapeHtml(p.process_name)}</div>
          <div class="item-actions">
            <button class="btn-xs" style="color:var(--accent-red)" onclick="killPort(${p.port})">Terminate</button>
          </div>
        `;
        portsList.appendChild(card);
      });
    } catch (e) {
      console.error("Ports fetch error", e);
    }
  }

  async function fetchActivity() {
    try {
      const res = await fetch('/api/activity');
      activities = await res.json();
      renderActivity();
    } catch (e) {
      console.error("Activity fetch error", e);
    }
  }

  function renderActivity() {
    activityList.innerHTML = '';
    if (activities.length === 0) {
      activityList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">No recent file modifications detected by watcher.</div>';
      return;
    }
    activities.slice().reverse().forEach(a => {
      const card = document.createElement('div');
      card.className = 'item-card';
      const timeStr = new Date(a.timestamp * 1000).toLocaleTimeString();
      card.innerHTML = `
        <div class="item-top">
          <span class="status-badge ${a.type === 'modified' ? 'exploring' : (a.type === 'created' ? 'confirmed' : 'refuted')}">${a.type}</span>
          <span style="font-size:0.7rem;color:var(--text-dim)">${timeStr}</span>
        </div>
        <div style="font-family:var(--font-code);font-size:0.75rem;color:var(--accent-cyan);">${escapeHtml(a.file)}</div>
      `;
      activityList.appendChild(card);
    });
  }

  // --- Real-time SSE ---
  function connectSSE() {
    const sse = new EventSource('/api/events');
    sse.onopen = () => {
      connStatus.textContent = 'SYNCED (LIVE SSE)';
      connBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
    };
    sse.addEventListener('memory_update', () => {
      fetchMemory();
      fetchStatus();
    });
    sse.addEventListener('scan_complete', () => {
      fetchStatus();
      fetchGraph();
      fetchRadar();
    });
    sse.addEventListener('ports_update', () => {
      fetchPorts();
    });
    sse.addEventListener('file_activity', (e) => {
      try {
        const item = JSON.parse(e.data);
        activities.push(item);
        if (activities.length > 50) activities.shift();
        renderActivity();
        fetchStatus();
      } catch (err) {}
    });
    sse.onerror = () => {
      connStatus.textContent = 'RECONNECTING...';
      connBadge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
    };
  }

  // --- Render Memory Panels ---

  function renderMemory() {
    if (!memoryData) return;

    // 1. Hypotheses
    const hypos = memoryData.hypotheses || [];
    countHypo.textContent = hypos.length;
    hypoList.innerHTML = '';
    if (hypos.length === 0) {
      hypoList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">No active hypotheses. Post one above to track debugging theories.</div>';
    } else {
      hypos.forEach(h => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span class="status-badge ${h.status}">${h.status}</span>
            <span style="font-size:0.7rem;color:var(--text-dim)">#${h.id}</span>
          </div>
          <div class="item-title">${escapeHtml(h.statement)}</div>
          ${h.evidence ? `<div class="item-evidence">Evidence: ${escapeHtml(h.evidence)}</div>` : ''}
          <div class="item-actions">
            ${h.status === 'exploring' ? `
              <button class="btn-xs" style="color:var(--accent-green)" onclick="updateHypo(${h.id}, 'confirmed')">✓ Confirm</button>
              <button class="btn-xs" style="color:var(--accent-red)" onclick="updateHypo(${h.id}, 'refuted')">✗ Refute</button>
            ` : ''}
          </div>
        `;
        hypoList.appendChild(card);
      });
    }

    // 2. Tasks
    const tasks = memoryData.tasks || [];
    countTasks.textContent = tasks.length;
    taskList.innerHTML = '';
    if (tasks.length === 0) {
      taskList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">No tasks queued. Add one above.</div>';
    } else {
      tasks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'item-card';
        const isDone = t.status === 'done';
        card.innerHTML = `
          <div class="item-top">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
              <input type="checkbox" ${isDone ? 'checked' : ''} onchange="toggleTask(${t.id}, this.checked)">
              <span class="item-title" style="${isDone ? 'text-decoration:line-through;color:var(--text-dim)' : ''}">${escapeHtml(t.title)}</span>
            </label>
            <span class="status-badge ${t.status}">${t.status}</span>
          </div>
          ${t.notes ? `<div class="item-notes">${escapeHtml(t.notes)}</div>` : ''}
        `;
        taskList.appendChild(card);
      });
    }

    // 3. Decisions
    const decs = memoryData.decisions || [];
    decisionsList.innerHTML = '';
    if (decs.length === 0) {
      decisionsList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">No architectural decisions logged yet.</div>';
    } else {
      decs.forEach(d => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span style="font-weight:600;color:var(--accent-cyan);">${escapeHtml(d.title)}</span>
          </div>
          <div style="font-size:0.8rem;color:var(--text-main);margin-top:4px;">${escapeHtml(d.rationale)}</div>
          ${d.tradeoffs ? `<div class="item-notes">Trade-offs: ${escapeHtml(d.tradeoffs)}</div>` : ''}
        `;
        decisionsList.appendChild(card);
      });
    }

    // 4. Scratchpad
    if (memoryData.scratchpad && memoryData.scratchpad.content) {
      if (document.activeElement !== scratchpadArea) {
        scratchpadArea.value = memoryData.scratchpad.content;
      }
    }
  }

  // --- Graph Physics & Rendering Engine ---

  function initGraph(data) {
    const nodeMap = new Map();
    const nodes = data.nodes.map((n, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      const radius = 140 + Math.random() * 100;
      const node = {
        ...n,
        x: (width / 2) + Math.cos(angle) * radius,
        y: (height / 2) + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        radius: Math.max(6, Math.min(18, 6 + (n.dependents_count || 0) * 3)),
      };
      nodeMap.set(n.id, node);
      return node;
    });

    const links = data.links.map(l => ({
      source: nodeMap.get(l.source) || l.source,
      target: nodeMap.get(l.target) || l.target,
    })).filter(l => typeof l.source === 'object' && typeof l.target === 'object');

    graphData = { nodes, links };
    transform = { x: 0, y: 0, k: 1 };
  }

  function simulatePhysics() {
    const nodes = graphData.nodes;
    const links = graphData.links;
    if (!nodes.length) return;

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const distSq = dx * dx + dy * dy || 1;
        if (distSq < 40000) {
          const force = 300 / distSq;
          const fx = (dx / Math.sqrt(distSq)) * force;
          const fy = (dy / Math.sqrt(distSq)) * force;
          nodes[i].vx -= fx;
          nodes[i].vy -= fy;
          nodes[j].vx += fx;
          nodes[j].vy += fy;
        }
      }
    }

    for (const l of links) {
      const dx = l.target.x - l.source.x;
      const dy = l.target.y - l.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - 90) * 0.03;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      l.source.vx += fx;
      l.source.vy += fy;
      l.target.vx -= fx;
      l.target.vy -= fy;
    }

    const cx = width / 2;
    const cy = height / 2;
    for (const n of nodes) {
      if (n === draggedNode) continue;
      n.vx += (cx - n.x) * 0.005;
      n.vy += (cy - n.y) * 0.005;
      n.vx *= 0.85;
      n.vy *= 0.85;
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  function renderGraph() {
    ctx.save();
    ctx.clearRect(0, 0, width, height);

    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    for (const l of graphData.links) {
      const isHigh = highlightedNodes.has(l.source.id) && highlightedNodes.has(l.target.id);
      ctx.beginPath();
      ctx.moveTo(l.source.x, l.source.y);
      ctx.lineTo(l.target.x, l.target.y);
      ctx.strokeStyle = isHigh ? 'rgba(239, 68, 68, 0.8)' : 'rgba(59, 130, 246, 0.18)';
      ctx.lineWidth = isHigh ? 2 : 1;
      ctx.stroke();
    }

    for (const n of graphData.nodes) {
      const isSelected = selectedNode && selectedNode.id === n.id;
      const isHighlighted = highlightedNodes.has(n.id);

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);

      let color = '#10b981';
      if (n.dependents_count >= 3) color = '#ef4444';
      else if (n.dependents_count >= 1) color = '#f59e0b';

      if (isHighlighted) color = '#ef4444';

      ctx.fillStyle = color;
      ctx.shadowColor = isSelected || isHighlighted ? color : 'transparent';
      ctx.shadowBlur = isSelected || isHighlighted ? 15 : 0;
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(255,255,255,0.2)';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      ctx.font = '10px "Fira Code", monospace';
      ctx.fillStyle = isSelected ? '#00f2fe' : '#94a3b8';
      ctx.textAlign = 'center';
      ctx.fillText(n.name, n.x, n.y + n.radius + 12);
    }

    ctx.restore();
  }

  function animationLoop() {
    simulatePhysics();
    renderGraph();
    requestAnimationFrame(animationLoop);
  }
  animationLoop();

  // --- Graph Interactions ---

  function screenToWorld(sx, sy) {
    return {
      x: (sx - transform.x) / transform.k,
      y: (sy - transform.y) / transform.k,
    };
  }

  function findNodeAt(wx, wy) {
    for (const n of graphData.nodes) {
      const dx = n.x - wx;
      const dy = n.y - wy;
      if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) {
        return n;
      }
    }
    return null;
  }

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const world = screenToWorld(sx, sy);
    const hit = findNodeAt(world.x, world.y);

    if (hit) {
      draggedNode = hit;
      selectNode(hit);
    } else {
      isDraggingCanvas = true;
      dragStart = { x: sx - transform.x, y: sy - transform.y };
    }
  });

  window.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;

    if (draggedNode) {
      const world = screenToWorld(sx, sy);
      draggedNode.x = world.x;
      draggedNode.y = world.y;
    } else if (isDraggingCanvas) {
      transform.x = sx - dragStart.x;
      transform.y = sy - dragStart.y;
    }
  });

  window.addEventListener('mouseup', () => {
    draggedNode = null;
    isDraggingCanvas = false;
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const zoom = e.deltaY < 0 ? 1.1 : 0.9;

    const newK = Math.max(0.3, Math.min(3, transform.k * zoom));
    transform.x = sx - (sx - transform.x) * (newK / transform.k);
    transform.y = sy - (sy - transform.y) * (newK / transform.k);
    transform.k = newK;
  }, { passive: false });

  resetZoomBtn.addEventListener('click', () => {
    transform = { x: 0, y: 0, k: 1 };
  });

  graphSearchInput.addEventListener('input', (e) => {
    const term = e.target.value.trim().toLowerCase();
    if (!term) {
      highlightedNodes.clear();
      return;
    }
    const match = graphData.nodes.find(n => n.name.toLowerCase().includes(term) || n.id.toLowerCase().includes(term));
    if (match) {
      selectNode(match);
      transform.x = (width / 2) - match.x * transform.k;
      transform.y = (height / 2) - match.y * transform.k;
    }
  });

  async function selectNode(node) {
    selectedNode = node;
    inspectTitle.textContent = node.name;
    inspectKind.textContent = "FILE";
    inspectFile.textContent = node.id;
    inspectLines.textContent = `${node.lines} lines`;
    inspectSig.textContent = `// File: ${node.id} (${node.symbols_count} symbols, ${node.dependents_count} dependents)`;
    inspectDoc.textContent = `Language: ${node.language}`;

    try {
      const res = await fetch(`/api/blast?file=${encodeURIComponent(node.id)}`);
      const blast = await res.json();
      inspectRisk.textContent = `RISK: ${blast.risk_level}`;
      inspectRisk.className = `risk-pill ${blast.risk_level}`;
      inspectBlastCount.textContent = `${blast.impacted_files.length} downstream files, ${blast.related_tests.length} test suites`;
      highlightedNodes = new Set([node.id, ...blast.impacted_files]);
    } catch (e) {
      console.error("Blast query error", e);
    }
  }

  // --- Hallucination Guard UI ---
  runGuardBtn.addEventListener('click', async () => {
    const file = guardFileInput.value.trim();
    if (!file) {
      showToast("Please enter a file to check.");
      return;
    }
    guardResultsList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">Auditing AST for hallucinations...</div>';
    try {
      const res = await fetch('/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file }),
      });
      const data = await res.json();
      guardResultsList.innerHTML = '';

      if (data.valid) {
        guardResultsList.innerHTML = `<div class="item-card"><span style="color:var(--accent-green);font-size:0.85rem;font-weight:600;">✓ Clean: 0 hallucinated calls or invalid imports found in ${escapeHtml(file)}.</span></div>`;
      } else {
        const topBanner = document.createElement('div');
        topBanner.className = 'item-card';
        topBanner.innerHTML = `<span style="color:var(--accent-red);font-weight:600;">✗ ${data.hallucination_count} potential hallucination(s) detected:</span>`;
        guardResultsList.appendChild(topBanner);

        data.hallucinations.forEach(h => {
          const card = document.createElement('div');
          card.className = 'item-card';
          card.innerHTML = `
            <div class="item-top">
              <span class="status-badge refuted">Line ${h.line}</span>
              <span style="font-size:0.75rem;font-family:var(--font-code);color:var(--accent-amber);">${escapeHtml(h.symbol)}</span>
            </div>
            <div style="font-size:0.8rem;color:var(--text-main);margin-top:4px;">${escapeHtml(h.message)}</div>
            ${h.suggested ? `<div class="item-notes">Recommended Fix: <strong>${escapeHtml(h.suggested)}</strong></div>` : ''}
          `;
          guardResultsList.appendChild(card);
        });
      }
    } catch (e) {
      guardResultsList.innerHTML = '<div style="color:var(--accent-red);padding:12px;">Verification failed.</div>';
    }
  });

  // --- Refactor Planner UI ---
  runPlanBtn.addEventListener('click', async () => {
    const file = planFileInput.value.trim();
    const symbol = planSymbolInput.value.trim() || null;
    const objective = planObjInput.value.trim() || "Refactor";
    if (!file) {
      showToast("Target file is required.");
      return;
    }

    planResultsList.innerHTML = '<div style="color:var(--text-dim);font-size:0.8rem;padding:12px;">Generating topologically sorted DAG plan...</div>';
    try {
      const res = await fetch('/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file, symbol, objective }),
      });
      const plan = await res.json();
      planResultsList.innerHTML = '';

      const header = document.createElement('div');
      header.className = 'item-card';
      header.innerHTML = `
        <div class="item-top">
          <span style="font-weight:600;color:var(--accent-cyan);">${escapeHtml(plan.objective)}</span>
          <span class="risk-pill ${plan.risk_level}">RISK: ${plan.risk_level}</span>
        </div>
        <div style="font-size:0.75rem;color:var(--text-dim);margin-top:4px;">${plan.total_steps} sequential execution steps generated.</div>
      `;
      planResultsList.appendChild(header);

      plan.execution_steps.forEach(s => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span class="action-badge ${s.action}">STEP ${s.step_number}: ${s.action}</span>
            <span style="font-size:0.75rem;color:var(--text-dim)">${escapeHtml(s.file)}</span>
          </div>
          <div style="font-size:0.8rem;color:var(--text-main);margin:4px 0;">${escapeHtml(s.description)}</div>
          <div class="item-notes">Verify: <code>${escapeHtml(s.preflight_cmd)}</code></div>
        `;
        planResultsList.appendChild(card);
      });
    } catch (e) {
      planResultsList.innerHTML = '<div style="color:var(--accent-red);padding:12px;">Plan generation failed.</div>';
    }
  });

  // --- Context Packer ---
  packBtn.addEventListener('click', async () => {
    const query = packerQuery.value.trim();
    const budget = parseInt(packerBudget.value, 10) || 1200;
    if (!query) return;

    packStats.textContent = 'Slicing AST...';
    try {
      const res = await fetch('/api/pack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, budget }),
      });
      const data = await res.json();
      packerResult.value = data.slice_content;
      packStats.textContent = `Sliced: ${data.target_symbol || query} (~${data.estimated_tokens} tokens / Budget: ${budget})`;
      showToast("AST Slice Generated!");
    } catch (e) {
      packStats.textContent = "Error packing context.";
    }
  });

  copySliceBtn.addEventListener('click', () => {
    if (packerResult.value) {
      navigator.clipboard.writeText(packerResult.value);
      showToast("Context slice copied!");
    }
  });

  // --- Ghost Patch Simulator ---
  ghostTestBtn.addEventListener('click', async () => {
    const file = ghostFile.value.trim();
    const content = ghostContent.value;
    if (!file || !content) {
      showToast("Please enter file path and proposed code.");
      return;
    }

    ghostVerdict.textContent = 'Simulating dry-run in shadow AST...';
    try {
      const res = await fetch('/api/ghost-patch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file, content }),
      });
      const data = await res.json();
      ghostVerdict.className = `verdict-banner ${data.verdict}`;
      let text = `Verdict: [${data.verdict}] (Safety: ${data.safety_score}/100)`;
      if (data.breakages && data.breakages.length > 0) {
        text += `\n${data.breakages.join('\n')}`;
      }
      if (data.warnings && data.warnings.length > 0) {
        text += `\n${data.warnings.join('\n')}`;
      }
      ghostVerdict.textContent = text;
      showToast(`Ghost Patch: ${data.verdict}`);
    } catch (e) {
      ghostVerdict.textContent = "Error testing patch.";
    }
  });

  // --- RepoMap ---
  if (genRepoMapBtn) {
    genRepoMapBtn.addEventListener('click', async () => {
      const budget = parseInt(repoMapBudgetInput.value, 10) || 1024;
      repoMapStats.textContent = 'Computing PageRank & symbol tree...';
      try {
        const res = await fetch(`/api/repomap?budget=${budget}`);
        const data = await res.json();
        repoMapResult.value = data.map_content;
        repoMapStats.textContent = `RepoMap: ${data.files_included}/${data.total_files} files, ${data.symbols_included} symbols (~${data.estimated_tokens} tokens)`;
        showToast("RepoMap Generated!");
      } catch (e) {
        repoMapStats.textContent = "Error generating RepoMap.";
      }
    });
  }

  if (copyRepoMapBtn) {
    copyRepoMapBtn.addEventListener('click', () => {
      if (repoMapResult.value) {
        navigator.clipboard.writeText(repoMapResult.value);
        showToast("RepoMap copied to clipboard!");
      }
    });
  }

  // --- Dynamic Risk ---
  if (runDynamicRiskBtn) {
    runDynamicRiskBtn.addEventListener('click', async () => {
      const symbol = dynamicRiskSymbolInput.value.trim();
      if (!symbol) return;
      dynamicRiskResultsList.innerHTML = '<div style="color:var(--text-dim);padding:12px;">Auditing symbol across AST & dynamic references...</div>';
      try {
        const res = await fetch(`/api/dynamic-risk?symbol=${encodeURIComponent(symbol)}`);
        const data = await res.json();
        dynamicRiskResultsList.innerHTML = '';
        const header = document.createElement('div');
        header.style.padding = '8px 12px';
        header.style.fontSize = '0.85rem';
        header.innerHTML = `<strong>Dynamic Risk:</strong> <span class="risk-pill ${data.dynamic_risk_level.toLowerCase()}">${data.dynamic_risk_level}</span> (${data.total_unverified_references} unverified dynamic references)`;
        dynamicRiskResultsList.appendChild(header);

        if (data.findings && data.findings.length > 0) {
          data.findings.forEach(f => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
              <div class="item-top">
                <span class="action-badge ${f.severity === 'HIGH' ? 'CREATE' : 'UPDATE'}">${f.severity}</span>
                <span style="font-size:0.75rem;color:var(--text-dim)">${escapeHtml(f.file)}:${f.line}</span>
              </div>
              <div style="font-size:0.8rem;color:var(--text-main);margin:4px 0;">${escapeHtml(f.detail)}</div>
              ${f.snippet ? `<div class="item-notes"><code>${escapeHtml(f.snippet)}</code></div>` : ''}
            `;
            dynamicRiskResultsList.appendChild(card);
          });
        } else {
          dynamicRiskResultsList.innerHTML += '<div style="color:var(--accent-green);padding:12px;">No unverified dynamic reflection or duck typing detected for this symbol.</div>';
        }
      } catch (e) {
        dynamicRiskResultsList.innerHTML = '<div style="color:var(--accent-red);padding:12px;">Dynamic risk audit failed.</div>';
      }
    });
  }

  // --- Port Sentinel ---
  refreshPortsBtn.addEventListener('click', fetchPorts);
  window.killPort = async (port) => {
    if (!confirm(`Are you sure you want to terminate the process on port ${port}?`)) return;
    try {
      const res = await fetch('/api/ports/kill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ port, confirm: true }),
      });
      const data = await res.json();
      showToast(data.message);
      fetchPorts();
    } catch (e) {
      showToast("Failed to kill port.");
    }
  };

  // --- Memory Actions ---

  addHypoBtn.addEventListener('click', async () => {
    const text = newHypoInput.value.trim();
    if (!text) return;
    await fetch('/api/memory/hypo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'add', statement: text, status: 'exploring' }),
    });
    newHypoInput.value = '';
    fetchMemory();
    fetchStatus();
  });

  addTaskBtn.addEventListener('click', async () => {
    const text = newTaskInput.value.trim();
    if (!text) return;
    await fetch('/api/memory/task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'add', title: text, status: 'pending' }),
    });
    newTaskInput.value = '';
    fetchMemory();
    fetchStatus();
  });

  saveScratchBtn.addEventListener('click', async () => {
    const content = scratchpadArea.value;
    await fetch('/api/memory/scratchpad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, updated_by: 'human' }),
    });
    showToast("Scratchpad saved to memory!");
  });

  rescanBtn.addEventListener('click', async () => {
    rescanBtn.disabled = true;
    rescanBtn.textContent = 'Scanning...';
    try {
      await fetch('/api/scan', { method: 'POST' });
      await fetchStatus();
      await fetchGraph();
      await fetchRadar();
      await fetchActivity();
      showToast("AST & Cartography re-scanned!");
    } finally {
      rescanBtn.disabled = false;
      rescanBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg> Re-scan AST';
    }
  });

  copyBriefBtn.addEventListener('click', () => {
    if (memoryData && memoryData.summary) {
      navigator.clipboard.writeText(memoryData.summary);
      showToast("Recovery Briefing copied!");
    }
  });

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
  }

  window.updateHypo = async (id, status) => {
    await fetch('/api/memory/hypo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update', id, status }),
    });
    fetchMemory();
  };

  window.toggleTask = async (id, isDone) => {
    await fetch('/api/memory/task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update', id, status: isDone ? 'done' : 'pending' }),
    });
    fetchMemory();
  };

  // Initial load
  fetchStatus();
  fetchMemory();
  fetchGraph();
  fetchRadar();
  fetchPorts();
  fetchActivity();
  connectSSE();
});
