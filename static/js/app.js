/**
 * Master Application Controller for Routing Algorithm Simulator
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Network Graph
  const networkGraph = new NetworkGraph('cy', {
    onNodeSelected: (nodeId) => {
      handleNodeClick(nodeId);
    },
    onEdgeSelected: (source, target, weight) => {
      openEditEdgeModal(source, target, weight);
    }
  });

  // 2. Initialize Simulator
  const simulator = new AlgorithmSimulator(networkGraph);

  // 3. Initialize Count to Infinity Lab
  let c2iLab = null;

  // Topology State
  let currentTopology = { nodes: [], edges: [], adjacency: {} };
  let selectedAlgorithm = 'dijkstra'; // 'dijkstra' | 'distance_vector'

  // ========================================================================
  // Tab Switching
  // ========================================================================
  const navTabs = document.querySelectorAll('.nav-tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      navTabs.forEach(t => t.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');

      if (targetId === 'tab-simulator') {
        setTimeout(() => networkGraph.fitGraph(), 100);
      } else if (targetId === 'tab-c2i') {
        if (!c2iLab) {
          c2iLab = new CountToInfinityLab();
          c2iLab.fetchAndRunSimulation();
        } else {
          setTimeout(() => {
            if (c2iLab.cy) c2iLab.cy.fit(null, 50);
          }, 100);
        }
      }
    });
  });

  // ========================================================================
  // Topology Loading & Rendering
  // ========================================================================
  async function loadNetwork() {
    try {
      const res = await fetch('/api/network');
      const data = await res.json();
      if (data.success) {
        currentTopology = data.topology;
        networkGraph.renderTopology(currentTopology);
        updateRouterDropdowns();
        showToast('Network topology loaded.', 'info');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to load network topology from backend.', 'error');
    }
  }

  function updateRouterDropdowns() {
    const nodes = currentTopology.nodes || [];
    const sourceSelect = document.getElementById('source-router-select');
    const viewSelect = document.getElementById('view-router-select');

    if (!sourceSelect) return;
    const currentVal = sourceSelect.value;
    sourceSelect.innerHTML = '';
    if (viewSelect) viewSelect.innerHTML = '';

    nodes.forEach(n => {
      const nid = typeof n === 'object' ? n.id : String(n);
      const opt1 = document.createElement('option');
      opt1.value = nid;
      opt1.textContent = `Router ${nid}`;
      sourceSelect.appendChild(opt1);

      if (viewSelect) {
        const opt2 = document.createElement('option');
        opt2.value = nid;
        opt2.textContent = `Router ${nid}`;
        viewSelect.appendChild(opt2);
      }
    });

    if (nodes.some(n => (typeof n === 'object' ? n.id : String(n)) === currentVal)) {
      sourceSelect.value = currentVal;
      if (viewSelect) viewSelect.value = currentVal;
    } else if (nodes.length > 0) {
      const firstId = typeof nodes[0] === 'object' ? nodes[0].id : String(nodes[0]);
      sourceSelect.value = firstId;
      if (viewSelect) viewSelect.value = firstId;
    }

    // Update connection modal dropdowns
    updateConnectionModalNodes(nodes);
  }

  function updateConnectionModalNodes(nodes) {
    const src = document.getElementById('edge-source-select');
    const tgt = document.getElementById('edge-target-select');
    if (!src || !tgt) return;

    src.innerHTML = '';
    tgt.innerHTML = '';
    nodes.forEach(n => {
      const nid = typeof n === 'object' ? n.id : String(n);
      const o1 = document.createElement('option');
      o1.value = nid;
      o1.textContent = `Router ${nid}`;
      src.appendChild(o1);

      const o2 = document.createElement('option');
      o2.value = nid;
      o2.textContent = `Router ${nid}`;
      tgt.appendChild(o2);
    });

    if (nodes.length >= 2) {
      tgt.selectedIndex = 1;
    }
  }

  function handleNodeClick(nodeId) {
    const sourceSelect = document.getElementById('source-router-select');
    const viewSelect = document.getElementById('view-router-select');

    if (sourceSelect) sourceSelect.value = nodeId;
    if (viewSelect) viewSelect.value = nodeId;

    simulator.switchViewRouter(nodeId);
    networkGraph.highlightSourceNode(nodeId);
    showToast(`Selected Router ${nodeId}`, 'info');
  }

  // ========================================================================
  // Algorithm Selection
  // ========================================================================
  const algoOptions = document.querySelectorAll('.algo-option-card');
  algoOptions.forEach(card => {
    card.addEventListener('click', () => {
      algoOptions.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        selectedAlgorithm = radio.value;
      }

      // Update explanatory banner
      const banner = document.getElementById('algo-desc-banner');
      if (banner) {
        if (selectedAlgorithm === 'dijkstra') {
          banner.innerHTML = `<strong>Link-State Routing (OSPF):</strong> Routers maintain complete network topology (LSDB) via Link State Advertisements (LSAs) and compute shortest paths locally using Dijkstra's algorithm.`;
        } else {
          banner.innerHTML = `<strong>Distance-Vector Routing (RIP / Bellman-Ford):</strong> Routers only know immediate neighbors and iteratively exchange distance vectors with neighbors: <code>D_x(y) = min_v [ c(x,v) + D_v(y) ]</code>.`;
        }
      }
    });
  });

  // ========================================================================
  // Run Simulation Handler
  // ========================================================================
  const btnStartSim = document.getElementById('btn-start-simulation');
  if (btnStartSim) {
    btnStartSim.addEventListener('click', async () => {
      const source = document.getElementById('source-router-select')?.value || 'A';
      simulator.clearLogs();

      if (selectedAlgorithm === 'dijkstra') {
        try {
          showToast(`Running Dijkstra's algorithm from Router ${source}...`, 'info');
          const res = await fetch('/api/simulation/dijkstra', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: source })
          });
          const data = await res.json();
          if (!data.success) {
            showToast(data.error || 'Dijkstra simulation failed', 'error');
            return;
          }
          simulator.loadSimulation(data.data, 'dijkstra');
          showToast('Dijkstra Shortest Path Tree built successfully.', 'success');
        } catch (err) {
          console.error(err);
          showToast('Failed to execute Dijkstra simulation.', 'error');
        }
      } else {
        // Distance Vector
        try {
          showToast(`Running Distance-Vector distributed exchange...`, 'info');
          const res = await fetch('/api/simulation/distance-vector', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: source, max_iterations: 50 })
          });
          const data = await res.json();
          if (!data.success) {
            showToast(data.error || 'Distance Vector simulation failed', 'error');
            return;
          }
          simulator.loadSimulation(data.data, 'distance_vector');
          showToast(`Distance Vector converged in ${data.data.iterations_count} iterations.`, 'success');
        } catch (err) {
          console.error(err);
          showToast('Failed to execute Distance Vector simulation.', 'error');
        }
      }
    });
  }

  // Simulator Player Controls
  document.getElementById('btn-play-pause')?.addEventListener('click', () => simulator.toggleAutoPlay());
  document.getElementById('btn-next-step')?.addEventListener('click', () => simulator.nextStep());
  document.getElementById('btn-prev-step')?.addEventListener('click', () => simulator.prevStep());
  document.getElementById('btn-run-all')?.addEventListener('click', () => simulator.runAll());
  document.getElementById('btn-reset-sim')?.addEventListener('click', () => simulator.resetSimulation());
  document.getElementById('btn-clear-logs')?.addEventListener('click', () => simulator.clearLogs());

  const speedSlider = document.getElementById('simulation-speed-slider');
  if (speedSlider) {
    speedSlider.addEventListener('input', (e) => {
      // Invert slider so higher value = faster (lower ms)
      const val = parseInt(e.target.value, 10);
      const delayMs = 1600 - val;
      simulator.setSpeed(delayMs);
      const speedValLabel = document.getElementById('speed-val-label');
      if (speedValLabel) speedValLabel.textContent = `${delayMs}ms`;
    });
  }

  const viewRouterSelect = document.getElementById('view-router-select');
  if (viewRouterSelect) {
    viewRouterSelect.addEventListener('change', (e) => {
      simulator.switchViewRouter(e.target.value);
    });
  }

  // ========================================================================
  // Topology Modals & Actions
  // ========================================================================
  // Preset Topologies
  document.getElementById('preset-sample-btn')?.addEventListener('click', () => loadPresetTopology('sample'));
  document.getElementById('preset-mesh-btn')?.addEventListener('click', () => loadPresetTopology('mesh'));
  document.getElementById('preset-c2i-btn')?.addEventListener('click', () => loadPresetTopology('c2i'));
  document.getElementById('preset-disconnected-btn')?.addEventListener('click', () => loadPresetTopology('disconnected'));

  async function loadPresetTopology(presetName) {
    try {
      const res = await fetch('/api/network/load-preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset: presetName })
      });
      const data = await res.json();
      if (data.success) {
        currentTopology = data.topology;
        networkGraph.renderTopology(currentTopology);
        updateRouterDropdowns();
        showToast(`Loaded preset '${presetName}' network.`, 'success');
      } else {
        showToast(data.error || 'Failed to load preset', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Error loading preset topology.', 'error');
    }
  }

  // Reset to Sample Network button
  document.getElementById('btn-reset-sample')?.addEventListener('click', () => loadPresetTopology('sample'));

  // Clear Network
  document.getElementById('btn-clear-network')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear all routers and connections from the network?')) return;
    try {
      const res = await fetch('/api/network/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'clear' })
      });
      const data = await res.json();
      if (data.success) {
        currentTopology = data.topology;
        networkGraph.renderTopology(currentTopology);
        updateRouterDropdowns();
        simulator.clearLogs();
        document.getElementById('routing-table-body').innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding: 1.5rem;">Network cleared. Add routers to begin.</td></tr>`;
        showToast('Network cleared.', 'info');
      }
    } catch (err) {
      showToast('Error clearing network.', 'error');
    }
  });

  // Fit & Relayout
  document.getElementById('btn-fit-graph')?.addEventListener('click', () => networkGraph.fitGraph());
  document.getElementById('btn-relayout-graph')?.addEventListener('click', () => networkGraph.applySmartLayout());

  // Add Node Modal
  const modalAddNode = document.getElementById('modal-add-node');
  document.getElementById('btn-open-add-node')?.addEventListener('click', () => {
    // Suggest next letter
    const existing = new Set((currentTopology.nodes || []).map(n => typeof n === 'object' ? n.id : String(n)));
    let nextLetter = 'A';
    for (let i = 0; i < 26; i++) {
      const letter = String.fromCharCode(65 + i);
      if (!existing.has(letter)) {
        nextLetter = letter;
        break;
      }
    }
    const input = document.getElementById('input-new-node-id');
    if (input) input.value = nextLetter;
    openModal(modalAddNode);
  });

  document.getElementById('btn-submit-add-node')?.addEventListener('click', async () => {
    const input = document.getElementById('input-new-node-id');
    const nodeId = input?.value.trim().toUpperCase();
    if (!nodeId) {
      showToast('Please enter a valid router identifier.', 'error');
      return;
    }

    try {
      const res = await fetch('/api/network/nodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: nodeId })
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || 'Failed to add router', 'error');
        return;
      }
      currentTopology = data.topology;
      networkGraph.renderTopology(currentTopology);
      updateRouterDropdowns();
      closeModal(modalAddNode);
      showToast(`Router ${nodeId} added successfully.`, 'success');
    } catch (err) {
      showToast('Error adding router.', 'error');
    }
  });

  // Delete Node Modal
  const modalDeleteNode = document.getElementById('modal-delete-node');
  document.getElementById('btn-open-delete-node')?.addEventListener('click', () => {
    const select = document.getElementById('select-delete-node');
    if (!select) return;
    select.innerHTML = '';
    (currentTopology.nodes || []).forEach(n => {
      const nid = typeof n === 'object' ? n.id : String(n);
      const opt = document.createElement('option');
      opt.value = nid;
      opt.textContent = `Router ${nid}`;
      select.appendChild(opt);
    });
    openModal(modalDeleteNode);
  });

  document.getElementById('btn-submit-delete-node')?.addEventListener('click', async () => {
    const nodeId = document.getElementById('select-delete-node')?.value;
    if (!nodeId) return;

    try {
      const res = await fetch(`/api/network/nodes/${encodeURIComponent(nodeId)}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || 'Failed to delete router', 'error');
        return;
      }
      currentTopology = data.topology;
      networkGraph.renderTopology(currentTopology);
      updateRouterDropdowns();
      closeModal(modalDeleteNode);
      showToast(`Router ${nodeId} and associated connections removed.`, 'success');
    } catch (err) {
      showToast('Error deleting router.', 'error');
    }
  });

  // Add Edge Modal
  const modalAddEdge = document.getElementById('modal-add-edge');
  document.getElementById('btn-open-add-edge')?.addEventListener('click', () => {
    openModal(modalAddEdge);
  });

  document.getElementById('btn-submit-add-edge')?.addEventListener('click', async () => {
    const u = document.getElementById('edge-source-select')?.value;
    const v = document.getElementById('edge-target-select')?.value;
    const weight = parseFloat(document.getElementById('edge-weight-input')?.value || '1');

    if (!u || !v) {
      showToast('Select both router endpoints.', 'error');
      return;
    }
    if (u === v) {
      showToast('Cannot connect a router to itself.', 'error');
      return;
    }
    if (isNaN(weight) || weight <= 0) {
      showToast('Weight (cost) must be a positive number (> 0).', 'error');
      return;
    }

    try {
      const res = await fetch('/api/network/edges', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: u, target: v, weight: weight })
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || 'Failed to add connection', 'error');
        return;
      }
      currentTopology = data.topology;
      networkGraph.renderTopology(currentTopology);
      closeModal(modalAddEdge);
      showToast(`Connection ${u} <---> ${v} (cost: ${weight}) created.`, 'success');
    } catch (err) {
      showToast('Error adding connection.', 'error');
    }
  });

  // Edit Edge Modal
  const modalEditEdge = document.getElementById('modal-edit-edge');
  function openEditEdgeModal(u, v, weight) {
    const label = document.getElementById('edit-edge-endpoints-label');
    const input = document.getElementById('edit-edge-weight-input');
    const hiddenU = document.getElementById('edit-edge-u');
    const hiddenV = document.getElementById('edit-edge-v');

    if (label) label.textContent = `${u} <---> ${v}`;
    if (input) input.value = weight;
    if (hiddenU) hiddenU.value = u;
    if (hiddenV) hiddenV.value = v;

    openModal(modalEditEdge);
  }

  document.getElementById('btn-submit-update-edge')?.addEventListener('click', async () => {
    const u = document.getElementById('edit-edge-u')?.value;
    const v = document.getElementById('edit-edge-v')?.value;
    const weight = parseFloat(document.getElementById('edit-edge-weight-input')?.value || '1');

    if (isNaN(weight) || weight <= 0) {
      showToast('Weight must be positive.', 'error');
      return;
    }

    try {
      const res = await fetch('/api/network/edges/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: u, target: v, weight: weight })
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || 'Failed to update cost', 'error');
        return;
      }
      currentTopology = data.topology;
      networkGraph.renderTopology(currentTopology);
      closeModal(modalEditEdge);
      showToast(`Connection ${u} <---> ${v} cost updated to ${weight}.`, 'success');
    } catch (err) {
      showToast('Error updating connection.', 'error');
    }
  });

  document.getElementById('btn-delete-edge-action')?.addEventListener('click', async () => {
    const u = document.getElementById('edit-edge-u')?.value;
    const v = document.getElementById('edit-edge-v')?.value;

    try {
      const res = await fetch('/api/network/edges', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: u, target: v })
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || 'Failed to delete connection', 'error');
        return;
      }
      currentTopology = data.topology;
      networkGraph.renderTopology(currentTopology);
      closeModal(modalEditEdge);
      showToast(`Connection ${u} <---> ${v} deleted.`, 'success');
    } catch (err) {
      showToast('Error deleting connection.', 'error');
    }
  });

  // Random Network Generator Modal
  const modalRandom = document.getElementById('modal-random-network');
  document.getElementById('btn-open-random-modal')?.addEventListener('click', () => openModal(modalRandom));

  document.getElementById('btn-submit-random-gen')?.addEventListener('click', async () => {
    const numNodes = parseInt(document.getElementById('random-node-count')?.value || '6', 10);
    const density = parseFloat(document.getElementById('random-density')?.value || '0.45');
    const minW = parseInt(document.getElementById('random-min-weight')?.value || '1', 10);
    const maxW = parseInt(document.getElementById('random-max-weight')?.value || '12', 10);

    try {
      const res = await fetch('/api/network/random', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_nodes: numNodes,
          density: density,
          min_weight: minW,
          max_weight: maxW
        })
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || 'Failed to generate random network', 'error');
        return;
      }
      currentTopology = data.topology;
      networkGraph.renderTopology(currentTopology);
      updateRouterDropdowns();
      closeModal(modalRandom);
      showToast(`Generated random network with ${numNodes} routers.`, 'success');
    } catch (err) {
      showToast('Error generating random network.', 'error');
    }
  });

  // Export CSV
  document.getElementById('btn-export-csv')?.addEventListener('click', async () => {
    const rows = [];
    const tableBody = document.getElementById('routing-table-body');
    if (!tableBody || tableBody.rows.length === 0) {
      showToast('No routing table data to export. Run a simulation first.', 'error');
      return;
    }

    for (let r of tableBody.rows) {
      if (r.cells.length < 5) continue;
      rows.push({
        router: r.cells[0].textContent.trim(),
        destination: r.cells[1].textContent.trim(),
        next_hop: r.cells[2].textContent.trim(),
        cost_display: r.cells[3].textContent.trim(),
        path: r.cells[4].textContent.trim()
      });
    }

    try {
      const res = await fetch('/api/export/csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table: rows, router: simulator.viewRouter })
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `routing_table_${simulator.viewRouter}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('Routing table exported as CSV.', 'success');
    } catch (err) {
      showToast('Failed to export CSV.', 'error');
    }
  });

  // Modal helpers
  function openModal(el) {
    if (el) el.classList.add('active');
  }
  function closeModal(el) {
    if (el) el.classList.remove('active');
  }
  document.querySelectorAll('.modal-close-btn, .modal-cancel-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal-overlay');
      closeModal(modal);
    });
  });

  // Toast Notifications
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-triangle';

    toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Initial load
  loadNetwork();
});
