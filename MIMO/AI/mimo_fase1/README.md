# Sistemas MIMO 2026/27 – Fase 1 (CSI perfeita)

## Conteúdo
- `python/` – simulador de referência (usado para gerar TODOS os resultados): `mimo.py`, `run_phase1.py`, `analyze.py`, `tests.py`, `complexity.py`, `diagram.py`
- `matlab/` – o mesmo simulador em Matlab/Octave (**não foi executado** ao fazer a entrega; ver abaixo)
- `results/` – figuras (`figuras/`), tabelas CSV e dados brutos `.pkl`

## Como correr (Matlab/Octave)
1. `tests_phase1` → tem de acabar em "TODOS OS TESTES PASSARAM". Se algo falhar, diz-me qual.
2. `run_phase1` (com `quick = true` para um teste rápido) → gera `results_phase1.mat` e figuras.
3. `complexity_test` → tempos por subcarrier.

## Como correr (Python)
`python3 tests.py` · `python3 run_phase1.py 1a 1b 2a 2b` · `python3 analyze.py` · `python3 complexity.py`

## Convenções
- H (Nrt×Nt) ~ CN(0,1) i.i.d. por subcarrier (Rayleigh plano). Ruído CN(0,1) por antena receptora.
- SNR = P_T / (Ns · σ_n²) = potência por stream / ruído.
- x = W·sqrt(Λ)·u, com Σ λ_i ||w_i||² = P_T. ZF: ganho comum β² = P_T / tr(WᴴW).
- "SVD" = SVD do canal completo (receptores cooperantes, limite superior). "BD" = Block Diagonalization (SVD por utilizador).
- eq = potência igual por stream; wf = water-filling. EVM e BER do wf só contam streams activos.
- Limiares EVM 5G NR (3GPP TS 38.104, PDSCH): QPSK 17,5 %, 16-QAM 12,5 %.
