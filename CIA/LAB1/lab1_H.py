"""
CIA - LAB1 b)/c): função de transferência, ganho DC, polos e zeros
H(s) = VoutR/Vref   (pip install sympy numpy)
"""
import sympy as sp
import numpy as np

s = sp.symbols('s')
V1, V2, V3, Vo, Vref = sp.symbols('V1 V2 V3 V_outR V_ref')

# ---- parâmetros ----
gm1B, gm2B, gm5, gm1 = sp.symbols('g_m1B g_m2B g_m5 g_m1', positive=True)
gds1B, gds2B, gds3B, gds4, gds5, gds1, gdsIB3 = sp.symbols(
    'g_ds1B g_ds2B g_ds3B g_ds4 g_ds5 g_ds1 g_dsIB3', positive=True)
C1, C2, C3, C4 = sp.symbols('C_1 C_2 C_3 C_4', positive=True)      # capacidades à massa de cada nó
Cgd1B, Cdb2B, Cgd5, Cc, Cgs1 = sp.symbols('C_gd1B C_db2B C_gd5 C_c C_gs1', positive=True)  # flutuantes
# C1 = Cdb1B+Cgd2B+Cgs5 | C2 = Cp+Cdb5+Cdb4+Cgd4+Cgs11+Cgd11+Cgd1
# C3 = Cgs2B+Cgd3B+Cdb3B | C4 = Cdb1+CdbIB3+Cgs1A+Cgd1A

# ---- equações nodais (soma das correntes que saem = 0) ----
eqs = [
    gm1B*Vref + V1*gds1B + (V1-V3)*gds2B + gm2B*(-V3)
      + s*(V1*C1 + (V1-Vref)*Cgd1B + (V1-V3)*Cdb2B + (V1-V2)*Cgd5),               # V1
    gm5*V1 + V2*(gds4+gds5) + s*(V2*C2 + (V2-V1)*Cgd5 + (V2-V3)*Cc + (V2-Vo)*Cgs1),  # V2
    V3*gds3B + (V3-V1)*gds2B - gm2B*(-V3) + s*(V3*C3 + (V3-V1)*Cdb2B + (V3-V2)*Cc),  # V3
    -gm1*(V2-Vo) + Vo*(gds1+gdsIB3) + s*(Vo*C4 + (Vo-V2)*Cgs1),                      # VoutR
]

# ---- resolver (regra de Cramer) ----
Y, rhs = sp.linear_eq_to_matrix(eqs, [V1, V2, V3, Vo])
D = sp.expand(Y.det(method='berkowitz'))
Y4 = Y.copy(); Y4[:, 3] = rhs
N = sp.expand(Y4.det(method='berkowitz') / Vref)
H = N / D                                            # função de transferência

# ---- ganho DC ----
A0 = sp.factor(N.subs(s, 0)) / sp.factor(D.subs(s, 0))
print("Ganho DC  A0 = H(0) ="); sp.pprint(A0)

# ---- polos e zeros ----
# preencher com os valores do dimensionamento (alínea e) para obter números
valores = {
    gm1B: None, gm2B: None, gm5: None, gm1: None,
    gds1B: None, gds2B: None, gds3B: None, gds4: None, gds5: None, gds1: None, gdsIB3: None,
    C1: None, C2: None, C3: None, C4: None,
    Cgd1B: None, Cdb2B: None, Cgd5: None, Cc: None, Cgs1: None,
}
if None in valores.values():
    print("\nPolos/zeros: preencher o dicionário 'valores' para os calcular.")
else:
    a = [float(c) for c in sp.Poly(D.subs(valores), s).all_coeffs()]   # s^4 ... s^0
    b = [float(c) for c in sp.Poly(N.subs(valores), s).all_coeffs()]
    polos, zeros = np.roots(a), np.roots(b)
    A0n = float(A0.subs(valores))
    print(f"\nA0 = {A0n:.1f}  ({20*np.log10(abs(A0n)):.1f} dB)")
    print("Polos [Hz]:", *[f"{p/(2*np.pi):.4g}" for p in polos], sep="\n  ")
    print("Zeros [Hz]:", *[f"{z/(2*np.pi):.4g}" for z in zeros], sep="\n  ")
