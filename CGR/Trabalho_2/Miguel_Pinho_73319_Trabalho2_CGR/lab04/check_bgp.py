#!/usr/bin/env python3
"""
check_bgp.py - check the Lab 04 requirements by reading the routers' state over RESTCONF.

    ./scripts/check_bgp.py            run all checks, exit code 0 only if all pass
    ./scripts/check_bgp.py --no-ssh   skip req 11 (ping/traceroute over SSH)

Idea: the script does NOT trust the intent file. It reads what the routers really have
(state/route, state/ospf-neighbor, state/bgp-neighbor, state/interface, plus the configuration
of the ospf and bgp containers) and compares it with what each requirement demands.
The summaries are DISCOVERED from the routers (R2's / R5's aggregate) and compared with the
smallest prefix that covers their loopbacks, so the same script passes before and after the
Part C change (4 -> 8 networks, /22 -> /21) without being edited.

Numbers = requirements of the statement:
  1 addressing       2/3 OSPF area 0 (Bank / Provider)   4 AS numbers      5 eBGP links not in OSPF
  6 iBGP full mesh   7 Bank announces only the summary    8 Provider announces only the summary
  9 R4 prefers R3    10 Bank prefers R1                   11 ping / traceroute R2 <-> R5
"""
import ipaddress
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # /root/cgr
from cgrlib import Device, load_inventory      # noqa: E402
from restconf import Restconf                  # noqa: E402

inv = load_inventory()
results = []
BANK, PROV = ["R1", "R2", "R3"], ["R4", "R5", "R6"]
ALL = BANK + PROV
ASN = {r: 65500 for r in BANK} | {r: 64600 for r in PROV}
LOOP = {"R1": "10.1.1.1", "R2": "10.2.2.2", "R3": "10.3.3.3",
        "R4": "10.4.4.4", "R5": "10.5.5.5", "R6": "10.6.6.6"}
EBGP_LINKS = ["192.168.14.0/30", "192.168.34.0/30"]
EBGP_PORTS = {"R1": ["swp1"], "R3": ["swp3"], "R4": ["swp1", "swp3"]}   # ports of the eBGP links

# requirement 1: addressing of the statement (interface -> addresses)
ADDR = {
    "R1": ["10.1.1.1/24", "192.168.14.1/30", "10.1.102.1/29", "10.1.103.1/29"],
    "R2": ["10.2.2.2/24", "10.20.0.1/24", "10.20.1.1/24", "10.20.2.1/24", "10.20.3.1/24",
           "10.1.102.2/29", "10.1.203.2/29"],
    "R3": ["10.3.3.3/24", "10.1.103.3/29", "192.168.34.1/30", "10.1.203.3/29"],
    "R4": ["10.4.4.4/24", "192.168.14.2/30", "10.1.45.4/29", "192.168.34.2/30", "10.1.46.4/29"],
    "R5": ["10.5.5.5/24", "172.16.0.1/22", "172.16.4.1/22", "172.16.8.1/22", "172.16.12.1/22",
           "10.1.56.5/29", "10.1.45.5/29"],
    "R6": ["10.6.6.6/24", "10.1.56.6/29", "10.1.46.6/29"],
}
# requirement 6: number of BGP peers of each router (iBGP full mesh + eBGP links)
PEERS = {"R1": 3, "R2": 2, "R3": 3, "R4": 4, "R5": 2, "R6": 2}
# requirement 2/3/5: number of OSPF neighbours (only the internal links)
OSPF_NBRS = {"R1": 2, "R2": 2, "R3": 2, "R4": 2, "R5": 2, "R6": 2}

_rc = {}


def rc(router):
    if router not in _rc:
        _rc[router] = Restconf(inv[router]["host"])
    return _rc[router]


def state(router, what):
    """GET .../cgr-device:device/state/<what> on a router; returns a list of entries."""
    data = rc(router).get(f"state/{what}", content="nonconfig")
    return data.get(f"cgr-device:{what}", [])


def config(router, what):
    """The configuration container (ospf / bgp) of a router, as a dict ({} if absent)."""
    try:
        data = rc(router).get(what, content="config")
    except Exception:       # noqa: BLE001 - e.g. 404 when the container does not exist
        return {}
    return data.get(f"cgr-device:{what}", {})


def routes(router):
    """{prefix: (protocol, [next hops])} - the routing table."""
    return {r["prefix"]: (r.get("protocol", ""), r.get("next-hop", [])) for r in state(router, "route")}


def bgp_routes(router):
    return {p: nh for p, (proto, nh) in routes(router).items() if proto == "bgp"}


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def summary_of(prefixes):
    """The smallest single prefix that covers all the prefixes."""
    nets = [ipaddress.ip_network(p, strict=False) for p in prefixes]
    sup = nets[0]
    while not all(n.subnet_of(sup) for n in nets):
        sup = sup.supernet()
    return str(sup)


def discover(router, base):
    """(aggregate configured on router, the loopback networks it must cover) for 'base' (a /16)."""
    base = ipaddress.ip_network(base)
    nets = set()
    for i in state(router, "interface"):
        for a in i.get("address", []):
            n = ipaddress.ip_interface(a).network
            if i["name"] == "lo" and n.subnet_of(base):
                nets.add(str(n))
    aggs = [a["prefix"] for a in config(router, "bgp").get("aggregate", [])]
    return aggs, sorted(nets)


# ------------------------------------------------------------------ requirement 1
for r in ALL:
    have = {a for i in state(r, "interface") for a in i.get("address", [])}
    missing = [a for a in ADDR[r] if a not in have]
    check(f"req 1  {r} addresses of the statement", not missing,
          f"missing: {missing}" if missing else f"{len(ADDR[r])} addresses")

# ------------------------------------------------------------------ requirements 2, 3, 5 (OSPF)
for r in ALL:
    cfg = config(r, "ospf")
    areas = {str(i.get("area")) for i in cfg.get("interface", [])}
    which = "2" if r in BANK else "3"
    check(f"req {which}  {r} OSPF: a single area, area 0", areas == {"0"}, f"areas {sorted(areas)}")
    nbrs = state(r, "ospf-neighbor")
    not_full = [n["interface"] for n in nbrs if not str(n.get("state", "")).startswith("Full")]
    check(f"req {which}  {r} OSPF neighbours Full", len(nbrs) == OSPF_NBRS[r] and not not_full,
          f"{len(nbrs)}/{OSPF_NBRS[r]} neighbours" + (f", not Full: {not_full}" if not_full else ""))
    ospf_ifs = {i.get("name") for i in cfg.get("interface", [])}
    bad = [p for p in EBGP_PORTS.get(r, []) if p in ospf_ifs]
    nbr_on_ebgp = [n["interface"] for n in nbrs if n["interface"] in EBGP_PORTS.get(r, [])]
    check(f"req 5  {r} eBGP link not in OSPF", not bad and not nbr_on_ebgp,
          f"in OSPF: {bad + nbr_on_ebgp}" if bad or nbr_on_ebgp else "")
    ospf_rt = [p for p, (proto, _) in routes(r).items() if proto == "ospf"]
    leak = [p for p in ospf_rt if any(ipaddress.ip_network(p).subnet_of(ipaddress.ip_network(e))
                                      or ipaddress.ip_network(e).subnet_of(ipaddress.ip_network(p))
                                      for e in EBGP_LINKS)]
    check(f"req 5  {r} no OSPF route for the eBGP /30s", not leak, f"{leak}" if leak else "")

# ------------------------------------------------------------------ requirements 4 and 6 (BGP)
for r in ALL:
    cfg = config(r, "bgp")
    check(f"req 4  {r} runs BGP AS {ASN[r]}", cfg.get("asn") == ASN[r], f"asn {cfg.get('asn')}")
    peers = state(r, "bgp-neighbor")
    down = [p["address"] for p in peers if p.get("state") != "Established"]
    check(f"req 6  {r} BGP sessions Established", len(peers) == PEERS[r] and not down,
          f"{len(peers)}/{PEERS[r]} peers" + (f", not established: {down}" if down else ""))
    same = {LOOP[x] for x in (BANK if r in BANK else PROV) if x != r}
    ibgp = {p["address"] for p in peers if p.get("remote-as") == ASN[r]}
    check(f"req 6  {r} full iBGP mesh (to the loopbacks)", ibgp == same,
          f"iBGP peers {sorted(ibgp)}" if ibgp != same else "")

# ------------------------------------------------------------------ requirements 7 and 8 (summaries)
bank_aggs, bank_nets = discover("R2", "10.20.0.0/16")
prov_aggs, prov_nets = discover("R5", "172.16.0.0/16")
bank_agg = summary_of(bank_nets) if bank_nets else None
prov_agg = summary_of(prov_nets) if prov_nets else None
check("req 7  R2 has ONE aggregate = smallest summary of Lo200+",
      bank_aggs == [bank_agg], f"configured {bank_aggs}, expected {bank_agg} for {len(bank_nets)} networks")
check("req 8  R5 has ONE aggregate = smallest summary of Lo0/4/8/12",
      prov_aggs == [prov_agg], f"configured {prov_aggs}, expected {prov_agg} for {len(prov_nets)} networks")
for r in ALL:
    seen = bgp_routes(r)
    # BGP routes the router has: only the two summaries (the specifics must be suppressed)
    extra = sorted(set(seen) - {bank_agg, prov_agg})
    check(f"req 7/8  {r} BGP table: only the summaries, no specifics", not extra,
          f"extra BGP routes: {extra}" if extra else f"BGP routes {sorted(seen)}")
for r in PROV:
    check(f"req 7  {r} learns the Bank summary {bank_agg}", bank_agg in bgp_routes(r))
for r in BANK:
    check(f"req 8  {r} learns the Provider summary {prov_agg}", prov_agg in bgp_routes(r))

# ------------------------------------------------------------------ requirement 9 (R4 -> Bank via R3)
nh = bgp_routes("R4").get(bank_agg, [])
check("req 9  R4 reaches the Bank summary through R3 (192.168.34.1)", nh == ["192.168.34.1"], f"next hop {nh}")

# ------------------------------------------------------------------ requirement 10 (Bank -> Provider via R1)
# R1: directly over the eBGP link.  R2 and R3 (iBGP): next hop = R1 (loopback or the link to R1).
EXIT_R1 = {"R1": {"192.168.14.2"}, "R2": {"10.1.1.1", "10.1.102.1"}, "R3": {"10.1.1.1", "10.1.103.1"}}
for r in BANK:
    nh = set(bgp_routes(r).get(prov_agg, []))
    check(f"req 10 {r} exits to the Provider through R1", nh and nh <= EXIT_R1[r], f"next hop {sorted(nh)}")

# ------------------------------------------------------------------ requirement 11 (ping / traceroute)
if "--no-ssh" not in sys.argv:
    src2, dst5 = "10.20.0.1", "172.16.4.1"
    tests = [("R2", src2, dst5), ("R5", dst5, src2)]
    for router, src, dst in tests:
        try:
            with Device(inv[router]) as d:
                _, ping, _ = d.exec(f"sudo ping -c 3 -W 2 -I {src} {dst}")
                _, trace, _ = d.exec(f"sudo traceroute -n -w 2 -m 8 -s {src} {dst}")
        except Exception as e:      # noqa: BLE001
            check(f"req 11 {router} ping/traceroute {src} -> {dst}", False, f"SSH error: {e}")
            continue
        ok = " 0% packet loss" in ping
        check(f"req 11 ping {router} -I {src} -> {dst}", ok, ping.strip().splitlines()[-2] if ok else "no reply")
        hops = [l.split()[1] for l in trace.splitlines()[1:] if len(l.split()) > 1 and l.split()[1] != "*"]
        check(f"req 11 traceroute {router} -> {dst} reaches the destination", dst in hops,
              "path: " + " > ".join(hops))

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
