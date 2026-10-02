# SUPERSEDED — SEEM-Cognitive-Microservice

**Classification:** SUPERSEDED  
**Successor (new work only):** [sovereign-clean-room](https://github.com/beyond-repair/sovereign-clean-room)  
**Identity note:** This hyphenated repository is not the same Git object as `SEEM-Cognitive_Microservice`. Do not collapse identities. See `seem-identity-unifier`.  
**Re-audit:** Sweep-169 / 2026-10-01  
**Head reviewed:** `473ef52e46886c411a4570ec756ee86b5be8e222`  
**GitHub archived flag:** false (operator-only)

## What is preserved

Historical microservice packaging, bootstrap, HybridCortex sketch, TECHNICAL_VSA_FHRR prose, plugin and systemd scaffolding.

## What is not claimed

- No production readiness.
- No validated invertibility target (`min_invert=0.925` is a historical constant, not evidence).
- No experimental validation of FHRR, BaNEL, or Dream consolidation.
- Checklist marks in `CHECKLIST.md` are historical intent only.
- A later repair added `pytest` for install/run behavior. Those tests are not experimental validation.

## Discover snapshot (Sweep-169)

- Default branch `main`. Public. Not archived. Open issues 0.
- No `.github/workflows`. Behavior tests live under `tests/` and do not certify scientific claims. No release tags observed this pass.
- Runtime imports `torch` (`core/resonator.py`, `seem.py`). `config.json` is gitignored; example only. Default `dim` in the example is 256.
- Placeholder default API key string in `seem.py` is not a committed live credential. Daemon binds `localhost` only.
- Default plugin is `plugins/soc_check.py` (mission log). `plugins/log_to_file.py` remains optional and is not called unless `plugin` is set to `log_to_file`.

## Operator-only residual

Set GitHub `archived=true` when the operator accepts the archive queue. Do not delete the repository.
