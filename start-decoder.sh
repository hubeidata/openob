#!/bin/bash
# Script para iniciar el Decoder
# Uso: ./start-decoder.sh (NO usar sudo)

REPEATER_HOST="${1:-${REPEATER_HOST:-enlace.maxtelperu.com}}"

echo "=== Iniciando OpenOB Decoder ==="
echo "IP Repeater: $REPEATER_IP"
echo "Output: plughw:0"
echo "Presiona Ctrl+C para detener"
echo ""

# Verificar que no se esté usando sudo
if [ "$EUID" -eq 0 ]; then
    echo "❌ ERROR: No ejecutes este script con sudo"
    echo "Uso correcto: ./start-decoder.sh [repeater_host]"
    exit 1
fi

# Leer contraseña de Redis desde la variable de entorno si existe
if [ -z "$REDIS_PASSWORD" ]; then
    echo "⚠️  REDIS_PASSWORD no está definido en el entorno. Por favor exporta REDIS_PASSWORD antes de ejecutar si tu Redis requiere autenticación."
fi

# Verificar y activar volumen
echo "Verificando volumen de audio..."
sg audio -c "amixer set Master unmute" > /dev/null 2>&1
sg audio -c "amixer set Speaker unmute" > /dev/null 2>&1
echo "✓ Volumen activado"
echo ""

# Determinar ejecutable openob en el árbol local
OPENOB_BIN="/home/ubuntu/openob/bin/openob"
if [ ! -x "$OPENOB_BIN" ]; then
    if [ -x "/home/pi/openob/bin/openob" ]; then
        OPENOB_BIN="/home/pi/openob/bin/openob"
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
CMD="$CMD /usr/bin/env python3 $OPENOB_BIN $REPEATER_HOST decoder transmission rx -a alsa -d hw:1,0"

echo "Ejecutando: $CMD"
exec sg audio -c "$CMD"
