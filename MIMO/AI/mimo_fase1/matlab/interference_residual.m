function r = interference_residual(H, pre)
% INTERFERENCE_RESIDUAL  ||Gx H W - diag(e)||_F / ||diag(e)||_F  (0 = sem interferencia)
HW = H * pre.W;
if isempty(pre.Gx), A = HW; else, A = pre.Gx * HW; end
D = diag(pre.e);
r = norm(A - D, 'fro') / norm(D, 'fro');
end
