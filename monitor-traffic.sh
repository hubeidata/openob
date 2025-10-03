#!/bin/bash

# Script para monitorear el tráfico de red del repeater OpenOB
# Muestra el tráfico RTP/RTCP en tiempo real

echo "════════════════════════════════════════════════════════════"
echo "  📊 MONITOR DE TRÁFICO OPENOB REPEATER"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Este script mostrará el tráfico de red en la interfaz eno1"
echo "relacionado con los puertos RTP (5004) y RTCP (5005)"
echo ""
echo "Presiona Ctrl+C para salir"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Verificar si tiene permisos de root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Este script requiere permisos de root para capturar tráfico"
    echo "   Ejecuta: sudo ./monitor-traffic.sh"
    exit 1
fi

# Opción 1: Usar iftop con filtro de puertos
echo "Selecciona el modo de monitoreo:"
echo ""
echo "1) iftop - Interfaz visual interactiva (recomendado)"
echo "2) tcpdump - Captura de paquetes detallada"
echo "3) iftop texto - Salida de texto simple"
echo "4) Estadísticas rápidas (5 segundos)"
echo ""
read -p "Opción [1-4]: " OPTION

case $OPTION in
    1)
        echo ""
        echo "Iniciando iftop en modo interactivo..."
        echo "Mostrando tráfico en puertos 5004 y 5005"
        echo ""
        sleep 2
        
        # iftop con filtro para puertos RTP/RTCP
        iftop -i eno1 -f "port 5004 or port 5005" -P -B
        ;;
    
    2)
        echo ""
        echo "Iniciando tcpdump para puertos RTP/RTCP..."
        echo "Presiona Ctrl+C para detener"
        echo ""
        sleep 2
        
        tcpdump -i eno1 -n "port 5004 or port 5005" -c 100
        ;;
    
    3)
        echo ""
        echo "Capturando tráfico por 10 segundos..."
        echo ""
        
        iftop -i eno1 -f "port 5004 or port 5005" -P -B -t -s 10
        ;;
    
    4)
        echo ""
        echo "Capturando estadísticas por 5 segundos..."
        echo ""
        
        # Capturar paquetes RTP entrantes (desde encoder)
        RTP_IN=$(timeout 5 tcpdump -i eno1 -n "dst port 5004 and src 192.168.18.16" 2>/dev/null | wc -l)
        
        # Capturar paquetes RTP salientes (hacia decoder)
        RTP_OUT=$(timeout 5 tcpdump -i eno1 -n "src port 5004 and dst 192.168.18.35" 2>/dev/null | wc -l)
        
        echo "════════════════════════════════════════════════════════════"
        echo "  📊 ESTADÍSTICAS DE TRÁFICO (5 segundos)"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        echo "🎤 Encoder → Repeater (RTP entrante):"
        echo "   Paquetes: $RTP_IN"
        echo "   Tasa: $((RTP_IN / 5)) pps"
        echo ""
        echo "📡 Repeater → Decoder (RTP saliente):"
        echo "   Paquetes: $RTP_OUT"
        echo "   Tasa: $((RTP_OUT / 5)) pps"
        echo ""
        
        if [ $RTP_IN -gt 0 ] && [ $RTP_OUT -gt 0 ]; then
            echo "✅ Sistema funcionando correctamente"
            echo "   Ratio de forwarding: $(echo "scale=2; $RTP_OUT * 100 / $RTP_IN" | bc)%"
        elif [ $RTP_IN -gt 0 ] && [ $RTP_OUT -eq 0 ]; then
            echo "⚠️  Encoder enviando pero decoder NO recibiendo"
        elif [ $RTP_IN -eq 0 ]; then
            echo "❌ NO se detecta tráfico desde el encoder"
        fi
        
        echo ""
        echo "════════════════════════════════════════════════════════════"
        ;;
    
    *)
        echo "Opción inválida"
        exit 1
        ;;
esac
