#!/bin/bash
# Script para iniciar el Encoder
# Uso: ./start-encoder.sh [bitrate] (NO usar sudo)
# Ejemplo: ./start-encoder.sh 128

REPEATER_HOST="${2:-${REPEATER_HOST:-enlace.maxtelperu.com}}"
BITRATE="${1:-128}"  # Default 128kbps si no se especifica

echo "=== Iniciando OpenOB Encoder ==="
echo "IP Repeater: $REPEATER_IP"
echo "Bitrate: $BITRATE kbps (Opus)"
echo "Sample rate: 48000 Hz"
echo "Jitter buffer: 60ms"
echo "Input: plughw:0"
echo "Presiona Ctrl+C para detener"
echo ""

# Verificar que no se esté usando sudo
if [ "$EUID" -eq 0 ]; then
    echo "❌ ERROR: No ejecutes este script con sudo"
    echo "Uso correcto: ./start-encoder.sh [bitrate] [repeater_host]"
    exit 1
fi

# Leer contraseña de Redis desde la variable de entorno si existe
if [ -z "$REDIS_PASSWORD" ]; then
    echo "⚠️  REDIS_PASSWORD no está definido en el entorno. Por favor exporta REDIS_PASSWORD antes de ejecutar si tu Redis requiere autenticación."
    echo "Ejemplo: export REDIS_PASSWORD=\"<la_contraseña>\""
    # No salimos automáticamente: el proceso intentará conectar sin contraseña y fallará si Redis la requiere.
fi

# Determinar ejecutable openob en el árbol local
OPENOB_BIN="/home/ubuntu/openob/bin/openob"
if [ ! -x "$OPENOB_BIN" ]; then
    # Fallbacks frecuentes
    if [ -x "/home/server/openob/bin/openob" ]; then
        OPENOB_BIN="/home/server/openob/bin/openob"
    elif [ -x "./bin/openob" ]; then
        OPENOB_BIN="$(pwd)/bin/openob"
    else
        echo "❌ ERROR: no se encontró el ejecutable openob en $OPENOB_BIN ni en los paths alternativos."
        exit 2
    fi
fi

# Construir y ejecutar comando exportando PYTHONPATH y REDIS_PASSWORD
CMD="env PYTHONPATH=/home/ubuntu/openob"
if [ -n "$REDIS_PASSWORD" ]; then
    CMD="$CMD REDIS_PASSWORD=\"$REDIS_PASSWORD\""
fi
CMD="$CMD /usr/bin/env python3 $OPENOB_BIN $REPEATER_HOST encoder transmission tx $REPEATER_HOST -e opus -b $BITRATE -r 48000 -j 60 -a alsa -d plughw:0 -p 5004"

echo "Ejecutando: $CMD"
exec sg audio -c "$CMD"
#openob 192.168.18.34 emetteur transmission tx 192.168.18.34 -e pcm -r 48000 -j 60 -a alsa -d hw:0,0 -p 5004
