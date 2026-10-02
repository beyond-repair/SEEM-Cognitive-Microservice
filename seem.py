# seem.py
import argparse
import hashlib
import json
import os
import socket
import signal
import sys
import random
from datetime import datetime

import torch

from core.resonator import ResonatorVSA
from core.banel import BaNEL, Route
from core.dream import DreamPhase

# ========================= CONFIG =========================
CONFIG_PATH = "config.json"
DEFAULTS = {
    "api_key": "your-secure-vsa-key-123",
    "daemon_port": 5555,
    "dim": 256,
    "sparsity_k": 32,
    "iters": 5,
    "tau": 9.0,
    # Gate constant from the historical checklist. Not a measured recovery rate.
    "min_invert": 0.925,
    "plugin": "soc_check",
    "dream_probability": 0.2,
}


def load_config():
    path = os.environ.get("SEEM_CONFIG", CONFIG_PATH)
    cfg = dict(DEFAULTS)
    if os.path.isfile(path):
        with open(path) as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise SystemExit(f"{path} must be a JSON object")
        cfg.update({k: v for k, v in loaded.items() if v is not None})
    return cfg


CONFIG = load_config()
API_KEY = CONFIG.get("api_key", DEFAULTS["api_key"])
DAEMON_PORT = int(CONFIG.get("daemon_port", DEFAULTS["daemon_port"]))

_engine = None
_loaded_twin = None
active_twin = None


def twins_root():
    return os.environ.get("SEEM_TWINS_DIR", "twins")


def twin_dir(twin):
    safe = str(twin).replace("/", "_").replace("..", "_")
    return os.path.join(twins_root(), safe)


def active_path():
    return os.path.join(twins_root(), "active.json")


def read_active():
    path = active_path()
    if os.path.isfile(path):
        try:
            with open(path) as f:
                name = json.load(f).get("name")
            if isinstance(name, str) and name:
                return name
        except (json.JSONDecodeError, OSError):
            pass
    return "brian_new"


def write_active(name):
    os.makedirs(twins_root(), exist_ok=True)
    with open(active_path(), "w") as f:
        json.dump({"name": name}, f)


def get_engine():
    global _engine
    if _engine is None:
        dim = int(CONFIG.get("dim", DEFAULTS["dim"]))
        sparsity = int(CONFIG.get("sparsity_k", DEFAULTS["sparsity_k"]))
        iters = int(CONFIG.get("iters", DEFAULTS["iters"]))
        vsa = ResonatorVSA(dim=dim, sparsity_k=sparsity, iters=iters)
        banel = BaNEL(
            tau=float(CONFIG.get("tau", DEFAULTS["tau"])),
            min_invert=float(CONFIG.get("min_invert", DEFAULTS["min_invert"])),
        )
        dream_phase = DreamPhase(banel)
        _engine = (vsa, banel, dream_phase)
    return _engine


# ========================= PERSISTENCE =========================
def save_state(twin):
    _, banel, _ = get_engine()
    path = os.path.join(twin_dir(twin), "state.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {}
    if os.path.isfile(path):
        try:
            with open(path) as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            data = {}
    routes = {}
    for rid, r in banel.routes.items():
        hv = r.hv.detach().cpu()
        routes[rid] = {
            "hv": torch.stack([hv.real, hv.imag], dim=-1).tolist(),
            "fitness": float(r.fitness),
            "successes": int(r.successes),
            "dreams": int(r.dreams),
        }
    data["routes"] = routes
    with open(path, "w") as f:
        json.dump(data, f)


def load_state(twin):
    vsa, banel, _ = get_engine()
    path = os.path.join(twin_dir(twin), "state.json")
    if not os.path.isfile(path):
        return
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return
    for rid, rd in data.get("routes", {}).items():
        raw = torch.tensor(rd["hv"], dtype=torch.float32)
        hv = torch.complex(raw[..., 0], raw[..., 1]).to(vsa.device)
        route = Route(rid, hv, rd.get("fitness", 0.5))
        route.successes = rd.get("successes", 0)
        route.dreams = rd.get("dreams", 0)
        banel.register_route(route)


def ensure_twin_loaded(twin):
    global _loaded_twin, active_twin
    _, banel, _ = get_engine()
    if _loaded_twin != twin:
        banel.routes.clear()
        load_state(twin)
        _loaded_twin = twin
        active_twin = twin


# ========================= PLUGIN LOADER =========================
def load_plugin(plugin_name):
    try:
        mod = __import__(f"plugins.{plugin_name}", fromlist=["execute"])
        return mod.execute
    except (ImportError, AttributeError):
        return None


# ========================= MISSION EXECUTION =========================
def execute_mission(intent, twin, max_retries=2):
    if not isinstance(intent, str) or not intent.strip():
        return {
            "status": "ERROR",
            "fidelity": None,
            "effect": "intent must be a non-empty string",
            "twin": twin,
            "route_id": None,
        }

    vsa, banel, dream_phase = get_engine()
    ensure_twin_loaded(twin)

    for attempt in range(max_retries + 1):
        try:
            composite = vsa.random_hv()
            binder = vsa.random_hv()
            _recovered, invert_score = vsa.unbind(composite, binder, verbose=False)

            intent_hash = hashlib.sha256(intent.encode()).hexdigest()[:12]
            route_id = f"route_{twin}_{intent_hash}"

            if route_id not in banel.routes:
                route_hv = vsa.random_hv()
                banel.register_route(Route(route_id, route_hv))

            route = banel.routes[route_id]
            success = invert_score >= banel.min_invert
            banel.update(route_id, invert_score, success)

            if not success:
                child = banel.trigger_micro_dream(route_id, vsa, composite)
                if child:
                    print(f"[MICRO-DREAM] Repaired → {child.id} (fitness {child.fitness:.4f})")
                    route = child

            plugin_name = CONFIG.get("plugin", "soc_check")
            plugin = load_plugin(plugin_name)
            context = {
                "intent": intent,
                "twin": twin,
                "log_path": os.path.join(twin_dir(twin), "missions.log"),
            }
            result = plugin(invert_score, context) if plugin else "No plugin"

            dream_p = float(CONFIG.get("dream_probability", DEFAULTS["dream_probability"]))
            if random.random() < dream_p:
                dream_phase.consolidate()

            save_state(twin)

            return {
                "status": "SUCCESS" if success else "REPAIRED",
                "fidelity": invert_score,
                "effect": result,
                "twin": twin,
                "route_id": route.id,
            }

        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1}/{max_retries + 1} failed: {e}")
            if attempt == max_retries:
                return {
                    "status": "ERROR",
                    "fidelity": None,
                    "effect": f"mission failed: {type(e).__name__}: {e}",
                    "twin": twin,
                    "route_id": None,
                }


# ========================= DAEMON =========================
def start_daemon():
    def signal_handler(sig, frame):
        print(f"[SHUTDOWN] Saving state at {datetime.now()}")
        save_state(read_active())
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", DAEMON_PORT))
        server.listen()
        print(f"[DAEMON] SEEM 2.0 listening on 127.0.0.1:{DAEMON_PORT}", flush=True)

        while True:
            conn, _addr = server.accept()
            with conn:
                data = conn.recv(8192)
                if not data:
                    continue
                try:
                    req = json.loads(data.decode())
                    if req.get("auth_token") != API_KEY:
                        conn.sendall(json.dumps({"status": "UNAUTHORIZED"}).encode())
                        continue
                    twin = req.get("twin") or read_active()
                    intent = req.get("intent")
                    result = execute_mission(intent, twin)
                    conn.sendall(json.dumps(result).encode())
                except Exception as e:
                    conn.sendall(json.dumps({"status": "ERROR", "message": str(e)}).encode())


# ========================= CLI =========================
def cmd_init(name):
    path = twin_dir(name)
    os.makedirs(path, exist_ok=True)
    for fname in ("vault.json", "missions.log"):
        fpath = os.path.join(path, fname)
        if not os.path.exists(fpath):
            open(fpath, "w").close()
    state_path = os.path.join(path, "state.json")
    data = {"gates": {"alpha": False, "beta": False}, "vault": 0}
    if os.path.isfile(state_path):
        try:
            with open(state_path) as f:
                old = json.load(f)
            if isinstance(old, dict):
                old.setdefault("gates", data["gates"])
                old.setdefault("vault", 0)
                data = old
        except (json.JSONDecodeError, OSError):
            pass
    with open(state_path, "w") as f:
        json.dump(data, f)
    write_active(name)
    print(f"[INIT] Sovereign Identity created: {name}")


def cmd_switch(name):
    if os.path.isdir(twin_dir(name)):
        write_active(name)
        print(f"[SWITCH] Active Identity: {name}")
    else:
        print(f"[ERROR] Twin {name} not found")
        sys.exit(1)


def cmd_do(intent):
    twin = read_active()
    print(f"[DO] Processing intent: {intent}")
    result = execute_mission(intent, twin)
    print(json.dumps(result, indent=2))
    if result.get("status") == "ERROR":
        sys.exit(1)


def cmd_council(intent):
    from skills.hybrid_cortex import HybridCortex
    import asyncio

    vsa, _, _ = get_engine()
    result = asyncio.run(HybridCortex(vsa).execute(intent))
    print(json.dumps({
        "consensus": result["consensus"],
        "hv_checksum": result["hv_checksum"],
        "note": "Simulated council. No network call and no model weights.",
    }, indent=2))


def cmd_status():
    print(f"Active Twin: {read_active()}")
    print("Daemon Port:", DAEMON_PORT)
    print("API Key Set:", bool(API_KEY))
    print("Dim:", int(CONFIG.get("dim", DEFAULTS["dim"])))
    print("Plugin:", CONFIG.get("plugin", "soc_check"))
    print("min_invert gate constant (not a measured score):", CONFIG.get("min_invert"))


def build_parser():
    parser = argparse.ArgumentParser(description="SEEM Sovereign Agent (Claim-0 historical microservice)")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init").add_argument("name")
    subparsers.add_parser("switch").add_argument("name")
    subparsers.add_parser("do").add_argument("intent")
    subparsers.add_parser("council").add_argument("intent")
    subparsers.add_parser("status")
    subparsers.add_parser("daemon")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        cmd_init(args.name)
    elif args.command == "switch":
        cmd_switch(args.name)
    elif args.command == "do":
        cmd_do(args.intent)
    elif args.command == "council":
        cmd_council(args.intent)
    elif args.command == "status":
        cmd_status()
    elif args.command == "daemon":
        start_daemon()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
