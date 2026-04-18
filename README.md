# NeuroFlow X — Smart Stadium Assistant
## Hackathon-Ready MVP

---

## 🚀 Quick Start (2 ways)

### Option 1: Frontend Only (Instant — no backend needed)
Just open the file in any browser:
```
frontend/index.html  →  double-click to open
```
Works with full simulation. All algorithms run in the browser (BFS, crowd sim, vendor logic).

---

### Option 2: Full Stack (Frontend + FastAPI Backend)

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend runs at: http://localhost:8000

API Docs: http://localhost:8000/docs

#### Frontend
Just open `frontend/index.html` in your browser.
The frontend auto-detects if the backend is available and falls back to local simulation if not.

---

## 📁 Project Structure

```
neuroflow-x/
├── backend/
│   ├── main.py              # FastAPI app + all logic
│   └── requirements.txt
└── frontend/
    └── index.html           # Complete single-file React-like app
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /sync | Live stadium state (crowd, users, friends, vendors) |
| GET | /route?src=A&dst=G | Dijkstra best path avoiding crowds |
| GET | /meet | Optimal meeting point for all users |
| POST | /order | Place food order, assign nearest vendor |
| POST | /set-location | Update user's location |

---

## 🧠 Algorithm Details

### Routing (Dijkstra)
- Nodes = Stadium sections (A–R, 16 total)
- Edge weights: base 1 + crowd penalty (low=1, medium=3, high=8)
- Avoids high-crowd sections automatically

### Meeting Point
- Tries every section as candidate
- Picks section that minimizes total BFS distance from all users
- Generates individual routes for each person

### Vendor Assignment
- Nearest vendor by unweighted BFS
- Vendor "moves" toward user each update tick

---

## 🎨 Features

| Feature | Description |
|---------|-------------|
| 🗺️ Stadium Map | SVG circular map with real-time crowd colors |
| 🧭 Smart Navigation | Crowd-aware Dijkstra routing with ETA |
| 👥 GroupSync | Friend tracking + optimal meeting point |
| 🍕 Food Ordering | Zomato-style ordering + vendor tracking |
| 🚨 Smart Alerts | Live notifications for high-crowd sections |
| 🔄 Live Simulation | Crowd + friends + vendor movement every 4s |

---

## 🏟️ Stadium Layout

```
Circular ring: A ↔ B ↔ C ↔ D ↔ E ↔ F ↔ G ↔ H ↔ R ↔ Q ↔ P ↔ N ↔ M ↔ L ↔ K ↔ J ↔ A
```

16 sections arranged in a circle. Each section connects to its neighbors.

---

## 💡 Demo Tips for Hackathon

1. Open `frontend/index.html` (no server needed)
2. **Map Tab**: Show real-time crowd heat map — green/yellow/red sections update every 4 seconds
3. **Navigate Tab**: Select Section A → Section N, show route avoids red sections
4. **GroupSync Tab**: Hit "Find Meeting Point" — shows optimal point + individual routes on map
5. **Order Tab**: Select Pizza → Place Order → Show vendor tracking on map
6. **Move Me Button**: Simulates user walking through stadium
