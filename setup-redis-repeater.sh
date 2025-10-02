#!/bin/bash
# Script para configurar Redis en el Repeater (192.168.18.34)
# Ejecutar con: sudo ./setup-redis-repeater.sh

echo "=== Configuración de Redis para OpenOB Repeater ==="
echo ""

# Verificar que se ejecuta con sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERROR: Debes ejecutar este script con sudo"
    echo "Uso: sudo ./setup-redis-repeater.sh"
    exit 1
fi

# Instalar Redis si no está instalado
if ! command -v redis-server &> /dev/null; then
    echo "📦 Instalando Redis..."
    apt-get update
    apt-get install -y redis-server
    echo "✓ Redis instalado"
else
    echo "✓ Redis ya está instalado"
fi

# Backup del archivo de configuración
if [ -f /etc/redis/redis.conf ]; then
    echo "📋 Creando backup de redis.conf..."
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ Backup creado"
fi

# Configurar Redis para aceptar conexiones externas
echo "⚙️  Configurando Redis..."

# Cambiar bind a 0.0.0.0 para aceptar conexiones de cualquier IP
sed -i 's/^bind 127.0.0.1.*/bind 0.0.0.0/' /etc/redis/redis.conf

# Asegurar que protected-mode esté en no
sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf

# Si no existe la línea protected-mode, agregarla
if ! grep -q "^protected-mode" /etc/redis/redis.conf; then
    echo "protected-mode no" >> /etc/redis/redis.conf
fi

echo "✓ Configuración aplicada"

# Reiniciar Redis
echo "🔄 Reiniciando Redis..."
systemctl restart redis-server
systemctl enable redis-server

sleep 2

# Verificar que Redis esté corriendo
if systemctl is-active --quiet redis-server; then
    echo "✓ Redis está corriendo"
    
    # Mostrar IP y puerto
    REDIS_IP=$(hostname -I | awk '{print $1}')
    REDIS_PORT=$(grep "^port" /etc/redis/redis.conf | awk '{print $2}')
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Redis configurado correctamente"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Escuchando en: $REDIS_IP:${REDIS_PORT:-6379}"
    echo "   Aceptando conexiones externas: SÍ"
    echo ""
    echo "Ahora puedes:"
    echo "  1. Iniciar el repeater: ./start-repeater.sh"
    echo "  2. Iniciar el encoder desde 192.168.18.16"
    echo "  3. Iniciar el decoder desde 192.168.18.35"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ ERROR: Redis no se pudo iniciar"
    echo "Revisa los logs: sudo journalctl -u redis-server -n 50"
    exit 1
fi

# Verificar firewall (opcional)
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        echo ""
        echo "⚠️  FIREWALL DETECTADO"
        echo "Si tienes problemas de conexión, permite el puerto 6379:"
        echo "   sudo ufw allow 6379/tcp"
    fi
fi

echo ""
echo "✅ Configuración completa"
