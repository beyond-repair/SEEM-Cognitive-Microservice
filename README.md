<div align="center">

[![Lifecycle](https://img.shields.io/badge/●_SUPERSEDED-f59e0b?style=for-the-badge&labelColor=0f0f23)](https://github.com/beyond-repair/ADL-Governance)
[![Claim](https://img.shields.io/badge/Claim_0-22c55e?style=for-the-badge&labelColor=0f0f23)](https://github.com/beyond-repair/ADL-Governance/blob/main/docs/CLAIM_VALIDATION.md)
[![Governance](https://img.shields.io/badge/ADL--Governance-7c3aed?style=for-the-badge&labelColor=0f0f23)](https://github.com/beyond-repair/ADL-Governance)

```
LIFECYCLE   SUPERSEDED
CLAIM       0
SUCCESSOR   sovereign-clean-room
```

</div>

> **SUPERSEDED.** Canonical successor for new VSA work: [sovereign-clean-room](https://github.com/beyond-repair/sovereign-clean-room). This repository is the historical cognitive-microservice line. It now runs as a Claim-0 sketch. It is not a validated FHRR system, not an AGI, and not production ready.

# SEEM 2.0 — Cognitive Microservice (historical, runnable sketch)

Offline CLI and localhost TCP daemon that:

1. Creates named twin directories.
2. Hashes an intent string into a route id.
3. Runs the historical complex Resonator VSA (`core/resonator.py`) on random hypervectors.
4. Updates a BaNEL route and, when the score is under the gate constant, stores a micro-dream child (`core/banel.py`).
5. Optionally mixes two high-fitness routes in `core/dream.py`.
6. Appends the score to that twin's `missions.log` via `plugins/soc_check.py`.
7. Persists route tensors in `twins/<name>/state.json`.

`python seem.py council` runs `skills/hybrid_cortex.py`, which returns simulated text only. It does not call a model API.

`min_invert` (default `0.925`) is a code gate, not a measured recovery rate. A `SUCCESS` status only means that one random unbind score met the constant. Do not treat `WHITE_PAPER.md`, `TECHNICAL_VSA_FHRR.md`, or `CHECKLIST.md` as evidence.

The runnable default dimension is **256** (`config.json.example`). The historical notes mention 16384; set `"dim": 16384` and `"sparsity_k": 256` yourself if you want that size. This sketch does not claim those settings recover symbols.

## Install

Python 3.10+.

```bash
git clone https://github.com/beyond-repair/SEEM-Cognitive-Microservice.git
cd SEEM-Cognitive-Microservice
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.json.example config.json
```

`config.json` is gitignored. The example `api_key` is a placeholder string, not a live credential. Edit it before exposing the daemon beyond your own machine. The daemon binds `127.0.0.1` only.

`requirements.txt` uses the PyTorch CPU index, so this does not download CUDA libraries. The sketch runs on CPU.

`bash bootstrap.sh` does the same venv, pip install, and example copy. It does not clone other repositories and it does not install systemd. `bash bootstrap.sh --dry-run` only prints the plan.

## Use

```bash
python seem.py init brian_new
python seem.py do "note a local route"
python seem.py status
python seem.py council "compare two notes"
```

`init` creates `twins/<name>/` and selects that twin. `switch <name>` selects an existing twin. `do` prints a JSON object with `status` (`SUCCESS`, `REPAIRED`, or `ERROR`), `fidelity` (a cosine score, or `null` on error), `effect`, `twin`, and `route_id`.

Daemon (separate terminal):

```bash
python seem.py daemon
```

Client:

```bash
python - << 'PY'
import json, socket
cfg = json.load(open("config.json"))
payload = {
    "auth_token": cfg["api_key"],
    "intent": "daemon note",
    "twin": "brian_new",
}
with socket.create_connection(("127.0.0.1", int(cfg["daemon_port"]))) as sock:
    sock.sendall(json.dumps(payload).encode())
    print(sock.recv(8192).decode())
PY
```

A wrong `auth_token` returns `{"status": "UNAUTHORIZED"}`.

`scripts/ping_seem.sh` is an optional `nc` heartbeat for a daemon you already started. It does not post to ntfy. `systemd/seem-agent.service` is a template with placeholder paths. Telegram (`telegram_bot.py`, `requirements-telegram.txt`) is optional and stays off unless you set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_USER_ID`.

## Test

```bash
pytest -q
```

Tests check shapes, persistence, the daemon auth boundary, and that the council text is marked simulated. They do not certify invertibility, holographic recovery, or Dream consolidation quality.

## Layout

| Path | Role |
| --- | --- |
| `seem.py` | CLI and localhost daemon |
| `core/resonator.py` | Complex bind / iterative unbind |
| `core/banel.py` | Route fitness and micro-dream |
| `core/dream.py` | Optional route mix; fitness `0.98` is an assigned label |
| `plugins/soc_check.py` | Writes `missions.log` |
| `skills/hybrid_cortex.py` | Simulated council |
| `config.json.example` | Defaults copied to `config.json` |

## What this line contributed

- Microservice packaging and bootstrap patterns
- HybridCortex distillation idea (still a simulation here)
- TECHNICAL_VSA_FHRR documentation (historical prose)
- Plugin / systemd scaffolding

Built by: Brian Ware (AtomicDreamlabs)

---

<div align="center">

**REWRITE · BUILD · TRANSCEND**

Governing source: [ADL-Governance](https://github.com/beyond-repair/ADL-Governance) · [Claim levels 0–5](https://github.com/beyond-repair/ADL-Governance/blob/main/docs/CLAIM_VALIDATION.md)

</div>
