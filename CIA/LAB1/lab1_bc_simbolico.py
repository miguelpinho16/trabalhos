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

# ---------------- resolver (rápido: matriz + regra de Cramer) ----------------
import time
t0 = time.time()
def passo(msg): print(f"[{time.time()-t0:6.1f} s] {msg}", flush=True)

incog = [V1, V2, V3, VoutR]
Y, rhs = sp.linear_eq_to_matrix([e.lhs - e.rhs for e in (eqV1, eqV2, eqV3, eqVo)], incog)
passo("Sistema escrito na forma matricial  Y(s)·x = rhs")

D = sp.expand(Y.det(method='berkowitz'))
passo("Denominador D(s) = det(Y) calculado")

Y4 = Y.copy(); Y4[:, 3] = rhs                     # Cramer: VoutR é a 4.ª incógnita
N = sp.expand(Y4.det(method='berkowitz') / Vref)  # numerador (já dividido por Vref)
passo("Numerador N(s) calculado")

Dp, Np = sp.Poly(D, s), sp.Poly(N, s)
if Dp.coeff_monomial(1).could_extract_minus_sign():   # termo s^0 positivo
    Np, Dp = -Np, -Dp
print(f"\nGrau de N(s) = {Np.degree()}   Grau de D(s) = {Dp.degree()}")

# ---------------- c) ganho DC exato ----------------
a0, b0 = Dp.coeff_monomial(1), Np.coeff_monomial(1)
A0 = sp.factor(b0) / sp.factor(a0)
passo("Ganho DC calculado")
print("\n=== Ganho DC exato  A0 = b0/a0 ===")
sp.pprint(sp.cancel(A0))

A0_cadeia = (gm1B/(gds1B + gds2B*gds3B/(gm2B + gds2B + gds3B))) \
            * (gm5/(gds4 + gds5)) * (gm1/(gm1 + gds1 + gdsIB3))
print("Confere com a expressão em cadeia?", sp.cancel(A0 - A0_cadeia) == 0)

# ---------------- c) coeficientes exatos ----------------
# (sem factor/simplify nos coeficientes grandes — é isso que demora muito)
a = [Dp.coeff_monomial(s**k) for k in range(Dp.degree() + 1)]
b = [Np.coeff_monomial(s**k) for k in range(Np.degree() + 1)]
for nome, lista in (("a", a), ("b", b)):
    for k, c_ in enumerate(lista):
        print(f"{nome}{k}: {len(sp.Add.make_args(c_))} termos")
passo("Coeficientes extraídos")

with open("H_exata.tex", "w") as fh:
    fh.write("A_0 = " + sp.latex(sp.cancel(A0)) + "\n\n")
    for k, ak in enumerate(a):
        fh.write(f"a_{k} = " + sp.latex(ak) + "\n\n")
    for k, bk in enumerate(b):
        fh.write(f"b_{k} = " + sp.latex(bk) + "\n\n")
passo("Expressões em LaTeX guardadas em H_exata.tex")

# Polos exatos = raízes de D(s) (4.ª ordem). Na d) aproximam-se a partir dos
# coeficientes, p.ex. polo dominante  p1 ≈ -a0/a1  (se os polos estiverem afastados).
