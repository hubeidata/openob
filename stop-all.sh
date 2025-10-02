#!/bin/bash
# Script para detener todos los procesos OpenOB
# Uso: ./stop-all.sh

echo "Deteniendo todos los procesos OpenOB..."
pkill -f "openob.*transmission"

if [ $? -eq 0 ]; then
    echo "✓ OpenOB detenido exitosamente"
else
    echo "✗ No se encontraron procesos OpenOB en ejecución"
fi
