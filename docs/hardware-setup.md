# Hardware setup

## What you need

- The old Ethernet security cameras (PoE-powered, per camera — verify this; if
  a camera has its own power brick, it doesn't need a PoE switch port for power,
  just a data connection to a switch/router port).
- A PoE switch with enough ports for all cameras plus one uplink port.
- Raspberry Pi 3B, with its onboard Ethernet and Wi-Fi both available.

## Wiring

1. Connect each camera to a PoE port on the switch.
2. Connect the switch's **uplink port directly to the Pi's Ethernet port (`eth0`)** —
   not the home router. This is the isolated camera segment; see
   [`network-topology.md`](network-topology.md) for why.
3. Connect the Pi to your home Wi-Fi via `wlan0` (`raspi-config` or
   `nmcli device wifi connect <ssid> --ask` depending on your OS version).
4. **Do not** configure port forwarding, UPnP, or a DMZ entry on your home
   router for the Pi's `wlan0` IP or for any of these ports. The whole point
   of this project is that it stays LAN-only.

## Raspberry Pi 3B limitations to keep in mind

- **100 Mbps Ethernet** (USB-bus-shared, not Gigabit). This is now the ingest
  path for every camera stream. Fine for a handful of compressed H.264
  streams (a few Mbps each), but it's the first thing to hit a ceiling if you
  add many more cameras or higher resolutions later. If that happens, the
  fix is a Pi 4/5, or a USB3-to-Gigabit-Ethernet adapter on the 3B.
- **1 GB RAM, quad-core Cortex-A53.** MediaMTX (stream-copy, no transcoding)
  and FastAPI are both light enough for this — the design deliberately avoids
  ever transcoding video on the Pi.
- **2.4 GHz-only Wi-Fi.** This is the path from the Pi to every browser
  viewing the app. Fine for a few concurrent viewers of compressed streams;
  if you regularly have several people viewing at once and it feels sluggish,
  a wired uplink for the Pi (in place of Wi-Fi) is the fix.
- Boot from a good SD card, or a USB SSD if you have one — this is meant to
  run as an always-on appliance, and a worn SD card is the most common cause
  of a Pi "randomly" failing.
