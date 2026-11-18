# Routing Algorithm Simulator

An interactive, educational web application designed for Computer Networks students and educators to visualize, simulate, and analyze network routing algorithms.

Built with **Python (Flask)**, pure Python algorithm engines (without third-party graph blackboxes), and an interactive frontend powered by **Cytoscape.js** and modern dark-mode responsive design.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Technology Stack](#technology-stack)
3. [Project Architecture](#project-architecture)
4. [Installation & Setup](#installation--setup)
5. [Running the Application](#running-the-application)
6. [Module Explanations](#module-explanations)
7. [Algorithm Implementations & Theory](#algorithm-implementations--theory)
   - [Dijkstra's Algorithm (Link State)](#dijkstras-algorithm-link-state)
   - [Distributed Distance Vector Routing (Bellman-Ford)](#distributed-distance-vector-routing-bellman-ford)
   - [Count-to-Infinity Problem & Remedies](#count-to-infinity-problem--remedies)
8. [Sample Network Walkthrough & Verification](#sample-network-walkthrough--verification)
9. [Running Unit & Integration Tests](#running-unit--integration-tests)
10. [College Project Presentation Guide](#college-project-presentation-guide)
11. [Known Limitations](#known-limitations)

---

## 1. Key Features

- **Pure Python Graph & Algorithm Engine**: Dijkstra and Bellman-Ford algorithms are implemented from scratch using an adjacency list data structure with no dependencies on NetworkX.
- **Dynamic Topology Editor**:
  - Add, edit, connect, and delete routers and links.
  - Interactive edge weight modification.
  - Predefined topologies: Canonical 5-Router Sample (`A-E`), 6-Router Mesh, Line Topology, and Partitioned / Disconnected Networks.
  - Spanning-tree guaranteed random network generator.
- **Step-by-Step Simulation Player**:
  - Auto-play with adjustable speed slider (150ms – 1500ms).
  - Next step, previous step, run all steps, and reset controls.
  - Visual step narrative explaining edge relaxations, neighbor inspections, and settling of nodes.
- **Interactive Network Visualization (Cytoscape.js)**:
  - Circular dark-violet nodes with neon border glows.
  - Curved links displaying edge cost weights.
  - Color-coded visual states: Source (Blue), Settled/Visited (Green), Examining (Amber), Shortest Path Tree (Cyan), Severed (Dashed Red).
  - Click any router on the canvas to set it as source or view its routing table.
- **Dynamic Routing Table**:
  - Live table displaying: **Router**, **Destination**, **Next Hop**, **Total Cost**, and **Complete Path**.
  - Animated row highlights when a routing entry changes.
  - Click any row in the routing table to highlight that exact shortest path on the canvas.
  - One-click **Export to CSV**.
- **Real-Time Simulation Log Stream**:
  - Educational log messages with color-coded category badges (`[INIT]`, `[RELAX]`, `[CHECK]`, `[EXCHANGE]`, `[UPDATE]`, `[DONE]`).
- **Dedicated Count-to-Infinity Lab**:
  - Real-time simulation of link cuts (`C <---> DEST`).
  - Demonstrates mutual stale routing advertisement loops.
  - Interactive loop detector displaying active cycle chains (e.g. `A -> B -> A`).
  - Side-by-side comparison of **Standard Distance Vector**, **Split Horizon**, and **Poison Reverse**.
  - Configurable infinity metric threshold (e.g. 16 as in RIP).
- **Educational Guide**:
  - Built-in comprehensive reference with theory, formulas, and a side-by-side comparison table between Link-State and Distance-Vector.

---

## 2. Technology Stack

- **Backend**: Python 3.9+ with Flask 3.x and Flask-CORS
- **Frontend**: HTML5, CSS3, JavaScript (ES6+ Classes)
- **Graph Visualization**: Cytoscape.js 3.30+ (offline bundled with CDN fallback)
- **Data Structures**: Pure Python dictionary-based Adjacency List
- **Testing**: Python `unittest` framework

---

## 3. Project Architecture

```
project/
├── app.py                     # Flask application, REST API routes, and CSV export
├── requirements.txt           # Python dependencies (Flask, flask-cors)
├── README.md                  # Complete documentation and presentation guide
│
├── algorithms/                # Pure Python routing algorithm implementations
│   ├── __init__.py
│   ├── dijkstra.py            # Dijkstra shortest path with step-by-step trace & SPT builder
│   └── bellman_ford.py        # Distributed Distance Vector with neighbor exchanges
│
├── network/                   # Topology representation and validation
│   ├── __init__.py
│   └── topology.py            # Adjacency list, presets, and random graph generator
│
├── simulation/                # Specialized networking event simulations
│   ├── __init__.py
│   ├── count_to_infinity.py   # Count-to-Infinity engine (Standard, Split Horizon, Poison Reverse)
│   └── link_failure.py        # Link cut and recovery management
│
├── tests/                     # Comprehensive automated unit & integration test suite
│   ├── __init__.py
│   ├── test_dijkstra.py       # Dijkstra tests on sample and edge-case graphs
│   ├── test_bellman_ford.py   # Distance Vector convergence and parity tests
│   ├── test_count_to_infinity.py # Loop detection and split horizon verification
│   ├── test_api.py            # Flask REST API endpoint tests
│   └── test_e2e_integration.py# Full end-to-end integration tests
│
├── static/
│   ├── css/
│   │   └── style.css          # Modern dark navy/charcoal styling with cyan/purple accents
│   ├── js/
│   │   ├── network_graph.js   # Cytoscape.js visualization wrapper and styling
│   │   ├── simulator.js       # Playback controller, step animator, and routing table renderer
│   │   ├── count_infinity.js  # Dedicated Count-to-Infinity lab controller and loop tracer
│   │   └── app.js             # UI coordinator, modal manager, and API client
│   └── vendor/
│       └── cytoscape.min.js   # Local bundled Cytoscape.js for 100% offline usage
│
└── templates/
    └── index.html             # Single-page application dashboard layout
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.9 or higher
- `pip` (Python package installer)

### Step 1: Clone or Navigate to Project Directory
```powershell
cd "c:\Users\rkgul\Documents\ppt clg 3rd\CN\project"
```

### Step 2: (Optional but Recommended) Create a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 5. Running the Application

### Start the Flask Server:
```powershell
python app.py
```

Output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Open in Your Browser:
Visit **`http://127.0.0.1:5000`** in any modern web browser (Chrome, Edge, Firefox, Safari).

---

## 6. Module Explanations

### `network/topology.py`
Maintains the network graph using an adjacency list: `Dict[str, Dict[str, float]]`.
- **Validation**: Rejects self-loops, duplicate routers, empty labels, and non-positive weights ($\le 0$).
- **Presets**: Provides instant one-click loading of the canonical 5-router sample (`A-E`), 6-router ring mesh, partitioned networks, and line topologies.
- **Random Network Generator**: Employs a randomized spanning tree to guarantee connectivity, then adds random cross-links based on a configurable density metric.

### `algorithms/dijkstra.py`
Pure Python implementation of Dijkstra's Shortest Path Algorithm for Link-State routing:
- Validates that all edge costs are non-negative.
- Produces a detailed chronological trace of every event: initialization, extracting the minimum-cost node from the unvisited set, relaxing candidate edges, and settling nodes.
- Reconstructs complete paths and extracts the immediate `next_hop`.
- Handles disconnected/unreachable partitions gracefully by outputting `cost: ∞` and `path: Unreachable`.

### `algorithms/bellman_ford.py`
True distributed Distance Vector simulation:
- Does **not** run a centralized Bellman-Ford shortcut. Instead, it accurately models asynchronous or synchronous rounds of router-to-router vector exchanges.
- Each router $x$ maintains its own local table and neighbor vectors $D_v$.
- In each round, routers exchange vectors with direct neighbors and apply:
  $$D_x(y) = \min_{v \in N(x)} [c(x, v) + D_v(y)]$$
- Automatically tracks each sent message, identifies route updates, detects convergence when no table changes occur, and reconstructs the packet forwarding path across the network.

### `simulation/count_to_infinity.py`
Simulates the classic Distance Vector routing loop anomaly:
- Takes a topology (defaulting to `A --(1)-- B --(1)-- C --(1)-- DEST`) and severs the link to `DEST`.
- Tracks the mutual stale advertisement cycle between `A` and `B`.
- Features an active cycle detector that detects loops such as `A -> B -> A`.
- Implements:
  1. **Standard Mode**: Loop increments metric until `infinity_threshold` (e.g. 16) is reached.
  2. **Split Horizon**: Suppresses route advertisement out the interface from which the route was learned.
  3. **Poison Reverse**: Advertises the route back to the source router with metric set to $\infty$.

---

## 7. Algorithm Implementations & Theory

### Dijkstra's Algorithm (Link State)
- **Protocol**: OSPF (Open Shortest Path First), IS-IS.
- **Concept**: Every router floods Link State Advertisements (LSAs) so that every node has an identical, complete map of the network (Link State Database).
- **Execution**: Each node runs Dijkstra independently with itself as the root to build a Shortest Path Tree (SPT).

### Distributed Distance Vector Routing (Bellman-Ford)
- **Protocol**: RIP (Routing Information Protocol - RFC 1058), Cisco IGRP/EIGRP.
- **Concept**: "Routing by rumor" — routers know only their directly connected links and learn about distant networks exclusively from neighbor distance vector advertisements.
- **Equation**:
  $$D_x(y) = \min_{v \in \text{Neighbors}(x)} \left[ c(x, v) + D_v(y) \right]$$

### Count-to-Infinity Problem & Remedies
When router `C` loses its direct link to `DEST`, it sets $D_C(\text{DEST}) = \infty$. However, neighbor `B` had previously advertised $D_B(\text{DEST}) = 2$ via `C`. Router `A` had advertised $D_A(\text{DEST}) = 2$ to `B`. Router `B` falsely assumes `A` has an alternate path to `DEST` with cost $1 + 2 = 3$ and updates its next hop to `A`! `A` then recomputes its cost via `B` as $1 + 3 = 4$. Packets bounce endlessly between `A` and `B` while the cost climbs until the infinity threshold is reached.

**Remedies in the Simulator:**
- **Split Horizon**: Router `A` will never advertise a route for `DEST` to `B` because `A` learned that route through `B`.
- **Poison Reverse**: Router `A` advertises `DEST` to `B` with metric $\infty$ (16).

---

## 8. Sample Network Walkthrough & Verification

The application comes pre-loaded with the standard college sample network:

### Topology:
- **Routers**: `A`, `B`, `C`, `D`, `E`
- **Connections & Costs**:
  - `A - B`: 4
  - `A - C`: 2
  - `B - C`: 1
  - `B - D`: 5
  - `C - D`: 8
  - `C - E`: 10
  - `D - E`: 2

### Shortest Paths from Source Router `A`:
| Destination | Total Cost | Next Hop | Complete Shortest Path | Calculation Notes |
|:-----------:|:----------:|:--------:|:----------------------:|:------------------|
| **A** | **0** | `-` | `A` | Source router (local) |
| **B** | **3** | **C** | `A -> C -> B` | Via C: $2 + 1 = 3$ (better than direct $A-B = 4$) |
| **C** | **2** | **C** | `A -> C` | Direct link: cost 2 |
| **D** | **8** | **C** | `A -> C -> B -> D` | Via B: $2 + 1 + 5 = 8$ (better than $A-C-D = 2 + 8 = 10$) |
| **E** | **10** | **C** | `A -> C -> B -> D -> E`| Via D: $8 + 2 = 10$ (better than $A-C-E = 2 + 10 = 12$) |

*Both Dijkstra and Distributed Distance Vector converge to these exact values in the simulator.*

---

## 9. Running Unit & Integration Tests

The project includes 23 automated tests covering Dijkstra, Distance Vector convergence, parity between algorithms, Count-to-Infinity loop detection, Split Horizon, Poison Reverse, REST API endpoints, and end-to-end integration.

Run all tests:
```powershell
python -m unittest discover -s tests
```

Output:
```
.......................
----------------------------------------------------------------------
Ran 23 tests in 0.048s

OK
```

---

## 10. College Project Presentation Guide

When presenting this project to your professor or viva examiner, use this structured walkthrough:

1. **Introduction**:
   - State the project title: **Routing Algorithm Simulator**.
   - Explain the core motivation: Visualizing the fundamental divergence between **Link-State (Dijkstra)** and **Distance-Vector (Bellman-Ford)** routing.
2. **Demonstrate Dijkstra (Link State)**:
   - Select Source Router `A` on the sample network.
   - Click **Start Simulation**, then step through with **Next Step** or **Play**.
   - Point out how node `C` is visited first (cost 2), which then relaxes node `B`'s cost from 4 down to 3 ($A \to C \to B$).
   - Show the resulting **Routing Table** and click on row `E` to highlight the full shortest path `A -> C -> B -> D -> E` on the graph.
3. **Demonstrate Distance Vector**:
   - Switch to **Bellman-Ford** and click **Start Simulation**.
   - Explain that each iteration represents a round of **Distance Vector Exchanges** between directly connected neighbors.
   - Show how tables update iteratively over rounds until convergence is achieved.
4. **Demonstrate Count-to-Infinity Lab**:
   - Switch to the **Count-to-Infinity Lab** tab.
   - Run **Standard Distance Vector**: Observe the **Routing Loop Alert** (`A -> B -> A`) and watch the cost climb iteration by iteration up to the threshold of 16.
   - Switch mode to **Split Horizon** or **Poison Reverse** and re-run: show how the loop is immediately avoided and converges in just 2-3 iterations!
5. **Educational Guide & CSV Export**:
   - Highlight the built-in theory guide and download the routing table via **Export CSV**.

---

## 11. Known Limitations

- **Symmetric Costs**: Links are modeled as undirected edges (cost $c(u, v) = c(v, u)$), which is typical for LAN and enterprise topologies. Directed asymmetric link costs are supported by the underlying adjacency list but simplified for UI ergonomics.
- **Negative Weights**: By design, negative edge weights are disallowed because link metrics in real computer networks (bandwidth, delay, MTU, hop count) are strictly positive ($> 0$).
- **Maximum Graph Size for Smooth Animation**: The interactive Cytoscape canvas is optimized for 2 to 25 routers, which is ideal for classroom demonstrations and lab assignments.
# routing-table-stimulator
