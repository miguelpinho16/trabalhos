function pre = svd_precoder(H)
% SVD_PRECODER  SVD do canal completo (receptores cooperantes): limite superior.
[U, S, V] = svd(H, 'econ');
pre.name = 'svd';  pre.W = V;  pre.Gx = U';  pre.e = diag(S);  pre.Ns = size(S, 1);
end
