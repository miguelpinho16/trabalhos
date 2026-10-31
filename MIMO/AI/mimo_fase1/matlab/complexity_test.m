% COMPLEXITY_TEST  Tempo de calculo do pre-codificador por subcarrier (Fase 1).
%   BD classica = K SVDs de H~_j ((Nrt-Nr_j) x Nt); para 2b mede-se 1 utilizador e multiplica-se por K.
cen = {'1a', 16, ones(1, 16); '1b', 16, [8 8]; '2a', 512, ones(1, 512); '2b', 512, 8*ones(1, 64)};
nrep = 3;
fprintf('%-4s %10s %12s %14s %12s\n', 'cen', 'ZF [s]', 'BD fast [s]', 'BD classica[s]', 'SVD coop [s]');
for c = 1:4
    Nt = cen{c, 2};  sizes = cen{c, 3};  Nrt = sum(sizes);  K = numel(sizes);
    H = (randn(Nrt, Nt) + 1j*randn(Nrt, Nt)) / sqrt(2);
    tz = inf; tf = inf; ts = inf; tb = inf;
    for r = 1:nrep
        tic; zf_precoder(H);                    tz = min(tz, toc);
        tic; bd_precoder(H, sizes, 'fast');     tf = min(tf, toc);
        tic; svd_precoder(H);                   ts = min(ts, toc);
        Ht = H([sizes(1)+1:Nrt], :);            % H~ do utilizador 1
        tic; [~, ~, V] = svd(Ht); V0 = V(:, size(Ht, 1)+1:end);
        [~, ~, ~] = svd(H(1:sizes(1), :) * V0, 'econ');  tb = min(tb, toc);
    end
    fprintf('%-4s %10.4f %12.4f %14.4f %12.4f\n', cen{c, 1}, tz, tf, K*tb, ts);
end
