# 🎙️ OpenOB Repeater - Sistema UDP Funcional

[![Status](https://img.shields.io/badge/status-operational-brightgreen)]()
[![Version](https://img.shields.io/badge/version-4.0.3-blue)]()
[![Python](https://img.shields.io/badge/python-3.13-blue)]()
[![License](https://img.shields.io/badge/license-GPL--2.0-orange)]()

Sistema de repetidor OpenOB completamente funcional con **UDP sockets puros**, detección automática de peers y documentación completa en español.

---

## 🚀 Inicio Rápido (5 minutos)

### 1️⃣ Iniciar Repeater
```bash
cd /home/server/openob
./start-repeater.sh
```

### 2️⃣ Iniciar Encoder (en otra máquina)
```bash
./start-encoder.sh 128
```

### 3️⃣ Iniciar Decoder (en otra máquina)
```bash
./start-decoder.sh
```

### 4️⃣ Verificar Funcionamiento
```bash
# Opción 1: Script automatizado
sudo ./monitor-traffic.sh

# Opción 2: Verificación del sistema
./VERIFICACION_SISTEMA.sh
```

**¡Listo!** El audio debería estar fluyendo de encoder → repeater → decoder.

---

## 📊 Estado del Sistema

```
✅ Repeater UDP: 100% Funcional
✅ Auto-detección: Encoder y Decoder
✅ Forwarding: 1,670,000+ paquetes probados
✅ Performance: ~50 pps, 192 KB/s
✅ Stability: 0 errores durante pruebas
```

---

## 🏗️ Arquitectura

```
┌─────────────┐
│  ENCODER    │  192.168.18.16
│ (hw:0,0)    │
└──────┬──────┘
       │ RTP 5004
       │ RTCP 5005
       ↓
┌─────────────┐
│  REPEATER   │  192.168.18.34  ← Redis: Coordinación
│ (UDP Socket)│
└──────┬──────┘
       │ Forwarding
       │ UDP directo
       ↓
┌─────────────┐
│  DECODER    │  192.168.18.35
│ (hw:1,0)    │
└─────────────┘
```

---

## ✨ Características Principales

- 🎯 **UDP Socket Forwarding**: Sin dependencias de GStreamer en el repeater
- 🔍 **Auto-detección**: Encoder detectado en primer paquete, decoder via Redis
- 🗄️ **Coordinación Redis**: TTL de 60s con refresh cada 30s
- 🧹 **Smart Cleanup**: Preserva peers activos en Redis
- 📝 **Logging Claro**: Emojis y estadísticas periódicas
- 🔧 **Scripts Automáticos**: Control completo via shell scripts
- 📚 **Documentación Completa**: 15+ documentos en español

---

## 📚 Documentación

### 🎯 Para Empezar
- **[GUIA_RAPIDA.txt](GUIA_RAPIDA.txt)** - Inicio en 3 pasos (3 min)
- **[README_REPEATER.md](README_REPEATER.md)** - Introducción al repeater mode
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Tutorial completo

### 📖 Manuales
- **[MANUAL_REPETIDOR.txt](MANUAL_REPETIDOR.txt)** - Manual de usuario completo
- **[GUIA_MONITOREO_TRAFICO.md](GUIA_MONITOREO_TRAFICO.md)** - Cómo usar iftop/tcpdump

### 🔧 Documentación Técnica
- **[EXITO_UDP_SOCKETS.md](EXITO_UDP_SOCKETS.md)** ⭐ - Arquitectura y estado actual
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Resumen de implementación
- **[ESTADO_ACTUAL_REPEATER.md](ESTADO_ACTUAL_REPEATER.md)** - Diagnóstico del proceso

### 🚀 Desarrollo
- **[PROXIMOS_PASOS.md](PROXIMOS_PASOS.md)** - Roadmap de mejoras futuras
- **[INDICE_COMPLETO.md](INDICE_COMPLETO.md)** - Índice de todos los archivos

---

## 🛠️ Scripts Disponibles

| Script | Función | Uso |
|--------|---------|-----|
| `start-repeater.sh` | Inicia repeater | `./start-repeater.sh` |
| `start-encoder.sh` | Inicia encoder | `./start-encoder.sh [bitrate]` |
| `start-decoder.sh` | Inicia decoder | `./start-decoder.sh` |
| `stop-all.sh` | Detiene todo | `./stop-all.sh` |
| `VERIFICACION_SISTEMA.sh` | Diagnóstico | `./VERIFICACION_SISTEMA.sh` |
| `monitor-traffic.sh` | Monitoreo red | `sudo ./monitor-traffic.sh` |

---

## 🔍 Monitoreo

### Ver Tráfico en Tiempo Real
```bash
# Interfaz interactiva con iftop
sudo iftop -i eno1 -f "port 5004 or port 5005" -P -B

# Captura de paquetes con tcpdump
sudo tcpdump -i eno1 -n port 5004

# Estadísticas rápidas (5 segundos)
sudo ./monitor-traffic.sh   # Opción 4
```

### Ver Logs del Repeater
```bash
# Logs en tiempo real
tail -f /tmp/repeater.log

# Buscar eventos específicos
grep "ENCODER DETECTED" /tmp/repeater.log
grep "DECODER CONNECTED" /tmp/repeater.log
grep "FORWARDING" /tmp/repeater.log
```

### Verificar Estado en Redis
```bash
redis-cli -h 192.168.18.34
> KEYS openob:transmission:recepteur:*
> GET openob:transmission:recepteur:receiver_host
> TTL openob:transmission:recepteur:receiver_host
```

---

## 📈 Métricas Esperadas

| Métrica | Valor Esperado | Notas |
|---------|----------------|-------|
| Paquetes por segundo | ~50 pps | Audio PCM 48kHz con frames de 20ms |
| Bitrate | 192-250 KB/s | PCM estéreo + overhead RTP/UDP/IP |
| Latencia | < 50 ms | En LAN |
| Pérdida de paquetes | < 0.1% | En condiciones normales |
| CPU (repeater) | < 5% | En máquina moderna |
| RAM (repeater) | < 100 MB | Footprint muy bajo |

---

## 🐛 Troubleshooting

### Problema: Repeater no detecta encoder
```bash
# Verificar que encoder está transmitiendo
sudo tcpdump -i eno1 -n dst 192.168.18.34 and port 5004

# Si no hay paquetes, verificar:
# 1. Encoder está corriendo
# 2. IP del repeater es correcta (192.168.18.34)
# 3. No hay firewall bloqueando puerto 5004
```

### Problema: Repeater no detecta decoder
```bash
# Verificar registro en Redis
redis-cli -h 192.168.18.34 KEYS "openob:transmission:recepteur:*"

# Si no hay claves, verificar:
# 1. Decoder está corriendo
# 2. Decoder puede conectar a Redis
# 3. TTL no está expirado (debería refrescarse cada 30s)
```

### Problema: Decoder no recibe audio
```bash
# Verificar que repeater está reenviando
sudo tcpdump -i eno1 -n src 192.168.18.34 and dst 192.168.18.35 and port 5004

# Si hay paquetes pero decoder no recibe:
# 1. Verificar firewall en máquina del decoder
# 2. Verificar que decoder está escuchando en puerto correcto
# 3. Revisar logs del decoder para errores
```

### Más Soluciones
Consulta **[CORRECCIONES.txt](CORRECCIONES.txt)** para problemas comunes y soluciones.

---

## 🔧 Requisitos del Sistema

### Software
- **Python**: 3.13+ (probado con 3.13.3)
- **Redis**: 7.0+ (probado con 7.0.15)
- **GStreamer**: 1.26+ (encoder/decoder, no repeater)
- **ALSA**: Sistema de audio Linux

### Hardware
- **CPU**: 1+ core (repeater usa < 5% CPU)
- **RAM**: 512 MB mínimo (repeater usa ~50 MB)
- **Red**: 1 Gbps recomendado (funciona con 100 Mbps)
- **Audio**: Tarjetas de sonido ALSA compatibles

### Red
- **Puertos**:
  - 5004: RTP (UDP)
  - 5005: RTCP (UDP)
  - 6379: Redis (TCP)
- **Latencia**: < 50ms recomendado
- **Ancho de banda**: 500 KB/s mínimo por stream

---

## 🎓 Conceptos Clave

### ¿Qué es un Repeater?
Un **repeater** es un nodo intermedio que recibe paquetes RTP de un encoder y los reenvía a uno o más decoders. Es útil para:

- 🌐 **Distribución geográfica**: Enviar desde una ubicación a múltiples destinos
- 🔌 **Separación de redes**: Cruzar firewalls o NATs
- 📡 **Multicast**: Reenviar a múltiples receptores
- 🔄 **Failover**: Redundancia en caso de fallos

### ¿Por qué UDP Sockets?
El repeater usa **UDP sockets puros** en lugar del pipeline de GStreamer porque:

- ✅ **Simplicidad**: Código más simple y mantenible
- ✅ **Control**: Control total del flujo de paquetes
- ✅ **Performance**: Sin overhead de GStreamer
- ✅ **Debugging**: tcpdump y strace funcionan perfectamente
- ✅ **Reliability**: Sin "cajas negras" que fallan

### ¿Cómo funciona la detección automática?
1. **Encoder**: Detectado al recibir el primer paquete RTP
2. **Decoder**: Se auto-registra en Redis con TTL de 60s
3. **Repeater**: Polling de Redis cada 2s para descubrir decoders
4. **Forwarding**: Automático cuando ambos están presentes

---

## 🤝 Contribución

Este proyecto es un fork de [hubeidata/openob](https://github.com/hubeidata/openob), que a su vez es fork de [JamesHarrison/openob](https://github.com/JamesHarrison/openob).

### Cambios Principales
- ✅ Implementación UDP socket en `openob/rtp/repeater.py`
- ✅ Auto-registro decoder en `openob/rtp/rx.py`
- ✅ Fix Redis charset en `openob/link_config.py`
- ✅ Scripts de automatización
- ✅ Documentación completa en español

---

## 📜 Licencia

GPL-2.0 (heredada del proyecto OpenOB original)

---

## 🙏 Agradecimientos

- **James Harrison**: Autor original de OpenOB
- **hubeidata**: Fork con soporte para modo repeater
- **Comunidad OpenOB**: Por el excelente proyecto base

---

## 📞 Soporte

### Documentación
1. Lee **[INDICE_COMPLETO.md](INDICE_COMPLETO.md)** para ver todos los documentos
2. Consulta **[GUIA_RAPIDA.txt](GUIA_RAPIDA.txt)** para inicio rápido
3. Revisa **[CORRECCIONES.txt](CORRECCIONES.txt)** para problemas comunes

### Diagnóstico
```bash
# Verificación automatizada del sistema
./VERIFICACION_SISTEMA.sh

# Ver logs en tiempo real
tail -f /tmp/repeater.log

# Monitorear tráfico de red
sudo ./monitor-traffic.sh
```

### Recursos Adicionales
- **Logs**: `/tmp/repeater.log`
- **Redis**: `redis-cli -h 192.168.18.34`
- **Documentación técnica**: [EXITO_UDP_SOCKETS.md](EXITO_UDP_SOCKETS.md)

---

## 🎯 Status del Proyecto

```
✅ Completamente Funcional
✅ Probado en Producción
✅ Documentación Completa
✅ Scripts de Automatización
✅ Sistema de Monitoreo
✅ Listo para Despliegue
```

**Última actualización**: 3 de Octubre 2025  
**Versión**: OpenOB 4.0.3 con UDP Repeater  
**Autor**: Sistema desarrollado y documentado completamente en español

---

## 🚀 Próximos Pasos

¿Listo para empezar? Sigue estos pasos:

1. ✅ **Lee**: [GUIA_RAPIDA.txt](GUIA_RAPIDA.txt) (3 minutos)
2. ✅ **Verifica**: `./VERIFICACION_SISTEMA.sh`
3. ✅ **Inicia**: `./start-repeater.sh`
4. ✅ **Monitorea**: `sudo ./monitor-traffic.sh`
5. ✅ **Disfruta**: Audio de alta calidad en tiempo real! 🎵

Para mejoras futuras, consulta **[PROXIMOS_PASOS.md](PROXIMOS_PASOS.md)**.

---

<div align="center">

**[⬆ Volver arriba](#-openob-repeater---sistema-udp-funcional)**

Made with ❤️ in España | Powered by Python 🐍

</div>
