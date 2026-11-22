#!/usr/bin/env bash
# Lab 04 - Parte C: comandos a correr em netauto (/root/cgr). Nada de CLI nos routers.
set -e
cd /root/cgr

echo "== C1: mudança de pedido (intent já tem as 8 redes e o /21) =="
./apply_intent.py intent/lab04.yml --check
./apply_intent.py intent/lab04.yml --restconf --diff      # só R2 deve mudar
./apply_intent.py intent/lab04.yml --restconf
./scripts/check_bgp.py                                    # tem de passar sem alterações

echo "== C2: falha do link R3-R4 (ESCREVE ANTES A PREVISÃO) =="
./restconf.py R3 patch interface=swp3 '{"cgr-device:interface":[{"name":"swp3","enabled":false}]}'
sleep 40                                                  # hold-time do BGP / link-down
./restconf.py R4 get state/bgp-neighbor --content nonconfig
./restconf.py R4 get state/route --content nonconfig | grep -A4 '10.20.0.0/21'
./restconf.py R2 get state/route --content nonconfig | grep -A4 '172.16.0.0/20'
./scripts/check_bgp.py || true                            # R3-R4 em baixo: a falhar é esperado (req 6/9)
./restconf.py R3 patch interface=swp3 '{"cgr-device:interface":[{"name":"swp3","enabled":true}]}'
sleep 40
./scripts/check_bgp.py

echo "== C3: prepend em R3 (acrescenta ao intent, em R3, no vizinho 192.168.34.2:  as-path-prepend-out: 3) =="
# editar intent/lab04.yml:   - {address: 192.168.34.2, remote-as: 64600, ..., as-path-prepend-out: 3}
# ./apply_intent.py intent/lab04.yml --restconf
# ./restconf.py R4 get state/route --content nonconfig | grep -A4 '10.20.0.0/21'   # continua via R3 (192.168.34.1)
# depois REMOVE a linha e volta a fazer push para deixar o intent final limpo
