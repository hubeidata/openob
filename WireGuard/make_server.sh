#!/usr/bin/env bash
# Generate WireGuard server keypair and create a wg0-server.conf in current dir.
# Run this on EC2. Use sudo if you plan to move the conf to /etc/wireguard.

set -euo pipefail
UMASK=${UMASK:-077}
umask "$UMASK"
OUT_DIR="$(pwd)"
SERVER_PRIV="$OUT_DIR/server_private.key"
SERVER_PUB="$OUT_DIR/server_public.key"

if command -v wg >/dev/null 2>&1; then
  echo "wg is installed"
else
  echo "Warning: wireguard tools not found. Install wireguard (apt install wireguard) before enabling interface."
fi

wg genkey | tee "$SERVER_PRIV" | wg pubkey > "$SERVER_PUB"
chmod 600 "$SERVER_PRIV" "$SERVER_PUB"

cat > "$OUT_DIR/wg0-server.conf" <<'EOF'
[Interface]
Address = 10.255.0.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY>
SaveConfig = true
# Add Peer sections after you obtain client public keys

# Example Peer block (replace <CLIENT_PUBKEY> when ready):
#[Peer]
#PublicKey = <CLIENT_PUBKEY>
#AllowedIPs = 10.255.0.2/32
#PersistentKeepalive = 25
EOF

echo "Generated server keys:" 
echo " - $SERVER_PRIV"
echo " - $SERVER_PUB"
echo
echo "Created template: $OUT_DIR/wg0-server.conf"
echo
cat <<USAGE
Next steps (on EC2):
  1) Open UDP 51820 in EC2 Security Group (inbound).
  2) Install wireguard: sudo apt update && sudo apt install -y wireguard
  3) Inspect the generated public key and give it to the Pi (client):
     cat $SERVER_PUB
  4) Edit $OUT_DIR/wg0-server.conf and replace <SERVER_PRIVATE_KEY> with the contents of $SERVER_PRIV (one line).
  5) After you fill client public key(s) in the Peer section, move the file to /etc/wireguard/wg0.conf as root:
     sudo mv $OUT_DIR/wg0-server.conf /etc/wireguard/wg0.conf
     sudo chown root:root /etc/wireguard/wg0.conf
     sudo chmod 600 /etc/wireguard/wg0.conf
  6) Start the tunnel: sudo wg-quick up wg0
  7) Enable on boot: sudo systemctl enable wg-quick@wg0
USAGE

exit 0
