/**
 * Cytoscape.js Network Graph Visualization Manager
 */

class NetworkGraph {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.cy = null;
    this.options = options;
    this.onNodeSelected = options.onNodeSelected || null;
    this.onEdgeSelected = options.onEdgeSelected || null;
    this.initCytoscape();
  }

  initCytoscape() {
    if (!window.cytoscape) {
      console.error("Cytoscape.js library is not loaded.");
      return;
    }

    this.cy = window.cytoscape({
      container: this.container,
      boxSelectionEnabled: false,
      autounselectify: false,
      wheelSensitivity: 0.25,
      style: [
        // Base Node Style
        {
          selector: 'node',
          style: {
            'label': 'data(id)',
            'color': '#ffffff',
            'font-family': 'Consolas, Segoe UI, sans-serif',
            'font-size': '15px',
            'font-weight': 'bold',
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': '#1e293b',
            'background-blacken': 0,
            'border-width': 3,
            'border-color': '#6366f1',
            'border-opacity': 0.9,
            'width': 50,
            'height': 50,
            'transition-property': 'background-color, border-color, border-width, width, height, box-shadow',
            'transition-duration': '0.25s'
          }
        },
        // Source Node Style
        {
          selector: 'node.source-node',
          style: {
            'background-color': '#1d4ed8',
            'border-color': '#38bdf8',
            'border-width': 4,
            'width': 56,
            'height': 56
          }
        },
        // Settled / Visited Node Style
        {
          selector: 'node.visited-node',
          style: {
            'background-color': '#065f46',
            'border-color': '#10b981',
            'border-width': 3.5
          }
        },
        // Currently Active / Examining Node Style
        {
          selector: 'node.active-node',
          style: {
            'background-color': '#b45309',
            'border-color': '#f59e0b',
            'border-width': 4,
            'width': 58,
            'height': 58
          }
        },
        // Neighbor Node Style
        {
          selector: 'node.neighbor-node',
          style: {
            'background-color': '#4338ca',
            'border-color': '#818cf8',
            'border-width': 3.5
          }
        },
        // Destination Node in C2I
        {
          selector: 'node.dest-node',
          style: {
            'background-color': '#831843',
            'border-color': '#f43f5e',
            'border-width': 4
          }
        },
        // Base Edge Style
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
            'text-border-color': '#334155',
            'text-border-width': 1,
            'text-border-opacity': 0.8,
            'width': 3,
            'line-color': '#334155',
            'curve-style': 'bezier',
            'transition-property': 'line-color, width, text-background-color',
            'transition-duration': '0.2s'
          }
        },
        // Examining Edge Style
        {
          selector: 'edge.examining-edge',
          style: {
            'line-color': '#f59e0b',
            'width': 4.5
          }
        },
        // Relaxed Edge Style
        {
          selector: 'edge.relaxed-edge',
          style: {
            'line-color': '#10b981',
            'width': 5
          }
        },
        // Tree / Shortest Path Edge Style
        {
          selector: 'edge.tree-edge',
          style: {
            'line-color': '#38bdf8',
            'width': 5.5,
            'z-index': 10
          }
        },
        // Severed / Failed Link Style
        {
          selector: 'edge.severed-edge',
          style: {
            'line-color': '#f43f5e',
            'line-style': 'dashed',
            'width': 3.5,
            'label': 'SEVERED (∞)',
            'color': '#fda4af',
            'text-background-color': '#4c0519'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 50
      }
    });

    // Node click event
    this.cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      if (this.onNodeSelected) {
        this.onNodeSelected(nodeId);
      }
    });

    // Edge click event
    this.cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const data = edge.data();
      if (this.onEdgeSelected) {
        this.onEdgeSelected(data.source, data.target, data.weight);
      }
    });
  }

  renderTopology(topologyData) {
    if (!this.cy) return;

    this.cy.elements().remove();
    const elements = [];

    // Add nodes
    (topologyData.nodes || []).forEach(node => {
      const id = typeof node === 'object' ? node.id : String(node);
      elements.push({
        group: 'nodes',
        data: { id: id, label: id }
      });
    });

    // Add undirected edges
    (topologyData.edges || []).forEach(edge => {
      const edgeId = `${edge.source}-${edge.target}`;
      elements.push({
        group: 'edges',
        data: {
          id: edgeId,
          source: edge.source,
          target: edge.target,
          weight: edge.weight
        }
      });
    });

    this.cy.add(elements);
    this.applySmartLayout(elements.length);
  }

  applySmartLayout(elementCount) {
    if (!this.cy) return;

    // Use circular or concentric for clean networking aesthetics
    const nodes = this.cy.nodes();
    if (nodes.length <= 7) {
      this.cy.layout({
        name: 'circle',
        padding: 60,
        animate: true,
        animationDuration: 350
      }).run();
    } else {
      this.cy.layout({
        name: 'cose',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 40,
        randomize: false,
        animate: true,
        animationDuration: 400
      }).run();
    }
  }

  fitGraph() {
    if (this.cy) {
      this.cy.fit(null, 40);
    }
  }

  clearHighlights() {
    if (!this.cy) return;
    this.cy.nodes().removeClass('source-node visited-node active-node neighbor-node dest-node');
    this.cy.edges().removeClass('examining-edge relaxed-edge tree-edge');
  }

  highlightSourceNode(sourceId) {
    if (!this.cy) return;
    this.clearHighlights();
    const node = this.cy.getElementById(sourceId);
    if (node) {
      node.addClass('source-node');
    }
  }

  applyStepHighlights(stepData) {
    if (!this.cy || !stepData) return;
    this.clearHighlights();

    // Highlight visited nodes
    if (stepData.visited && Array.isArray(stepData.visited)) {
      stepData.visited.forEach(nodeId => {
        const n = this.cy.getElementById(nodeId);
        if (n) n.addClass('visited-node');
      });
    }

    // Highlight current active node
    if (stepData.current_node) {
      const curr = this.cy.getElementById(stepData.current_node);
      if (curr) curr.addClass('active-node');
    }

    // Highlight neighbor node
    if (stepData.neighbor) {
      const nbr = this.cy.getElementById(stepData.neighbor);
      if (nbr) nbr.addClass('neighbor-node');
    }

    // Highlight shortest path tree edges
    if (stepData.tree_edges && Array.isArray(stepData.tree_edges)) {
      stepData.tree_edges.forEach(e => {
        const edge1 = this.cy.getElementById(`${e.source}-${e.target}`);
        const edge2 = this.cy.getElementById(`${e.target}-${e.source}`);
        if (edge1.length) edge1.addClass('tree-edge');
        if (edge2.length) edge2.addClass('tree-edge');
      });
    }

    // Highlight active step edge
    if (stepData.highlight_edges && Array.isArray(stepData.highlight_edges)) {
      stepData.highlight_edges.forEach(e => {
        const edge1 = this.cy.getElementById(`${e.source}-${e.target}`);
        const edge2 = this.cy.getElementById(`${e.target}-${e.source}`);
        const targetEdge = edge1.length ? edge1 : edge2;
        if (targetEdge.length) {
          if (e.status === 'relaxed') {
            targetEdge.addClass('relaxed-edge');
          } else {
            targetEdge.addClass('examining-edge');
          }
        }
      });
    }
  }

  highlightPath(pathNodes) {
    if (!this.cy || !pathNodes || pathNodes.length < 2) return;
    this.clearHighlights();

    for (let i = 0; i < pathNodes.length; i++) {
      const n = this.cy.getElementById(pathNodes[i]);
      if (n) {
        if (i === 0) n.addClass('source-node');
        else if (i === pathNodes.length - 1) n.addClass('active-node');
        else n.addClass('visited-node');
      }

      if (i < pathNodes.length - 1) {
        const u = pathNodes[i];
        const v = pathNodes[i + 1];
        const edge1 = this.cy.getElementById(`${u}-${v}`);
        const edge2 = this.cy.getElementById(`${v}-${u}`);
        if (edge1.length) edge1.addClass('tree-edge');
        if (edge2.length) edge2.addClass('tree-edge');
      }
    }
  }

  markSeveredEdge(u, v) {
    if (!this.cy) return;
    const edge1 = this.cy.getElementById(`${u}-${v}`);
    const edge2 = this.cy.getElementById(`${v}-${u}`);
    if (edge1.length) edge1.addClass('severed-edge');
    if (edge2.length) edge2.addClass('severed-edge');
  }
}
