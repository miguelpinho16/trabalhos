import sys, time, csv
sys.path.insert(0, "/home/claude/mimo_sm/python")
import numpy as np
from mimo import *

def tmin(f, n=3):
    best = 1e9
    for _ in range(n):
        t = time.perf_counter(); f(); best = min(best, time.perf_counter() - t)
    return best

rng = np.random.default_rng(5)
rows = []
for name in ("1a", "1b", "2a", "2b"):
    sc = SCENARIOS[name]; Nt, sizes = sc["Nt"], sc["sizes"]; Nrt = sum(sizes); K = len(sizes); Nr = sizes[0]
    H = crandn(rng, Nrt, Nt)
    t_zf = tmin(lambda: zf_precoder(H))
    t_bdf = tmin(lambda: bd_precoder(H, sizes, "fast"))
    t_svd = tmin(lambda: svd_precoder(H))
    if K <= 16:
        t_bdc = tmin(lambda: bd_precoder(H, sizes, "svd")); nota = "medido (todos os users)"
    else:
        a, b = 0, sizes[0]
        def one():
            Ht = H[b:]; _, _, Vh = np.linalg.svd(Ht, full_matrices=True)
            V0 = Vh[min(Ht.shape):].conj().T
            np.linalg.svd(H[a:b] @ V0, full_matrices=False)
        t_bdc = K * tmin(one, 2); nota = f"1 user medido x K={K} (extrapolado)"
    # operacoes (MACs complexas) por subcarrier
    mac_zf = Nrt**2 * Nt + Nrt**3 + Nt * Nrt**2
    mac_bdf = Nt**3 + K * (2 * Nt * Nr**2) + K * Nr**3 + K * Nr * Nt * Nr
    rows.append(dict(cenario=name, Nt=Nt, K=K, Nr_por_user=Nr,
                     t_ZF_ms=1e3 * t_zf, t_BD_rapido_ms=1e3 * t_bdf, t_BD_classico_ms=1e3 * t_bdc,
                     t_SVD_coop_ms=1e3 * t_svd, MAC_ZF=mac_zf, MAC_BD_rapido=mac_bdf, nota_BD_classico=nota))
    print(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
with open("/home/claude/mimo_sm/results/tabela_complexidade.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
