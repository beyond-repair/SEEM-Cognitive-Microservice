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

## Discover snapshot (Sweep-169)

- Default branch `main`. Public. Not archived. Open issues 0.
- No `.github/workflows`. No test suite. No release tags observed this pass.
- Runtime imports `torch` (`core/banel.py`, `seem.py`). `config.json` is gitignored; example only.
- Placeholder default API key string in `seem.py` is not a committed live credential. Daemon binds `localhost` only.
- Dynamic plugin import is historical and not a supported extension surface.

## Operator-only residual

Set GitHub `archived=true` when the operator accepts the archive queue. Do not delete the repository.
