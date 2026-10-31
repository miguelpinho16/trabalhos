import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

INK, SOFT = "#0b0b0b", "#52514e"
fig, ax = plt.subplots(figsize=(13, 5.2))
ax.set_xlim(0, 13); ax.set_ylim(0, 5.2); ax.axis("off")
fig.patch.set_facecolor("#fcfcfb")

def box(x, y, w, h, text, fc="#ffffff", ec=INK, fs=8.6, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", linespacing=1.25)

def arrow(x1, y1, x2, y2, text=None, dy=0.12, ls="-", c=INK):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11, lw=1.2,
                                 color=c, linestyle=ls))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, text, ha="center", fontsize=7.6, color=SOFT)

ym, h = 3.0, 1.1
# cadeia principal (BS -> canal -> utilizadores)
box(0.15, ym, 1.25, h, "Bits\naleatórios", "#f3f2ee")
box(1.75, ym, 1.45, h, "Mapeador\nQPSK / 16-QAM\n(Gray)", "#f3f2ee")
box(3.55, ym, 1.5, h, "Divisão em\nNs streams\nu (Ns×1)", "#f3f2ee")
box(5.4, ym, 1.8, h, "Pré-codificador\nx = W √Λ u\nZF · BD · SVD", "#dbe8f7", bold=True)
box(7.55, ym, 1.35, h, "IFFT + CP\n(por antena TX)", "#f3f2ee")
box(9.25, ym, 1.5, h, "Canal Rayleigh\ny = H x + n\n(mesmo H do gerador)", "#fbe3d6")
box(11.1, ym, 1.75, h, "Remoção CP + FFT\nCombinador Gx\n(Uᴴ ; ZF: I)", "#f3f2ee")
for x1, x2 in ((1.4, 1.75), (3.2, 3.55), (5.05, 5.4), (7.2, 7.55), (8.9, 9.25), (10.75, 11.1)):
    arrow(x1, ym + h / 2, x2, ym + h / 2)
# linha inferior (receptor)
box(11.1, 1.2, 1.75, 1.0, "Equalização\nû = ỹ / (e √λ)", "#f3f2ee")
box(8.75, 1.2, 1.75, 1.0, "Decisão dura\n(QAM demod)", "#f3f2ee")
box(6.2, 1.2, 2.0, 1.0, "BER · EVM\n(vs limiar 5G NR)", "#dff1e8", bold=True)
arrow(11.975, ym, 11.975, 2.2)
arrow(11.1, 1.7, 10.5, 1.7); arrow(8.75, 1.7, 8.2, 1.7)
# projecto do precoder
box(3.55, 1.2, 2.2, 1.0, "Projecto do pré-codificador\n(ZF: H⁺ · BD: espaço nulo+SVD\nSVD: H=UΣVᴴ ; water-filling Λ)", "#dbe8f7", fs=7.8)
box(0.15, 1.2, 2.5, 1.0, "Gerador de canal\nH ~ CN(0,1) i.i.d.\nCSI perfeita (Fase 1)", "#fbe3d6", fs=8.2)
arrow(2.65, 1.7, 3.55, 1.7, "H")
arrow(4.65, 2.2, 6.0, ym)
ax.text(4.75, 2.62, "W, Λ", fontsize=7.6, color=SOFT)
ax.text(5.2, 0.55, "Capacidade: C = Σ log₂(1 + λᵢ eᵢ²) , média sobre realizações de H  (calculada directamente a partir de W, Λ, e)",
        ha="center", fontsize=8.2, color=INK)
ax.text(0.15, 4.75, "Fase 1 – downlink MU-MIMO / massive MIMO com OFDM (CSI perfeita)", fontsize=10.5, fontweight="bold", color=INK)
ax.text(0.15, 4.45, "Cada subcarrier vê um H independente (Rayleigh plano); IFFT/CP/FFT são transparentes se CP ≥ duração do canal (validado em tests.py).",
        fontsize=8, color=SOFT)
fig.savefig("/home/claude/mimo_sm/results/figuras/diagrama_blocos_fase1.png", dpi=170, bbox_inches="tight")
