import numpy as np
V0=1.1; CDAC=0.5e-12; T=4e-9; eps=5e-4; tno=0.1e-9
t1=T/2-tno; t2=T/2-tno
def lin_err(g,CD):
    Ct=CD+CDAC; x1=np.exp(-g*t1/Ct); x2=np.exp(-g*t2/CD) if CD>0 else 0
    return (CDAC/Ct)*x1/(1-(CD/Ct)*x1*x2)          # relativo a V0 (regime periódico)
def bis(f,lo=1e-5,hi=10):
    for _ in range(80):
        m=np.sqrt(lo*hi); lo,hi=(lo,m) if f(m) else (m,hi)
    return hi
def g_lin(CD): return bis(lambda g: lin_err(g,CD)<=eps)
# EKV grande sinal (fonte comum ao corpo à massa: g_out = gms = n*gm)
UT=0.02585; n=1.3
def ekv_err(gms,CD,gmid=15):
    gms_id=n*gmid                        # gms/ID
    IB=gms/gms_id
    # IC a partir de gms/ID = (1/UT)*2/(1+sqrt(1+4IC))  (EKV/ACM)
    IC=((2/(UT*gms_id)-1)**2-1)/4
    IS=IB/IC
    v0=2*np.log(np.exp(np.sqrt(IC))-1)   # (VP-VS)/UT no ponto de repouso
    I=lambda dV: IS*np.log1p(np.exp(v0/2+dV/(2*UT)))**2   # dV = queda de Vout
    e=0.0  # queda relativa a V0 (em V)
    N=400
    for cyc in range(30):
        # fase 1: partilha de carga + recuperação
        Ct=CD+CDAC; e=V0-(CD*(V0-e))/Ct
        dt=t1/N
        for k in range(N):   # RK2
            f=lambda x: -(I(x)-IB)/Ct
            k1=f(e); k2=f(e+dt*k1); e+=dt*(k1+k2)/2
        e1=e
        if CD>0:
            dt=t2/N
            for k in range(N):
                f=lambda x: -(I(x)-IB)/CD
                k1=f(e); k2=f(e+dt*k1); e+=dt*(k1+k2)/2
    return e1/V0, IB, IC
def g_ekv(CD,gmid=15): return bis(lambda g: ekv_err(g,CD,gmid)[0]<=eps,1e-4,1)
print(f"t1=t2={t1*1e9:.2f} ns")
print(" CD[pF] dV0[mV]  gout_lin[mS]  gout_EKV[mS]  gm11=gout/n [mS]  IB11@gm/ID=15 [uA]")
rows=[]
for CD in [0.1e-12,0.25e-12,0.5e-12,1e-12,2e-12,5e-12,10e-12,100e-12,1e-9]:
    gl=g_lin(CD); ge=g_ekv(CD); _,IB,IC=ekv_err(ge,CD)
    rows.append((CD,gl,ge))
    print(f"{CD*1e12:6.2f} {V0*CDAC/(CD+CDAC)*1e3:7.1f} {gl*1e3:10.2f} {ge*1e3:12.2f} {ge/n*1e3:14.2f} {IB*1e6:14.0f}  IC={IC:.2f}")
np.save('rows.npy',np.array(rows))