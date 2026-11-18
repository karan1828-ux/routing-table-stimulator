/**
 * Count-to-Infinity Interactive Lab Controller
 */

class CountToInfinityLab {
  constructor() {
    this.cy = null;
    this.simulationData = null;
    this.steps = [];
    this.currentStepIdx = 0;
    this.isPlaying = false;
    this.playTimer = null;
    this.speedMs = 800;
    this.linkSevered = false;

    this.initGraph();
    this.bindEvents();
  }

  initGraph() {
    const container = document.getElementById('cy-c2i');
    if (!container || !window.cytoscape) return;

    this.cy = window.cytoscape({
      container: container,
      boxSelectionEnabled: false,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(id)',
            'color': '#ffffff',
            'font-family': 'Consolas, Segoe UI, sans-serif',
            'font-size': '16px',
            'font-weight': 'bold',
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': '#1e293b',
            'border-width': 3,
            'border-color': '#6366f1',
            'width': 54,
            'height': 54
          }
        },
        {
          selector: 'node.dest-node',
          style: {
            'background-color': '#831843',
            'border-color': '#f43f5e',
            'border-width': 4,
            'label': 'DEST\n(Network X)',
            'font-size': '12px',
            'text-wrap': 'wrap'
          }
        },
        {
          selector: 'node.loop-node',
          style: {
            'border-color': '#f43f5e',
            'background-color': '#4c0519',
            'border-width': 4
          }
        },
        {
          selector: 'edge',
          style: {
            'label': 'data(weight)',
            'font-family': 'Consolas, monospace',
            'font-size': '13px',
            'font-weight': 'bold',
            'color': '#38bdf8',
            'text-background-color': '#0f172a',
            'text-background-opacity': 0.9,
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'width': 3.5,
            'line-color': '#334155',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge.severed-edge',
          style: {
            'line-color': '#f43f5e',
            'line-style': 'dashed',
            'label': 'SEVERED (∞)',
            'color': '#fda4af',
            'text-background-color': '#4c0519',
            'width': 4
          }
        },
        {
          selector: 'edge.loop-edge',
          style: {
            'line-color': '#f59e0b',
            'width': 5,
            'curve-style': 'bezier'
          }
        }
      ],
      layout: {
        name: 'grid',
        rows: 1,
        padding: 50
      }
    });

    this.renderDefaultTopology();
  }

  renderDefaultTopology() {
    if (!this.cy) return;
    this.cy.elements().remove();

    const elements = [
      { group: 'nodes', data: { id: 'A' }, position: { x: 100, y: 180 } },
      { group: 'nodes', data: { id: 'B' }, position: { x: 260, y: 180 } },
      { group: 'nodes', data: { id: 'C' }, position: { x: 420, y: 180 } },
      { group: 'nodes', data: { id: 'DEST' }, classes: 'dest-node', position: { x: 580, y: 180 } },
      { group: 'edges', data: { id: 'A-B', source: 'A', target: 'B', weight: 1 } },
      { group: 'edges', data: { id: 'B-C', source: 'B', target: 'C', weight: 1 } },
      { group: 'edges', data: { id: 'C-DEST', source: 'C', target: 'DEST', weight: 1 } }
    ];

    this.cy.add(elements);
    this.cy.fit(null, 50);
  }

  bindEvents() {
    const btnRunC2I = document.getElementById('btn-run-c2i');
    if (btnRunC2I) {
      btnRunC2I.addEventListener('click', () => this.fetchAndRunSimulation());
    }

    const btnNext = document.getElementById('c2i-btn-next');
    if (btnNext) btnNext.addEventListener('click', () => this.nextStep());

    const btnPrev = document.getElementById('c2i-btn-prev');
    if (btnPrev) btnPrev.addEventListener('click', () => this.prevStep());

    const btnPlay = document.getElementById('c2i-btn-play');
    if (btnPlay) btnPlay.addEventListener('click', () => this.toggleAutoPlay());

    const btnReset = document.getElementById('c2i-btn-reset');
    if (btnReset) btnReset.addEventListener('click', () => this.resetSimulation());

    const modeSelect = document.getElementById('c2i-mode-select');
    if (modeSelect) {
      modeSelect.addEventListener('change', () => this.fetchAndRunSimulation());
    }

    const thresholdInput = document.getElementById('c2i-threshold-input');
    if (thresholdInput) {
      thresholdInput.addEventListener('change', () => this.fetchAndRunSimulation());
    }
  }

  async fetchAndRunSimulation() {
    const mode = document.getElementById('c2i-mode-select')?.value || 'standard';
    const threshold = parseInt(document.getElementById('c2i-threshold-input')?.value || '16', 10);

    try {
      const response = await fetch('/api/simulation/count-to-infinity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: mode,
          infinity_threshold: threshold,
          destination: 'DEST',
          failed_link: ['C', 'DEST']
        })
      });

      const res = await response.json();
      if (!res.success) {
        alert(res.error || 'Failed to simulate Count-to-Infinity');
        return;
      }

      this.simulationData = res.data;
      this.steps = this.simulationData.steps || [];
      this.currentStepIdx = 0;
      this.stopAutoPlay();
      this.renderCurrentStep();
      this.renderSummary();
    } catch (err) {
      console.error(err);
      alert('Error connecting to backend simulation API.');
    }
  }

  renderCurrentStep() {
    if (!this.steps || this.steps.length === 0) return;
    const step = this.steps[this.currentStepIdx];
    const total = this.steps.length;

    // Progress bar
    const bar = document.getElementById('c2i-progress-bar');
    if (bar) {
      const pct = total > 1 ? Math.round((this.currentStepIdx / (total - 1)) * 100) : 100;
      bar.style.width = `${pct}%`;
    }

    // Step counter
    const counter = document.getElementById('c2i-step-counter');
    if (counter) counter.textContent = `Iteration ${this.currentStepIdx} of ${total - 1}`;

    // Description
    const desc = document.getElementById('c2i-step-desc');
    if (desc) desc.textContent = step.description;

    // Update Node visual state on graph
    this.updateGraphForStep(step);

    // Update Router Metrics Display Cards
    const destCosts = step.dest_costs || {};
    const destHops = step.dest_next_hops || {};

    ['A', 'B', 'C'].forEach(nodeId => {
      const costEl = document.getElementById(`c2i-cost-${nodeId.toLowerCase()}`);
      const hopEl = document.getElementById(`c2i-hop-${nodeId.toLowerCase()}`);
      if (costEl) costEl.textContent = destCosts[nodeId] !== undefined ? destCosts[nodeId] : '-';
      if (hopEl) hopEl.textContent = destHops[nodeId] || '-';
    });

    // Loop Alert Banner
    const loopAlert = document.getElementById('c2i-loop-alert');
    const loopPath = document.getElementById('c2i-loop-path');
    if (loopAlert) {
      if (step.loop_detected && step.routing_loop) {
        loopAlert.style.display = 'flex';
        if (loopPath) loopPath.textContent = step.routing_loop.join(' -> ');
      } else {
        loopAlert.style.display = 'none';
      }
    }

    // Update step logs
    this.renderStepLogs(step);
    this.updateButtons();
  }

  updateGraphForStep(step) {
    if (!this.cy) return;

    this.cy.nodes().removeClass('loop-node');
    this.cy.edges().removeClass('severed-edge loop-edge');

    // If link is DOWN, sever edge C-DEST
    if (step.link_status === 'DOWN') {
      const edge = this.cy.getElementById('C-DEST');
      if (edge.length) edge.addClass('severed-edge');
    }

    // If routing loop active, highlight loop nodes and edges
    if (step.loop_detected && step.routing_loop) {
      step.routing_loop.forEach(nodeId => {
        const n = this.cy.getElementById(nodeId);
        if (n.length) n.addClass('loop-node');
      });
      const edgeAB = this.cy.getElementById('A-B');
      if (edgeAB.length) edgeAB.addClass('loop-edge');
    }
  }

  renderStepLogs(step) {
    const list = document.getElementById('c2i-log-list');
    if (!list) return;

    list.innerHTML = '';
    // Show updates
    if (step.updates && step.updates.length > 0) {
      step.updates.forEach(u => {
        const li = document.createElement('li');
        li.style.padding = '0.35rem 0';
        li.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
        li.style.color = '#cbd5e1';
        li.innerHTML = `<strong style="color:#38bdf8;">${u.router}:</strong> ${u.reason}`;
        list.appendChild(li);
      });
    }

    // Show advertisements
    if (step.advertisements && step.advertisements.length > 0) {
      step.advertisements.forEach(adv => {
        const li = document.createElement('li');
        li.style.padding = '0.35rem 0';
        li.style.color = '#94a3b8';
        li.innerHTML = `<span style="color:#c084fc;">ADV:</span> ${adv.sender} -> ${adv.recipient} advertises cost <strong>${adv.advertised_cost}</strong>${adv.note ? `<em style="color:#fbbf24;">${adv.note}</em>` : ''}`;
        list.appendChild(li);
      });
    }

    if (list.children.length === 0) {
      list.innerHTML = `<li style="color:var(--text-muted);">${step.description}</li>`;
    }
  }

  renderSummary() {
    if (!this.simulationData) return;
    const summary = this.simulationData.summary || {};

    const elMode = document.getElementById('c2i-sum-mode');
    const elIters = document.getElementById('c2i-sum-iters');
    const elMax = document.getElementById('c2i-sum-max');
    const elExpl = document.getElementById('c2i-sum-expl');

    if (elMode) elMode.textContent = summary.mode_name || '-';
    if (elIters) elIters.textContent = summary.iterations_to_resolve !== undefined ? summary.iterations_to_resolve : '-';
    if (elMax) elMax.textContent = summary.max_metric_reached !== undefined ? summary.max_metric_reached : '-';
    if (elExpl) elExpl.textContent = summary.explanation || '';
  }

  nextStep() {
    if (!this.steps || this.currentStepIdx >= this.steps.length - 1) {
      this.stopAutoPlay();
      return;
    }
    this.currentStepIdx++;
    this.renderCurrentStep();
  }

  prevStep() {
    if (this.currentStepIdx <= 0) return;
    this.currentStepIdx--;
    this.renderCurrentStep();
  }

  resetSimulation() {
    this.stopAutoPlay();
    this.currentStepIdx = 0;
    this.renderCurrentStep();
  }

  toggleAutoPlay() {
    if (this.isPlaying) {
      this.stopAutoPlay();
    } else {
      this.startAutoPlay();
    }
  }

  startAutoPlay() {
    if (this.isPlaying) return;
    if (this.currentStepIdx >= this.steps.length - 1) {
      this.currentStepIdx = 0;
    }
    this.isPlaying = true;
    this.updateButtons();

    this.playTimer = setInterval(() => {
      if (this.currentStepIdx < this.steps.length - 1) {
        this.nextStep();
      } else {
        this.stopAutoPlay();
      }
    }, this.speedMs);
  }

  stopAutoPlay() {
    if (this.playTimer) {
      clearInterval(this.playTimer);
      this.playTimer = null;
    }
    this.isPlaying = false;
    this.updateButtons();
  }

  updateButtons() {
    const btnPlay = document.getElementById('c2i-btn-play');
    if (btnPlay) {
      btnPlay.innerHTML = this.isPlaying
        ? `<i class="fas fa-pause"></i> Pause`
        : `<i class="fas fa-play"></i> Auto Play`;
    }

    const btnPrev = document.getElementById('c2i-btn-prev');
    if (btnPrev) btnPrev.disabled = this.currentStepIdx <= 0;

    const btnNext = document.getElementById('c2i-btn-next');
    if (btnNext) btnNext.disabled = !this.steps || this.currentStepIdx >= this.steps.length - 1;
  }
}
