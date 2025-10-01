# Ejemplos Prácticos de Uso - OpenOB Repeater Mode

## Caso de Uso 1: Radio por Internet (Studio a Transmisor)

### Escenario
Un estudio de radio necesita enviar audio en vivo a un transmisor remoto a través de Internet sin abrir puertos en el router del estudio ni del transmisor.

### Configuración

**En AWS EC2 (Repetidor):**
```bash
# IP pública: 18.211.119.253

# Iniciar repetidor con Opus 128kbps (eficiente)
openob 18.211.119.253 radio-repeater broadcast-link repeater -p 5004 -j 30
```

**En el Estudio (Encoder):**
```bash
# Enviar audio desde tarjeta de sonido
openob 18.211.119.253 radio-studio broadcast-link tx 18.211.119.253 \
  -e opus -b 128 -r 48000 -j 50 \
  -a alsa -d hw:CARD=USB,DEV=0 \
  --fec --no-dtx
```

**En el Transmisor (Decoder):**
```bash
# Recibir y reproducir en tarjeta de sonido
openob 18.211.119.253 radio-transmitter broadcast-link rx \
  -a alsa -d hw:CARD=PCH,DEV=0
```

### Características
- **Codec**: Opus 128kbps con FEC (Forward Error Correction)
- **Latencia**: ~200-300ms total (aceptable para radio)
- **Consumo de datos**: ~60 MB/hora
- **Costo EC2**: ~$0.005/hora

---

## Caso de Uso 2: Transmisión de Eventos en Vivo (Baja Latencia)

### Escenario
Cobertura de evento deportivo con retorno de audio para comentaristas. Requiere latencia mínima.

### Configuración

**En AWS EC2 (Repetidor):**
```bash
# Usar jitter buffer mínimo para baja latencia
openob 54.23.45.67 event-repeater sports-coverage repeater -p 6000 -j 15
```

**En el Evento (Encoder):**
```bash
# PCM para latencia mínima (transparente)
openob 54.23.45.67 event-encoder sports-coverage tx 54.23.45.67 \
  -e pcm -r 48000 -j 20 \
  -a jack -jn event-audio --jack-auto
```

**En el Estudio (Decoder):**
```bash
# Recibir con latencia mínima
openob 54.23.45.67 studio-decoder sports-coverage rx \
  -a jack -jn studio-return --jack-auto
```

### Características
- **Codec**: PCM (sin compresión)
- **Latencia**: ~50-80ms total (excelente)
- **Consumo de datos**: ~1.15 GB/hora
- **Costo EC2**: ~$0.09/hora

---

## Caso de Uso 3: Múltiples Enlaces (Multi-Link)

### Escenario
Estación de radio con varios estudios remotos enviando audio simultáneamente.

### Configuración

**En AWS EC2 (Repetidores Múltiples):**
```bash
# Link 1: Studio A
openob 18.211.119.253 repeater-a link-studio-a repeater -p 5004 -j 30

# Link 2: Studio B (en otra terminal/screen)
openob 18.211.119.253 repeater-b link-studio-b repeater -p 5104 -j 30

# Link 3: Studio C
openob 18.211.119.253 repeater-c link-studio-c repeater -p 5204 -j 30
```

**En cada Studio Remoto:**
```bash
# Studio A
openob 18.211.119.253 studio-a link-studio-a tx 18.211.119.253 \
  -e opus -b 96 -p 5004 -a alsa -d hw:0,0

# Studio B
openob 18.211.119.253 studio-b link-studio-b tx 18.211.119.253 \
  -e opus -b 96 -p 5104 -a alsa -d hw:1,0

# Studio C
openob 18.211.119.253 studio-c link-studio-c tx 18.211.119.253 \
  -e opus -b 96 -p 5204 -a alsa -d hw:2,0
```

**En el Estudio Central (Mezclador):**
```bash
# Recibir los 3 enlaces en diferentes dispositivos JACK
openob 18.211.119.253 mixer link-studio-a rx \
  -a jack -jn studio-a-in --jack-auto &

openob 18.211.119.253 mixer link-studio-b rx \
  -a jack -jn studio-b-in --jack-auto &

openob 18.211.119.253 mixer link-studio-c rx \
  -a jack -jn studio-c-in --jack-auto &
```

### Características
- **3 enlaces simultáneos**
- **Consumo total**: ~180 MB/hora (Opus 96kbps × 3)
- **Costo EC2**: ~$0.015/hora

---

## Caso de Uso 4: Backup/Redundancia (Dual Link)

### Escenario
Enlace crítico con redundancia: usar dos servidores EC2 en diferentes regiones.

### Configuración

**En AWS EC2 (Región us-east-1):**
```bash
# Primary repeater
openob 18.211.119.253 primary-repeater main-link repeater -p 5004 -j 30
```

**En AWS EC2 (Región eu-west-1):**
```bash
# Backup repeater
openob 52.19.88.140 backup-repeater main-link repeater -p 5004 -j 30
```

**En el Encoder (envía a ambos):**
```bash
# Script para iniciar dos transmisores
#!/bin/bash

# Primary
openob 18.211.119.253 encoder-primary main-link tx 18.211.119.253 \
  -e opus -b 128 -a alsa -d hw:0,0 &

# Backup (mismo audio source)
openob 52.19.88.140 encoder-backup main-link tx 52.19.88.140 \
  -e opus -b 128 -a alsa -d hw:0,0 &

wait
```

**En el Decoder (switchear manual o automático):**
```bash
# Usar primary por defecto
openob 18.211.119.253 decoder main-link rx -a alsa -d hw:1,0

# Si falla primary, switchear a backup:
# Ctrl+C y reiniciar con:
openob 52.19.88.140 decoder main-link rx -a alsa -d hw:1,0
```

### Características
- **Alta disponibilidad**
- **Consumo dual**: ~120 MB/hora
- **Costo EC2**: ~$0.02/hora (dos instancias)

---

## Caso de Uso 5: Pruebas y Desarrollo (Modo Test)

### Escenario
Probar OpenOB localmente sin hardware de audio real.

### Configuración

**Servidor Local (simula EC2):**
```bash
# Iniciar Redis localmente
sudo systemctl start redis-server

# Iniciar repeater local
openob 127.0.0.1 test-repeater test-link repeater -p 5004 -j 30
```

**Encoder de Prueba (genera tono de 1kHz):**
```bash
openob 127.0.0.1 test-encoder test-link tx 127.0.0.1 \
  -e opus -b 64 -a test -j 40
```

**Decoder de Prueba (sin salida de audio):**
```bash
openob 127.0.0.1 test-decoder test-link rx -a test
```

### Monitoreo con GStreamer:
```bash
# Ver estadísticas de RTP
gst-launch-1.0 -v udpsrc port=5004 caps="application/x-rtp" ! \
  rtpjitterbuffer latency=30 ! fakesink
```

---

## Caso de Uso 6: Con VPN WireGuard (Producción Segura)

### Escenario
Enlace de producción con máxima seguridad y estabilidad.

### Configuración

**1. Configurar WireGuard en EC2:**
```bash
# Instalar WireGuard
sudo apt install wireguard

# Generar claves
wg genkey | tee server_private.key | wg pubkey > server_public.key

# Crear /etc/wireguard/wg0.conf
[Interface]
Address = 10.200.0.1/24
ListenPort = 51820
PrivateKey = <server_private.key>

[Peer]
# Encoder
PublicKey = <encoder_public.key>
AllowedIPs = 10.200.0.2/32

[Peer]
# Decoder
PublicKey = <decoder_public.key>
AllowedIPs = 10.200.0.3/32

# Iniciar
sudo wg-quick up wg0
```

**2. Configurar WireGuard en Endpoints:**
```bash
# En Encoder y Decoder
sudo apt install wireguard
wg genkey | tee client_private.key | wg pubkey > client_public.key

# /etc/wireguard/wg0.conf (Encoder)
[Interface]
PrivateKey = <client_private.key>
Address = 10.200.0.2/24

[Peer]
PublicKey = <server_public.key>
Endpoint = 18.211.119.253:51820
AllowedIPs = 10.200.0.0/24
PersistentKeepalive = 25

sudo wg-quick up wg0
```

**3. Usar IPs de VPN:**
```bash
# En EC2
openob 10.200.0.1 vpn-repeater secure-link repeater -p 5004 -j 30

# En Encoder
openob 10.200.0.1 encoder secure-link tx 10.200.0.1 \
  -e opus -b 128 -a alsa -d hw:0,0

# En Decoder
openob 10.200.0.1 decoder secure-link rx -a alsa -d hw:1,0
```

### Características
- **Encriptación completa** (WireGuard)
- **Sin problemas de NAT**
- **Más estable** que conexión directa
- **Overhead mínimo** (~4% latencia adicional)

---

## Scripts de Automatización

### Auto-restart en caso de fallo:
```bash
#!/bin/bash
# /usr/local/bin/openob-repeater-watchdog.sh

while true; do
  echo "Starting OpenOB repeater..."
  openob 18.211.119.253 repeater transmission repeater -p 5004 -j 30
  
  echo "Repeater stopped. Restarting in 5 seconds..."
  sleep 5
done
```

### Monitoreo de estadísticas:
```bash
#!/bin/bash
# /usr/local/bin/openob-monitor.sh

echo "Monitoring OpenOB repeater on port 5004..."
while true; do
  echo "=== $(date) ==="
  
  # Verificar proceso
  if pgrep -f "openob.*repeater" > /dev/null; then
    echo "✓ Repeater is running"
  else
    echo "✗ Repeater is NOT running"
  fi
  
  # Estadísticas de red
  echo "Network stats:"
  netstat -su | grep -E "(packet|error)"
  
  # Usar Redis para info
  redis-cli get "openob:transmission:caps" 2>/dev/null || echo "No caps set"
  
  echo ""
  sleep 30
done
```

---

## Troubleshooting Común

### Audio entrecortado:
```bash
# Aumentar jitter buffer
openob ... repeater -j 80  # en lugar de -j 30
```

### Latencia alta:
```bash
# Reducir jitter buffer
openob ... repeater -j 15

# Usar PCM en lugar de Opus
openob ... tx ... -e pcm
```

### Verificar conectividad RTP:
```bash
# Escuchar paquetes en el repeater
sudo tcpdump -i any -n udp port 5004 -c 100

# Enviar test UDP
echo "test" | nc -u <REPEATER_IP> 5004
```

### Ver logs detallados:
```bash
# GStreamer debug level 5
GST_DEBUG=5 openob ... repeater -v
```

---

## Mejores Prácticas

1. **Usar Opus para Internet**: Mejor eficiencia, menor costo
2. **Usar PCM para LAN**: Latencia mínima, calidad perfecta
3. **Jitter buffer**: 30-50ms para Internet, 10-20ms para LAN
4. **Monitorear regularmente**: Usar scripts de watchdog
5. **Backup**: Siempre tener un enlace de respaldo
6. **VPN en producción**: WireGuard para seguridad y estabilidad
7. **Limitar acceso a Redis**: Solo IPs de confianza

---

Para más información, consulta [REPEATER_MODE.md](REPEATER_MODE.md)
