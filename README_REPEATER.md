# OpenOB - Repeater Mode Implementation

## Nuevo Modo: Repeater (Passthrough)

Este fork de OpenOB implementa un nuevo modo **repeater** que permite crear enlaces de audio punto a punto a través de Internet usando un servidor en la nube (como EC2) como repetidor, sin necesidad de abrir puertos en los routers locales.

### ✨ Características del Modo Repeater

- 🚀 **Baja latencia**: Solo 10-40ms adicionales (sin decodificar/encodear)
- 🔄 **Passthrough**: Reenvía paquetes RTP/RTCP sin procesamiento
- 🌐 **NAT-friendly**: Los endpoints se conectan saliente al servidor
- 💻 **CPU eficiente**: Sin carga de procesamiento de audio
- 🔌 **Plug & Play**: Registro automático de peers

## Uso Rápido

### 1. En el servidor (EC2/VPS):

```bash
# Instalar y configurar (script automatizado)
sudo bash setup_ec2_repeater.sh

# Iniciar repeater
openob <SERVER_IP> repeater transmission repeater -p 5004 -j 30
```

### 2. En el encoder (local):

```bash
openob <SERVER_IP> encoder transmission tx <SERVER_IP> \
  -e pcm -r 48000 -j 60 -a alsa -d hw:0,0
```

### 3. En el decoder (local):

```bash
openob <SERVER_IP> decoder transmission rx -a alsa -d hw:1,0
```

## Documentación Completa

- 📖 [REPEATER_MODE.md](REPEATER_MODE.md) - Guía completa del modo repeater
- 🚀 [setup_ec2_repeater.sh](setup_ec2_repeater.sh) - Script de instalación para EC2

## Comparación con Configuración Tradicional

| Aspecto | Modo RX+TX | Modo Repeater |
|---------|------------|---------------|
| **Latencia** | +100-150ms | +10-40ms |
| **CPU** | Alta | Baja |
| **Configuración** | 2 procesos | 1 proceso |
| **Puertos locales** | ❌ Requiere NAT | ✅ No requiere |

## Requisitos

- Python 3.6+
- GStreamer 1.0+
- Redis (para coordinación)
- Servidor con IP pública (EC2, VPS, etc.)

## Instalación

### Desde source:

```bash
git clone https://github.com/hubeidata/openob.git
cd openob
sudo pip3 install -e .
```

### Dependencias del sistema:

```bash
# Debian/Ubuntu
sudo apt-get install redis-server python3-gst-1.0 \
  gstreamer1.0-plugins-{base,good,bad,ugly}
```

## Arquitectura

```
┌─────────────┐                    ┌─────────────┐
│   Encoder   │────(outbound)─────▶│             │
│   (Local)   │                    │  Repeater   │
└─────────────┘                    │    (EC2)    │
                                   │             │
┌─────────────┐                    │  Forward    │
│   Decoder   │◀────(outbound)─────│  RTP/RTCP   │
│   (Local)   │                    │             │
└─────────────┘                    └─────────────┘
```

Los endpoints se conectan **saliente** al repeater, evitando problemas de NAT.

## Costos de Red (EC2)

**Con PCM 48kHz/16bit/stereo:**
- Consumo: ~1.15 GB/hora
- Costo aproximado: $0.09/hora (us-east-1)

**Con Opus 128kbps:**
- Consumo: ~113 MB/hora
- Costo aproximado: $0.01/hora

## Seguridad

⚠️ **Importante:**
- Limita acceso a Redis (puerto 6379) solo a IPs de confianza
- Considera usar WireGuard VPN para producción
- Los paquetes RTP no están cifrados por defecto

## Ejemplos de Uso

### Modo básico (puerto por defecto):

```bash
openob 18.211.119.253 repeater transmission repeater
```

### Con configuración personalizada:

```bash
openob 18.211.119.253 repeater transmission repeater \
  -p 5004 \           # Puerto RTP
  -j 30 \             # Jitter buffer (ms)
  -v                  # Verbose logging
```

### Pre-registrando peers:

```bash
openob 18.211.119.253 repeater transmission repeater \
  --peer encoder1 192.168.1.10:5004 \
  --peer decoder1 10.0.0.5:5004
```

## Troubleshooting

### El repeater no recibe paquetes

```bash
# Verificar que los puertos estén abiertos
sudo netstat -tulpn | grep 5004

# Verificar Security Group (AWS)
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Verificar conectividad
nc -zuv <SERVER_IP> 5004
```

### Ver logs en detalle:

```bash
# Si usas systemd
sudo journalctl -u openob-repeater -f

# Si ejecutas manualmente
openob <SERVER_IP> repeater transmission repeater -v
```

## Próximas Mejoras

- [ ] Soporte para SRTP (RTP seguro)
- [ ] Interfaz web de monitoreo
- [ ] Métricas de latencia en tiempo real
- [ ] Soporte multicast (>2 peers)
- [ ] IPv6 support

## Contribuir

¡Contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Copyright (c) 2018, James Harrison  
Copyright (c) 2025, Hubeidata (Repeater Mode Extension)

Licencia BSD de 3 cláusulas - ver archivo LICENSE para detalles.

## Soporte

- 📧 Email: [Crear issue en GitHub](https://github.com/hubeidata/openob/issues)
- 📚 Documentación: [REPEATER_MODE.md](REPEATER_MODE.md)

## Agradecimientos

- James Harrison - Creador original de OpenOB
- Comunidad GStreamer
- ChatGPT/Claude - Asistencia en diseño e implementación del modo repeater

---

**⚠️ Nota**: El proyecto OpenOB original no está siendo mantenido activamente. Este fork añade el modo repeater pero puede requerir actualizaciones para versiones modernas de GStreamer/Python.
