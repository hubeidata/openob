#!/usr/bin/env bash
# Generate WireGuard client keypair and create a wg0-client.conf in current dir.
# Run on the Pi. You must provide SERVER_PUB and SERVER_ENDPOINT (EC2_IP:PORT)

set -euo pipefail
UMASK=${UMASK:-077}
umask "$UMASK"
OUT_DIR="$(pwd)"
CLIENT_PRIV="$OUT_DIR/client_private.key"
CLIENT_PUB="$OUT_DIR/client_public.key"

if [ -z "${SERVER_PUB:-}" ]; then
  read -rp "Paste server public key (wg pubkey from EC2): " SERVER_PUB
fi
if [ -z "${SERVER_ENDPOINT:-}" ]; then
  read -rp "Enter server endpoint (EC2_PUBLIC_IP:51820): " SERVER_ENDPOINT
fi

wg genkey | tee "$CLIENT_PRIV" | wg pubkey > "$CLIENT_PUB"
chmod 600 "$CLIENT_PRIV" "$CLIENT_PUB"

cat > "$OUT_DIR/wg0-client.conf" <<EOF
[Interface]
Address = 10.255.0.2/24
PrivateKey = <CLIENT_PRIVATE_KEY>
DNS = 1.1.1.1

[Peer]
PublicKey = ${SERVER_PUB}
Endpoint = ${SERVER_ENDPOINT}
AllowedIPs = 10.255.0.1/32
PersistentKeepalive = 25
EOF

echo "Generated client keys:"
echo " - $CLIENT_PRIV"
echo " - $CLIENT_PUB"
echo
cat <<USAGE
Next steps (on Pi):
  1) Install wireguard: sudo apt update && sudo apt install -y wireguard
  2) Replace <CLIENT_PRIVATE_KEY> in $OUT_DIR/wg0-client.conf with the contents of $CLIENT_PRIV (one line).
  3) Move the file as root: sudo mv $OUT_DIR/wg0-client.conf /etc/wireguard/wg0.conf
     sudo chown root:root /etc/wireguard/wg0.conf
     sudo chmod 600 /etc/wireguard/wg0.conf
  4) Start the tunnel: sudo wg-quick up wg0
  5) Enable on boot: sudo systemctl enable wg-quick@wg0
  6) Optional routing (to force repeater public IP via wg0):
     sudo ip route add <REPEATER_PUBLIC_IP>/32 dev wg0
     # Example: sudo ip route add 34.204.129.133/32 dev wg0

If you want, copy the client public key and paste it into the server Peer section on EC2.

USAGE

exit 0
