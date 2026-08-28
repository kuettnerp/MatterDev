# MatterDev — LAN-only camera viewer

A small, self-hosted web app for viewing old Ethernet security cameras over
your home network — nothing exposed to the internet. Runs on a Raspberry Pi
that sits between an isolated PoE camera segment and your home Wi-Fi, so the
cameras are reachable *only* through this app.

## How it works

- Cameras plug into a PoE switch that uplinks into the Pi's Ethernet port —
  a separate, isolated network segment, not your home router.
- The Pi joins your home Wi-Fi separately, and never routes traffic between
  the two networks.
- [MediaMTX](https://github.com/bluenviron/mediamtx) pulls each camera's RTSP
  stream and republishes it as HLS, which a small FastAPI app serves in a
  simple grid UI (built with `hls.js`, vendored locally).

See [`docs/network-topology.md`](docs/network-topology.md) for the full
rationale and diagram.

## Setup

Start with [`SETUP.md`](SETUP.md) — it walks through hardware wiring,
network isolation, camera discovery, and installing the services.

## Repo layout

```
app/        FastAPI application (config loading, routes, models)
templates/  Jinja2 templates for the grid UI
static/     CSS/JS, including vendored hls.js
config/     cameras.yaml (your cameras, gitignored) + MediaMTX base template
tools/      discover_cameras.py, gen_mediamtx_config.py
deploy/     systemd units, dnsmasq config, nftables rules
docs/       hardware setup, network topology, camera discovery, troubleshooting
tests/      pytest tests for config loading and routes
```

## Local development (without real cameras)

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp config/cameras.example.yaml config/cameras.yaml   # edit rtsp_url as needed
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload
```

The page will render even without MediaMTX/real cameras running — the video
tiles just won't have anything to play until a real HLS stream is reachable
at the configured URLs. Run the test suite with `.venv/bin/pytest`.

## Verifying the LAN-only / isolation guarantees

1. On the Pi: `curl http://127.0.0.1:9997/v3/paths/list` — each camera path
   shows `"ready": true`.
2. From a home Wi-Fi machine: `curl -sf http://<pi-wlan0-ip>:8888/<camera_id>/index.m3u8`
   returns a valid HLS playlist.
3. `curl http://<pi-wlan0-ip>:8000/` returns 200; `/healthz` returns `ok`.
4. Open `http://<pi-wlan0-ip>:8000` in a browser on the home Wi-Fi and
   confirm video actually plays.
5. **Isolation check**: `cat /proc/sys/net/ipv4/ip_forward` on the Pi must
   read `0`. Temporarily plug a laptop into the PoE switch in place of a
   camera — it should get a `192.168.50.x` DHCP lease but be unable to ping
   the internet or the home router.
6. From a device off the home Wi-Fi entirely (e.g. cellular hotspot), confirm
   `http://<home-public-ip>:8000` and `:8888` fail/time out, and that the
   router admin UI has no port-forward/UPnP entries for the Pi.
7. `systemctl status mediamtx matterdev-web dnsmasq` — kill one and confirm
   it auto-restarts.

## Future ideas (not built yet)

- WebRTC output from MediaMTX for sub-second latency (config flag away, see
  `config/mediamtx.template.yml`).
- Recording to disk (MediaMTX supports this natively).
- Motion/object detection.
- Possible eventual Matter/smart-home integration.
