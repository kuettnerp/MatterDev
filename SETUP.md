# Setup

Full walkthrough, in order. Details for each step link out to the relevant
doc.

1. **Wire the hardware.** PoE switch → Pi's `eth0`; Pi's `wlan0` → home Wi-Fi.
   See [`docs/hardware-setup.md`](docs/hardware-setup.md).

2. **Set up the isolated camera segment.** Static IP on `eth0`, `dnsmasq` for
   camera DHCP, `nftables` isolation rules. See
   [`docs/network-topology.md`](docs/network-topology.md).

3. **Clone this repo onto the Pi** (e.g. to `/opt/matterdev`) and set up Python:

   ```
   sudo mkdir -p /opt/matterdev && sudo chown $USER /opt/matterdev
   git clone <this-repo-url> /opt/matterdev
   cd /opt/matterdev
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

4. **Discover your cameras** and fill in `config/cameras.yaml`. See
   [`docs/camera-discovery.md`](docs/camera-discovery.md).

   ```
   cp config/cameras.example.yaml config/cameras.yaml
   # edit config/cameras.yaml with the cameras discover_cameras.py finds
   ```

5. **Download the MediaMTX binary** for the Pi's architecture into
   `deploy/mediamtx/` (not committed to the repo):

   ```
   uname -m   # armv7l -> arm7 build; aarch64 -> arm64 build
   ```

   Grab the matching release tarball from the
   [MediaMTX releases page](https://github.com/bluenviron/mediamtx/releases),
   extract it, and place the `mediamtx` binary at `deploy/mediamtx/mediamtx`
   (`chmod +x` it).

6. **Set up `.env`:**

   ```
   cp .env.example .env
   # edit .env - set PUBLIC_HOST to the Pi's wlan0 IP (`hostname -I`)
   ```

7. **Install the systemd services:**

   ```
   sudo cp deploy/systemd/*.service /etc/systemd/system/
   sudo useradd -r -s /usr/sbin/nologin matterdev || true
   sudo chown -R matterdev:matterdev /opt/matterdev
   sudo systemctl daemon-reload
   sudo systemctl enable --now mediamtx matterdev-web
   ```

8. **Open the app** from any device on your home Wi-Fi:
   `http://<pi-wlan0-ip>:8000`

See [`docs/troubleshooting.md`](docs/troubleshooting.md) if something isn't
working, and the Verification section of `README.md` for how to confirm the
camera segment is actually isolated.
