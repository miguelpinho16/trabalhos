function pre = zf_precoder(H)
% ZF_PRECODER  W = H^H (H H^H)^-1  (pseudo-inversa de Moore-Penrose).
Nrt = size(H, 1);
W = H' / (H*H');
pre.name = 'zf';   pre.W = W;   pre.Gx = [];   pre.e = ones(Nrt, 1);
pre.Ns = Nrt;      pre.normW2 = sum(abs(W(:)).^2);
end
