function s = qam_mod(idx, k)
% QAM_MOD  Modulacao QPSK (k=2) ou 16-QAM (k=4), codigo Gray, potencia media 1.
%   idx : inteiros em [0, 2^k-1] (qualquer dimensao)
if k == 2
    b0 = bitand(bitshift(idx, -1), 1);
    b1 = bitand(idx, 1);
    s = ((1 - 2*b0) + 1j*(1 - 2*b1)) / sqrt(2);
elseif k == 4
    lv = [-3 -1 3 1];                      % codigo Gray 00,01,10,11 -> nivel
    s = (lv(bitshift(idx, -2) + 1) + 1j*lv(bitand(idx, 3) + 1)) / sqrt(10);
else
    error('k deve ser 2 ou 4');
end
end
