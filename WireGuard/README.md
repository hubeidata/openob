WireGuard setup for OpenOB repeater (EC2) and Raspberry Pi (decoder)

Overview

This folder contains scripts and templates to generate WireGuard configs for a server (EC2) and a client (Raspberry Pi). The goal: create a persistent, low-latency tunnel so the EC2 repeater can reliably deliver RTP UDP to the Pi even behind restrictive NAT/CGNAT.

High level steps (quick):

1. On EC2: open UDP/51820 in the Security Group. Install WireGuard.
2. On EC2: run the server script to create server keys and a server config in this directory.
3. On the Pi: install WireGuard and run the client script (you'll need the server public key and EC2 public IP).
4. Copy the generated `wg0.conf` files to `/etc/wireguard/wg0.conf` on each host and `wg-quick up wg0`.
5. Add a route on the Pi so that traffic destined to the repeater (EC2 public IP) goes through `wg0` (optional but recommended).

Files in this folder

- `make_server.sh` — generate server keypair and a `wg0-server.conf` file in this folder. Run on EC2.
- `make_client.sh` — generate client keypair and a `wg0-client.conf` file in this folder. Run on the Pi; it asks for the server public key and endpoint if not provided as env vars.
- `wg0-server.conf.template` — example template showing fields to replace.
- `wg0-client.conf.template` — example template showing fields to replace.

Notes

- Choose a tunnel network not conflicting with your LAN; default in templates: 10.255.0.0/24 (EC2=10.255.0.1, Pi=10.255.0.2).
- Make sure EC2's Security Group allows inbound UDP/51820.
- The scripts generate files under the current directory; you must move them to `/etc/wireguard/wg0.conf` as root to enable the interface (or run `wg-quick` with the full path).
- The scripts do not enable systemd services automatically; after verifying the tunnel you can enable `wg-quick@wg0`.

If you want, I can (A) fill the templates with the actual keys here if you let me generate them and provide the EC2 public IP, or (B) you can run the scripts on each host and paste the produced public keys and I will produce the final confs for you.

Recommended follow-up after tunnel is up

- Start `openob` decoder on the Pi so it registers via the tunnel.
- Check `/tmp/repeater.log` on EC2; it should show the decoder registered as `RTP=10.255.0.2:5004` (or similar).
- On EC2 test sending packets to `10.255.0.2:5004` and verify with `tcpdump` on the Pi.

Security

- Keep the private keys safe (file mode 600). The scripts set restrictive umask for key generation.

