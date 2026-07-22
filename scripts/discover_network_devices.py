#!/usr/bin/env python3
"""
Discover likely Aruba/Cisco/FortiGate devices and build inventory CSV.

This script is intended to run from inside your network where the devices are
reachable. It performs lightweight probing (TCP/SSH/HTTP and optional SNMP)
and writes a CSV compatible with aruba_account_maintenance.py.
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import re
import shutil
import socket
import ssl
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set
from urllib.error import URLError
from urllib.request import urlopen


SUPPORTED_PLATFORMS = {"aruba_6300", "cisco_3700", "fortigate"}
SNMP_SYS_DESCR_OID = "1.3.6.1.2.1.1.1.0"


@dataclass
class ProbeResult:
    host: str
    is_alive: bool
    ssh_open: bool
    https_open: bool
    ssh_banner: str = ""
    http_title: str = ""
    snmp_descr: str = ""
    detected_platform: str = ""
    reason: str = ""


def read_baseline_inventory(baseline_csv: Path) -> Dict[str, str]:
    baseline: Dict[str, str] = {}
    if not baseline_csv.exists():
        return baseline
    with baseline_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            host = (row.get("host") or "").strip()
            platform = (row.get("platform") or "").strip().lower()
            if not host:
                continue
            baseline[host] = platform
    return baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan CIDRs and generate network_devices.csv for Aruba/Cisco/FortiGate."
        )
    )
    parser.add_argument(
        "--cidrs",
        required=True,
        help="Comma-separated CIDRs to scan (example: 10.0.10.0/24,10.0.20.0/24).",
    )
    parser.add_argument(
        "--output-csv",
        default="network_devices_discovered.csv",
        help="Output CSV path for supported platforms.",
    )
    parser.add_argument(
        "--unknown-csv",
        default="network_devices_unknown.csv",
        help="Output CSV path for hosts with unknown platform.",
    )
    parser.add_argument(
        "--baseline-csv",
        default="",
        help=(
            "Optional existing inventory CSV (host,platform,...) used to create "
            "delta report (new, changed, missing, rogue)."
        ),
    )
    parser.add_argument(
        "--delta-csv",
        default="network_devices_delta.csv",
        help="Delta report output path when --baseline-csv is supplied.",
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--keep-users", default="admin")
    parser.add_argument("--threads", type=int, default=128)
    parser.add_argument("--connect-timeout", type=float, default=0.8)
    parser.add_argument("--http-timeout", type=float, default=1.5)
    parser.add_argument("--max-hosts", type=int, default=4096)
    parser.add_argument(
        "--require-open-ports",
        default="22,443",
        help="Comma-separated ports used to decide host liveness.",
    )
    parser.add_argument(
        "--snmp-community",
        default="",
        help=(
            "Optional SNMP v2c community for improved fingerprinting. "
            "Requires snmpget installed on scanning host."
        ),
    )
    parser.add_argument(
        "--include-unknown-in-output",
        action="store_true",
        help="Also place unknown platform rows in output CSV (platform=unknown).",
    )
    return parser.parse_args()


def expand_cidrs(cidrs_csv: str, max_hosts: int) -> List[str]:
    hosts: List[str] = []
    cidrs = [item.strip() for item in cidrs_csv.split(",") if item.strip()]
    for cidr in cidrs:
        network = ipaddress.ip_network(cidr, strict=False)
        for host in network.hosts():
            hosts.append(str(host))
            if len(hosts) > max_hosts:
                raise ValueError(
                    f"Host limit exceeded ({max_hosts}). Narrow CIDRs or increase --max-hosts."
                )
    return hosts


def check_tcp_port(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def fetch_ssh_banner(host: str, timeout: float) -> str:
    try:
        with socket.create_connection((host, 22), timeout=timeout) as sock:
            sock.settimeout(timeout)
            data = sock.recv(512)
            return data.decode("utf-8", errors="ignore").strip()
    except OSError:
        return ""


def fetch_https_title(host: str, timeout: float) -> str:
    context = ssl._create_unverified_context()
    try:
        with urlopen(
            f"https://{host}",
            timeout=timeout,
            context=context,
        ) as response:
            body = response.read(8192).decode("utf-8", errors="ignore")
            match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.I | re.S)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip()
            return body[:120].strip()
    except (URLError, OSError, ValueError, ssl.SSLError):
        return ""


def fetch_snmp_sysdescr(host: str, community: str) -> str:
    if not community:
        return ""
    if not shutil.which("snmpget"):
        return ""
    try:
        completed = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                community,
                "-Oqv",
                "-t",
                "1",
                "-r",
                "0",
                host,
                SNMP_SYS_DESCR_OID,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.5,
            check=False,
        )
        value = completed.stdout.strip()
        return value.strip('"')
    except (OSError, subprocess.TimeoutExpired):
        return ""


def detect_platform(ssh_banner: str, http_title: str, snmp_descr: str) -> tuple[str, str]:
    haystack = " | ".join([ssh_banner, http_title, snmp_descr]).lower()

    if any(token in haystack for token in ("fortigate", "fortios", "fortinet")):
        return "fortigate", "forti signature in SSH/HTTP/SNMP"
    if any(token in haystack for token in ("aruba", "aos-cx", "hpe aruba", "procurve")):
        return "aruba_6300", "aruba signature in SSH/HTTP/SNMP"
    if any(token in haystack for token in ("cisco", "ios xe", "ios software")):
        return "cisco_3700", "cisco signature in SSH/HTTP/SNMP"
    return "", "no confident signature"


def probe_host(
    host: str,
    required_ports: Sequence[int],
    connect_timeout: float,
    http_timeout: float,
    snmp_community: str,
) -> ProbeResult:
    open_ports: Set[int] = set()
    for port in required_ports:
        if check_tcp_port(host, port, connect_timeout):
            open_ports.add(port)

    alive = bool(open_ports)
    if not alive:
        return ProbeResult(
            host=host,
            is_alive=False,
            ssh_open=False,
            https_open=False,
            reason="no required ports open",
        )

    ssh_banner = fetch_ssh_banner(host, connect_timeout) if 22 in open_ports else ""
    http_title = fetch_https_title(host, http_timeout) if 443 in open_ports else ""
    snmp_descr = fetch_snmp_sysdescr(host, snmp_community)
    platform, reason = detect_platform(ssh_banner, http_title, snmp_descr)

    return ProbeResult(
        host=host,
        is_alive=True,
        ssh_open=22 in open_ports,
        https_open=443 in open_ports,
        ssh_banner=ssh_banner,
        http_title=http_title,
        snmp_descr=snmp_descr,
        detected_platform=platform,
        reason=reason,
    )


def write_supported_csv(
    output_csv: Path,
    rows: Iterable[ProbeResult],
    username: str,
    port: int,
    keep_users: str,
    include_unknown: bool,
) -> int:
    count = 0
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["host", "platform", "username", "port", "keep_users"],
        )
        writer.writeheader()
        for row in rows:
            platform = row.detected_platform or ("unknown" if include_unknown else "")
            if not platform:
                continue
            writer.writerow(
                {
                    "host": row.host,
                    "platform": platform,
                    "username": username,
                    "port": port,
                    "keep_users": keep_users,
                }
            )
            count += 1
    return count


def write_unknown_csv(unknown_csv: Path, rows: Iterable[ProbeResult]) -> int:
    count = 0
    with unknown_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "host",
                "reason",
                "ssh_open",
                "https_open",
                "ssh_banner",
                "http_title",
                "snmp_descr",
            ],
        )
        writer.writeheader()
        for row in rows:
            if row.detected_platform:
                continue
            writer.writerow(
                {
                    "host": row.host,
                    "reason": row.reason,
                    "ssh_open": row.ssh_open,
                    "https_open": row.https_open,
                    "ssh_banner": row.ssh_banner,
                    "http_title": row.http_title,
                    "snmp_descr": row.snmp_descr,
                }
            )
            count += 1
    return count


def build_delta_rows(
    *,
    discovered: Sequence[ProbeResult],
    baseline: Dict[str, str],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    discovered_by_host = {item.host: item for item in discovered}

    for host, item in discovered_by_host.items():
        baseline_platform = baseline.get(host, "")
        detected_platform = item.detected_platform or "unknown"

        if not baseline_platform:
            status = (
                "NEW_SUPPORTED"
                if item.detected_platform
                else "NEW_ROGUE_UNKNOWN"
            )
            rows.append(
                {
                    "host": host,
                    "status": status,
                    "baseline_platform": "",
                    "detected_platform": detected_platform,
                    "notes": item.reason,
                }
            )
            continue

        if not item.detected_platform:
            rows.append(
                {
                    "host": host,
                    "status": "ROGUE_UNKNOWN",
                    "baseline_platform": baseline_platform,
                    "detected_platform": "unknown",
                    "notes": item.reason,
                }
            )
            continue

        if baseline_platform != item.detected_platform:
            rows.append(
                {
                    "host": host,
                    "status": "PLATFORM_CHANGED",
                    "baseline_platform": baseline_platform,
                    "detected_platform": item.detected_platform,
                    "notes": "Detected platform differs from baseline inventory",
                }
            )
            continue

        rows.append(
            {
                "host": host,
                "status": "KNOWN_SUPPORTED",
                "baseline_platform": baseline_platform,
                "detected_platform": item.detected_platform,
                "notes": "Matches baseline",
            }
        )

    for host, baseline_platform in baseline.items():
        if host in discovered_by_host:
            continue
        rows.append(
            {
                "host": host,
                "status": "MISSING_FROM_SCAN",
                "baseline_platform": baseline_platform,
                "detected_platform": "",
                "notes": "Present in baseline but not seen in current scan",
            }
        )

    def _sort_key(row: Dict[str, str]) -> tuple[int, object]:
        host = row["host"]
        try:
            return (0, ipaddress.ip_address(host))
        except ValueError:
            return (1, host)

    rows.sort(key=_sort_key)
    return rows


def write_delta_csv(delta_csv: Path, rows: Sequence[Dict[str, str]]) -> int:
    with delta_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "host",
                "status",
                "baseline_platform",
                "detected_platform",
                "notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


def parse_required_ports(value: str) -> List[int]:
    ports: List[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        port = int(token)
        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid port: {port}")
        ports.append(port)
    if not ports:
        raise ValueError("At least one required port is needed.")
    return sorted(set(ports))


def main() -> int:
    args = parse_args()

    try:
        required_ports = parse_required_ports(args.require_open_ports)
        hosts = expand_cidrs(args.cidrs, args.max_hosts)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Scanning {len(hosts)} host(s) across {args.cidrs} ...")

    discovered: List[ProbeResult] = []
    with ThreadPoolExecutor(max_workers=max(1, args.threads)) as pool:
        futures = {
            pool.submit(
                probe_host,
                host,
                required_ports,
                args.connect_timeout,
                args.http_timeout,
                args.snmp_community,
            ): host
            for host in hosts
        }
        for future in as_completed(futures):
            result = future.result()
            if result.is_alive:
                discovered.append(result)

    discovered.sort(key=lambda item: ipaddress.ip_address(item.host))
    supported = [item for item in discovered if item.detected_platform in SUPPORTED_PLATFORMS]
    unknown = [item for item in discovered if not item.detected_platform]

    output_csv = Path(args.output_csv)
    unknown_csv = Path(args.unknown_csv)

    supported_count = write_supported_csv(
        output_csv=output_csv,
        rows=discovered,
        username=args.username,
        port=args.port,
        keep_users=args.keep_users,
        include_unknown=args.include_unknown_in_output,
    )
    unknown_count = write_unknown_csv(unknown_csv=unknown_csv, rows=unknown)
    delta_count = 0
    if args.baseline_csv:
        baseline = read_baseline_inventory(Path(args.baseline_csv))
        delta_rows = build_delta_rows(discovered=discovered, baseline=baseline)
        delta_count = write_delta_csv(Path(args.delta_csv), delta_rows)

    print(
        "Done. Alive hosts: {alive}, Supported detected: {supported}, Unknown: {unknown}".format(
            alive=len(discovered),
            supported=len(supported),
            unknown=len(unknown),
        )
    )
    print(f"Wrote supported inventory: {output_csv} ({supported_count} row(s))")
    print(f"Wrote unknown review file: {unknown_csv} ({unknown_count} row(s))")
    if args.baseline_csv:
        print(
            f"Wrote delta report: {args.delta_csv} ({delta_count} row(s)) "
            f"using baseline {args.baseline_csv}"
        )
    if args.snmp_community and not shutil.which("snmpget"):
        print(
            "NOTE: snmpget not found; SNMP fingerprinting skipped.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
