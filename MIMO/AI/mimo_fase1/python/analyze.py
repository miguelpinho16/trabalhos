import sys, pickle, csv
sys.path.insert(0, "/home/claude/mimo_sm/python")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "/home/claude/mimo_sm/results/"
FIG = R + "figuras/"
import os; os.makedirs(FIG, exist_ok=True)
LAB = ["ZF", "BD-eq", "BD-wf", "SVD-eq", "SVD-wf"]
COL = dict(zip(LAB, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
MRK = {"ZF": "o", "BD-eq": "s", "BD-wf": "s", "SVD-eq": "^", "SVD-wf": "^"}
LST = {"ZF": "-", "BD-eq": "--", "BD-wf": "-", "SVD-eq": "--", "SVD-wf": "-"}
NAME = {"1a": "Cenário 1a: Nt=16, 16 users × 1 ant", "1b": "Cenário 1b: Nt=16, 2 users × 8 ant",
        "2a": "Cenário 2a: Nt=512, 512 users × 1 ant", "2b": "Cenário 2b: Nt=512, 64 users × 8 ant"}
THR = {2: 17.5, 4: 12.5}      # TS 38.104, EVM [%] PDSCH QPSK / 16QAM
MN = {2: "QPSK", 4: "16-QAM"}

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b",
                     "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "grid.color": "#e4e3df", "grid.linewidth": 0.7, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "legend.frameon": False})

def line(ax, x, y, l, **kw):
    ax.plot(x, y, LST[l], color=COL[l], marker=MRK[l], ms=4.5, lw=1.6, mfc=COL[l], mec="#fcfcfb",
            mew=0.8, label=l, **kw)

rows = []
summ = {}
for sc in ("1a", "1b", "2a", "2b"):
    p = R + f"phase1_{sc}.pkl"
    if not os.path.exists(p):
        print("falta", p); continue
    o = pickle.load(open(p, "rb"))
    snr = o["snr_db"]; Ns = o["Nrt"]
    fig, axs = plt.subplots(2, 3, figsize=(13, 7.2), constrained_layout=True)
    ax = axs[0, 0]
    for l in LAB: line(ax, snr, o["cap"][l].mean(0), l)
    ax.set(xlabel="SNR por stream [dB]", ylabel="Capacidade soma [bit/s/Hz por subcarrier]", title="Capacidade (média)")
    ax.legend(loc="upper left"); ax.grid(True)
    for c, k in enumerate((2, 4), start=1):
        ax = axs[0, c]
        for l in LAB:
            ber = o["errs"][(l, k)].sum(0) / o["bits"][(l, k)].sum(0)
            ber = np.where(ber > 0, ber, np.nan)
            line(ax, snr, ber, l)
        ax.set_yscale("log"); ax.set_ylim(1e-5, 1)
        ax.set(xlabel="SNR por stream [dB]", ylabel="BER", title=f"BER {MN[k]}"); ax.grid(True)
    for c, k in enumerate((2, 4)):
        ax = axs[1, c]
        for l in LAB: line(ax, snr, 100 * np.nanmedian(o["evm"][(l, k)], 0), l)
        ax.axhline(THR[k], color="#0b0b0b", ls=":", lw=1.3)
        ax.text(snr[-1], THR[k] * 1.08, f"limiar 5G NR {THR[k]}%", fontsize=8, color="#0b0b0b", ha="right")
        ax.set_yscale("log"); ax.set(xlabel="SNR por stream [dB]", ylabel="EVM mediana [%]",
                                      title=f"EVM {MN[k]} (mediana; só streams activos)"); ax.grid(True)
    ax = axs[1, 2]
    for l in ("BD-wf", "SVD-wf"): line(ax, snr, 100 * o["act"][l].mean(0), l)
    ax.set(xlabel="SNR por stream [dB]", ylabel="Streams activos [%]",
           title="Water-filling: streams com potência > 0"); ax.grid(True); ax.legend(loc="lower right")
    fig.suptitle(NAME[sc] + f"  (D={o['D']} realizações, Ns={Ns} streams)", fontsize=11)
    fig.savefig(FIG + f"fase1_{sc}.png", dpi=150); plt.close(fig)

    # tabelas
    for sdb in (10, 20, 30, 40):
        i = int(np.where(snr == sdb)[0][0])
        for l in LAB:
            r = dict(cenario=sc, snr_db=sdb, esquema=l, Ns=Ns,
                     cap_total=o["cap"][l][:, i].mean(), cap_por_stream=o["cap"][l][:, i].mean() / Ns,
                     streams_activos_pct=100 * o["act"][l][:, i].mean())
            for k in (2, 4):
                r[f"BER_{MN[k]}"] = o["errs"][(l, k)][:, i].sum() / o["bits"][(l, k)][:, i].sum()
                ev = o["evm"][(l, k)][:, i]
                r[f"EVM_med_{MN[k]}_pct"] = 100 * np.nanmedian(ev)
                r[f"cumpre_EVM_{MN[k]}_pct"] = 100 * np.mean(ev * 100 <= THR[k])
            rows.append(r)
    # SNR minimo (grelha) para cumprir EVM: mediana e 95% das realizacoes
    for l in LAB:
        for k in (2, 4):
            ev = 100 * o["evm"][(l, k)]
            med = np.nanmedian(ev, 0) <= THR[k]
            p95 = (ev <= THR[k]).mean(0) >= 0.95
            summ[(sc, l, k)] = (snr[np.argmax(med)] if med.any() else np.nan,
                                snr[np.argmax(p95)] if p95.any() else np.nan)
    print(sc, "residuo max interferencia:", {k: f"{v.max():.1e}" for k, v in o["resid"].items()}, "runtime", round(o["runtime_s"]), "s")

with open(R + "tabela_fase1.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(R + "tabela_snr_evm.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["cenario", "esquema", "modulacao", "SNR_mediana_cumpre_dB", "SNR_95pct_cumpre_dB"])
    for (sc, l, k), (a, b) in summ.items(): w.writerow([sc, l, MN[k], a, b])
print("ok")
