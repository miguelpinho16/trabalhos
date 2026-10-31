import sys, time, pickle
sys.path.insert(0, "/home/claude/mimo_sm/python")
import numpy as np
from mimo import run_scenario

CFG = {"1a": dict(D=2000, T=50), "1b": dict(D=2000, T=50),
       "2a": dict(D=1000, T=10), "2b": dict(D=1000, T=10)}
SNR_DB = np.arange(0, 41, 2.0)

for name in sys.argv[1:]:
    t = time.time()
    c = CFG[name]
    out = run_scenario(name, SNR_DB, D=c["D"], T=c["T"], seed={"1a": 11, "1b": 12, "2a": 21, "2b": 22}[name])
    out["runtime_s"] = time.time() - t
    with open(f"/home/claude/mimo_sm/results/phase1_{name}.pkl", "wb") as f:
        pickle.dump(out, f)
    print(name, "feito em", round(out["runtime_s"]), "s", flush=True)
