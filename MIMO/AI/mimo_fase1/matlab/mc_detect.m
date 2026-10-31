function [errs, nbits, e2, ns] = mc_detect(snr_i, k, T)
% MC_DETECT  Monte Carlo equivalente a cadeia (interferencia nula): u_hat = u + n/sqrt(snr_i).
%   Devolve erros de bit, n. de bits, soma |u_hat-u|^2 e n. de simbolos (so streams activos).
act = snr_i(:) > 0;   na = sum(act);
if na == 0, errs = 0; nbits = 0; e2 = 0; ns = 0; return; end
s = snr_i(:);  s = s(act);
idx = floor(rand(na, T) * 2^k);
u  = qam_mod(idx, k);
nz = (randn(na, T) + 1j*randn(na, T)) / sqrt(2);
uh = u + bsxfun(@rdivide, nz, sqrt(s));
ir = qam_demod(uh, k);
pc = [0 1 1 2 1 2 2 3 1 2 2 3 2 3 3 4];
errs  = sum(sum(pc(bitxor(idx, ir) + 1)));
nbits = na * T * k;
e2 = sum(sum(abs(uh - u).^2));
ns = na * T;
end
