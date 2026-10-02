import torch
import torch.nn.functional as F


class ResonatorVSA:
    def __init__(self, dim=16384, sparsity_k=256, iters=10, device=None):
        if dim < 4:
            raise ValueError("dim must be >= 4 so the codebook has at least one column")
        self.dim = int(dim)
        self.sparsity_k = max(1, min(int(sparsity_k), self.dim))
        self.iters = int(iters)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.codebook = self._generate_codebook()

    def _generate_codebook(self):
        cols = self.dim // 4
        cb = torch.randn(self.dim, cols, dtype=torch.complex64, device=self.device)
        return F.normalize(cb, dim=0)

    def random_hv(self):
        hv = torch.randn(self.dim, dtype=torch.complex64, device=self.device)
        return F.normalize(hv, dim=0)

    def bind(self, a, b):
        return a * b.conj()

    def unbind(self, composite, binder, verbose=False):
        x = composite.clone()
        for i in range(self.iters):
            x = x * binder.conj()
            mag = torch.abs(x)
            thresh = torch.topk(mag, self.sparsity_k).values[-1]
            x = x * (mag >= thresh).to(x.dtype)
            if i < self.iters - 1:
                proj = torch.matmul(x, self.codebook)
                x = torch.matmul(proj, self.codebook.T.conj())
            x = F.normalize(x, dim=0)

        recovered = self.bind(x, binder)
        invert_score = F.cosine_similarity(recovered.real, composite.real, dim=0).item()
        if verbose:
            print(f"Resonator invert: {invert_score:.4f}")
        return x, invert_score
