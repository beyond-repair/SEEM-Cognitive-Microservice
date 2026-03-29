

```markdown
# SEEM 2.0 – Sovereign Evolving Emergent Mind

**A local-first, offline neurosymbolic agent that truly evolves from your own interactions.**

SEEM 2.0 turns your usage history into a persistent, self-repairing digital twin using high-dimensional Vector Symbolic Architectures (VSA), Bayesian Negative Evidence Learning (BaNEL), and semantic memory consolidation (Dream Phase). No pre-training. No cloud. No data leaks.

Your failures become fuel. Your successes become permanent MemSkills.

## Key Features

- **Resonator VSA Kernel** — 16,384-dimensional complex hypervectors with iterative unbinding (invertibility ≥ 0.925)
- **BaNEL Learning** — Learns from failures via directional repulsion and Micro-Dream repair
- **Dream Phase** — Background consolidation of episodic memory into stable semantic MemSkills
- **Persistent Twins** — Sovereign identity isolation with deterministic SHA256 routing and state reload on switch
- **Dynamic Plugins** — Extend capabilities without restarting the daemon
- **Robust Deployment** — One-command bootstrap with systemd, raw TCP daemon, and Telegram bridge

## Quick Start

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

Then:

1. Edit `config.json` with your secure API key
2. Start the Telegram bot (in another terminal):
   ```bash
   python telegram_bot.py
   ```
3. Test the agent:
   ```bash
   scripts/ping_seem.sh
   ```

Create your first twin:
```bash
python seem.py init brian_new
```

Talk to it via Telegram or send intents directly.

## Architecture Overview

- **`core/resonator.py`** — High-dimensional VSA engine (FHRR phasors, binding/unbinding, sparsity projection)
- **`core/banel.py`** — Bayesian Negative Evidence Learning with Micro-Dream mutation on failure
- **`core/dream.py`** — Semantic consolidation and crossover of successful routes into MemSkills
- **`seem.py`** — Main daemon + CLI orchestrator with raw TCP socket and persistence
- **`plugins/`** — Executable grounding (soc_check, log_to_file, etc.)
- **`scripts/ping_seem.sh`** — Cron heartbeat with fidelity-based alerts (local + ntfy.sh)
- **`bootstrap.sh`** — Full environment setup, Torch check, systemd service generation

All state is persisted in `twins/<twin>/state.json` using safe tensor serialization (real/imag split). The agent survives reboots and maintains learned skills.

## Philosophy

SEEM is **sovereign**:
- 100% offline and air-gapped by default
- Your interaction history is the only training data
- No prompts leave your machine
- Failures are treated as valuable negative evidence

It is **adaptive**:
- Learns continuously through BaNEL + Dream Phase
- Repairs its own routes on failure
- Consolidates successful patterns into permanent MemSkills

It is **auditable**:
- Deterministic SHA256 route IDs
- Immutable L0 evidence base (planned expansion)
- Full state persistence with clean reload

## Current Status (v1.0.0)

**Live & Functional:**
- Full Resonator VSA + BaNEL + Dream Phase loop
- Persistent twin identities with state reload
- Raw TCP daemon with auth
- Dynamic plugin system
- Telegram bridge
- Hardened bootstrap + systemd deployment

**Roadmap (v1.1+):**
- Length-prefixed socket framing for larger payloads
- Route pruning and memory bounds
- Plugin sandboxing
- Full HDDL hierarchical planning + SMT verification

## License

This project is released under a custom sovereign license. See `LICENSE` for details. Commercial use and redistribution require explicit permission.

## Repository

[https://github.com/beyond-repair/SEEM-Cognitive-Microservice]

Built as a personal sovereign cognitive microservice. Use it, improve it, make it yours.

**Your history becomes its intelligence.**

— Atomic Dream Labs Team
```

