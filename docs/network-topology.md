# Network topology

## Why isolate the cameras

These are old cameras of unknown make, model, and firmware. Rather than
plugging the PoE switch straight into the home router (which would put them
on the same network as every other device in the house, and potentially let
them reach the internet), this project puts the **Raspberry Pi as the only
device bridging the camera segment and the home network** — and configures
it to never actually route between the two. That means:

- The cameras can't be reached from any other device on the home network or
  the internet, at all.
- The cameras can't reach the internet either (no unexpected phone-home
  behavior, no exposure to being pulled into a botnet if the firmware turns
  out to have a known vulnerability).
- The only way to see camera feeds is through the Pi's own web app.

## Layout

```
[cameras] --PoE switch--> [eth0: 192.168.50.1/24] Pi [wlan0: home Wi-Fi] --> [home router] --> internet
```

- `eth0` (camera segment): static IP, DHCP served by `dnsmasq` running on the
  Pi (see `deploy/dnsmasq/camera-segment.conf`), no route out.
- `wlan0` (home network): normal DHCP client of your home router.
- **`net.ipv4.ip_forward` must stay `0`** — this is the actual mechanism that
  keeps `eth0` and `wlan0` unbridged. Raspberry Pi OS ships with this off by
  default; nothing in this project turns it on. Verify with:
  ```
  cat /proc/sys/net/ipv4/ip_forward   # must print 0
  ```
- `deploy/nftables/camera-isolation.nft` adds an explicit firewall rule on
  top of that, dropping `FORWARD` traffic between the two interfaces
  outright, so a future unrelated config change can't silently re-enable
  bridging without you noticing.

## Setting eth0's static IP

Check which network stack your Raspberry Pi OS image uses first:

```
cat /etc/os-release   # look for VERSION_CODENAME
```

**Bookworm and newer (NetworkManager):**

```
sudo nmcli con add type ethernet ifname eth0 con-name camera-segment \
  ipv4.addresses 192.168.50.1/24 ipv4.method manual
sudo nmcli con up camera-segment
```

**Bullseye and older (`dhcpcd`):**

Add to `/etc/dhcpcd.conf`:

```
interface eth0
static ip_address=192.168.50.1/24
nohook wpa_supplicant
```

Then `sudo systemctl restart dhcpcd`.

## Applying the firewall rules

```
sudo apt install nftables
sudo cp deploy/nftables/camera-isolation.nft /etc/nftables.d/camera-isolation.nft
```

Include it from `/etc/nftables.conf` (add `include "/etc/nftables.d/*.nft";`
if not already present), then:

```
sudo systemctl enable --now nftables
sudo nft -f /etc/nftables.conf
```

Double-check your interface names first with `ip link` — adjust the
`eth0`/`wlan0` names in the `.nft` file if your Pi differs.
