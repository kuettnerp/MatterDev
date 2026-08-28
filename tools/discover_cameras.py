#!/usr/bin/env python3
"""Identify cameras on the isolated camera segment (see docs/camera-discovery.md)
and print a suggested config/cameras.yaml block.

Usage:
    python tools/discover_cameras.py 192.168.50.0/24 --user admin --password admin

Run this ON THE PI, after wiring the PoE switch into eth0 and confirming
dnsmasq is handing out leases (check /var/lib/misc/dnsmasq.leases).

This never writes config/cameras.yaml directly - it only prints a suggested
block for you to review and paste in yourself.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass

COMMON_RTSP_PATHS = [
    "Streaming/Channels/101",  # Hikvision-style
    "cam/realmonitor?channel=1&subtype=0",  # Dahua-style (also common on generic NVR/DVR boxes)
    "live",
    "11",
    "videoMain",
]


@dataclass
class DiscoveredCamera:
    ip: str
    rtsp_url: str | None = None
    source: str = ""  # "onvif" or "fallback-probe"
    onvif_xaddr: str | None = None


def scan_network(subnet: str) -> list[str]:
    """Find live hosts on `subnet` via `nmap -sn`. Requires nmap installed
    (`sudo apt install nmap`). `arp-scan --localnet` is an equally valid
    lighter-weight alternative if you'd rather use that instead.
    """
    try:
        result = subprocess.run(
            ["nmap", "-sn", subnet], capture_output=True, text=True, timeout=60
        )
    except FileNotFoundError:
        print("error: nmap not found. Install it with `sudo apt install nmap`.", file=sys.stderr)
        return []

    hosts = []
    for line in result.stdout.splitlines():
        if line.startswith("Nmap scan report for"):
            host = line.rsplit(" ", 1)[-1].strip("()")
            hosts.append(host)
    return hosts


def onvif_discover(timeout: float = 3.0) -> list[str]:
    """WS-Discovery probe for ONVIF device service addresses (xaddrs) on the LAN.
    Does not require knowing IPs in advance. Requires the WSDiscovery package.
    """
    try:
        from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
    except ImportError:
        print(
            "warning: WSDiscovery not installed (pip install WSDiscovery); "
            "skipping ONVIF discovery, falling back to RTSP pattern probing.",
            file=sys.stderr,
        )
        return []

    wsd = WSDiscovery()
    wsd.start()
    try:
        services = wsd.searchServices(timeout=timeout)
    finally:
        wsd.stop()

    xaddrs = []
    for service in services:
        xaddrs.extend(service.getXAddrs())
    return xaddrs


def onvif_get_stream_uri(xaddr: str, user: str, password: str) -> str | None:
    """Given an ONVIF device service address, pull its RTSP stream URI via the
    ONVIF media service. Requires onvif-zeep (or its async fork).
    """
    try:
        from urllib.parse import urlparse

        from onvif import ONVIFCamera
    except ImportError:
        print(
            "warning: onvif-zeep not installed (pip install onvif-zeep); "
            "cannot query ONVIF stream URIs.",
            file=sys.stderr,
        )
        return None

    parsed = urlparse(xaddr)
    host = parsed.hostname
    port = parsed.port or 80
    if not host:
        return None

    try:
        camera = ONVIFCamera(host, port, user, password)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        if not profiles:
            return None

        stream_setup = {
            "StreamSetup": {"Stream": "RTP-Unicast", "Transport": {"Protocol": "RTSP"}},
            "ProfileToken": profiles[0].token,
        }
        uri_response = media_service.GetStreamUri(stream_setup)
        return uri_response.Uri
    except Exception as exc:  # ONVIF/SOAP errors vary widely by camera firmware
        print(f"warning: ONVIF query failed for {host}: {exc}", file=sys.stderr)
        return None


def try_common_rtsp_patterns(ip: str, user: str, password: str, port: int = 554) -> str | None:
    """Fallback for hosts with port 554 open but no ONVIF response: try common
    per-vendor RTSP URL patterns, validating each with ffprobe. If the cameras
    were wired to a proprietary NVR/DVR box, that box's own IP is the first
    thing worth trying this against - many expose RTSP even for otherwise
    proprietary camera inputs.
    """
    for path in COMMON_RTSP_PATHS:
        url = f"rtsp://{user}:{password}@{ip}:{port}/{path}"
        if _probe_rtsp_url(url):
            return url
    return None


def _probe_rtsp_url(url: str, timeout_us: int = 3_000_000) -> bool:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-rtsp_transport", "tcp",
                "-i", url,
                "-show_streams",
                "-timeout", str(timeout_us),
                "-loglevel", "error",
            ],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("error: ffprobe not found. Install it with `sudo apt install ffmpeg`.", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        return False


def discover(subnet: str, user: str, password: str) -> list[DiscoveredCamera]:
    print(f"scanning {subnet} for live hosts...")
    hosts = scan_network(subnet)
    print(f"found {len(hosts)} host(s): {', '.join(hosts) or '(none)'}")

    print("probing for ONVIF devices via WS-Discovery...")
    xaddrs = onvif_discover()
    onvif_hosts_by_ip: dict[str, str] = {}
    for xaddr in xaddrs:
        from urllib.parse import urlparse

        host = urlparse(xaddr).hostname
        if host:
            onvif_hosts_by_ip[host] = xaddr

    discovered: list[DiscoveredCamera] = []
    for ip in hosts:
        if ip in onvif_hosts_by_ip:
            xaddr = onvif_hosts_by_ip[ip]
            rtsp_url = onvif_get_stream_uri(xaddr, user, password)
            if rtsp_url:
                discovered.append(DiscoveredCamera(ip=ip, rtsp_url=rtsp_url, source="onvif", onvif_xaddr=xaddr))
                continue

        rtsp_url = try_common_rtsp_patterns(ip, user, password)
        if rtsp_url:
            discovered.append(DiscoveredCamera(ip=ip, rtsp_url=rtsp_url, source="fallback-probe"))

    return discovered


def print_yaml_suggestion(cameras: list[DiscoveredCamera]) -> None:
    if not cameras:
        print(
            "\nNo cameras identified automatically. If these were wired to an NVR/DVR "
            "box rather than being standalone IP cameras, try running this script "
            "against the NVR box's own IP - many expose RTSP for their camera inputs "
            "even when the cameras themselves don't. See docs/camera-discovery.md."
        )
        return

    print("\nSuggested config/cameras.yaml block (review and rename ids/names before saving):\n")
    print("cameras:")
    for i, cam in enumerate(cameras, start=1):
        print(f"  - id: camera_{i}")
        print(f"    name: \"Camera {i} ({cam.ip})\"")
        print(f"    rtsp_url: \"{cam.rtsp_url}\"  # via {cam.source}")
        print("    enabled: true")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subnet", help="Camera segment CIDR, e.g. 192.168.50.0/24")
    parser.add_argument("--user", default="admin", help="Camera username to try (default: admin)")
    parser.add_argument("--password", default="admin", help="Camera password to try (default: admin)")
    args = parser.parse_args()

    cameras = discover(args.subnet, args.user, args.password)
    print_yaml_suggestion(cameras)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
