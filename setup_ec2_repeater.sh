#!/bin/bash
# OpenOB Repeater - EC2 Setup Script
# Este script configura automáticamente una instancia EC2 como repetidor OpenOB

set -e

echo "================================================"
echo "OpenOB Repeater - EC2 Setup Script"
echo "================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Este script debe ejecutarse como root (usa sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}[1/6] Actualizando sistema...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

echo -e "${GREEN}[2/6] Instalando Redis...${NC}"
apt-get install -y redis-server

echo -e "${GREEN}[3/6] Instalando GStreamer y dependencias...${NC}"
apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    python3-redis \
    python3-pip

echo -e "${GREEN}[4/6] Configurando Redis para acceso remoto...${NC}"
# Backup de configuración original
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Permitir conexiones remotas
sed -i 's/^bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf

# Configurar seguridad básica
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "requirepass ${REDIS_PASSWORD}" >> /etc/redis/redis.conf

# Reiniciar Redis
systemctl restart redis-server
systemctl enable redis-server

echo -e "${YELLOW}Redis password generado: ${REDIS_PASSWORD}${NC}"
echo -e "${YELLOW}Guarda esta contraseña en un lugar seguro.${NC}"
echo "${REDIS_PASSWORD}" > /root/redis_password.txt
chmod 600 /root/redis_password.txt

echo -e "${GREEN}[5/6] Instalando OpenOB...${NC}"
# Opción 1: desde PyPI (si está disponible)
# pip3 install openob

# Opción 2: desde source (desarrollo)
if [ ! -d "/opt/openob" ]; then
    cd /opt
    git clone https://github.com/JamesHarrison/openob.git || \
    git clone https://github.com/hubeidata/openob.git  # Fork alternativo
    cd openob
    pip3 install -e .
else
    echo "OpenOB ya está instalado en /opt/openob"
fi

echo -e "${GREEN}[6/6] Creando servicio systemd...${NC}"

# Obtener IP pública de la instancia EC2
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

cat > /etc/systemd/system/openob-repeater.service << EOF
[Unit]
Description=OpenOB Repeater Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="GST_DEBUG=2"
ExecStart=/usr/local/bin/openob ${PUBLIC_IP} ec2-repeater transmission repeater -p 5004 -j 30
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable openob-repeater

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Instalación completada exitosamente!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}Configuración:${NC}"
echo "  - IP Pública: ${PUBLIC_IP}"
echo "  - Puerto RTP: 5004 (UDP)"
echo "  - Puerto RTCP: 5005 (UDP)"
echo "  - Puerto Redis: 6379 (TCP)"
echo "  - Redis Password: guardado en /root/redis_password.txt"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo ""
echo "1. Configura el Security Group de AWS para permitir:"
echo "   - TCP 6379 desde IPs de confianza (Redis)"
echo "   - UDP 5004-5005 desde 0.0.0.0/0 (RTP/RTCP)"
echo ""
echo "2. Inicia el servicio:"
echo "   sudo systemctl start openob-repeater"
echo ""
echo "3. Verifica el estado:"
echo "   sudo systemctl status openob-repeater"
echo ""
echo "4. Ver logs en tiempo real:"
echo "   sudo journalctl -u openob-repeater -f"
echo ""
echo -e "${YELLOW}Comandos para los endpoints:${NC}"
echo ""
echo "Encoder:"
echo "  openob ${PUBLIC_IP} encoder transmission tx ${PUBLIC_IP} \\"
echo "    -e pcm -r 48000 -j 60 -a alsa -d hw:0,0"
echo ""
echo "Decoder:"
echo "  openob ${PUBLIC_IP} decoder transmission rx -a alsa -d hw:1,0"
echo ""
echo -e "${GREEN}================================================${NC}"
