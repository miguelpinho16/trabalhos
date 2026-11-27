# CGR 2026/27 - Lab 06 (SDN) - trabalho individual
# Miguel Pinho, n.º 73319 (sem número de grupo: trabalho individual)

"""CGR switch - an os-ken (OpenFlow 1.3) application.

As provided, this application makes every switch behave like a HUB: every packet goes to the
controller (PACKET_IN) and the controller tells the switch to flood it (PACKET_OUT).
Your job is to turn it into the learning switch with a connection limit and TCP statistics
described in STATEMENT.md. Look for the TODO markers.

Run it with:      osken-manager controller/cgr_switch.py
Then, in another terminal:      cgr-net --topo tree,2
"""
import os
import sys
import time

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.lib.packet import ether_types, in_proto, tcp
from os_ken.ofproto import ofproto_v1_3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofhelpers  # noqa: E402  (helpers next to this file)

CONFIG_FILE = os.environ.get(
    "CGR_CONFIG",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "limits.yaml"))

# Cookies: vêm de volta no FLOW_REMOVED e distinguem os tipos de entrada.
COOKIE_LIMIT = 1   # entrada IPv4 (não TCP) que serve para controlar os destinos de um host limitado
COOKIE_TCP = 2     # entrada de uma ligação TCP (um sentido) que serve para as estatísticas

# Prioridades: a mais específica ganha.
PRIO_L2 = 10       # ARP e outros não-IPv4: (porta, MAC origem, MAC destino)
PRIO_IP = 20       # IPv4 não TCP: (IP origem, IP destino, protocolo)
PRIO_TCP = 30      # TCP: (IP origem, porta origem, IP destino, porta destino)


class CGRSwitch(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ofhelpers.load_config(CONFIG_FILE)
        self.idle_timeout = self.config["idle_timeout"]
        self.limits = self.config["limited_hosts"]          # {"10.0.0.1": 2, ...}
        self.tcp_stats_file = self.config["tcp_stats_file"]
        self.logger.info("CGR switch loaded: idle_timeout=%ss, limited hosts %s, TCP stats in %s",
                         self.idle_timeout, self.limits or "none", self.tcp_stats_file)

        # TODO 1: data structures. At least a MAC table per switch:
        #         self.mac_to_port[dpid][mac] = port
        #         and whatever you need for the connection limit and the TCP statistics.

        # Tabela de MACs, uma por switch: mac_to_port[dpid][mac] = porta onde o MAC foi aprendido.
        self.mac_to_port = {}
        # Limite de ligações (global, não por switch, para cada coisa contar uma só vez):
        #   users[(ip_origem, ip_destino)] = nº de entradas vivas dessa origem limitada para esse
        #   destino. O destino está "em uso" enquanto o número for > 0.
        self.users = {}
        # owner[chave] = (dpid, cookie) do switch "dono" da entrada (o primeiro que a viu) e o
        # cookie com que a entrada foi registada. Só a entrada desse switch pede FLOW_REMOVED,
        # para cada coisa ser contada/libertada uma única vez. O cookie fica guardado para que
        # um pacote posterior (não SYN) que reinstale a entrada não lhe troque o tipo.
        #   chave de IPv4 não TCP: ("ip", src, dst, proto)
        #   chave de TCP (um sentido): ("tcp", src, porta_src, dst, porta_dst)
        self.owner = {}

    def destinations_in_use(self, src):
        """Destinos em uso por um host limitado (os que têm entradas vivas)."""
        return {d for (s, d), n in self.users.items() if s == src and n > 0}

    # ------------------------------------------------------------------ switch connects
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.logger.info("switch %016x connected", datapath.id)
        # Entry with priority 0 that sends every unmatched packet to the controller.
        ofhelpers.install_table_miss(datapath)
        # TODO 2 (optional): entries you want in every switch from the start, and resetting
        #         any state you keep about this switch (it may be a new run of cgr-net).

        # Se o cgr-net for reiniciado, os switches voltam com a tabela vazia e as portas podem
        # ser outras: limpa o que o controller sabia (MACs deste switch e o resto do estado).
        self.mac_to_port[datapath.id] = {}
        self.users.clear()
        self.owner.clear()

    # ------------------------------------------------------------------ PACKET_IN
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofp = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        in_port = msg.match["in_port"]
        h = ofhelpers.Headers(msg.data)

        if h.eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return  # ignore link-discovery packets

        # TODO 3: learn the port of the source MAC address on this switch.

        # Garante que existe o dicionário deste switch.
        self.mac_to_port.setdefault(dpid, {})
        # O MAC de origem está na porta por onde o pacote entrou.
        self.mac_to_port[dpid][h.eth.src] = in_port

        # TODO 4: find the output port of the destination MAC address (flood if unknown).

        # Se conhece o MAC destino, usa essa porta; se não, inunda (FLOOD).
        out_port = self.mac_to_port[dpid].get(h.eth.dst, ofp.OFPP_FLOOD)
        known = out_port != ofp.OFPP_FLOOD      # True se o destino é conhecido

        if h.ip:                                # pacote IPv4
            src, dst = h.ip.src, h.ip.dst
            limited = src in self.limits        # a origem é um host limitado?

            # TODO 5: connection limit. If the source is a limited host (self.limits) that is
            #         already communicating with its maximum number of destinations, and this
            #         packet is for a new destination, drop it (do not send a PACKET_OUT).

            # Host limitado + destino novo + já está no máximo de destinos: descarta.
            if limited:
                used = self.destinations_in_use(src)
                if dst not in used and len(used) >= self.limits[src]:
                    return      # sai sem PACKET_OUT e sem instalar entrada

            # TODO 6: when the output port is known, install a flow entry so that the next packets
            #         are forwarded by the switch itself, e.g.
            #   match = parser.OFPMatch(in_port=in_port, eth_src=h.eth.src, eth_dst=h.eth.dst)
            #   ofhelpers.add_flow(datapath, 10, match, [parser.OFPActionOutput(out_port)],
            #                      idle_timeout=self.idle_timeout)
            #         Think about which entries the connection limit and the TCP statistics need
            #         (match fields, priorities, idle timeouts, notify_removal, cookies).

            # TODO 7: TCP statistics. When a TCP connection starts (h.is_tcp_syn()), install an
            #         entry for it in ONE switch, with notify_removal=True, to collect its counters.

            # Três tipos de entrada IPv4, para o switch nunca esconder ao controller o que ele
            # precisa de ver (destinos novos e ligações TCP novas):
            #   TCP     -> uma entrada por ligação e por sentido (IPs + portas), prioridade 30.
            #              Um SYN novo não casa com nenhuma entrada, por isso chega ao controller.
            #   não TCP -> uma entrada por (IP origem, IP destino, protocolo), prioridade 20.
            #              Leva o protocolo no match para não apanhar TCP entre os mesmos hosts.
            if h.tcp:
                key = ("tcp", src, h.tcp.src_port, dst, h.tcp.dst_port)
                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                        ip_proto=in_proto.IPPROTO_TCP,
                                        ipv4_src=src, ipv4_dst=dst,
                                        tcp_src=h.tcp.src_port, tcp_dst=h.tcp.dst_port)
                priority = PRIO_TCP
                # SYN (cliente->servidor) ou SYN+ACK (servidor->cliente): o início de um sentido
                # da ligação. is_tcp_syn() só apanha o SYN puro, por isso uso o has_flags.
                counts = h.tcp.has_flags(tcp.TCP_SYN)
            else:
                key = ("ip", src, dst, h.ip.proto)
                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=h.ip.proto,
                                        ipv4_src=src, ipv4_dst=dst)
                priority = PRIO_IP
                counts = False

            if h.tcp:   # log de diagnóstico: o que o controller viu desta ligação
                self.logger.debug("TCP %s dpid=%d flags=%#x counts=%s known=%s",
                                 key[1:], dpid, h.tcp.bits, counts, known)

            if known:
                # Esta entrada precisa de aviso de expiração se for do limite (origem limitada)
                # ou das estatísticas (início de ligação TCP). O "dono" é o primeiro switch.
                if key not in self.owner and (limited or counts):
                    self.owner[key] = (dpid, COOKIE_TCP if counts else COOKIE_LIMIT)
                    if limited:     # mais uma entrada viva desta origem para este destino
                        self.users[(src, dst)] = self.users.get((src, dst), 0) + 1
                mine = self.owner.get(key)
                notify = mine is not None and mine[0] == dpid
                # Se este switch é o dono, reutiliza o cookie guardado (não o recalcula a partir
                # deste pacote, que pode já não ser um SYN).
                # Nos outros switches o cookie não importa (não avisam), mas fica coerente.
                cookie = mine[1] if notify else (COOKIE_TCP if counts else COOKIE_LIMIT)
                ofhelpers.add_flow(datapath, priority, match, [parser.OFPActionOutput(out_port)],
                                   idle_timeout=self.idle_timeout,
                                   notify_removal=notify, cookie=cookie)
        elif known:
            # Não-IPv4 (ARP, etc.): entrada L2 por (porta, MAC origem, MAC destino), prioridade 10.
            # O eth_type no match evita que apanhe tráfego IPv4, que o controller tem de ver.
            match = parser.OFPMatch(in_port=in_port, eth_type=h.eth.ethertype,
                                    eth_src=h.eth.src, eth_dst=h.eth.dst)
            ofhelpers.add_flow(datapath, PRIO_L2, match, [parser.OFPActionOutput(out_port)],
                               idle_timeout=self.idle_timeout)

        # Forward this packet (as a hub: flood).
        # Envia ESTE pacote (o que gerou o PACKET_IN) pela porta escolhida; as entradas só
        # tratam dos seguintes.
        ofhelpers.send_packet_out(datapath, msg, in_port, out_port)

    # ------------------------------------------------------------------ FLOW_REMOVED
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        msg = ev.msg
        # Received only for entries installed with notify_removal=True.
        # msg.match, msg.cookie, msg.reason (OFPRR_IDLE_TIMEOUT = 0, OFPRR_HARD_TIMEOUT = 1,
        # OFPRR_DELETE = 2), msg.byte_count, msg.packet_count, msg.duration_sec
        self.logger.info("FLOW_REMOVED switch %016x cookie=%d reason=%d bytes=%d match=%s",
                         msg.datapath.id, msg.cookie, msg.reason, msg.byte_count, msg.match)

        if msg.cookie not in (COOKIE_LIMIT, COOKIE_TCP):
            return
        ofp = msg.datapath.ofproto
        m = msg.match
        src, dst = m["ipv4_src"], m["ipv4_dst"]
        if m.get("ip_proto") == in_proto.IPPROTO_TCP:
            key = ("tcp", src, m["tcp_src"], dst, m["tcp_dst"])
        else:
            key = ("ip", src, dst, m.get("ip_proto"))
        self.owner.pop(key, None)       # a entrada acabou: já não há dono

        # TODO 8: free the destination of a limited host when its connection ends.

        # Menos uma entrada viva desta origem limitada para este destino. Quando chega a zero,
        # o destino deixa de estar em uso e o host limitado pode falar com outro.
        if src in self.limits:
            n = self.users.get((src, dst), 0) - 1
            if n > 0:
                self.users[(src, dst)] = n
            else:
                self.users.pop((src, dst), None)

        # TODO 9: write the TCP statistics of a finished connection, e.g.
        #   ofhelpers.append_tcp_stats(self.tcp_stats_file, {"src_ip": ..., "src_port": ...,
        #       "dst_ip": ..., "dst_port": ..., "bytes": ..., "packets": ..., "duration_s": ...})

        if msg.cookie == COOKIE_TCP:
            # duration_sec é o tempo que a ENTRADA existiu. Se expirou por inatividade, inclui
            # os idle_timeout segundos finais sem tráfego, que não fazem parte da ligação.
            duration = msg.duration_sec + msg.duration_nsec / 1e9
            end = time.time()
            if msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
                duration -= msg.idle_timeout
                end -= msg.idle_timeout          # o fim real foi há idle_timeout segundos
            ofhelpers.append_tcp_stats(self.tcp_stats_file, {
                "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end)),
                "src_ip": src, "src_port": m["tcp_src"],
                "dst_ip": dst, "dst_port": m["tcp_dst"],
                "bytes": msg.byte_count, "packets": msg.packet_count,
                "duration_s": round(max(duration, 0), 3)})
