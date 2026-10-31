function lam = power_alloc(pre, snr, mode)
% POWER_ALLOC  Potencia por stream. snr = P_T/(Ns*sigma_n^2) (linear).
%   mode: 'eq' (igual) ou 'wf' (water-filling); ignorado no ZF (ganho comum beta^2).
Ns = pre.Ns;  P = Ns * snr;
if strcmp(pre.name, 'zf')
    lam = (P / pre.normW2) * ones(Ns, 1);
elseif strcmp(mode, 'eq')
    lam = (P / Ns) * ones(Ns, 1);
elseif strcmp(mode, 'wf')
    lam = water_filling(pre.e.^2, P);
else
    error('mode invalido');
end
end
