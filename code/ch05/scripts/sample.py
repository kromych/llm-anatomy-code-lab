# sample.py LOGITS.npy TOKEN -- Algorithm T on a vector of logits (NumPy)
import sys
import numpy as np

def softmax(z):
    e = np.exp(z - z.max())
    return e / e.sum()

def penalize(z, recent, theta, presence=0.0, frequency=0.0):   # T1
    ids, count = np.unique(np.asarray(recent, dtype=np.intp),
                           return_counts=True)
    z = z.copy()
    z[ids] = np.where(z[ids] > 0, z[ids] / theta, z[ids] * theta)
    z[ids] -= presence + frequency * count
    return z

def top_k(z, k):                          # T2
    k = min(k, len(z))
    return z if k <= 0 else np.where(z >= np.sort(z)[-k], z, -np.inf)

def top_p(z, P):                          # T3
    p = softmax(z)
    order = np.argsort(-p)
    n = np.searchsorted(np.cumsum(p[order]), P) + 1
    kept = np.full_like(z, -np.inf)
    kept[order[:n]] = z[order[:n]]
    return kept

def min_p(z, m):                          # T4
    p = softmax(z)
    return np.where(p >= m * p.max(), z, -np.inf)

def temperature(z, T):                    # T5; T = 0 keeps the maximum
    return z / T if T > 0 else np.where(z == z.max(), z, -np.inf)

def draw(z, rng, n=None):                 # T6
    p = softmax(z)
    return rng.choice(len(p), size=n, p=p)

ORDER = {"llama.cpp":    (top_k, top_p, min_p, temperature),
         "vLLM":         (temperature, min_p, top_k, top_p),
         "Transformers": (temperature, top_k, top_p, min_p)}

def chain(z, order, par):                 # T2-T5 in an engine's order
    for step in order:
        z = step(z, par[step])
    return z

if __name__ == "__main__":
    z = np.load(sys.argv[1]).astype(np.float64)
    tok = int(sys.argv[2])
    par = {temperature: 0.8, top_k: 40, top_p: 0.95, min_p: 0.05}
    for engine, order in ORDER.items():
        y = chain(z, order, par)
        hits = (draw(y, np.random.default_rng(1), 10000) == tok).sum()
        print(f"{engine:12s} keeps {np.isfinite(y).sum()} tokens,"
              f" p({tok}) = {softmax(y)[tok]:.4f}; {hits} of 10000 draws")
    y = penalize(np.array([2.0, -1.0, 0.0]), [0, 1, 2], 1.3)
    print("penalty 1.3 on the logits 2, -1, 0:", np.round(y, 3).tolist())
    print("T = 0 draws", draw(temperature(z, 0), np.random.default_rng(1)))
