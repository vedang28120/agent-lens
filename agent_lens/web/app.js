// ==========================================================================
// AgentLens Mission Control Client Engine (UI/UX 2.0)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Navigation & View Router
  const navItems = document.querySelectorAll('.nav-item');
  const viewPanels = document.querySelectorAll('.view-panel');

  // Vital Metric Badges
  const valFiles = document.getElementById('valFiles');
  const valSymbols = document.getElementById('valSymbols');
  const valHealth = document.getElementById('valHealth');
  const valHypo = document.getElementById('valHypo');
  const valPorts = document.getElementById('valPorts');
  const badgePorts = document.getElementById('badgePorts');
  const countHypo = document.getElementById('countHypo');
  const countTasks = document.getElementById('countTasks');

  // Connection & Header Actions
  const connStatus = document.getElementById('connStatus');
  const connBadge = document.getElementById('connBadge');
  const rescanBtn = document.getElementById('rescanBtn');
  const copyBriefBtn = document.getElementById('copyBriefBtn');
  const toast = document.getElementById('toast');

  // Command Palette & Help Modals
  const cmdPaletteTrigger = document.getElementById('cmdPaletteTrigger');
  const cmdModal = document.getElementById('cmdModal');
  const cmdInput = document.getElementById('cmdInput');
  const cmdResultsList = document.getElementById('cmdResultsList');
  const closeCmdBtn = document.getElementById('closeCmdBtn');
  const helpModalBtn = document.getElementById('helpModalBtn');
  const helpModal = document.getElementById('helpModal');
  const closeHelpBtn = document.getElementById('closeHelpBtn');

  // Lists & Containers
  const hypoList = document.getElementById('hypoList');
  const taskList = document.getElementById('taskList');
  const decisionsList = document.getElementById('decisionsList');
  const scratchpadArea = document.getElementById('scratchpadArea');
  const saveScratchBtn = document.getElementById('saveScratchBtn');
  const scratchSavedIndicator = document.getElementById('scratchSavedIndicator');
  const radarDetailsList = document.getElementById('radarDetailsList');
  const radarScoreCircle = document.getElementById('radarScoreCircle');
  const radarStatusText = document.getElementById('radarStatusText');
  const portsList = document.getElementById('portsList');
  const refreshPortsBtn = document.getElementById('refreshPortsBtn');
  const activityList = document.getElementById('activityList');

  // Inputs & Actions
  const newHypoInput = document.getElementById('newHypoInput');
  const addHypoBtn = document.getElementById('addHypoBtn');
  const newTaskInput = document.getElementById('newTaskInput');
  const addTaskBtn = document.getElementById('addTaskBtn');

  // RepoMap Elements
  const repoMapBudgetInput = document.getElementById('repoMapBudgetInput');
  const genRepoMapBtn = document.getElementById('genRepoMapBtn');
  const copyRepoMapBtn = document.getElementById('copyRepoMapBtn');
  const repoMapStats = document.getElementById('repoMapStats');
  const repoMapResult = document.getElementById('repoMapResult');

  // Context Packer Elements
  const packerQuery = document.getElementById('packerQuery');
  const packerBudget = document.getElementById('packerBudget');
  const packBtn = document.getElementById('packBtn');
  const packerResult = document.getElementById('packerResult');
  const packStats = document.getElementById('packStats');
  const copySliceBtn = document.getElementById('copySliceBtn');

  // Blast Elements
  const blastFileInput = document.getElementById('blastFileInput');
  const blastSymbolInput = document.getElementById('blastSymbolInput');
  const runBlastBtn = document.getElementById('runBlastBtn');
  const blastResultsList = document.getElementById('blastResultsList');

  // Dynamic Risk Elements
  const dynamicRiskSymbolInput = document.getElementById('dynamicRiskSymbolInput');
  const runDynamicRiskBtn = document.getElementById('runDynamicRiskBtn');
  const dynamicRiskResultsList = document.getElementById('dynamicRiskResultsList');

  // Hallucination Guard Elements
  const guardFileInput = document.getElementById('guardFileInput');
  const runGuardBtn = document.getElementById('runGuardBtn');
  const guardResultsList = document.getElementById('guardResultsList');

  // Ghost Patch Elements
  const ghostFile = document.getElementById('ghostFile');
  const ghostContent = document.getElementById('ghostContent');
  const ghostTestBtn = document.getElementById('ghostTestBtn');
  const ghostVerdict = document.getElementById('ghostVerdict');
  const ghostVerdictDetails = document.getElementById('ghostVerdictDetails');

  // Planner Elements
  const planFileInput = document.getElementById('planFileInput');
  const planSymbolInput = document.getElementById('planSymbolInput');
  const planObjInput = document.getElementById('planObjInput');
  const runPlanBtn = document.getElementById('runPlanBtn');
  const planResultsList = document.getElementById('planResultsList');

  // Graph Canvas & Drawer Elements
  const canvas = document.getElementById('graphCanvas');
  const ctx = canvas.getContext('2d');
  const graphSearchInput = document.getElementById('graphSearchInput');
  const zoomInBtn = document.getElementById('zoomInBtn');
  const zoomOutBtn = document.getElementById('zoomOutBtn');
  const resetZoomBtn = document.getElementById('resetZoomBtn');
  const chipFilters = document.querySelectorAll('.chip-filter');

  const symbolDrawer = document.getElementById('symbolDrawer');
  const closeDrawerBtn = document.getElementById('closeDrawerBtn');
  const inspectTitle = document.getElementById('inspectTitle');
  const inspectKind = document.getElementById('inspectKind');
  const inspectRisk = document.getElementById('inspectRisk');
  const inspectSig = document.getElementById('inspectSig');
  const inspectFile = document.getElementById('inspectFile');
  const inspectLines = document.getElementById('inspectLines');
  const inspectDoc = document.getElementById('inspectDoc');
  const inspectBlastCount = document.getElementById('inspectBlastCount');
  const actionSimBlast = document.getElementById('actionSimBlast');
  const actionPackContext = document.getElementById('actionPackContext');
  const actionAuditRisk = document.getElementById('actionAuditRisk');

  // Shared State
  let memoryData = null;
  let graphData = { nodes: [], links: [] };
  let selectedNode = null;
  let activeLanguageFilter = 'all';
  let activities = [];
  let cmdItems = [];
  let activeCmdIndex = 0;

  // --------------------------------------------------------------------------
  // Navigation & View Router
  // --------------------------------------------------------------------------

  function switchView(viewId) {
    navItems.forEach(item => {
      if (item.getAttribute('data-view') === viewId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    viewPanels.forEach(panel => {
      if (panel.id === viewId) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    if (viewId === 'view-graph') {
      resizeCanvas();
    }
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const viewId = item.getAttribute('data-view');
      switchView(viewId);
    });
  });

  // --------------------------------------------------------------------------
  // Toast Notifications
  // --------------------------------------------------------------------------

  let toastTimeout;
  function showToast(msg) {
    clearTimeout(toastTimeout);
    toast.textContent = msg;
    toast.classList.add('show');
    toastTimeout = setTimeout(() => {
      toast.classList.remove('show');
    }, 2800);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.toString()
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // --------------------------------------------------------------------------
  // Server API & Polling
  // --------------------------------------------------------------------------

  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      valFiles.textContent = data.files_count;
      valSymbols.textContent = data.symbols_count;
      valHypo.textContent = data.hypotheses_count;
      valPorts.textContent = `${data.ports_count} Active`;
      badgePorts.textContent = data.ports_count;
      countHypo.textContent = data.hypotheses_count;
      countTasks.textContent = data.tasks_count;
    } catch (e) {
      console.error("Status fetch error", e);
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
          <div style="font-size:0.75rem;color:var(--accent-rose);margin-top:4px;font-family:var(--font-mono);">
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
          <div style="font-size:0.75rem;color:var(--text-primary);margin-top:4px;">
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
          <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;font-family:var(--font-mono);">
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
      const data = await res.json();
      const ports = data.ports || data;
      valPorts.textContent = `${ports.filter(p => p.is_dev_port).length} Active`;
      badgePorts.textContent = ports.filter(p => p.is_dev_port).length;
      portsList.innerHTML = '';
      if (!ports || ports.length === 0) {
        portsList.innerHTML = `
          <div class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/></svg>
            <h3>No Listening Ports Found</h3>
            <p>No active listening dev servers detected.</p>
          </div>
        `;
        return;
      }
      ports.forEach(p => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span class="status-badge ${p.is_dev_port ? 'exploring' : 'pending'}">PORT ${p.port}</span>
            <span style="font-size:0.75rem;color:var(--text-muted);font-family:var(--font-mono);">PID ${p.pid}</span>
          </div>
          <div style="font-size:0.85rem;color:var(--accent-cyan);font-family:var(--font-mono);font-weight:600;">${escapeHtml(p.process_name)}</div>
          <div style="font-size:0.75rem;color:var(--text-secondary);">${escapeHtml(p.address || '0.0.0.0')}</div>
          <div class="item-actions">
            <button class="btn btn-secondary btn-xs" style="color:var(--accent-rose);border-color:rgba(244,63,94,0.3);" onclick="killPort(${p.port})">
              Terminate (Safe Confirm)
            </button>
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
      const data = await res.json();
      activities = data.activities || data;
      renderActivity();
    } catch (e) {
      console.error("Activity fetch error", e);
    }
  }

  function renderActivity() {
    activityList.innerHTML = '';
    if (!activities || activities.length === 0) {
      activityList.innerHTML = `
        <div class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <h3>No Live Drift Recorded</h3>
          <p>Filesystem events captured by the background watcher will appear here.</p>
        </div>
      `;
      return;
    }

    activities.slice().reverse().forEach(act => {
      const card = document.createElement('div');
      card.className = 'item-card';
      const timeStr = act.timestamp ? new Date(act.timestamp * 1000).toLocaleTimeString() : '';
      card.innerHTML = `
        <div class="item-top">
          <span class="status-badge ${act.event_type === 'created' ? 'confirmed' : 'exploring'}">${act.event_type}</span>
          <span style="font-size:0.7rem;color:var(--text-muted);font-family:var(--font-mono);">${timeStr}</span>
        </div>
        <div style="font-size:0.8rem;color:var(--text-primary);font-family:var(--font-mono);">${escapeHtml(act.file)}</div>
      `;
      activityList.appendChild(card);
    });
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

  function renderMemory() {
    if (!memoryData) return;

    // 1. Hypotheses
    const hypos = memoryData.hypotheses || [];
    countHypo.textContent = hypos.length;
    hypoList.innerHTML = '';
    if (hypos.length === 0) {
      hypoList.innerHTML = `
        <div class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18h6"/><path d="M10 22h4"/></svg>
          <h3>No Hypotheses Logged</h3>
          <p>Post a reasoning hypothesis above to track architectural or debugging claims.</p>
        </div>
      `;
    } else {
      hypos.forEach(h => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span class="item-title">#${h.id} ${escapeHtml(h.statement)}</span>
            <span class="status-badge ${h.status}">${h.status}</span>
          </div>
          ${h.evidence ? `<div class="item-notes">Evidence: ${escapeHtml(h.evidence)}</div>` : ''}
          <div class="item-actions">
            <button class="btn btn-secondary btn-xs" onclick="toggleHypoStatus(${h.id}, 'confirmed')">Confirm</button>
            <button class="btn btn-secondary btn-xs" onclick="toggleHypoStatus(${h.id}, 'refuted')">Refute</button>
          </div>
        `;
        hypoList.appendChild(card);
      });
    }

    // 2. Tasks
    const tasks = memoryData.tasks || [];
    countTasks.textContent = tasks.filter(t => t.status !== 'done').length;
    taskList.innerHTML = '';
    if (tasks.length === 0) {
      taskList.innerHTML = `
        <div class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/></svg>
          <h3>No Active Tasks</h3>
          <p>Add tasks above to organize refactoring or feature implementation milestones.</p>
        </div>
      `;
    } else {
      tasks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'item-card';
        const isDone = t.status === 'done';
        card.innerHTML = `
          <div class="item-top">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
              <input type="checkbox" ${isDone ? 'checked' : ''} onchange="toggleTask(${t.id}, this.checked)">
              <span class="item-title" style="${isDone ? 'text-decoration:line-through;color:var(--text-muted)' : ''}">${escapeHtml(t.title)}</span>
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
      decisionsList.innerHTML = `
        <div class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
          <h3>No Architectural Decisions Recorded</h3>
          <p>Decisions recorded via <code>lens_manage_memory(action='add_decision')</code> will appear here.</p>
        </div>
      `;
    } else {
      decs.forEach(d => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="item-top">
            <span style="font-weight:700;color:var(--accent-cyan);">${escapeHtml(d.title)}</span>
          </div>
          <div style="font-size:0.8rem;color:var(--text-primary);margin-top:4px;">${escapeHtml(d.rationale)}</div>
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

  // --------------------------------------------------------------------------
  // Server-Sent Events (Live SSE Stream)
  // --------------------------------------------------------------------------

  function initSSE() {
    try {
      const evtSource = new EventSource('/api/events');
      evtSource.onopen = () => {
        connStatus.textContent = 'SYNCED (LIVE SSE)';
        connBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      };

      evtSource.addEventListener('memory_update', () => {
        fetchMemory();
        fetchStatus();
      });

      evtSource.addEventListener('scan_complete', () => {
        fetchStatus();
        fetchGraph();
        fetchRadar();
        showToast("AST re-scan completed!");
      });

      evtSource.addEventListener('file_change', (e) => {
        const d = JSON.parse(e.data);
        activities.push(d);
        renderActivity();
      });

      evtSource.addEventListener('ports_update', () => {
        fetchPorts();
      });

      evtSource.onerror = () => {
        connStatus.textContent = 'DISCONNECTED';
        connBadge.style.borderColor = 'rgba(244, 63, 94, 0.4)';
      };
    } catch (e) {
      console.warn("SSE not available");
    }
  }

  // --------------------------------------------------------------------------
  // Code Graph Physics, Canvas Rendering, & Selection Drawer
  // --------------------------------------------------------------------------

  let width = 800;
  let height = 600;
  let transform = { x: 0, y: 0, k: 0.9 };
  let isDragging = false;
  let dragStart = { x: 0, y: 0 };
  let draggedNode = null;
  let hoveredNode = null;

  function resizeCanvas() {
    const parent = canvas.parentElement;
    if (parent) {
      width = parent.clientWidth;
      height = parent.clientHeight;
      canvas.width = width * window.devicePixelRatio;
      canvas.height = height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  function initGraph(data) {
    const nodeMap = new Map();
    const nodes = data.nodes.map((n, i) => {
      const angle = i * 2.39996;
      const dist = 70 + Math.sqrt(i) * 55;
      const node = {
        ...n,
        x: (width / 2) + Math.cos(angle) * dist,
        y: (height / 2) + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        radius: Math.max(7, Math.min(15, 7 + (n.dependents_count || 0) * 1.2)),
      };
      nodeMap.set(n.id, node);
      return node;
    });

    const links = data.links.map(l => ({
      source: nodeMap.get(l.source) || l.source,
      target: nodeMap.get(l.target) || l.target,
    })).filter(l => typeof l.source === 'object' && typeof l.target === 'object');

    graphData = { nodes, links };
    transform = { x: 0, y: 0, k: 0.85 };
  }

  function simulatePhysics() {
    const nodes = graphData.nodes;
    const links = graphData.links;
    if (!nodes.length) return;

    // 1. Repulsion & Collision Avoidance
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const distSq = dx * dx + dy * dy || 1;
        const dist = Math.sqrt(distSq);

        const minDist = nodes[i].radius + nodes[j].radius + 36;
        if (dist < minDist) {
          const overlap = (minDist - dist) * 0.35;
          const nx = dx / dist;
          const ny = dy / dist;
          nodes[i].vx -= nx * overlap;
          nodes[i].vy -= ny * overlap;
          nodes[j].vx += nx * overlap;
          nodes[j].vy += ny * overlap;
        }

        if (dist < 420) {
          const repForce = 2200 / (distSq + 200);
          const fx = (dx / dist) * repForce;
          const fy = (dy / dist) * repForce;
          nodes[i].vx -= fx;
          nodes[i].vy -= fy;
          nodes[j].vx += fx;
          nodes[j].vy += fy;
        }
      }
    }

    // 2. Spring Links
    for (const l of links) {
      const dx = l.target.x - l.source.x;
      const dy = l.target.y - l.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 130;
      const force = (dist - targetDist) * 0.02;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      l.source.vx += fx;
      l.source.vy += fy;
      l.target.vx -= fx;
      l.target.vy -= fy;
    }

    // 3. Ultra-soft Centering Gravity & Friction
    const cx = width / 2;
    const cy = height / 2;
    for (const n of nodes) {
      if (n === draggedNode) continue;
      n.vx += (cx - n.x) * 0.0006;
      n.vy += (cy - n.y) * 0.0006;
      n.vx *= 0.86;
      n.vy *= 0.86;
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  function renderGraph() {
    ctx.save();
    ctx.clearRect(0, 0, width, height);

    // Subtle space grid dots
    ctx.fillStyle = 'rgba(255, 255, 255, 0.03)';
    const gridStep = 40;
    for (let gx = 0; gx < width; gx += gridStep) {
      for (let gy = 0; gy < height; gy += gridStep) {
        ctx.fillRect(gx, gy, 1.5, 1.5);
      }
    }

    // Apply viewport zoom & pan transform
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    const nodes = graphData.nodes;
    const links = graphData.links;

    // Filter nodes by active language if set
    const isVisible = (n) => {
      if (activeLanguageFilter === 'all') return true;
      if (activeLanguageFilter === 'python') return n.language === 'python';
      if (activeLanguageFilter === 'javascript') return n.language === 'javascript' || n.language === 'typescript';
      if (activeLanguageFilter === 'other') return n.language !== 'python' && n.language !== 'javascript';
      return true;
    };

    // Draw Links
    ctx.lineWidth = 1;
    for (const l of links) {
      if (!isVisible(l.source) || !isVisible(l.target)) continue;
      const isConnectedToSelected = selectedNode && (l.source === selectedNode || l.target === selectedNode);
      if (isConnectedToSelected) {
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.7)';
        ctx.lineWidth = 2;
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
        ctx.lineWidth = 1;
      }
      ctx.beginPath();
      ctx.moveTo(l.source.x, l.source.y);
      ctx.lineTo(l.target.x, l.target.y);
      ctx.stroke();
    }

    // Draw Nodes
    for (const n of nodes) {
      if (!isVisible(n)) continue;
      const isSelected = n === selectedNode;
      const isHovered = n === hoveredNode;

      // Color coding by blast risk
      let fillCol = '#10b981';
      let glowCol = 'rgba(16, 185, 129, 0.4)';
      if (n.risk === 'HIGH' || n.dependents_count >= 8) {
        fillCol = '#f43f5e';
        glowCol = 'rgba(244, 63, 94, 0.4)';
      } else if (n.risk === 'MEDIUM' || n.dependents_count >= 3) {
        fillCol = '#f59e0b';
        glowCol = 'rgba(245, 158, 11, 0.4)';
      }

      // Outer glow for selected or hovered nodes
      if (isSelected || isHovered) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 6, 0, Math.PI * 2);
        ctx.fillStyle = glowCol;
        ctx.fill();
      }

      // Main node body
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? '#00f2fe' : fillCol;
      ctx.fill();
      ctx.strokeStyle = '#090c12';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node label with dark outline stroke for legibility
      const label = n.label || n.id.split('/').pop();
      ctx.font = '500 10px "Fira Code", monospace';
      ctx.textAlign = 'center';

      // Outline stroke behind text
      ctx.strokeStyle = '#090c12';
      ctx.lineWidth = 3.5;
      ctx.strokeText(label, n.x, n.y + n.radius + 12);

      // Text fill
      ctx.fillStyle = isSelected ? '#00f2fe' : '#e2e8f0';
      ctx.fillText(label, n.x, n.y + n.radius + 12);
    }

    ctx.restore();
  }

  function tick() {
    simulatePhysics();
    renderGraph();
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // Mouse & Touch Interactions on Canvas
  function getCanvasCoords(evt) {
    const rect = canvas.getBoundingClientRect();
    const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
    const clientY = evt.touches ? evt.touches[0].clientY : evt.clientY;
    return {
      x: (clientX - rect.left - transform.x) / transform.k,
      y: (clientY - rect.top - transform.y) / transform.k,
    };
  }

  function getNodeAtCoords(coords) {
    const nodes = graphData.nodes;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = coords.x - n.x;
      const dy = coords.y - n.y;
      if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) {
        return n;
      }
    }
    return null;
  }

  canvas.addEventListener('mousedown', (e) => {
    const coords = getCanvasCoords(e);
    const hit = getNodeAtCoords(coords);
    if (hit) {
      draggedNode = hit;
      selectedNode = hit;
      inspectNode(hit);
    } else {
      isDragging = true;
      dragStart = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (draggedNode) {
      const coords = getCanvasCoords(e);
      draggedNode.x = coords.x;
      draggedNode.y = coords.y;
      draggedNode.vx = 0;
      draggedNode.vy = 0;
    } else if (isDragging) {
      transform.x = e.clientX - dragStart.x;
      transform.y = e.clientY - dragStart.y;
    } else {
      const coords = getCanvasCoords(e);
      hoveredNode = getNodeAtCoords(coords);
    }
  });

  window.addEventListener('mouseup', () => {
    draggedNode = null;
    isDragging = false;
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.08 : 0.92;
    transform.k = Math.max(0.2, Math.min(3.0, transform.k * factor));
  }, { passive: false });

  // Floating Graph Controls
  zoomInBtn.addEventListener('click', () => {
    transform.k = Math.min(3.0, transform.k * 1.2);
  });
  zoomOutBtn.addEventListener('click', () => {
    transform.k = Math.max(0.2, transform.k / 1.2);
  });
  resetZoomBtn.addEventListener('click', () => {
    transform = { x: 0, y: 0, k: 0.85 };
  });

  // Language Filter Chips
  chipFilters.forEach(chip => {
    chip.addEventListener('click', () => {
      chipFilters.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      activeLanguageFilter = chip.getAttribute('data-lang');
    });
  });

  // Graph Search Highlight
  graphSearchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    if (!q) {
      selectedNode = null;
      return;
    }
    const match = graphData.nodes.find(n => n.id.toLowerCase().includes(q) || (n.label && n.label.toLowerCase().includes(q)));
    if (match) {
      selectedNode = match;
      inspectNode(match);
      transform.x = (width / 2) - match.x * transform.k;
      transform.y = (height / 2) - match.y * transform.k;
    }
  });

  // Symbol Drawer Details
  async function inspectNode(node) {
    symbolDrawer.classList.remove('hidden');
    inspectTitle.textContent = node.label || node.id;
    inspectFile.textContent = node.file || node.id;
    inspectKind.textContent = (node.kind || 'MODULE').toUpperCase();

    const risk = node.risk || (node.dependents_count >= 8 ? 'HIGH' : node.dependents_count >= 3 ? 'MODERATE' : 'LOW');
    inspectRisk.textContent = `RISK: ${risk}`;
    inspectRisk.className = `risk-pill ${risk.toLowerCase()}`;
    inspectBlastCount.textContent = `${node.dependents_count || 0} downstream callers`;

    try {
      const sym = node.label || node.id.split('/').pop().replace(/\.[^/.]+$/, "");
      const res = await fetch(`/api/card?symbol=${encodeURIComponent(sym)}&file=${encodeURIComponent(node.file || node.id)}`);
      if (res.ok) {
        const card = await res.json();
        inspectSig.textContent = card.signature || '// No signature available';
        inspectLines.textContent = `${card.line_start} - ${card.line_end} (${card.line_count} LOC)`;
        inspectDoc.textContent = card.docstring || 'No docstring provided';
      } else {
        inspectSig.textContent = `// File: ${node.file || node.id}`;
        inspectLines.textContent = `${node.lines || '--'} LOC`;
        inspectDoc.textContent = 'Module level definition';
      }
    } catch (e) {
      inspectSig.textContent = '// Unable to fetch symbol card';
    }
  }

  closeDrawerBtn.addEventListener('click', () => {
    symbolDrawer.classList.add('hidden');
    selectedNode = null;
  });

  // Quick Action Triggers from Drawer
  actionSimBlast.addEventListener('click', () => {
    if (selectedNode) {
      switchView('view-blast');
      blastFileInput.value = selectedNode.file || selectedNode.id;
      blastSymbolInput.value = selectedNode.label || '';
      runBlastBtn.click();
    }
  });

  actionPackContext.addEventListener('click', () => {
    if (selectedNode) {
      switchView('view-packer');
      packerQuery.value = selectedNode.label || selectedNode.id;
      packBtn.click();
    }
  });

  actionAuditRisk.addEventListener('click', () => {
    if (selectedNode) {
      switchView('view-dynamic-risk');
      dynamicRiskSymbolInput.value = selectedNode.label || selectedNode.id;
      runDynamicRiskBtn.click();
    }
  });

  // --------------------------------------------------------------------------
  // Global Command Palette (Ctrl+K)
  // --------------------------------------------------------------------------

  function openCommandPalette() {
    buildCmdItems();
    cmdModal.showModal();
    cmdInput.value = '';
    renderCmdResults('');
    cmdInput.focus();
  }

  function closeCommandPalette() {
    cmdModal.close();
  }

  cmdPaletteTrigger.addEventListener('click', openCommandPalette);
  closeCmdBtn.addEventListener('click', closeCommandPalette);

  cmdModal.addEventListener('click', (e) => {
    const rect = cmdModal.getBoundingClientRect();
    if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
      closeCommandPalette();
    }
  });

  function buildCmdItems() {
    cmdItems = [
      { type: 'view', title: 'Open Code Graph', icon: '🗺️', view: 'view-graph', category: 'Navigation' },
      { type: 'view', title: 'Open PageRank RepoMap', icon: '📑', view: 'view-repomap', category: 'Navigation' },
      { type: 'view', title: 'Open Context Slicer', icon: '✂️', view: 'view-packer', category: 'Navigation' },
      { type: 'view', title: 'Open Blast Radius Simulator', icon: '🎯', view: 'view-blast', category: 'Navigation' },
      { type: 'view', title: 'Open Dynamic Risk Auditor', icon: '⚡', view: 'view-dynamic-risk', category: 'Navigation' },
      { type: 'view', title: 'Open Hallucination Guard', icon: '🛡️', view: 'view-guard', category: 'Navigation' },
      { type: 'view', title: 'Open Ghost Patch Dry-Run', icon: '👻', view: 'view-ghost', category: 'Navigation' },
      { type: 'view', title: 'Open Port Sentinel', icon: '🔌', view: 'view-sentinel', category: 'Navigation' },
      { type: 'view', title: 'Open Hypotheses Ledger', icon: '💡', view: 'view-hypo', category: 'Navigation' },
      { type: 'view', title: 'Open Task Checklist', icon: '✅', view: 'view-tasks', category: 'Navigation' },
      { type: 'view', title: 'Open Scratchpad', icon: '📝', view: 'view-scratchpad', category: 'Navigation' },
      { type: 'action', title: 'Trigger AST Re-Scan', icon: '🔄', action: () => rescanBtn.click(), category: 'Action' },
      { type: 'action', title: 'Copy Agent Recovery Briefing', icon: '📋', action: () => copyBriefBtn.click(), category: 'Action' },
      { type: 'action', title: 'Generate PageRank RepoMap', icon: '⚡', action: () => { switchView('view-repomap'); genRepoMapBtn.click(); }, category: 'Action' },
    ];

    // Add symbols from graph
    if (graphData.nodes) {
      graphData.nodes.slice(0, 50).forEach(n => {
        cmdItems.push({
          type: 'symbol',
          title: n.label || n.id,
          icon: 'ƒ',
          node: n,
          category: 'Symbol',
        });
      });
    }
  }

  function renderCmdResults(query) {
    const q = query.toLowerCase();
    const filtered = cmdItems.filter(item => item.title.toLowerCase().includes(q) || item.category.toLowerCase().includes(q));
    cmdResultsList.innerHTML = '';
    activeCmdIndex = 0;

    if (filtered.length === 0) {
      cmdResultsList.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:0.8rem;text-align:center;">No matching symbols or commands.</div>';
      return;
    }

    filtered.forEach((item, idx) => {
      const row = document.createElement('div');
      row.className = `cmd-item ${idx === 0 ? 'selected' : ''}`;
      row.innerHTML = `
        <span style="font-family:var(--font-mono);color:var(--accent-cyan);">${item.icon}</span>
        <span>${escapeHtml(item.title)}</span>
        <span class="cmd-item-category">${item.category}</span>
      `;
      row.addEventListener('click', () => {
        executeCmdItem(item);
      });
      cmdResultsList.appendChild(row);
    });
  }

  function executeCmdItem(item) {
    closeCommandPalette();
    if (item.type === 'view') {
      switchView(item.view);
    } else if (item.type === 'action') {
      item.action();
    } else if (item.type === 'symbol') {
      switchView('view-graph');
      selectedNode = item.node;
      inspectNode(item.node);
      transform.x = (width / 2) - item.node.x * transform.k;
      transform.y = (height / 2) - item.node.y * transform.k;
    }
  }

  cmdInput.addEventListener('input', (e) => {
    renderCmdResults(e.target.value);
  });

  cmdInput.addEventListener('keydown', (e) => {
    const items = cmdResultsList.querySelectorAll('.cmd-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeCmdIndex = Math.min(items.length - 1, activeCmdIndex + 1);
      updateCmdSelection(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeCmdIndex = Math.max(0, activeCmdIndex - 1);
      updateCmdSelection(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const q = cmdInput.value.toLowerCase();
      const filtered = cmdItems.filter(item => item.title.toLowerCase().includes(q) || item.category.toLowerCase().includes(q));
      if (filtered[activeCmdIndex]) {
        executeCmdItem(filtered[activeCmdIndex]);
      }
    } else if (e.key === 'Escape') {
      closeCommandPalette();
    }
  });

  function updateCmdSelection(items) {
    items.forEach((it, idx) => {
      if (idx === activeCmdIndex) {
        it.classList.add('selected');
        it.scrollIntoView({ block: 'nearest' });
      } else {
        it.classList.remove('selected');
      }
    });
  }

  // Global Keyboard Shortcuts
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openCommandPalette();
    } else if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      helpModal.showModal();
    } else if (e.key.toLowerCase() === 'r' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      rescanBtn.click();
    } else if (e.key.toLowerCase() === 'b' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      copyBriefBtn.click();
    }
  });

  helpModalBtn.addEventListener('click', () => helpModal.showModal());
  closeHelpBtn.addEventListener('click', () => helpModal.close());
  helpModal.addEventListener('click', (e) => {
    const rect = helpModal.getBoundingClientRect();
    if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
      helpModal.close();
    }
  });

  // --------------------------------------------------------------------------
  // Tool View Actions
  // --------------------------------------------------------------------------

  // 1. RepoMap
  genRepoMapBtn.addEventListener('click', async () => {
    const budget = parseInt(repoMapBudgetInput.value, 10) || 1024;
    repoMapStats.textContent = 'Computing PageRank & symbol tree...';
    try {
      const res = await fetch(`/api/repomap?budget=${budget}`);
      const data = await res.json();
      repoMapResult.value = data.map_content;
      repoMapStats.textContent = `RepoMap: ${data.files_included}/${data.total_files} files, ${data.symbols_included} symbols (~${data.estimated_tokens} tokens)`;
      showToast("RepoMap Computed!");
    } catch (e) {
      repoMapStats.textContent = "Error generating RepoMap.";
    }
  });

  copyRepoMapBtn.addEventListener('click', () => {
    if (repoMapResult.value) {
      navigator.clipboard.writeText(repoMapResult.value);
      showToast("RepoMap copied to clipboard!");
    }
  });

  // 2. Context Packer
  packBtn.addEventListener('click', async () => {
    const q = packerQuery.value.trim();
    const budget = parseInt(packerBudget.value, 10) || 1200;
    if (!q) {
      showToast("Please enter target symbol or module name.");
      return;
    }
    packStats.textContent = "Pruning AST and extracting context slice...";
    try {
      const res = await fetch('/api/pack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, budget }),
      });
      const data = await res.json();
      packerResult.value = data.slice_content;
      packStats.textContent = `Packed: ${data.lines_returned} lines (~${data.estimated_tokens} tokens) for '${q}'`;
      showToast("Context slice ready!");
    } catch (e) {
      packStats.textContent = "Error slicing context.";
    }
  });

  copySliceBtn.addEventListener('click', () => {
    if (packerResult.value) {
      navigator.clipboard.writeText(packerResult.value);
      showToast("Context slice copied!");
    }
  });

  // 3. Blast Radius
  runBlastBtn.addEventListener('click', async () => {
    const file = blastFileInput.value.trim();
    const sym = blastSymbolInput.value.trim();
    if (!file) {
      showToast("Please enter a file path.");
      return;
    }

    blastResultsList.innerHTML = '<div style="color:var(--text-muted);padding:14px;">Calculating transitive reverse blast radius...</div>';
    try {
      const url = `/api/blast?file=${encodeURIComponent(file)}${sym ? `&symbol=${encodeURIComponent(sym)}` : ''}`;
      const res = await fetch(url);
      const data = await res.json();
      blastResultsList.innerHTML = '';

      const summaryCard = document.createElement('div');
      summaryCard.className = 'item-card';
      summaryCard.innerHTML = `
        <div class="item-top">
          <span style="font-weight:700;color:var(--text-primary);">${escapeHtml(data.target_file)}</span>
          <span class="risk-pill ${data.risk_level.toLowerCase()}">RISK: ${data.risk_level}</span>
        </div>
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
          Impacts <strong>${data.impacted_files.length}</strong> downstream files, <strong>${data.impacted_symbols.length}</strong> callers, and <strong>${data.related_tests.length}</strong> test suites.
        </div>
      `;
      blastResultsList.appendChild(summaryCard);

      if (data.related_tests.length > 0) {
        const testCard = document.createElement('div');
        testCard.className = 'item-card';
        testCard.innerHTML = `
          <div class="item-top"><span class="status-badge confirmed">ASSOCIATED TEST SUITES</span></div>
          <div style="font-size:0.75rem;font-family:var(--font-mono);color:var(--accent-green);margin-top:4px;">
            ${data.related_tests.map(t => `• ${escapeHtml(t)}`).join('<br>')}
          </div>
        `;
        blastResultsList.appendChild(testCard);
      }

      if (data.impacted_files.length > 0) {
        const callerCard = document.createElement('div');
        callerCard.className = 'item-card';
        callerCard.innerHTML = `
          <div class="item-top"><span class="status-badge exploring">IMPACTED DOWNSTREAM FILES</span></div>
          <div style="font-size:0.75rem;font-family:var(--font-mono);color:var(--text-secondary);margin-top:4px;">
            ${data.impacted_files.map(f => `• ${escapeHtml(f)}`).join('<br>')}
          </div>
        `;
        blastResultsList.appendChild(callerCard);
      }
    } catch (e) {
      blastResultsList.innerHTML = '<div style="color:var(--accent-rose);padding:14px;">Error calculating blast radius.</div>';
    }
  });

  // 4. Dynamic Risk
  window.setAndAuditRisk = (symbol) => {
    dynamicRiskSymbolInput.value = symbol;
    runDynamicRiskBtn.click();
  };

  runDynamicRiskBtn.addEventListener('click', async () => {
    const symbol = dynamicRiskSymbolInput.value.trim();
    if (!symbol) return;
    dynamicRiskResultsList.innerHTML = '<div style="color:var(--text-muted);padding:14px;">Auditing symbol across AST & dynamic references...</div>';
    try {
      const res = await fetch(`/api/dynamic-risk?symbol=${encodeURIComponent(symbol)}`);
      const data = await res.json();
      dynamicRiskResultsList.innerHTML = '';

      const summaryCard = document.createElement('div');
      summaryCard.className = 'item-card';
      summaryCard.innerHTML = `
        <div class="item-top">
          <span style="font-weight:700;font-family:var(--font-mono);color:var(--accent-cyan);">${escapeHtml(symbol)}</span>
          <span class="risk-pill ${data.dynamic_risk_level.toLowerCase()}">DYNAMIC RISK: ${data.dynamic_risk_level}</span>
        </div>
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
          Detected <strong>${data.total_unverified_references}</strong> unverified dynamic references (reflection, registry lookups, duck typing).
        </div>
      `;
      dynamicRiskResultsList.appendChild(summaryCard);

      if (data.findings && data.findings.length > 0) {
        data.findings.forEach(f => {
          const card = document.createElement('div');
          card.className = 'item-card';
          card.innerHTML = `
            <div class="item-top">
              <span class="status-badge ${f.severity === 'HIGH' ? 'refuted' : 'pending'}">${f.severity}</span>
              <span style="font-size:0.75rem;font-family:var(--font-mono);color:var(--text-muted);">${escapeHtml(f.file)}:${f.line}</span>
            </div>
            <div style="font-size:0.8rem;color:var(--text-primary);margin:4px 0;">${escapeHtml(f.detail)}</div>
            ${f.snippet ? `<div class="item-notes"><code>${escapeHtml(f.snippet)}</code></div>` : ''}
          `;
          dynamicRiskResultsList.appendChild(card);
        });
      } else {
        const cleanCard = document.createElement('div');
        cleanCard.className = 'item-card';
        cleanCard.innerHTML = '<span style="color:var(--accent-green);font-size:0.8rem;">✓ No unverified dynamic reflection or duck typing detected for this symbol.</span>';
        dynamicRiskResultsList.appendChild(cleanCard);
      }
    } catch (e) {
      dynamicRiskResultsList.innerHTML = '<div style="color:var(--accent-rose);padding:14px;">Dynamic risk audit failed.</div>';
    }
  });

  // 5. Hallucination Guard
  runGuardBtn.addEventListener('click', async () => {
    const file = guardFileInput.value.trim();
    if (!file) return;
    guardResultsList.innerHTML = '<div style="color:var(--text-muted);padding:14px;">Cross-checking imports against workspace exports and stdlib...</div>';
    try {
      const res = await fetch('/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file }),
      });
      const data = await res.json();
      guardResultsList.innerHTML = '';

      const summaryCard = document.createElement('div');
      summaryCard.className = 'item-card';
      summaryCard.innerHTML = `
        <div class="item-top">
          <span style="font-weight:700;font-family:var(--font-mono);color:var(--text-primary);">${escapeHtml(data.file)}</span>
          <span class="status-badge ${data.is_clean ? 'confirmed' : 'refuted'}">${data.is_clean ? 'CLEAN' : 'FLAGGED'}</span>
        </div>
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
          ${data.is_clean ? 'All imported modules and methods exist in the project or stdlib.' : `Found ${data.flagged_count} phantom imports or nonexistent symbols.`}
        </div>
      `;
      guardResultsList.appendChild(summaryCard);

      if (data.hallucinations && data.hallucinations.length > 0) {
        data.hallucinations.forEach(h => {
          const card = document.createElement('div');
          card.className = 'item-card';
          card.innerHTML = `
            <div class="item-top"><span class="status-badge refuted">UNRESOLVED IMPORT</span></div>
            <div style="font-size:0.8rem;color:var(--accent-rose);font-family:var(--font-mono);">${escapeHtml(h.symbol)}</div>
            ${h.suggested_match ? `<div class="item-notes">Nearest match suggestion: <strong>${escapeHtml(h.suggested_match)}</strong></div>` : ''}
          `;
          guardResultsList.appendChild(card);
        });
      }
    } catch (e) {
      guardResultsList.innerHTML = '<div style="color:var(--accent-rose);padding:14px;">File verification failed.</div>';
    }
  });

  // 6. Ghost Patch Dry-Run
  ghostTestBtn.addEventListener('click', async () => {
    const file = ghostFile.value.trim();
    const content = ghostContent.value;
    if (!file || !content) {
      showToast("Please enter file path and proposed patch.");
      return;
    }

    ghostVerdict.textContent = 'Simulating dry-run in shadow AST...';
    ghostVerdict.className = 'verdict-banner waiting';
    try {
      const res = await fetch('/api/ghost-patch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file, content }),
      });
      const data = await res.json();
      ghostVerdict.className = `verdict-banner ${data.verdict}`;
      ghostVerdict.textContent = `Verdict: [${data.verdict}] (Safety Score: ${data.safety_score}/100)`;

      let detailsHtml = '';
      if (data.breakages && data.breakages.length > 0) {
        detailsHtml += `<div style="color:var(--accent-rose);margin-top:8px;"><strong>Breakages:</strong><br>${data.breakages.map(b => `• ${escapeHtml(b)}`).join('<br>')}</div>`;
      }
      if (data.warnings && data.warnings.length > 0) {
        detailsHtml += `<div style="color:var(--accent-amber);margin-top:8px;"><strong>Warnings:</strong><br>${data.warnings.map(w => `• ${escapeHtml(w)}`).join('<br>')}</div>`;
      }
      if (data.caveats && data.caveats.length > 0) {
        detailsHtml += `<div style="color:var(--text-muted);font-size:0.75rem;margin-top:8px;"><strong>Caveats:</strong><br>${data.caveats.map(c => `• ${escapeHtml(c)}`).join('<br>')}</div>`;
      }
      ghostVerdictDetails.innerHTML = detailsHtml || '<p class="muted-note">No caller breakages detected in static AST analysis.</p>';
      showToast(`Ghost Patch: ${data.verdict}`);
    } catch (e) {
      ghostVerdict.textContent = "Error testing patch.";
    }
  });

  // 7. Refactor Planner
  runPlanBtn.addEventListener('click', async () => {
    const file = planFileInput.value.trim();
    const sym = planSymbolInput.value.trim();
    const obj = planObjInput.value.trim();
    if (!file) return;

    planResultsList.innerHTML = '<div style="color:var(--text-muted);padding:14px;">Generating topologically sorted refactoring DAG plan...</div>';
    try {
      const res = await fetch('/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file, symbol: sym, objective: obj }),
      });
      const data = await res.json();
      planResultsList.innerHTML = '';

      const summaryCard = document.createElement('div');
      summaryCard.className = 'item-card';
      summaryCard.innerHTML = `
        <div class="item-top">
          <span style="font-weight:700;color:var(--accent-cyan);">${escapeHtml(data.objective || 'Refactor Plan')}</span>
          <span class="status-badge confirmed">${data.total_steps || data.steps.length} STEPS</span>
        </div>
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
          Target: <code>${escapeHtml(data.target_file)}</code> (${data.target_symbol || 'entire module'})
        </div>
      `;
      planResultsList.appendChild(summaryCard);

      if (data.steps && data.steps.length > 0) {
        data.steps.forEach((step, idx) => {
          const card = document.createElement('div');
          card.className = 'item-card';
          card.innerHTML = `
            <div class="item-top">
              <span class="status-badge exploring">STEP ${idx + 1}: ${step.action}</span>
              <span style="font-size:0.75rem;font-family:var(--font-mono);color:var(--text-muted);">${escapeHtml(step.file)}</span>
            </div>
            <div style="font-size:0.82rem;color:var(--text-primary);margin-top:4px;">${escapeHtml(step.description)}</div>
          `;
          planResultsList.appendChild(card);
        });
      }
    } catch (e) {
      planResultsList.innerHTML = '<div style="color:var(--accent-rose);padding:14px;">Error generating plan.</div>';
    }
  });

  // 8. Port Sentinel
  refreshPortsBtn.addEventListener('click', fetchPorts);
  window.killPort = async (port) => {
    if (!confirm(`Safety Check: Terminate dev server process listening on port ${port}?`)) return;
    try {
      const res = await fetch('/api/ports/kill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ port, confirm: true }),
      });
      const data = await res.json();
      showToast(data.message || `Terminated port ${port}`);
      fetchPorts();
    } catch (e) {
      showToast("Failed to kill port.");
    }
  };

  // 9. Memory Handlers
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
    showToast("Hypothesis added!");
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
    showToast("Task created!");
  });

  window.toggleHypoStatus = async (id, status) => {
    await fetch('/api/memory/hypo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update', id, status }),
    });
    fetchMemory();
    fetchStatus();
  };

  window.toggleTask = async (id, isDone) => {
    await fetch('/api/memory/task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update', id, status: isDone ? 'done' : 'pending' }),
    });
    fetchMemory();
    fetchStatus();
  };

  saveScratchBtn.addEventListener('click', async () => {
    const content = scratchpadArea.value;
    scratchSavedIndicator.textContent = 'Saving...';
    await fetch('/api/memory/scratchpad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, updated_by: 'human' }),
    });
    scratchSavedIndicator.textContent = 'Synced to SQLite';
    showToast("Scratchpad saved!");
  });

  // 10. Header Action Triggers
  rescanBtn.addEventListener('click', async () => {
    rescanBtn.disabled = true;
    rescanBtn.textContent = 'Scanning...';
    try {
      await fetch('/api/scan', { method: 'POST' });
    } catch (e) {
      console.error(e);
    } finally {
      rescanBtn.disabled = false;
      rescanBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
        Re-scan AST
      `;
    }
  });

  copyBriefBtn.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/memory');
      const data = await res.json();
      if (data.compact_summary) {
        navigator.clipboard.writeText(data.compact_summary);
        showToast("Recovery Briefing copied to clipboard!");
      }
    } catch (e) {
      showToast("Failed to copy briefing.");
    }
  });

  // Initial Boot
  fetchStatus();
  fetchGraph();
  fetchRadar();
  fetchPorts();
  fetchActivity();
  fetchMemory();
  initSSE();
});
