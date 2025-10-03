#!/bin/bash
# Script para iniciar el Decoder
# Uso: ./start-decoder.sh (NO usar sudo)

REPEATER_IP="192.168.18.34"

echo "=== Iniciando OpenOB Decoder ==="
echo "IP Repeater: $REPEATER_IP"
echo "Output: plughw:0"
echo "Presiona Ctrl+C para detener"
echo ""

# Verificar que no se esté usando sudo
if [ "$EUID" -eq 0 ]; then 
    echo "❌ ERROR: No ejecutes este script con sudo"
    echo "Uso correcto: ./start-decoder.sh"
    exit 1
fi

# Verificar y activar volumen
echo "Verificando volumen de audio..."
sg audio -c "amixer set Master unmute" > /dev/null 2>&1
sg audio -c "amixer set Speaker unmute" > /dev/null 2>&1
echo "✓ Volumen activado"
echo ""

exec sg audio -c "/home/pi/openob/bin/openob $REPEATER_IP decoder transmission rx -a alsa -d hw:1,0"
