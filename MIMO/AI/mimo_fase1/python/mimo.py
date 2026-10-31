"""
Sistemas MIMO - Trabalho 2026/2027 - Fase 1
Downlink MU-MIMO / massive MIMO com OFDM, canal Rayleigh plano por subcarrier,
CSI perfeita. Pre-codificacao ZF, BD (multiutilizador por SVD) e SVD cooperante
(limite superior).

Convencoes
  H      : (Nrt x Nt) canal de todos os utilizadores empilhados, CN(0,1) i.i.d.
  sizes  : lista com o n. de antenas de cada utilizador (soma = Nrt)
  ruido  : CN(0,1) por antena de receccao (sigma_n^2 = 1)
  SNR    : potencia por stream / ruido = P_T / (Ns * sigma_n^2)   (linear)
  u      : simbolos de potencia unitaria
  x      : x = W diag(sqrt(lam)) u,   sum_i lam_i ||w_i||^2 = P_T
  y      : y = H x + n ;   y_tilde = Gx y ;   u_hat = y_tilde / (e*sqrt(lam))
"""
import numpy as np

PC = np.array([bin(i).count("1") for i in range(16)])


def crandn(rng, *shape):
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2)


# ---------------------------------------------------------------- modulacao
_LV16 = np.array([-3, -1, 3, 1])          # codigo Gray 00,01,10,11 -> nivel
_CODE16 = np.array([0, 1, 3, 2])          # indice de nivel (-3,-1,+1,+3) -> codigo


def qam_mod(idx, k):
    """idx inteiros em [0, 2^k). k=2 QPSK, k=4 16-QAM (Gray, potencia media 1)."""
    if k == 2:
        b0 = (idx >> 1) & 1
        b1 = idx & 1
        return ((1 - 2 * b0) + 1j * (1 - 2 * b1)) / np.sqrt(2)
    if k == 4:
        return (_LV16[idx >> 2] + 1j * _LV16[idx & 3]) / np.sqrt(10)
    raise ValueError("k deve ser 2 ou 4")


def qam_demod(s, k):
    if k == 2:
        return ((s.real < 0).astype(int) << 1) | (s.imag < 0).astype(int)
    if k == 4:
        x = s.real * np.sqrt(10)
        y = s.imag * np.sqrt(10)
        li = (x > -2).astype(int) + (x > 0) + (x > 2)
        lq = (y > -2).astype(int) + (y > 0) + (y > 2)
        return (_CODE16[li] << 2) | _CODE16[lq]
    raise ValueError("k deve ser 2 ou 4")


# ------------------------------------------------------------- water-filling
def water_filling(g, P):
    """Maximiza sum log2(1+p_i g_i) com sum p_i = P (ruido unitario)."""
    g = np.asarray(g, float)
    n = g.size
    order = np.argsort(-g)
    with np.errstate(divide="ignore"):
        inv = 1.0 / g[order]
    cum = np.cumsum(inv)
    mu = (P + cum) / np.arange(1, n + 1)
    valid = mu > inv
    p = np.zeros(n)
    if not valid.any():
        return p
    kk = np.nonzero(valid)[0].max()
    with np.errstate(invalid="ignore"):
        p[order] = np.maximum(mu[kk] - inv, 0.0)
    return p


# ------------------------------------------------------------ pre-codificadores
def zf_precoder(H):
    Nrt, Nt = H.shape
    W = H.conj().T @ np.linalg.inv(H @ H.conj().T)
    return dict(name="zf", W=W, Gx=None, e=np.ones(Nrt), Ns=Nrt,
                normW2=float(np.sum(np.abs(W) ** 2)))


def bd_precoder(H, sizes, method="auto"):
    """Block Diagonalization: W_j = V0_j V1_j (espaco nulo dos outros users, depois SVD).
    method: 'svd'  -> espaco nulo por SVD de H~_j (versao classica, K SVDs de dimensao ~Nt)
            'fast' -> (so se Nrt==Nt) espaco nulo = colunas de inv(H) do user j
            'auto' -> 'fast' se Nrt==Nt, senao 'svd'."""
    Nrt, Nt = H.shape
    st = np.concatenate([[0], np.cumsum(sizes)])
    K = len(sizes)
    fast = (method == "fast") or (method == "auto" and Nrt == Nt)
    Hinv = np.linalg.inv(H) if fast else None
    Ws, es, Us, cols = [], [], [], []
    for j in range(K):
        a, b = st[j], st[j + 1]
        Hj = H[a:b]
        if fast:
            V0, _ = np.linalg.qr(Hinv[:, a:b])
        else:
            Ht = np.vstack([H[:a], H[b:]])
            rank = min(Ht.shape)
            _, _, Vh = np.linalg.svd(Ht, full_matrices=True)
            V0 = Vh[rank:].conj().T
        d0 = V0.shape[1]
        if d0 == 0:
            continue
        U, s, Vh2 = np.linalg.svd(Hj @ V0, full_matrices=False)
        Ws.append(V0 @ Vh2.conj().T)
        es.append(s)
        Us.append(U)
        cols.append((a, b))
    W = np.hstack(Ws)
    e = np.concatenate(es)
    Ns = e.size
    Gx = np.zeros((Ns, Nrt), complex)
    r = 0
    for U, (a, b) in zip(Us, cols):
        L = U.shape[1]
        Gx[r:r + L, a:b] = U.conj().T
        r += L
    return dict(name="bd", W=W, Gx=Gx, e=e, Ns=Ns)


def svd_precoder(H):
    """SVD do canal completo (receptores cooperantes): limite superior."""
    U, s, Vh = np.linalg.svd(H, full_matrices=False)
    return dict(name="svd", W=Vh.conj().T, Gx=U.conj().T, e=s, Ns=s.size)


def power_alloc(pre, snr, mode):
    """lambda_i para SNR por stream 'snr' (linear). P_T = Ns*snr."""
    Ns = pre["Ns"]
    P = Ns * snr
    if pre["name"] == "zf":
        return np.full(Ns, P / pre["normW2"])
    if mode == "eq":
        return np.full(Ns, P / Ns)
    if mode == "wf":
        return water_filling(pre["e"] ** 2, P)
    raise ValueError(mode)


def interference_residual(H, pre):
    """||Gx H W - diag(e)||_F / ||diag(e)||_F  (0 => sem interferencia entre streams)."""
    HW = H @ pre["W"]
    A = HW if pre["Gx"] is None else pre["Gx"] @ HW
    D = np.diag(pre["e"])
    return np.linalg.norm(A - D) / np.linalg.norm(D)


# -------------------------------------------------------------- cadeia de transmissao
def chain(H, pre, lam, u, n):
    """Cadeia completa explicita (matrizes cheias): x = W sqrt(lam) u ; y = Hx+n ; equalizacao."""
    x = pre["W"] @ (np.sqrt(lam)[:, None] * u)
    y = H @ x + n
    yt = y if pre["Gx"] is None else pre["Gx"] @ y
    with np.errstate(divide="ignore", invalid="ignore"):
        return yt / (pre["e"] * np.sqrt(lam))[:, None]


def stream_snr(pre, lam):
    return lam * pre["e"] ** 2


def mc_detect(rng, snr_i, k, T):
    """Monte Carlo equivalente a cadeia (valido com interferencia nula, ver tests):
       u_hat = u + n/sqrt(snr_i). Devolve erros de bit, n. bits, soma |erro|^2, n. simbolos
       apenas para streams activos (snr_i>0)."""
    act = snr_i > 0
    na = int(act.sum())
    if na == 0:
        return 0, 0, 0.0, 0
    s = snr_i[act]
    idx = rng.integers(0, 1 << k, size=(na, T))
    u = qam_mod(idx, k)
    uh = u + crandn(rng, na, T) / np.sqrt(s)[:, None]
    errs = int(PC[idx ^ qam_demod(uh, k)].sum())
    return errs, na * T * k, float(np.sum(np.abs(uh - u) ** 2)), na * T


# ---------------------------------------------------------------------- cenarios
SCENARIOS = {
    "1a": dict(Nt=16, sizes=[1] * 16),
    "1b": dict(Nt=16, sizes=[8] * 2),
    "2a": dict(Nt=512, sizes=[1] * 512),
    "2b": dict(Nt=512, sizes=[8] * 64),
}
SCHEMES = [("ZF", "zf", None), ("BD-eq", "bd", "eq"), ("BD-wf", "bd", "wf"),
           ("SVD-eq", "svd", "eq"), ("SVD-wf", "svd", "wf")]


def run_scenario(name, snr_db, D, T, seed=1, verbose=False):
    sc = SCENARIOS[name]
    Nt, sizes = sc["Nt"], sc["sizes"]
    Nrt = int(sum(sizes))
    rng = np.random.default_rng(seed)
    snr_db = np.asarray(snr_db, float)
    snr_lin = 10 ** (snr_db / 10)
    nS = len(snr_lin)
    labels = [s[0] for s in SCHEMES]
    out = dict(name=name, Nt=Nt, Nrt=Nrt, K=len(sizes), snr_db=snr_db, D=D, T=T,
               cap={l: np.zeros((D, nS)) for l in labels},
               act={l: np.zeros((D, nS)) for l in labels},
               errs={(l, k): np.zeros((D, nS)) for l in labels for k in (2, 4)},
               bits={(l, k): np.zeros((D, nS)) for l in labels for k in (2, 4)},
               evm={(l, k): np.zeros((D, nS)) for l in labels for k in (2, 4)},
               resid={l: np.zeros(D) for l in ("zf", "bd", "svd")})
    for d in range(D):
        H = crandn(rng, Nrt, Nt)
        pres = {"zf": zf_precoder(H), "bd": bd_precoder(H, sizes), "svd": svd_precoder(H)}
        for key, pre in pres.items():
            out["resid"][key][d] = interference_residual(H, pre)
        for (lab, key, mode) in SCHEMES:
            pre = pres[key]
            for i, snr in enumerate(snr_lin):
                lam = power_alloc(pre, snr, mode)
                si = stream_snr(pre, lam)
                out["cap"][lab][d, i] = np.sum(np.log2(1 + si))
                out["act"][lab][d, i] = np.mean(si > 0)
                for k in (2, 4):
                    er, nb, e2, ns = mc_detect(rng, si, k, T)
                    out["errs"][(lab, k)][d, i] = er
                    out["bits"][(lab, k)][d, i] = nb
                    out["evm"][(lab, k)][d, i] = np.sqrt(e2 / ns) if ns else np.nan
        if verbose and (d % 10 == 0):
            print(name, "draw", d, flush=True)
    return out
