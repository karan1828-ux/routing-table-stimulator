/**
 * Algorithm Simulation Player & Routing Table Manager
 */

class AlgorithmSimulator {
  constructor(networkGraph, uiCallbacks = {}) {
    this.graph = networkGraph;
    this.callbacks = uiCallbacks;

    // State
    this.algorithm = 'dijkstra'; // 'dijkstra' | 'distance_vector'
    this.simulationData = null;
    this.steps = [];
    this.currentStepIdx = 0;
    this.isPlaying = false;
    this.playTimer = null;
    this.speedMs = 700; // Step delay

    // Cache
    this.activeSource = 'A';
    this.viewRouter = 'A';
    this.allTables = {};
  }

  loadSimulation(data, algorithmType) {
    this.stopAutoPlay();
    this.algorithm = algorithmType;
    this.simulationData = data;
    this.currentStepIdx = 0;
    this.activeSource = data.source || 'A';
    this.viewRouter = this.activeSource;

    if (algorithmType === 'dijkstra') {
      this.steps = data.steps || [];
    } else {
      // Distance vector iterations
      this.steps = data.iterations || [];
      this.allTables = data.all_routing_tables || {};
    }

    this.renderCurrentStep();
    this.updateControls();
    this.updateStatistics();
  }

  setSpeed(ms) {
    this.speedMs = Math.max(150, Math.min(2500, ms));
    if (this.isPlaying) {
      this.stopAutoPlay();
      this.startAutoPlay();
    }
  }

  nextStep() {
    if (!this.steps || this.currentStepIdx >= this.steps.length - 1) {
      this.stopAutoPlay();
      return;
    }
    this.currentStepIdx++;
    this.renderCurrentStep();
    this.updateControls();
  }

  prevStep() {
    if (this.currentStepIdx <= 0) return;
    this.currentStepIdx--;
    this.renderCurrentStep();
    this.updateControls();
  }

  runAll() {
    this.stopAutoPlay();
    if (!this.steps || this.steps.length === 0) return;
    this.currentStepIdx = this.steps.length - 1;
    this.renderCurrentStep();
    this.updateControls();
  }

  resetSimulation() {
    this.stopAutoPlay();
    this.currentStepIdx = 0;
    if (this.steps && this.steps.length > 0) {
      this.renderCurrentStep();
    } else {
      this.graph.clearHighlights();
    }
    this.updateControls();
  }

  startAutoPlay() {
    if (this.isPlaying) return;
    if (this.currentStepIdx >= this.steps.length - 1) {
      this.currentStepIdx = 0;
    }
    this.isPlaying = true;
    this.updateControls();

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
    this.updateControls();
  }

  toggleAutoPlay() {
    if (this.isPlaying) {
      this.stopAutoPlay();
    } else {
      this.startAutoPlay();
    }
  }

  renderCurrentStep() {
    if (!this.steps || this.steps.length === 0) return;
    const step = this.steps[this.currentStepIdx];
    const total = this.steps.length;

    // Update Progress UI
    const progressPercent = total > 1 ? Math.round((this.currentStepIdx / (total - 1)) * 100) : 100;
    const bar = document.getElementById('simulation-progress-bar');
    if (bar) bar.style.width = `${progressPercent}%`;

    const label = document.getElementById('step-counter-label');
    if (label) {
      const stepWord = this.algorithm === 'dijkstra' ? 'Step' : 'Iteration';
      label.textContent = `${stepWord} ${this.currentStepIdx + 1} of ${total}`;
    }

    // Step Status Narrative
    const statusTitle = document.getElementById('step-status-title');
    const statusDesc = document.getElementById('step-status-desc');

    if (this.algorithm === 'dijkstra') {
      this.renderDijkstraStep(step);
    } else {
      this.renderDistanceVectorStep(step);
    }
  }

  renderDijkstraStep(step) {
    const statusTitle = document.getElementById('step-status-title');
    const statusDesc = document.getElementById('step-status-desc');

    if (statusTitle) {
      statusTitle.innerHTML = `<span><i class="fas fa-satellite-dish"></i> ${step.type.toUpperCase().replace('_', ' ')}</span> <span class="panel-badge">Step #${step.step}</span>`;
    }
    if (statusDesc) {
      statusDesc.textContent = step.description;
    }

    // Highlight Graph
    this.graph.applyStepHighlights(step);

    // Build intermediate routing table for Dijkstra
    this.renderDijkstraTableAtStep(step);

    // Add log entry
    this.appendLogEntry({
      badge: step.type === 'relax_edge' ? 'relax' : (step.type === 'init' ? 'init' : (step.type === 'completed' ? 'done' : 'check')),
      message: step.description,
      stepNum: step.step
    });
  }

  renderDistanceVectorStep(step) {
    const statusTitle = document.getElementById('step-status-title');
    const statusDesc = document.getElementById('step-status-desc');

    if (statusTitle) {
      statusTitle.innerHTML = `<span><i class="fas fa-network-wired"></i> ITERATION ${step.iteration}</span> <span class="panel-badge">${step.updates.length} Updates</span>`;
    }
    if (statusDesc) {
      statusDesc.textContent = step.description;
    }

    // Clear highlights, highlight source router
    this.graph.highlightSourceNode(this.viewRouter);

    // Render snapshot of tables
    const tableData = (step.tables && step.tables[this.viewRouter]) ? step.tables[this.viewRouter] : [];
    this.renderRoutingTableRows(tableData, step.updates);

    // Add logs for exchanges and updates
    if (step.updates && step.updates.length > 0) {
      step.updates.forEach(u => {
        this.appendLogEntry({
          badge: 'update',
          message: u.reason,
          stepNum: step.iteration
        });
      });
    } else {
      this.appendLogEntry({
        badge: step.iteration === 0 ? 'init' : 'done',
        message: step.description,
        stepNum: step.iteration
      });
    }
  }

  renderDijkstraTableAtStep(step) {
    // If completed step, use final table
    if (step.type === 'completed' && this.simulationData.routing_table) {
      this.renderRoutingTableRows(this.simulationData.routing_table);
      return;
    }

    const rows = [];
    const distances = step.distances || {};
    const preds = step.predecessors || {};
    const source = this.activeSource;

    Object.keys(distances).sort().forEach(dest => {
      const dist = distances[dest];
      const isInf = dist === 'inf' || dist === Infinity;
      const path = this.reconstructPathFromPredecessors(preds, source, dest);
      const nextHop = path.length >= 2 ? path[1] : (source === dest ? '-' : '-');

      rows.push({
        router: source,
        destination: dest,
        next_hop: nextHop,
        cost: isInf ? null : dist,
        cost_display: isInf ? '∞' : dist,
        path: path.length > 0 ? path.join(' -> ') : (isInf ? 'Unreachable' : source),
        path_nodes: path
      });
    });

    this.renderRoutingTableRows(rows);
  }

  reconstructPathFromPredecessors(predecessors, source, target) {
    if (source === target) return [source];
    if (!predecessors || !predecessors[target]) return [];

    const path = [];
    let curr = target;
    const seen = new Set();
    while (curr && !seen.has(curr)) {
      seen.add(curr);
      path.push(curr);
      if (curr === source) break;
      curr = predecessors[curr];
    }
    if (!path.includes(source)) return [];
    return path.reverse();
  }

  renderRoutingTableRows(rows, recentUpdates = []) {
    const tbody = document.getElementById('routing-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (!rows || rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding: 1.5rem;">No routing entries available.</td></tr>`;
      return;
    }

    // Determine updated destination keys for row flashing
    const updatedDests = new Set((recentUpdates || []).map(u => u.destination));

    rows.forEach(row => {
      const tr = document.createElement('tr');
      if (updatedDests.has(row.destination)) {
        tr.classList.add('highlight-updated');
      }

      // Allow clicking row to highlight path on graph
      tr.style.cursor = 'pointer';
      tr.title = 'Click to highlight this path on the network graph';
      tr.addEventListener('click', () => {
        if (row.path_nodes && row.path_nodes.length > 0) {
          this.graph.highlightPath(row.path_nodes);
        }
      });

      tr.innerHTML = `
        <td><strong style="color:#e2e8f0;">${row.router || this.viewRouter}</strong></td>
        <td><span style="color:#38bdf8; font-weight:700;">${row.destination}</span></td>
        <td class="cell-next-hop">${row.next_hop || '-'}</td>
        <td class="cell-cost">${row.cost_display || (row.cost !== null ? row.cost : '∞')}</td>
        <td class="cell-path">${row.path || 'Unreachable'}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  appendLogEntry(item) {
    const stream = document.getElementById('simulation-logs-stream');
    if (!stream) return;

    const entry = document.createElement('div');
    entry.className = 'log-entry';

    const badgeClass = `badge-${item.badge || 'check'}`;
    const badgeText = (item.badge || 'info').toUpperCase();

    entry.innerHTML = `
      <span class="log-badge ${badgeClass}">${badgeText}</span>
      <span class="log-msg">${item.message}</span>
    `;

    stream.appendChild(entry);
    stream.scrollTop = stream.scrollHeight;
  }

  clearLogs() {
    const stream = document.getElementById('simulation-logs-stream');
    if (stream) stream.innerHTML = '';
  }

  updateControls() {
    const btnPlay = document.getElementById('btn-play-pause');
    const btnPrev = document.getElementById('btn-prev-step');
    const btnNext = document.getElementById('btn-next-step');

    if (btnPlay) {
      btnPlay.innerHTML = this.isPlaying
        ? `<i class="fas fa-pause"></i> Pause`
        : `<i class="fas fa-play"></i> Play`;
      btnPlay.classList.toggle('btn-cyan', this.isPlaying);
      btnPlay.classList.toggle('btn-primary', !this.isPlaying);
    }

    if (btnPrev) {
      btnPrev.disabled = this.currentStepIdx <= 0;
    }
    if (btnNext) {
      btnNext.disabled = !this.steps || this.currentStepIdx >= this.steps.length - 1;
    }
  }

  updateStatistics() {
    if (!this.simulationData) return;
    const stats = this.simulationData.statistics || {};

    const elIters = document.getElementById('stat-iterations');
    const elUpdates = document.getElementById('stat-updates');
    const elRouters = document.getElementById('stat-routers');
    const elEdges = document.getElementById('stat-edges');
    const elStatus = document.getElementById('stat-convergence');

    if (elIters) elIters.textContent = stats.iterations_to_converge !== undefined ? stats.iterations_to_converge : (stats.total_steps || '-');
    if (elUpdates) elUpdates.textContent = stats.total_route_updates !== undefined ? stats.total_route_updates : (stats.total_updates || '-');
    if (elRouters) elRouters.textContent = stats.num_routers || '-';
    if (elEdges) elEdges.textContent = stats.num_connections || '-';
    if (elStatus) elStatus.textContent = stats.convergence_status || 'Ready';
  }

  switchViewRouter(routerId) {
    this.viewRouter = routerId;
    if (this.algorithm === 'distance_vector' && this.steps.length > 0) {
      const step = this.steps[this.currentStepIdx];
      const tableData = (step.tables && step.tables[this.viewRouter]) ? step.tables[this.viewRouter] : [];
      this.renderRoutingTableRows(tableData);
      this.graph.highlightSourceNode(this.viewRouter);
    }
  }
}
