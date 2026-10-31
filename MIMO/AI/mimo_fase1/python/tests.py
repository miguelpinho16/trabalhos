import sys, numpy as np
from scipy.special import erfc
sys.path.insert(0, "/home/claude/mimo_sm/python")
from mimo import *

ok_all = True
def check(name, cond, info=""):
    global ok_all
    ok_all &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("  " + info if info else ""))

rng = np.random.default_rng(7)

# 1. modulacao
for k in (2, 4):
    idx = np.arange(1 << k)
    s = qam_mod(idx, k)
    check(f"QAM k={k} ida-e-volta", np.array_equal(qam_demod(s, k), idx))
    check(f"QAM k={k} potencia media 1", abs(np.mean(np.abs(s) ** 2) - 1) < 1e-12)
# Gray: vizinhos a distancia minima diferem num bit
s16 = qam_mod(np.arange(16), 4)
dmin = np.min(np.abs(s16[:, None] - s16[None, :]) + 9 * np.eye(16))
gray_ok = all(PC[i ^ j] == 1 for i in range(16) for j in range(16)
              if i != j and abs(s16[i] - s16[j]) < dmin * 1.01)
check("16-QAM Gray (vizinhos diferem 1 bit)", gray_ok)

# 2. BER MC vs teoria em AWGN (Es/N0 = snr)
def ber_qpsk(snr): return 0.5 * erfc(np.sqrt(snr / 2))
def ber_16(snr):
    x = np.sqrt(snr / 10)
    return (3 / 8) * erfc(x) + (1 / 4) * erfc(3 * x) - (1 / 8) * erfc(5 * x)
for k, f, snrs_db in ((2, ber_qpsk, (4, 8, 10)), (4, ber_16, (10, 14, 16))):
    for sdb in snrs_db:
        snr = 10 ** (sdb / 10)
        er, nb, e2, ns = mc_detect(rng, np.full(200, snr), k, 2000)
        mc, th = er / nb, f(snr)
        check(f"BER k={k} SNR={sdb} dB", abs(mc - th) < 4 * np.sqrt(th / nb) + 1e-9,
              f"MC={mc:.3e} teoria={th:.3e}")
        check(f"EVM k={k} SNR={sdb} dB", abs(np.sqrt(e2 / ns) - snr ** -0.5) < 0.01 * snr ** -0.5 * 3,
              f"EVM={np.sqrt(e2/ns):.4f} 1/sqrt(snr)={snr**-0.5:.4f}")

# 3. water-filling: exemplo das notas (Precoding com SVD, p.4-5): lambda^2=52,13,4, P_T=2, sigma^2=1
p = water_filling(np.array([52., 13., 4.]), 2.0)
p_dB = 10 * np.log10(p)
check("water-filling exemplo das notas (-1.17,-1.52,-2.74 dB)",
      np.allclose(p_dB, [-1.17, -1.52, -2.74], atol=0.01) and abs(p.sum() - 2) < 1e-12,
      f"{np.round(p_dB,2)}")
p = water_filling(np.array([10., 1., 0.01]), 1.0)
check("water-filling desliga canal fraco", p[2] == 0 and abs(p.sum() - 1) < 1e-12, f"{np.round(p,3)}")
# optimalidade: nenhuma perturbacao melhora a capacidade
g = rng.random(8) * 5; P = 3.0; pw = water_filling(g, P)
cw = np.sum(np.log2(1 + pw * g)); best = True
for _ in range(2000):
    q = rng.random(8); q = q / q.sum() * P
    best &= np.sum(np.log2(1 + q * g)) <= cw + 1e-12
check("water-filling optimo (2000 alocacoes aleatorias)", best)

# 4-7. pre-codificadores nos 4 cenarios (dimensao reduzida para 2x e tamanho real para 1x)
for name, Nt, sizes in (("1a", 16, [1] * 16), ("1b", 16, [8, 8]), ("2a*", 64, [1] * 64), ("2b*", 64, [8] * 8)):
    H = crandn(rng, sum(sizes), Nt)
    zf, bd, sv = zf_precoder(H), bd_precoder(H, sizes), svd_precoder(H)
    check(f"[{name}] ZF: H W = I", np.linalg.norm(H @ zf["W"] - np.eye(sum(sizes))) < 1e-8)
    for pre in (zf, bd, sv):
        r = interference_residual(H, pre)
        check(f"[{name}] {pre['name'].upper()}: interferencia zero", r < 1e-8, f"residuo={r:.1e}")
    # BD: blocos fora da diagonal de H W exactamente nulos
    HW = H @ bd["W"]; st = np.concatenate([[0], np.cumsum(sizes)])
    cols = np.cumsum([0] + [s for s in sizes])  # cada user tem Nr_j streams (Nt>=Nrt)
    off = 0.0
    for j in range(len(sizes)):
        for i in range(len(sizes)):
            if i != j:
                off = max(off, np.linalg.norm(HW[st[i]:st[i+1], cols[j]:cols[j+1]]))
    check(f"[{name}] BD: H_i W_j = 0 (i!=j)", off < 1e-8, f"max={off:.1e}")
    # BD rapido == BD classico (valores singulares efectivos iguais)
    b2 = bd_precoder(H, sizes, method="svd")
    check(f"[{name}] BD fast == BD por SVD (valores singulares)",
          np.allclose(np.sort(bd['e']), np.sort(b2['e']), atol=1e-8))
    # colunas unitarias nos precodificadores de potencia unitaria
    check(f"[{name}] BD/SVD colunas de norma 1",
          np.allclose(np.linalg.norm(bd["W"], axis=0), 1) and np.allclose(np.linalg.norm(sv["W"], axis=0), 1))
    # potencia total
    for pre, mode in ((zf, None), (bd, "eq"), (bd, "wf"), (sv, "eq"), (sv, "wf")):
        for sdb in (0, 20):
            snr = 10 ** (sdb / 10); lam = power_alloc(pre, snr, mode)
            Pt = np.sum(lam * np.sum(np.abs(pre["W"]) ** 2, axis=0))
            if abs(Pt - pre["Ns"] * snr) > 1e-9 * pre["Ns"] * snr:
                check(f"[{name}] potencia {pre['name']}-{mode}", False, f"{Pt} vs {pre['Ns']*snr}")
    check(f"[{name}] potencia total = P_T (todos os esquemas)", True)

# 8. cadeia explicita == equivalente rapido; interferencia zero na cadeia real
H = crandn(rng, 16, 16); sizes = [8, 8]
for pre, mode in ((zf_precoder(H), None), (bd_precoder(H, sizes), "wf"), (svd_precoder(H), "eq")):
    snr = 10 ** (15 / 10); lam = power_alloc(pre, snr, mode); act = lam > 0
    u = qam_mod(rng.integers(0, 4, size=(pre["Ns"], 5)), 2)
    n = crandn(rng, 16, 5)
    uh = chain(H, pre, lam, u, n)
    nt = n if pre["Gx"] is None else pre["Gx"] @ n
    with np.errstate(divide="ignore", invalid="ignore"):
        uh2 = u + nt / (pre["e"] * np.sqrt(lam))[:, None]
    check(f"cadeia explicita == equivalente ({pre['name']})", np.allclose(uh[act], uh2[act], atol=1e-8))

# 9. OFDM no tempo (IFFT+CP+canal multipercurso+FFT) == modelo por subcarrier
Nsc, Lcp, L, Nr, Nt = 16, 4, 3, 4, 4
h = crandn(rng, Nr, Nt, L) / np.sqrt(L)
Hk = np.fft.fft(h, Nsc, axis=2)                    # (Nr, Nt, Nsc)
idx = rng.integers(0, 4, size=(Nr, Nsc)); U = qam_mod(idx, 2)
X = np.zeros((Nt, Nsc), complex); lamk = np.zeros(Nsc)
for k in range(Nsc):
    pre = zf_precoder(Hk[:, :, k]); lam = power_alloc(pre, 10.0, None)
    X[:, k] = pre["W"] @ (np.sqrt(lam) * U[:, k]); lamk[k] = lam[0]
xt = np.fft.ifft(X, axis=1)
xcp = np.concatenate([xt[:, -Lcp:], xt], axis=1)    # prefixo ciclico
yr = np.zeros((Nr, Nsc + Lcp), complex)
for r in range(Nr):
    for a in range(Nt):
        yr[r] += np.convolve(xcp[a], h[r, a])[:Nsc + Lcp]
Y = np.fft.fft(yr[:, Lcp:], axis=1)
Uh = Y / np.sqrt(lamk)[None, :]
check("OFDM no tempo (CP>=L-1) == modelo por subcarrier", np.allclose(Uh, U, atol=1e-9),
      f"erro max={np.max(np.abs(Uh-U)):.1e}")

# 10. capacidade: casos limite
h1 = crandn(rng, 1, 1); pre = svd_precoder(h1)
snr = 7.0; c = np.sum(np.log2(1 + stream_snr(pre, power_alloc(pre, snr, "wf"))))
check("capacidade SISO = log2(1+snr|h|^2)", abs(c - np.log2(1 + snr * abs(h1[0, 0]) ** 2)) < 1e-12)
Hb = crandn(rng, 16, 16); sv = svd_precoder(Hb); bd = bd_precoder(Hb, [8, 8]); zf = zf_precoder(Hb)
for sdb in (0, 10, 30):
    snr = 10 ** (sdb / 10)
    cs = np.sum(np.log2(1 + stream_snr(sv, power_alloc(sv, snr, "wf"))))
    cb = np.sum(np.log2(1 + stream_snr(bd, power_alloc(bd, snr, "wf"))))
    cz = np.sum(np.log2(1 + stream_snr(zf, power_alloc(zf, snr, None))))
    check(f"ordem das capacidades SVD>=BD>=ZF @ {sdb} dB", cs >= cb - 1e-9 and cb >= cz - 1e-9,
          f"{cs:.2f} {cb:.2f} {cz:.2f}")

print("\nTODOS OS TESTES PASSARAM" if ok_all else "\nHA FALHAS")
sys.exit(0 if ok_all else 1)
