#!/bin/bash
# Script para iniciar el Encoder
# Uso: ./start-encoder.sh [bitrate] (NO usar sudo)
# Ejemplo: ./start-encoder.sh 128

REPEATER_IP="192.168.18.34"
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
    echo "Uso correcto: ./start-encoder.sh [bitrate]"
    exit 1
fi

exec sg audio -c "/home/server/openob/bin/openob $REPEATER_IP encoder transmission tx $REPEATER_IP -e opus -b $BITRATE -r 48000 -j 60 -a alsa -d plughw:0 -p 5004"
#openob 192.168.18.34 emetteur transmission tx 192.168.18.34 -e pcm -r 48000 -j 60 -a alsa -d hw:0,0 -p 5004
