% RUN_PHASE1  Trabalho Sistemas MIMO 2026/27 - Fase 1 (CSI perfeita, canal Rayleigh plano por subcarrier)
%   Corre os cenarios 1a, 1b, 2a, 2b, guarda results_phase1.mat e desenha as figuras.
%   Para um teste rapido: quick = true.
clear; close all;
quick = true;
cen = {'1a', 16,  ones(1, 16);  '1b', 16,  [8 8];  '2a', 512, ones(1, 512);  '2b', 512, 8*ones(1, 64)};
snr_db = 0:2:40;
if quick, D = [50 50 3 3]; else, D = [2000 2000 200 200]; end
T = [50 50 10 10];
R = struct();
for c = 1:4
    fprintf('Cenario %s (Nt=%d, K=%d)\n', cen{c, 1}, cen{c, 2}, numel(cen{c, 3}));
    R.(['s' cen{c, 1}]) = run_scenario(cen{c, 2}, cen{c, 3}, snr_db, D(c), T(c), 100 + c);
end
save('results_phase1.mat', 'R', 'snr_db');

names = fieldnames(R);
col = {'k', 'b', 'c', 'r', 'm'};  lst = {'-', '--', '-', '--', '-'};  mrk = {'o', 's', 's', '^', '^'};
thr = [17.5 12.5];                              % limiares EVM 5G NR (TS 38.104): QPSK, 16-QAM [%]
mname = {'QPSK', '16-QAM'};
for c = 1:numel(names)
    o = R.(names{c});
    % --- capacidade (media sobre realizacoes)
    figure; hold on; grid on;
    for l = 1:5, plot(snr_db, mean(o.cap(:, :, l), 1), [col{l} lst{l} mrk{l}], 'LineWidth', 1.2); end
    xlabel('SNR por stream [dB]'); ylabel('Capacidade soma [bit/s/Hz por subcarrier]');
    title(['Cenario ' names{c}(2:end)]); legend(o.labels, 'Location', 'northwest');
    % --- BER
    for m = 1:2
        figure; hold on; grid on;
        for l = 1:5
            ber = sum(o.errs(:, :, l, m), 1) ./ sum(o.bits(:, :, l, m), 1);
            semilogy(snr_db, ber, [col{l} lst{l} mrk{l}], 'LineWidth', 1.2);
        end
        set(gca, 'YScale', 'log'); ylim([1e-5 1]);
        xlabel('SNR por stream [dB]'); ylabel('BER'); title(['Cenario ' names{c}(2:end) ' - ' mname{m}]);
        legend(o.labels, 'Location', 'southwest');
    end
    % --- EVM (mediana sobre realizacoes) e limiares
    for m = 1:2
        figure; hold on; grid on;
        for l = 1:5
            semilogy(snr_db, 100 * median(o.evm(:, :, l, m), 1), [col{l} lst{l} mrk{l}], 'LineWidth', 1.2);
        end
        plot(snr_db, thr(m) * ones(size(snr_db)), 'k:', 'LineWidth', 1.5);
        set(gca, 'YScale', 'log');
        xlabel('SNR por stream [dB]'); ylabel('EVM mediana [%]');
        title(['Cenario ' names{c}(2:end) ' - ' mname{m} ' (limiar 5G: ' num2str(thr(m)) '%)']);
        legend([o.labels {'limiar 5G'}], 'Location', 'northeast');
    end
end
