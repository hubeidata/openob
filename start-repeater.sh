#!/bin/bash
# Script para iniciar el Repeater
# Uso: ./start-repeater.sh (NO usar sudo)

echo "=== Iniciando OpenOB Repeater ==="
echo "Config host: 127.0.0.1 (Redis local)"
echo "Puerto RTP: 5004"
echo "Jitter buffer: 30ms"
echo "Presiona Ctrl+C para detener"
echo ""

# Verificar que no se esté usando sudo
if [ "$EUID" -eq 0 ]; then 
    echo "❌ ERROR: No ejecutes este script con sudo"
    echo "Uso correcto: ./start-repeater.sh"
    exit 1
fi

# Ruta al ejecutable local
OPENOB_BIN="/home/ubuntu/openob/bin/openob"

if [ ! -x "$OPENOB_BIN" ]; then
    echo "❌ ERROR: no se encontró el ejecutable local: $OPENOB_BIN"
    echo "Asegúrate de clonar el repo en /home/ubuntu/openob o ajusta OPENOB_BIN en este script."
    exit 1
fi

# Ejecutar con el grupo audio para acceso a dispositivos y exportando PYTHONPATH
# node_name elegido: ec2-repeater; link_name: transmission (igual que en systemd)
CMD="env PYTHONPATH=/home/ubuntu/openob /usr/bin/env python3 $OPENOB_BIN 127.0.0.1 ec2-repeater transmission repeater -p 5004 -j 30"

echo "Ejecutando: $CMD"
exec sg audio -c "$CMD"
