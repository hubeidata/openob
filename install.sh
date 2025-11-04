#!/bin/bash
# Installer para OpenOB (instala globalmente, sin virtualenv)
# Ejecutar como root: sudo bash install.sh

set -euo pipefail

OPENOB_DIR="/home/ubuntu/openob"
PYTHON_BIN="/usr/bin/python3"
PIP_BIN="/usr/bin/pip3"
SYSTEM_USER="ubuntu"

echo "=== Instalador OpenOB (sin virtualenv): inicio ==="

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: ejecuta este script como root (sudo)."
  exit 1
fi

echo "[1/6] Actualizando paquetes..."
apt-get update -qq
apt-get upgrade -y -qq

echo "[2/6] Instalando dependencias del sistema..."
apt-get install -y --no-install-recommends \
  $PYTHON_BIN $PIP_BIN python3-dev build-essential git \
  gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-alsa \
  libasound2-dev pkg-config libssl-dev ca-certificates curl

echo "[3/6] Asegurando grupo 'audio' y usuario $SYSTEM_USER..."
groupadd -f audio || true
if id -nG "$SYSTEM_USER" 2>/dev/null | grep -qw audio; then
  echo "Usuario $SYSTEM_USER ya pertenece a 'audio'."
else
  usermod -aG audio "$SYSTEM_USER"
  echo "Usuario $SYSTEM_USER añadido a 'audio'."
fi

echo "[4/6] Actualizando pip y herramientas..."
$PIP_BIN install --upgrade pip setuptools wheel

echo "[5/6] Instalando OpenOB globalmente (desde árbol local si existe)..."
if [ -d "$OPENOB_DIR" ]; then
  echo "Repositorio local detectado en $OPENOB_DIR -> instalando en modo editable (system-wide)"
  if [ -f "$OPENOB_DIR/requirements.txt" ]; then
    $PIP_BIN install -r "$OPENOB_DIR/requirements.txt"
  fi
  # Intentar instalación editable; si falla, avisar y usar el binario en el árbol local
  if $PIP_BIN install -e "$OPENOB_DIR"; then
    echo "openob instalado en modo editable."
  else
    echo "Advertencia: pip install -e falló. Se dejará el ejecutable en el árbol local y se creará enlace."
  fi
  # Crear enlace práctico si existe el ejecutable en el árbol
  if [ -x "$OPENOB_DIR/bin/openob" ]; then
    ln -sf "$OPENOB_DIR/bin/openob" /usr/local/bin/openob
  fi
else
  echo "No se detectó repo local. Instalando paquete 'openob' desde PyPI globalmente."
  $PIP_BIN install openob || {
    echo "ERROR: instalación desde PyPI falló."
    exit 1
  }
fi

# Asegurar que /usr/local/bin/openob existe (por si pip creó el script allí)
if [ -x "/usr/local/bin/openob" ]; then
  echo "/usr/local/bin/openob disponible."
else
  echo "Aviso: /usr/local/bin/openob no encontrado/executable. Revisa la instalación."
fi

echo "[6/6] Preparando archivo de entorno para systemd y permisos..."
mkdir -p /etc/openob
chown root:root /etc/openob
chmod 755 /etc/openob

# Si existe la contraseña generada por setup, copiarla en /etc/openob/redis.env (modo 600)
if [ -f /root/redis_password.txt ]; then
  REDIS_PASSWORD="$(cat /root/redis_password.txt)"
  echo "REDIS_PASSWORD=${REDIS_PASSWORD}" > /etc/openob/redis.env
  chmod 600 /etc/openob/redis.env
  chown root:root /etc/openob/redis.env
  echo "Archivo /etc/openob/redis.env creado."
else
  # crear plantilla vacía (modo 600)
  if [ ! -f /etc/openob/redis.env ]; then
    echo "REDIS_PASSWORD=zYWDZxDNBqSogfpurKx6CemmbAgJCTYBLcj/qPrsS7Y=" > /etc/openob/redis.env
    chmod 600 /etc/openob/redis.env
    chown root:root /etc/openob/redis.env
    echo "Plantilla /etc/openob/redis.env creada. Añade la contraseña para systemd."
  fi
fi

echo ""
echo "Instalación completada."
echo "- openob disponible en /usr/local/bin/openob (o enlace al árbol local)."
echo "- Si ejecutas encoder/decoder desde el árbol local, los scripts usarán /home/ubuntu/openob/bin/openob."
echo "- Para ejecutar scripts encoder/decoder como usuario $SYSTEM_USER,"
echo "  exporta REDIS_PASSWORD desde /etc/openob/redis.env:"
echo "    export REDIS_PASSWORD=\"\$(sudo sed -n 's/^REDIS_PASSWORD=//p' /etc/openob/redis.env)\""
echo ""
echo "Sugerencias siguientes:"
echo "- Verifica que el group audio esté activo en la sesión de $SYSTEM_USER: cerrar sesión y volver a entrar o ejecutar 'newgrp audio'."
echo "- Para ejecutar encoder: su - $SYSTEM_USER -c 'export REDIS_PASSWORD=...; /home/ubuntu/openob/start-encoder.sh'"
echo "- Para la unidad systemd del repetidor, asegúrate de que lea /etc/openob/redis.env"
echo ""
echo "=== Instalador OpenOB (sin virtualenv): fin ==="
exit 0