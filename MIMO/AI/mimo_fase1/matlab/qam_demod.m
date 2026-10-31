function idx = qam_demod(s, k)
% QAM_DEMOD  Decisao dura (distancia minima) para QPSK/16-QAM Gray.
if k == 2
    idx = 2*(real(s) < 0) + (imag(s) < 0);
elseif k == 4
    x = real(s)*sqrt(10);  y = imag(s)*sqrt(10);
    li = (x > -2) + (x > 0) + (x > 2);     % 0..3  <-> niveis -3,-1,+1,+3
    lq = (y > -2) + (y > 0) + (y > 2);
    code = [0 1 3 2];                      % indice de nivel -> codigo Gray
    idx = 4*code(li + 1) + code(lq + 1);
else
    error('k deve ser 2 ou 4');
end
end
