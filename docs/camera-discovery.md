# Camera discovery

## Known hardware in this setup

Two of the cameras in this system are identified as **LG Innotek RNTW-MN21A**
(label on the camera body: model, serial, and MAC address). This model is
from the LG Innotek line built for subscription home-security services
(Vivint and similar Icontrol-lineage systems), and is commonly sold
alongside a companion **LG Innotek TWFB-R101D "PoE to Wi-Fi Bridge"**
accessory - that bridge exists so a camera can be placed somewhere a wired
run back to the router isn't practical: it takes PoE in on one side and
broadcasts local Wi-Fi on the other, with the *camera* still connecting to
it over a short Ethernet/PoE cable, oblivious to the fact that its uplink is
wireless from there.

**These two cameras are wired with genuine Ethernet cable connections**
(confirmed by inspection), so the Wi-Fi bridge isn't needed here - they
should power up and get an address directly off the PoE switch like any
other PoE camera, same as the general discovery flow below. Two things
specific to this model are still worth knowing:

- If a camera doesn't power up on the switch, it's worth double-checking
  it's actually standard 802.3af/at PoE and not some non-standard voltage -
  the bridge accessory being marketed as a standalone "PoE" device suggests
  it is standard, but this hasn't been confirmed for the camera itself.
- These cameras are reported to serve **RTSP on port 1032** (in addition to
  the standard 554) - `tools/discover_cameras.py` already tries both.
- A commonly reported default credential pattern for this family: username
  `admin`, password = the **last 6 hex digits of the camera's own MAC
  address**, lowercase, no colons (e.g. MAC `30:A9:DE:A4:B7:B4` → password
  `a4b7b4`). The discovery script tries this automatically when it can read
  a MAC address off the `nmap` scan.
- If pattern probing doesn't find the stream, a packet capture while the
  camera boots and connects (`sudo tcpdump -i eth0 -w capture.pcap`, then
  filter for RTSP setup traffic in Wireshark) is a documented fallback
  specifically for this camera family.

The other (turret-style) camera in this system does not have a visible LG
Innotek label and may be a different, standalone Ethernet/PoE IP camera -
treat it separately with the general discovery process below.


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
