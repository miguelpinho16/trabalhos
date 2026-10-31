function uh = chain_explicit(H, pre, lam, u, n)
% CHAIN_EXPLICIT  Cadeia completa: x = W sqrt(lam) u ; y = Hx+n ; y~ = Gx y ; u_hat = y~/(e sqrt(lam)).
x = pre.W * bsxfun(@times, sqrt(lam(:)), u);
y = H * x + n;
if isempty(pre.Gx), yt = y; else, yt = pre.Gx * y; end
uh = bsxfun(@rdivide, yt, pre.e(:) .* sqrt(lam(:)));
end
