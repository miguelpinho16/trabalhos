function p = water_filling(g, P)
% WATER_FILLING  max sum log2(1+p_i g_i)  s.a.  sum p_i = P  (ruido unitario).
%   g : ganhos de potencia dos canais (sigma_i^2),  P : potencia total.
g = g(:);  n = numel(g);
[gs, order] = sort(g, 'descend');
ginv = 1 ./ gs;                            % Inf se ganho nulo
cum  = cumsum(ginv);
mu   = (P + cum) ./ (1:n)';
valid = mu > ginv;
p = zeros(n, 1);
if ~any(valid), return; end
kk = find(valid, 1, 'last');
pw = max(mu(kk) - ginv, 0);
p(order) = pw;
end
