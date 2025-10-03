# Estado Actual del Modo Repeater - OpenOB

**Fecha**: 3 de octubre de 2025

## ✅ Funcionalidades Implementadas

### 1. Detección Automática de Peers
- ✅ **Decoder**: Se detecta automáticamente cuando publica su IP en Redis (con TTL de 60s)
- ✅ **Encoder**: Se debería detectar cuando llega el primer paquete RTP
- ✅ **Limpieza inteligente de Redis**: Solo borra datos obsoletos (sin TTL), mantiene peers activos

### 2. Mensajes de Consola
- ✅ 🎤 **ENCODER DETECTED**: Cuando se reciben paquetes RTP del encoder
- ✅ 🔊 **DECODER CONNECTED**: Cuando el decoder publica su IP en Redis
- ✅ 📡 **STARTING RTP FORWARDING**: Cuando empieza el reenvío de paquetes
- ✅ Mensajes con formato claro y emojis distintivos

### 3. Publicación Automática del Decoder
- ✅ El decoder (`rx.py`) publica su IP en Redis al arrancar
- ✅ TTL de 60 segundos con refresco cada 30 segundos
- ✅ Las claves expiran automáticamente si el decoder se detiene

### 4. Scripts de Inicio
- ✅ `start-repeater.sh`: Inicia el repeater en 192.168.18.34
- ✅ `start-encoder.sh`: Inicia el encoder (ejemplo para 192.168.18.16)
- ✅ `start-decoder.sh`: Inicia el decoder (ejemplo para 192.168.18.35)
- ✅ Todos con detección de sudo y permisos de audio correctos

## ⚠️ Problema Actual

### Síntoma
El repeater detecta correctamente:
- ✅ Encoder detectado (primer paquete)
- ✅ Decoder conectado (desde Redis)
- ✅ Mensaje "Ready to forward packets"

**PERO**: Los paquetes RTP NO se reenvían al decoder

### Evidencia
```bash
# Tráfico observado con tcpdump:
- Encoder (192.168.18.16) → Repeater (192.168.18.34):5004 ✅ OK
- Repeater (192.168.18.34) → Decoder (192.168.18.35):5004 ❌ NO HAY TRÁFICO

# Logs del decoder:
- CRITICAL - No data received for 3 seconds!
```

### Diagnóstico Técnico

**Problema identificado**: El callback `on_rtp_packet` del `appsink` NO se está ejecutando después de la detección inicial del encoder.

**Causas posibles**:
1. El pipeline GStreamer `udpsrc -> appsink` no está fluyendo datos correctamente
2. El `appsink` no está emitiendo la señal `new-sample`
3. Hay un problema con los caps de `application/x-rtp`
4. El buffer del appsink se está bloqueando

## 📝 Archivos Modificados

### 1. `/home/server/openob/openob/rtp/repeater.py`
**Cambios principales**:
- Añadido método `discover_peers_from_redis()` que busca decoders en Redis cada 2 segundos
- Añadido método `_cleanup_old_peer_data()` para limpiar claves obsoletas
- Modificado `on_rtp_packet()` para detectar encoder y contar paquetes
- Añadido `forward_rtp_to_peers()` con logging detallado
- Flags `encoder_detected` y `decoder_detected` para mensajes únicos

### 2. `/home/server/openob/openob/rtp/rx.py`
**Cambios principales**:
- Añadido método `_publish_decoder_address()` que publica IP en Redis con TTL
- Añadido método `_refresh_decoder_registration()` que refresca el TTL cada 30s
- Importado módulo `socket` para detectar IP local
- Añadido `GLib.timeout_add_seconds()` para refrescos automáticos

### 3. Scripts de inicio
- `start-repeater.sh`: Ya existía, sin cambios
- `start-encoder.sh`: Ya existía, sin cambios  
- `start-decoder.sh`: Ya existía, sin cambios

## 🔧 Solución Pendiente

### Opción 1: Depurar el Pipeline GStreamer
Investigar por qué el `appsink` no está procesando los buffers:
```python
# Añadir debug al pipeline
GST_DEBUG=3,udpsrc:5,appsink:5 ./start-repeater.sh
```

### Opción 2: Cambiar a Socket UDP Directo
En lugar de usar GStreamer para recibir y reenviar, usar sockets UDP Python directamente:
```python
# Recibir en thread separado
rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rtp_socket.bind(('0.0.0.0', 5004))

while True:
    data, addr = rtp_socket.recvfrom(2048)
    # Detectar encoder
    # Reenviar a todos los peers
    for peer in self.peers.values():
        self.rtp_send_socket.sendto(data, peer['rtp_addr'])
```

### Opción 3: Usar rtpbin en Lugar de appsink
Probar con `rtpbin` que tiene mejor manejo de RTP:
```python
rtpbin = Gst.ElementFactory.make('rtpbin')
# Conectar señales de rtpbin
rtpbin.connect('pad-added', self.on_pad_added)
```

## 📊 Logs del Último Test

```
=== Iniciando OpenOB Repeater ===
2025-10-03 14:04:15 - Found active peer data: openob:transmission:recepteur:type (TTL: 36s)
2025-10-03 14:04:15 - RTP pipeline: udpsrc -> appsink (direct forwarding)
2025-10-03 14:04:15 - 🎤 ENCODER DETECTED!
2025-10-03 14:04:15 -    ⚠️  No decoders registered yet
2025-10-03 14:04:16 - 🔊 DECODER CONNECTED!
2025-10-03 14:04:16 -    RTP: 192.168.18.35:5004
2025-10-03 14:04:16 -    Status: Receiving audio from encoder
2025-10-03 14:04:16 -    📡 Ready to forward packets

NO SE VIO:
- ❌ "📡 STARTING RTP FORWARDING"
- ❌ "📊 Packet #100 received"
- ❌ Ningún paquete reenviado al decoder
```

## ✨ Lo Que Funciona Perfectamente

1. ✅ Detección de encoder en primer paquete RTP
2. ✅ Detección automática de decoder desde Redis
3. ✅ Limpieza inteligente de datos obsoletos en Redis
4. ✅ TTL y refresco automático de registro del decoder
5. ✅ Mensajes de consola claros y con emojis
6. ✅ Recepción de paquetes RTP (confirmado con tcpdump)

## 🎯 Próximos Pasos Recomendados

1. **Debug del Pipeline**: Ejecutar con `GST_DEBUG=5` para ver qué pasa con los buffers
2. **Verificar appsink**: Asegurar que `emit-signals=True` y los callbacks están registrados
3. **Alternativa con sockets**: Implementar recepción/reenvío con sockets UDP puros (más confiable)
4. **Test con gst-launch-1.0**: Probar el pipeline manualmente para validar que funciona

## 📞 Para Continuar

El código está casi completo. Solo falta resolver por qué los buffers no fluyen desde `udpsrc` hacia `appsink`. Una vez resuelto esto, el sistema debería funcionar perfectamente con auto-detección y reenvío automático de paquetes.
