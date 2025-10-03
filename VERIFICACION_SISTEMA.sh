#!/bin/bash

# Script de Verificación del Sistema OpenOB Repeater
# Este script verifica que todos los componentes estén funcionando correctamente

echo "════════════════════════════════════════════════════════════"
echo "  🔍 VERIFICACIÓN DEL SISTEMA OPENOB REPEATER"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar con check mark
check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Verificar procesos OpenOB
echo "─────────────────────────────────────────────────────────────"
echo "1️⃣  Verificando procesos OpenOB..."
echo "─────────────────────────────────────────────────────────────"

ENCODER_COUNT=$(ps aux | grep "bin/openob" | grep "transmitter" | grep -v grep | wc -l)
REPEATER_COUNT=$(ps aux | grep "bin/openob" | grep "repeater" | grep -v grep | wc -l)
DECODER_COUNT=$(ps aux | grep "bin/openob" | grep "receiver" | grep -v grep | wc -l)

if [ $ENCODER_COUNT -gt 0 ]; then
    check_ok "Encoder ejecutándose ($ENCODER_COUNT proceso)"
else
    check_fail "Encoder NO está ejecutándose"
fi

if [ $REPEATER_COUNT -gt 0 ]; then
    check_ok "Repeater ejecutándose ($REPEATER_COUNT proceso)"
else
    check_fail "Repeater NO está ejecutándose"
fi

if [ $DECODER_COUNT -gt 0 ]; then
    check_ok "Decoder ejecutándose ($DECODER_COUNT proceso)"
else
    check_warning "Decoder NO está ejecutándose (puede estar en otra máquina)"
fi

echo ""

# 2. Verificar Redis
echo "─────────────────────────────────────────────────────────────"
echo "2️⃣  Verificando conexión a Redis..."
echo "─────────────────────────────────────────────────────────────"

if redis-cli -h 192.168.18.34 ping > /dev/null 2>&1; then
    check_ok "Redis está accesible en 192.168.18.34"
    
    # Verificar claves del decoder
    DECODER_KEYS=$(redis-cli -h 192.168.18.34 KEYS "openob:transmission:recepteur:*" | wc -l)
    if [ $DECODER_KEYS -gt 0 ]; then
        check_ok "Decoder registrado en Redis ($DECODER_KEYS claves)"
        echo ""
        echo "   Información del decoder:"
        DECODER_HOST=$(redis-cli -h 192.168.18.34 GET "openob:transmission:recepteur:receiver_host")
        DECODER_PORT=$(redis-cli -h 192.168.18.34 GET "openob:transmission:recepteur:port")
        DECODER_TTL=$(redis-cli -h 192.168.18.34 TTL "openob:transmission:recepteur:receiver_host")
        echo "   - Host: $DECODER_HOST"
        echo "   - Port: $DECODER_PORT"
        echo "   - TTL: ${DECODER_TTL}s"
    else
        check_warning "Decoder NO registrado en Redis"
    fi
else
    check_fail "Redis NO accesible en 192.168.18.34"
fi

echo ""

# 3. Verificar puertos abiertos
echo "─────────────────────────────────────────────────────────────"
echo "3️⃣  Verificando puertos RTP/RTCP..."
echo "─────────────────────────────────────────────────────────────"

if ss -ulpn 2>/dev/null | grep -q ":5004"; then
    check_ok "Puerto RTP 5004 en uso"
    ss -ulpn 2>/dev/null | grep ":5004" | head -1 | awk '{print "   PID:", $7}'
else
    check_fail "Puerto RTP 5004 NO está en uso"
fi

if ss -ulpn 2>/dev/null | grep -q ":5005"; then
    check_ok "Puerto RTCP 5005 en uso"
    ss -ulpn 2>/dev/null | grep ":5005" | head -1 | awk '{print "   PID:", $7}'
else
    check_fail "Puerto RTCP 5005 NO está en uso"
fi

echo ""

# 4. Verificar tráfico RTP (requiere sudo)
echo "─────────────────────────────────────────────────────────────"
echo "4️⃣  Verificando tráfico RTP (5 segundos)..."
echo "─────────────────────────────────────────────────────────────"

if [ "$EUID" -ne 0 ]; then
    check_warning "Ejecuta con sudo para ver tráfico de red"
else
    # Capturar tráfico por 5 segundos
    RTP_PACKETS=$(timeout 5 tcpdump -i any -n port 5004 2>/dev/null | wc -l)
    
    if [ $RTP_PACKETS -gt 0 ]; then
        check_ok "Tráfico RTP detectado ($RTP_PACKETS paquetes en 5s)"
        echo "   Tasa aproximada: $((RTP_PACKETS / 5)) pps"
    else
        check_fail "NO se detectó tráfico RTP"
    fi
fi

echo ""

# 5. Verificar permisos de audio
echo "─────────────────────────────────────────────────────────────"
echo "5️⃣  Verificando permisos de audio..."
echo "─────────────────────────────────────────────────────────────"

if groups | grep -q audio; then
    check_ok "Usuario en grupo 'audio'"
else
    check_fail "Usuario NO está en grupo 'audio'"
    echo "   Ejecuta: sudo usermod -aG audio $USER"
fi

# Verificar dispositivos ALSA
if [ -e /dev/snd/pcmC0D0c ]; then
    check_ok "Dispositivo de captura hw:0,0 disponible"
else
    check_warning "Dispositivo de captura hw:0,0 NO disponible"
fi

if [ -e /dev/snd/pcmC1D0p ]; then
    check_ok "Dispositivo de reproducción hw:1,0 disponible"
else
    check_warning "Dispositivo de reproducción hw:1,0 NO disponible"
fi

echo ""

# 6. Verificar versiones de software
echo "─────────────────────────────────────────────────────────────"
echo "6️⃣  Versiones de software..."
echo "─────────────────────────────────────────────────────────────"

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
check_ok "Python: $PYTHON_VERSION"

REDIS_VERSION=$(redis-cli --version 2>&1 | awk '{print $2}')
check_ok "Redis CLI: $REDIS_VERSION"

GST_VERSION=$(gst-launch-1.0 --version 2>&1 | grep version | awk '{print $4}')
check_ok "GStreamer: $GST_VERSION"

echo ""

# 7. Resumen final
echo "════════════════════════════════════════════════════════════"
echo "  📊 RESUMEN"
echo "════════════════════════════════════════════════════════════"

TOTAL_ISSUES=0

if [ $ENCODER_COUNT -eq 0 ]; then ((TOTAL_ISSUES++)); fi
if [ $REPEATER_COUNT -eq 0 ]; then ((TOTAL_ISSUES++)); fi
if ! redis-cli -h 192.168.18.34 ping > /dev/null 2>&1; then ((TOTAL_ISSUES++)); fi

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ Sistema operativo - No se detectaron problemas críticos${NC}"
else
    echo -e "${RED}✗ Se detectaron $TOTAL_ISSUES problema(s) crítico(s)${NC}"
fi

echo ""
echo "Para más información, consulta:"
echo "  - Logs del repeater: ./start-repeater.sh"
echo "  - Manual: cat MANUAL_REPETIDOR.txt"
echo "  - Estado del sistema: cat EXITO_UDP_SOCKETS.md"
echo ""
echo "════════════════════════════════════════════════════════════"
