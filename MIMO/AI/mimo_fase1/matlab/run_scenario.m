function out = run_scenario(Nt, sizes, snr_db, D, T, seed)
% RUN_SCENARIO  Fase 1 (CSI perfeita): capacidade, BER (QPSK,16-QAM) e EVM para
%   ZF, BD (eq/wf) e SVD cooperante (eq/wf). D realizacoes independentes do canal
%   (= subcarriers/blocos independentes em canal Rayleigh plano por subcarrier),
%   T simbolos por stream e por realizacao.
try, rng(seed); catch, rand('state', seed); randn('state', seed); end   %#ok<NOCOMMA>
sizes = sizes(:)';  Nrt = sum(sizes);
snr_lin = 10 .^ (snr_db(:)' / 10);  nS = numel(snr_lin);
labels = {'ZF', 'BD-eq', 'BD-wf', 'SVD-eq', 'SVD-wf'};
keys   = {'zf', 'bd',    'bd',    'svd',    'svd'};
modes  = {'',   'eq',    'wf',    'eq',     'wf'};
mods = [2 4];
out.labels = labels;  out.snr_db = snr_db;  out.D = D;  out.T = T;
out.Nt = Nt;  out.Nrt = Nrt;  out.K = numel(sizes);
out.cap  = zeros(D, nS, 5);    out.act = zeros(D, nS, 5);
out.errs = zeros(D, nS, 5, 2); out.bits = zeros(D, nS, 5, 2); out.evm = zeros(D, nS, 5, 2);
out.resid = zeros(D, 3);       % zf, bd, svd
for d = 1:D
    H = (randn(Nrt, Nt) + 1j*randn(Nrt, Nt)) / sqrt(2);
    pres = {zf_precoder(H), bd_precoder(H, sizes), svd_precoder(H)};
    for q = 1:3, out.resid(d, q) = interference_residual(H, pres{q}); end
    for l = 1:5
        pre = pres{find(strcmp(keys{l}, {'zf', 'bd', 'svd'}))};   %#ok<FNDSB>
        for i = 1:nS
            lam = power_alloc(pre, snr_lin(i), modes{l});
            si  = lam .* pre.e.^2;
            out.cap(d, i, l) = sum(log2(1 + si));
            out.act(d, i, l) = mean(si > 0);
            for m = 1:2
                [er, nb, e2, ns] = mc_detect(si, mods(m), T);
                out.errs(d, i, l, m) = er;  out.bits(d, i, l, m) = nb;
                if ns > 0, out.evm(d, i, l, m) = sqrt(e2 / ns); else, out.evm(d, i, l, m) = NaN; end
            end
        end
    end
    if mod(d, 20) == 0, fprintf('  realizacao %d/%d\n', d, D); end
end
end
