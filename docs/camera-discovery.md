# Camera discovery

Since the camera brand/protocol is unknown, use this process once the PoE
switch is wired into the Pi's `eth0` and `dnsmasq` is running (see
[`network-topology.md`](network-topology.md)).

## 1. Confirm cameras are getting IPs

```
cat /var/lib/misc/dnsmasq.leases
```

You should see one line per camera, each with a `192.168.50.x` address. If a
camera doesn't show up here, it may be waiting on a DHCP timeout and falling
back to a hardcoded default IP (common on cheap IP cameras — often something
like `192.168.1.88`) — check the camera's manual/label for a default IP, and
try adding a temporary secondary address in that range to the Pi's `eth0` to
reach it directly and reconfigure it to use DHCP.

## 2. Run the discovery script

```
cd /opt/matterdev  # or wherever you cloned the repo
source .venv/bin/activate
python tools/discover_cameras.py 192.168.50.0/24 --user admin --password admin
```

Adjust `--user`/`--password` if you know the camera's actual credentials —
otherwise the script tries common defaults. This will:

1. `nmap`-scan the subnet for live hosts.
2. Try ONVIF WS-Discovery to identify ONVIF-capable devices directly and pull
   their real RTSP stream URI.
3. For any host that doesn't answer ONVIF, try a handful of common per-vendor
   RTSP URL patterns (Hikvision-, Dahua-style, and generic paths), validating
   each with `ffprobe`.
4. Print a suggested `config/cameras.yaml` block.

## 3. If cameras were wired to a proprietary NVR/DVR box

Many older "security camera systems" have the cameras wired to a central
NVR/DVR box that does the actual encoding, rather than each camera being a
standalone IP device. If the discovery script finds nothing for a camera's
apparent IP, check whether there's a separate NVR/DVR box on the segment
instead — **run the discovery script against the NVR box's own IP**. It's
very common for these boxes to expose RTSP for each of their camera channels
(often via URL patterns like `/cam/realmonitor?channel=1&subtype=0`) even
when the cameras themselves have no IP presence of their own.

## 4. Review and save

Copy the printed block into `config/cameras.yaml` (copy
`config/cameras.example.yaml` first if you haven't already), rename the
`id`/`name` fields to something meaningful, and remove any duplicate or
incorrect entries. Then add a `dhcp-host=` line per camera in
`deploy/dnsmasq/camera-segment.conf` (matching each camera's MAC address) so
its IP stays stable across reboots.
