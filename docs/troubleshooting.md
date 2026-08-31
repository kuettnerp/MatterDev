# Troubleshooting

## No cameras showing in the web UI

- Check `config/cameras.yaml` exists and has `enabled: true` entries.
- `curl http://127.0.0.1:9997/v3/paths/list` on the Pi — each configured
  camera should appear with `"ready": true`. If a path is missing entirely,
  `deploy/mediamtx/mediamtx.generated.yml` may be stale — check that
  `mediamtx.service`'s `ExecStartPre` (which runs
  `tools/gen_mediamtx_config.py`) actually ran: `journalctl -u mediamtx`.
- If a path exists but `"ready": false`, the RTSP URL is probably wrong or
  the camera dropped off the network — re-run `tools/discover_cameras.py` and
  check `/var/lib/misc/dnsmasq.leases` to confirm the camera's IP hasn't
  changed (add a `dhcp-host=` MAC reservation if it keeps moving).

## Page loads but video won't play

- Open the browser console — hls.js errors show up there.
- Confirm the HLS manifest is reachable directly:
  `curl -sf http://<pi-wlan0-ip>:8888/<camera_id>/index.m3u8`
- Latency of a few seconds is expected with HLS. If that's a problem, see
  the WebRTC note in `config/mediamtx.template.yml` — it's a documented
  future upgrade, not built by default.

## Services won't start

```
systemctl status mediamtx matterdev-web dnsmasq
journalctl -u mediamtx -n 50
journalctl -u matterdev-web -n 50
```

Common causes: `config/cameras.yaml` missing (see
`docs/camera-discovery.md`), the MediaMTX binary not downloaded into
`deploy/mediamtx/mediamtx`, or `.env` missing `PUBLIC_HOST`.

## Verifying isolation

See the "Verification" section of the project plan / `README.md` — in short:
`cat /proc/sys/net/ipv4/ip_forward` must read `0`, and a device plugged into
the PoE switch should get a `192.168.50.x` lease but be unable to reach the
internet or the home network.
