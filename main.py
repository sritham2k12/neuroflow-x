from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import heapq
import random
import math
import time
from pydantic import BaseModel

app = FastAPI(title="NeuroFlow X API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# STADIUM GRAPH
# ─────────────────────────────────────────────
SECTIONS = ["A","B","C","D","E","F","G","H","R","Q","P","N","M","L","K","J"]

# Circular adjacency
EDGES = []
ring = SECTIONS
for i in range(len(ring)):
    EDGES.append((ring[i], ring[(i+1) % len(ring)]))

def build_graph():
    graph = {s: {} for s in SECTIONS}
    for a, b in EDGES:
        graph[a][b] = 1
        graph[b][a] = 1
    return graph

BASE_GRAPH = build_graph()

# ─────────────────────────────────────────────
# SIMULATION STATE
# ─────────────────────────────────────────────
state = {
    "crowd": {},
    "user": "C",
    "friends": {
        "Alex": {"section": "F", "avatar": "🧑"},
        "Priya": {"section": "N", "avatar": "👩"},
    },
    "vendors": {
        "V1": {"section": "B", "name": "Raj Snacks", "emoji": "🍕"},
        "V2": {"section": "K", "name": "Spice Cart", "emoji": "🌮"},
    },
    "active_order": None,
    "last_update": 0,
}

# Initialize crowd
for s in SECTIONS:
    state["crowd"][s] = random.choice(["low", "low", "medium", "high"])

def update_simulation():
    now = time.time()
    if now - state["last_update"] < 4:
        return
    state["last_update"] = now

    # Update crowd randomly
    for s in SECTIONS:
        roll = random.random()
        cur = state["crowd"][s]
        if cur == "low":
            state["crowd"][s] = "medium" if roll > 0.85 else "low"
        elif cur == "medium":
            if roll > 0.7: state["crowd"][s] = "high"
            elif roll < 0.3: state["crowd"][s] = "low"
        else:
            state["crowd"][s] = "medium" if roll > 0.6 else "high"

    # Move friends slightly
    for friend in state["friends"].values():
        if random.random() > 0.7:
            neighbors = list(BASE_GRAPH[friend["section"]].keys())
            friend["section"] = random.choice(neighbors)

    # Move active order vendor
    if state["active_order"]:
        order = state["active_order"]
        vendor_id = order["vendor_id"]
        target = order["target"]
        v_section = state["vendors"][vendor_id]["section"]
        path = dijkstra(v_section, target, use_crowd=False)
        if path and len(path) > 1:
            state["vendors"][vendor_id]["section"] = path[1]
            order["eta"] = max(0, order["eta"] - 1)
            if order["eta"] <= 0 or path[1] == target:
                state["active_order"]["status"] = "delivered"

# ─────────────────────────────────────────────
# DIJKSTRA
# ─────────────────────────────────────────────
CROWD_WEIGHTS = {"low": 1, "medium": 3, "high": 8}

def dijkstra(start: str, end: str, use_crowd=True):
    if start == end:
        return [start]
    dist = {s: float("inf") for s in SECTIONS}
    dist[start] = 0
    prev = {}
    pq = [(0, start)]
    while pq:
        cost, node = heapq.heappop(pq)
        if node == end:
            path = []
            while node in prev:
                path.append(node)
                node = prev[node]
            path.append(start)
            return path[::-1]
        if cost > dist[node]:
            continue
        for neighbor in BASE_GRAPH[node]:
            edge_cost = 1
            if use_crowd:
                edge_cost += CROWD_WEIGHTS.get(state["crowd"].get(neighbor, "low"), 1)
            new_cost = dist[node] + edge_cost
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(pq, (new_cost, neighbor))
    return []

def section_positions():
    """Circular positions for each section"""
    positions = {}
    n = len(SECTIONS)
    for i, sec in enumerate(SECTIONS):
        angle = (2 * math.pi * i / n) - math.pi / 2
        positions[sec] = {
            "x": round(50 + 38 * math.cos(angle), 2),
            "y": round(50 + 38 * math.sin(angle), 2),
        }
    return positions

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────
@app.get("/sync")
def sync():
    update_simulation()
    alerts = []
    high_sections = [s for s in SECTIONS if state["crowd"][s] == "high"]
    if high_sections:
        alerts.append(f"🚨 High crowd in Section{'s' if len(high_sections)>1 else ''}: {', '.join(high_sections)}")
    return {
        "crowd": state["crowd"],
        "user": state["user"],
        "friends": state["friends"],
        "vendors": state["vendors"],
        "active_order": state["active_order"],
        "positions": section_positions(),
        "alerts": alerts,
        "sections": SECTIONS,
    }

@app.get("/route")
def route(src: str, dst: str):
    update_simulation()
    path = dijkstra(src, dst)
    eta = max(1, len(path) * 2)
    return {
        "path": path,
        "eta": eta,
        "crowd_along": {s: state["crowd"][s] for s in path},
    }

@app.get("/meet")
def meet():
    update_simulation()
    locations = [state["user"]] + [f["section"] for f in state["friends"].values()]
    best_point = None
    best_total = float("inf")
    for candidate in SECTIONS:
        total = 0
        valid = True
        for loc in locations:
            path = dijkstra(loc, candidate)
            if not path:
                valid = False
                break
            total += len(path)
        if valid and total < best_total:
            best_total = total
            best_point = candidate

    routes = {}
    routes["You"] = dijkstra(state["user"], best_point)
    for name, f in state["friends"].items():
        routes[name] = dijkstra(f["section"], best_point)

    return {
        "meeting_point": best_point,
        "routes": routes,
        "eta": {name: len(r) * 2 for name, r in routes.items()},
    }

class OrderItem(BaseModel):
    item: str
    section: str

@app.post("/order")
def order(payload: OrderItem):
    update_simulation()
    # Find nearest vendor
    best_vendor = None
    best_dist = float("inf")
    for vid, vendor in state["vendors"].items():
        path = dijkstra(vendor["section"], payload.section, use_crowd=False)
        if path and len(path) < best_dist:
            best_dist = len(path)
            best_vendor = vid

    if not best_vendor:
        return JSONResponse({"error": "No vendors available"}, 400)

    eta = best_dist * 3
    state["active_order"] = {
        "item": payload.item,
        "target": payload.section,
        "vendor_id": best_vendor,
        "vendor_name": state["vendors"][best_vendor]["name"],
        "vendor_emoji": state["vendors"][best_vendor]["emoji"],
        "eta": eta,
        "status": "on_way",
    }
    return state["active_order"]

@app.post("/set-location")
def set_location(payload: dict):
    state["user"] = payload.get("section", state["user"])
    return {"user": state["user"]}
