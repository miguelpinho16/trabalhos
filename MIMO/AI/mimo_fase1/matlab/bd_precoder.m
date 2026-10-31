function pre = bd_precoder(H, sizes, method)
% BD_PRECODER  Block Diagonalization: W_j = V0_j * V1_j
%   (V0_j: espaco nulo dos canais dos outros utilizadores; V1_j: SVD do canal efectivo H_j*V0_j)
%   method: 'svd'  espaco nulo por SVD de H~_j (versao classica)
%           'fast' (so Nrt==Nt) espaco nulo = colunas de inv(H) do utilizador j
%           'auto' (por defeito) 'fast' se Nrt==Nt, senao 'svd'
if nargin < 3, method = 'auto'; end
[Nrt, Nt] = size(H);
sizes = sizes(:)';
st = [0 cumsum(sizes)];
K = numel(sizes);
fast = strcmp(method, 'fast') || (strcmp(method, 'auto') && Nrt == Nt);
if fast, Hinv = inv(H); end
W = zeros(Nt, 0);  e = zeros(0, 1);  Gx = zeros(Nrt, Nrt);  r = 0;
for j = 1:K
    a = st(j) + 1;  b = st(j+1);
    Hj = H(a:b, :);
    if fast
        [V0, ~] = qr(Hinv(:, a:b), 0);
    else
        Ht = H([1:a-1, b+1:Nrt], :);
        rk = min(size(Ht));
        [~, ~, V] = svd(Ht);
        V0 = V(:, rk+1:end);
    end
    if size(V0, 2) == 0, continue; end
    [U, S, V2] = svd(Hj * V0, 'econ');
    s = diag(S);   L = numel(s);
    W = [W, V0 * V2];                       %#ok<AGROW>
    e = [e; s];                             %#ok<AGROW>
    Gx(r+1:r+L, a:b) = U';
    r = r + L;
end
pre.name = 'bd';  pre.W = W;  pre.Gx = Gx(1:r, :);  pre.e = e;  pre.Ns = r;
end
