# 📊 Guía de Monitoreo de Tráfico - OpenOB Repeater

## Comandos Básicos para Monitorear el Tráfico

### 🎯 Opción 1: Script Automatizado (Recomendado)
```bash
sudo ./monitor-traffic.sh
```

Opciones disponibles:
- **Opción 1**: iftop interactivo (visual, tiempo real)
- **Opción 2**: tcpdump detallado (muestra cada paquete)
- **Opción 3**: iftop texto (salida simple)
- **Opción 4**: Estadísticas rápidas (resumen de 5 segundos)

---

## 📡 Comandos Manuales de iftop

### 1. Monitorear TODO el tráfico en eno1
```bash
sudo iftop -i eno1 -P -B
```

**Opciones:**
- `-i eno1`: Especifica la interfaz de red
- `-P`: Muestra números de puerto
- `-B`: Muestra velocidad en Bytes (no bits)

### 2. Filtrar SOLO tráfico RTP/RTCP (Recomendado para OpenOB)
```bash
sudo iftop -i eno1 -f "port 5004 or port 5005" -P -B
```

**Opciones adicionales:**
- `-f "port 5004 or port 5005"`: Filtra solo puertos RTP y RTCP
- `-n`: No resolver nombres DNS (más rápido)
- `-N`: No convertir puertos a nombres de servicio

### 3. Monitorear tráfico desde/hacia IPs específicas
```bash
# Solo tráfico del encoder
sudo iftop -i eno1 -f "host 192.168.18.16" -P -B

# Solo tráfico hacia el decoder
sudo iftop -i eno1 -f "host 192.168.18.35" -P -B

# Tráfico entre encoder y decoder via repeater
sudo iftop -i eno1 -f "host 192.168.18.16 or host 192.168.18.35" -P -B
```

### 4. Modo texto (para scripts o logging)
```bash
# Captura 10 segundos y guarda en archivo
sudo iftop -i eno1 -f "port 5004 or port 5005" -P -B -t -s 10 > /tmp/traffic.log
```

**Opciones:**
- `-t`: Modo texto (sin interfaz interactiva)
- `-s 10`: Captura por 10 segundos y termina

---

## 🔍 Comandos tcpdump (Análisis Detallado)

### 1. Ver paquetes RTP en tiempo real
```bash
# Ver todos los paquetes RTP
sudo tcpdump -i eno1 -n port 5004

# Ver solo paquetes entrantes (desde encoder)
sudo tcpdump -i eno1 -n dst port 5004 and src 192.168.18.16

# Ver solo paquetes salientes (hacia decoder)
sudo tcpdump -i eno1 -n src port 5004 and dst 192.168.18.35
```

### 2. Contar paquetes en un intervalo
```bash
# Contar paquetes RTP por 5 segundos
timeout 5 sudo tcpdump -i eno1 -n port 5004 2>/dev/null | wc -l

# Calcular tasa de paquetes
PACKETS=$(timeout 5 sudo tcpdump -i eno1 -n port 5004 2>/dev/null | wc -l)
echo "Tasa: $((PACKETS / 5)) paquetes por segundo"
```

### 3. Capturar y analizar detalles
```bash
# Capturar primeros 100 paquetes con detalles
sudo tcpdump -i eno1 -n -v port 5004 -c 100

# Capturar y guardar para análisis posterior (Wireshark)
sudo tcpdump -i eno1 -w /tmp/rtp_capture.pcap port 5004 or port 5005
```

---

## 📈 Interpretación de Resultados

### iftop - Vista Interactiva

```
┌──────────────────────────────────────────────────────────────────┐
│ 192.168.18.16:58517  => 192.168.18.34:5004    1.2MB  1.1MB  1.0MB│
│ 192.168.18.34:5004   => 192.168.18.35:5004    1.2MB  1.1MB  1.0MB│
└──────────────────────────────────────────────────────────────────┘
```

**Interpretación:**
- **Primera línea**: Encoder → Repeater (entrada)
- **Segunda línea**: Repeater → Decoder (salida)
- **Columnas**: Promedio de 2s, 10s, 40s
- **Valores esperados**: ~1-2 MB/s para audio PCM estéreo 48kHz

### Tasas Esperadas para OpenOB

**Audio PCM 48kHz Estéreo:**
- **Bitrate**: 48000 Hz × 2 canales × 16 bits = 1536 kbps = **192 KB/s**
- **Con overhead RTP/UDP/IP**: ~220-250 KB/s
- **Paquetes por segundo**: ~50 pps (frames de 20ms)

**Indicadores de Problema:**
- ❌ Entrada > 0 pero Salida = 0 → Repeater no está reenviando
- ❌ Entrada = 0 → Encoder no está transmitiendo
- ❌ Tasa muy baja (< 100 KB/s) → Audio con pérdida o codec diferente

---

## 🎮 Controles Interactivos en iftop

Cuando ejecutas `iftop -i eno1`, puedes usar estas teclas:

| Tecla | Función |
|-------|---------|
| `h` | Mostrar ayuda |
| `n` | Toggle resolución de nombres |
| `s` | Toggle mostrar fuente |
| `d` | Toggle mostrar destino |
| `t` | Cambiar modo de visualización |
| `p` | Toggle modo promiscuo |
| `P` | Toggle mostrar puertos |
| `l` | Filtro de visualización |
| `q` | Salir |

---

## 🚀 Ejemplos Prácticos

### Escenario 1: Verificar que el repeater está recibiendo del encoder
```bash
sudo tcpdump -i eno1 -n "dst 192.168.18.34 and port 5004" -c 10
```

**Output esperado:**
```
10 packets captured
...
192.168.18.16.58517 > 192.168.18.34.5004: UDP, length 1200
192.168.18.16.58517 > 192.168.18.34.5004: UDP, length 1200
...
```

### Escenario 2: Verificar que el repeater está enviando al decoder
```bash
sudo tcpdump -i eno1 -n "src 192.168.18.34 and dst 192.168.18.35 and port 5004" -c 10
```

**Output esperado:**
```
10 packets captured
...
192.168.18.34.5004 > 192.168.18.35.5004: UDP, length 1200
192.168.18.34.5004 > 192.168.18.35.5004: UDP, length 1200
...
```

### Escenario 3: Comparar entrada vs salida
```bash
echo "Capturando entrada..."
IN=$(timeout 5 sudo tcpdump -i eno1 -n "dst 192.168.18.34 and port 5004" 2>/dev/null | wc -l)

echo "Capturando salida..."
OUT=$(timeout 5 sudo tcpdump -i eno1 -n "src 192.168.18.34 and dst 192.168.18.35 and port 5004" 2>/dev/null | wc -l)

echo ""
echo "Paquetes entrantes: $IN"
echo "Paquetes salientes: $OUT"
echo "Ratio: $(echo "scale=2; $OUT * 100 / $IN" | bc)%"
```

**Ratio esperado:** ~100% (todos los paquetes se reenvían)

---

## 🔧 Troubleshooting

### Problema: "iftop: found arguments following options"
**Solución:** Usa `-i` antes del nombre de la interfaz:
```bash
# ❌ Incorrecto
sudo iftop eno1

# ✅ Correcto
sudo iftop -i eno1
```

### Problema: "Permission denied"
**Solución:** Ejecuta con `sudo`:
```bash
sudo iftop -i eno1 -P -B
```

### Problema: "No se ve tráfico RTP"
**Verificaciones:**
1. Confirmar que el repeater está corriendo: `ps aux | grep openob`
2. Verificar que los puertos están abiertos: `ss -ulpn | grep 5004`
3. Verificar con tcpdump sin filtro: `sudo tcpdump -i eno1 -n port 5004`

### Problema: "Tráfico muy bajo"
**Posibles causas:**
1. Encoder no está transmitiendo
2. Codec diferente (no PCM)
3. Bitrate reducido
4. Pérdida de paquetes en la red

---

## 📋 Checklist de Verificación

- [ ] Repeater está corriendo (`ps aux | grep openob`)
- [ ] Puerto 5004 está escuchando (`ss -ulpn | grep 5004`)
- [ ] Tráfico entrante desde encoder (`sudo tcpdump -i eno1 dst port 5004`)
- [ ] Tráfico saliente hacia decoder (`sudo tcpdump -i eno1 src port 5004`)
- [ ] Tasas de entrada y salida son similares
- [ ] Bitrate aproximadamente 192-250 KB/s
- [ ] ~50 paquetes por segundo

---

## 📚 Recursos Adicionales

- **Manual de iftop**: `man iftop`
- **Manual de tcpdump**: `man tcpdump`
- **Logs del repeater**: `tail -f /tmp/repeater.log`
- **Verificación del sistema**: `./VERIFICACION_SISTEMA.sh`

---

*Última actualización: 3 de Octubre 2025*
