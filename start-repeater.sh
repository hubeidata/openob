#!/bin/bash
# Script para iniciar el Repeater
# Uso: ./start-repeater.sh (NO usar sudo)

echo "=== Iniciando OpenOB Repeater ==="
echo "IP: 192.168.18.34"
echo "Puerto: 5004"
echo "Jitter buffer: 30ms"
echo "Presiona Ctrl+C para detener"
echo ""

# Verificar que no se esté usando sudo
if [ "$EUID" -eq 0 ]; then 
    echo "❌ ERROR: No ejecutes este script con sudo"
    echo "Uso correcto: ./start-repeater.sh"
    exit 1
fi

exec sg audio -c "/home/server/openob/bin/openob 192.168.18.34 repeater transmission repeater -p 5004 -j 30"
