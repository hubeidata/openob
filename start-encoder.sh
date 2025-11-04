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



# Determinar ejecutable openob en el árbol local
OPENOB_BIN="/etc/openob/bin/openob"

CMD="$CMD $OPENOB_BIN $REPEATER_HOST encoder transmission tx $REPEATER_HOST -e opus -b $BITRATE -r 48000 -j 60 -a alsa -d plughw:0 -p 5004"

echo "Ejecutando: $CMD"
exec sg audio -c "$CMD"
#openob 192.168.18.34 emetteur transmission tx 192.168.18.34 -e pcm -r 48000 -j 60 -a alsa -d hw:0,0 -p 5004
