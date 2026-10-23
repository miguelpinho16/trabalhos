"""
CIA - LAB1, alíneas b) e c) — resolução SIMBÓLICA (sympy)
Requer:  pip install sympy

Nós:  V1 = vx (saída do 1.º andar)      V2 = Vctr (saída do 2.º andar)
      V3 = nó entre M2B e M3B           VoutR = saída do SF (M1)
Convenção: soma das correntes que SAEM de cada nó = 0
Bulk ligado à fonte (deep n-well) -> sem gmb
"""
import sympy as sp

s = sp.symbols('s')
V1, V2, V3, VoutR, Vref = sp.symbols('V1 V2 V3 V_outR V_ref')

# ---------------- parâmetros de pequeno sinal ----------------
gm1B, gm2B, gm3B, gm4, gm5, gm1 = sp.symbols('g_m1B g_m2B g_m3B g_m4 g_m5 g_m1', positive=True)
gds1B, gds2B, gds3B, gds4, gds5, gds1, gdsIB3 = sp.symbols(
    'g_ds1B g_ds2B g_ds3B g_ds4 g_ds5 g_ds1 g_dsIB3', positive=True)

Cgd1B, Cdb1B = sp.symbols('C_gd1B C_db1B', positive=True)                 # M1B
Cdb2B, Cgd2B, Cgs2B = sp.symbols('C_db2B C_gd2B C_gs2B', positive=True)   # M2B
Cgd3B, Cdb3B = sp.symbols('C_gd3B C_db3B', positive=True)                 # M3B
Cgs5, Cgd5, Cdb5 = sp.symbols('C_gs5 C_gd5 C_db5', positive=True)         # M5
Cdb4, Cgd4 = sp.symbols('C_db4 C_gd4', positive=True)                     # M4
Cgs1, Cgd1, Cdb1 = sp.symbols('C_gs1 C_gd1 C_db1', positive=True)         # M1 (SF)
Cp, Cc = sp.symbols('C_p C_c', positive=True)
Cgs11, Cgd11 = sp.symbols('C_gs11 C_gd11', positive=True)                 # M11 (carga em Vctr)
CdbIB3 = sp.symbols('C_dbIB3', positive=True)                             # fonte IB3
Cgs1A, Cgd1A = sp.symbols('C_gs1A C_gd1A', positive=True)                 # porta do M1A (carga do loop aberto)

# ---------------- tensões de controlo ----------------
vgs1B = Vref          # porta = Vref, fonte = cauda (massa AC)
vgs2B = 0 - V3        # porta = VB3 (massa AC), fonte = V3
vgs3B = 0             # porta e fonte à massa AC
vgs4  = 0             # porta e fonte à massa AC
vgs5  = V1 - 0
vgs1  = V2 - VoutR

# ---------------- equações nodais (iguais às do caderno) ----------------
# V1: fonte M1B com seta a ENTRAR e rótulo -gm1B*vgs1B  ->  -(-gm1B*vgs1B)
eqV1 = sp.Eq(  gm1B*vgs1B
             + V1*gds1B + V1*s*Cdb1B
             + (V1 - V3)*s*Cdb2B + (V1 - V3)*gds2B + gm2B*vgs2B
             + (V1 - Vref)*s*Cgd1B + V1*s*Cgd2B
             + (V1 - V2)*s*Cgd5 + V1*s*Cgs5, 0)

# V2: fonte M5 sai (D->S); fonte M4 nula
eqV2 = sp.Eq(  (V2 - V1)*s*Cgd5 + gm5*vgs5 + V2*gds5 + V2*s*Cdb5
             + V2*gds4 + gm4*vgs4 + V2*s*Cdb4 + V2*s*Cgd4
             + V2*s*(Cgs11 + Cp + Cgd11)
             + (V2 - VoutR)*s*Cgs1 + V2*s*Cgd1 + (V2 - V3)*s*Cc, 0)

# V3: fonte M2B ENTRA (vem do V1); fonte M3B nula
eqV3 = sp.Eq(  V3*s*Cgd3B + gm3B*vgs3B + V3*gds3B + V3*s*Cdb3B
             + (V3 - V2)*s*Cc
             + (V3 - V1)*s*Cdb2B + (V3 - V1)*gds2B - gm2B*vgs2B
             + V3*s*Cgs2B, 0)

# VoutR: fonte M1 ENTRA (vem do dreno = massa AC)
eqVo = sp.Eq(  VoutR*(gdsIB3 + s*CdbIB3 + s*Cgd1A + s*Cgs1A) + VoutR*s*Cdb1
             - gm1*vgs1 + VoutR*gds1 + (VoutR - V2)*s*Cgs1, 0)

# ---------------- capacidades agrupadas por nó (opcional) ----------------
# Capacidades à massa somadas por nó (a expressão continua EXATA):
#   C1 (V1)    = C_db1B + C_gd2B + C_gs5
#   C2 (V2)    = C_p + C_db5 + C_db4 + C_gd4 + C_gs11 + C_gd11 + C_gd1
#   C3 (V3)    = C_gs2B + C_gd3B + C_db3B
#   C4 (VoutR) = C_db1 + C_dbIB3 + C_gs1A + C_gd1A
# Flutuantes (mantêm-se): C_gd1B (V1-Vref), C_db2B (V1-V3), C_gd5 (V1-V2),
#                         C_c (V2-V3), C_gs1 (V2-VoutR)
C1, C2, C3, C4 = sp.symbols('C_1 C_2 C_3 C_4', positive=True)
agrupar = {Cdb1B: C1, Cgd2B: 0, Cgs5: 0,
           Cp: C2, Cdb5: 0, Cdb4: 0, Cgd4: 0, Cgs11: 0, Cgd11: 0, Cgd1: 0,
           Cgs2B: C3, Cgd3B: 0, Cdb3B: 0,
           Cdb1: C4, CdbIB3: 0, Cgs1A: 0, Cgd1A: 0}

import time
t0 = time.time()
def passo(msg): print(f"[{time.time()-t0:6.1f} s] {msg}", flush=True)

A0_compacto = ("A0 = [ g_m1B*(g_m2B+g_ds2B+g_ds3B) / ( g_ds1B*(g_m2B+g_ds2B+g_ds3B) + g_ds2B*g_ds3B ) ]\n"
               "     * [ g_m5/(g_ds4+g_ds5) ]\n"
               "     * [ g_m1/(g_m1+g_ds1+g_dsIB3) ]\n"
               "     (1.º andar)  x  (2.º andar)  x  (seguidor de fonte)")

def escreve_coef(fh, nome, expr):
    termos = sp.Add.make_args(sp.expand(expr))
    fh.write(f"{nome}  ({len(termos)} termos) =\n")
    fh.write("      " + "\n    + ".join(sp.sstr(t) for t in termos) + "\n\n")

def resolver(eqs, ficheiro, titulo):
    incog = [V1, V2, V3, VoutR]
    Y, rhs = sp.linear_eq_to_matrix([e.lhs - e.rhs for e in eqs], incog)
    D = sp.expand(Y.det(method='berkowitz'))
    Y4 = Y.copy(); Y4[:, 3] = rhs                     # regra de Cramer
    N = sp.expand(Y4.det(method='berkowitz') / Vref)
    Dp, Np = sp.Poly(D, s), sp.Poly(N, s)
    if Dp.coeff_monomial(1).could_extract_minus_sign():
        Np, Dp = -Np, -Dp
    a = [Dp.coeff_monomial(s**k) for k in range(Dp.degree() + 1)]
    b = [Np.coeff_monomial(s**k) for k in range(Np.degree() + 1)]
    passo(f"{titulo}: N(s) e D(s) calculados")

    A0 = sp.cancel(b[0] / a[0])
    A0_cadeia = (gm1B/(gds1B + gds2B*gds3B/(gm2B + gds2B + gds3B))) \
                * (gm5/(gds4 + gds5)) * (gm1/(gm1 + gds1 + gdsIB3))
    ok = sp.cancel(A0 - A0_cadeia) == 0

    with open(ficheiro, "w", encoding="utf-8") as fh:
        fh.write("="*78 + f"\nCIA - LAB1 - alíneas b)/c)  -  {titulo}\n" + "="*78 + "\n\n")
        fh.write("Nós: V1 = vx | V2 = Vctr | V3 = nó M2B/M3B | VoutR = saída do SF\n")
        fh.write("Bulk ligado à fonte (deep n-well) -> sem gmb\n\n")
        fh.write("FUNÇÃO DE TRANSFERÊNCIA (ganho de malha aberta)\n")
        fh.write("  H(s) = VoutR/Vref = (b0 + b1*s + b2*s^2 + b3*s^3 + b4*s^4)\n")
        fh.write("                     / (a0 + a1*s + a2*s^2 + a3*s^3 + a4*s^4)\n")
        fh.write(f"  Grau N(s) = {Np.degree()}, grau D(s) = {Dp.degree()}  -> 4 polos, 4 zeros\n\n")
        fh.write("GANHO DC EXATO (forma compacta)\n" + A0_compacto + "\n")
        fh.write(f"  Verificação (A0 = b0/a0 coincide com a forma compacta): {ok}\n\n")
        fh.write("POLOS E ZEROS\n")
        fh.write("  Polos exatos = raízes de D(s) = 0 (4.ª ordem, sem forma fechada útil)\n")
        fh.write("  Zeros exatos = raízes de N(s) = 0\n")
        fh.write("  Aproximações (alínea d), polos afastados):\n")
        fh.write("    p1 ≈ -a0/a1,  p2 ≈ -a1/a2,  p3 ≈ -a2/a3,  p4 ≈ -a3/a4\n")
        fh.write("    z1 ≈ -b0/b1,  ... (idem para o numerador)\n")
        fh.write("    GBW ≈ A0*|p1| = b0/a1\n\n")
        fh.write("Nº de termos por coeficiente:\n")
        for k, c_ in enumerate(a): fh.write(f"  a{k}: {len(sp.Add.make_args(c_))}\n")
        for k, c_ in enumerate(b): fh.write(f"  b{k}: {len(sp.Add.make_args(c_))}\n")
        fh.write("\n" + "-"*78 + "\nNUMERADOR N(s)\n" + "-"*78 + "\n")
        for k, c_ in enumerate(b): escreve_coef(fh, f"b{k}", c_)
        fh.write("-"*78 + "\nDENOMINADOR D(s)\n" + "-"*78 + "\n")
        for k, c_ in enumerate(a): escreve_coef(fh, f"a{k}", c_)
    passo(f"{titulo}: guardado em {ficheiro}  (A0 confere: {ok})")

eqs = [eqV1, eqV2, eqV3, eqVo]
resolver([e.subs(agrupar) for e in eqs], "resultados_agrupado.txt",
         "capacidades agrupadas por nó (C1..C4 + flutuantes)")
resolver(eqs, "resultados_completo.txt", "todas as capacidades individuais")
