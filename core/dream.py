import random
import torch.nn.functional as F
from .banel import Route

class DreamPhase:
    def __init__(self, banel):
        self.banel = banel

    def consolidate(self, min_successes=3, min_fitness=0.94):
        """Consolidate episodic successes into permanent semantic MemSkills."""
        candidates = [r for r in self.banel.routes.values() 
                      if r.successes >= min_successes and r.fitness >= min_fitness]
        if len(candidates) < 2:
            return None

        parents = random.sample(candidates, 2)
        alpha = random.uniform(0.4, 0.6)

        # Weighted phase averaging crossover + normalization
        c_hv = alpha * parents[0].hv + (1 - alpha) * parents[1].hv
        c_hv = F.normalize(c_hv, dim=0)

        cid = f"mem_{random.randint(1000, 9999)}"
        self.banel.register_route(Route(cid, c_hv, fitness=0.98))

        print(f"[DREAM] Consolidated: {cid}")
        return cid
