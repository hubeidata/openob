# OpenOB Repeater Mode (Passthrough)

## Descripción

El modo **repeater** (repetidor) de OpenOB implementa un repetidor RTP de baja latencia que reenvía paquetes sin decodificar/recodificar. Es ideal para crear enlaces punto a punto a través de Internet usando una instancia EC2 (u otro servidor en la nube) como punto de encuentro, evitando la necesidad de abrir puertos en los routers locales.

## Características

- ✅ **Passthrough mode**: No hay procesamiento de codec (decodificar/encodear)
- ✅ **Baja latencia**: ~10-40ms adicionales (solo jitter buffer mínimo)
- ✅ **NAT-friendly**: Los endpoints se conectan saliente al repetidor
- ✅ **Forwarding RTP + RTCP**: Mantiene control de calidad y estadísticas
- ✅ **Registro dinámico de peers**: Detecta automáticamente endpoints conectados
- ✅ **CPU eficiente**: Sin carga de procesamiento de audio

## Arquitectura

```
Encoder (local) ----(outbound)----> EC2 Repeater <----(outbound)---- Decoder (local)
                                         |
                                    Forwards packets
                                    between peers
```

## Comparación con RX+TX

| Aspecto | RX+TX (Anterior) | Repeater (Nuevo) |
|---------|------------------|------------------|
| **Latencia** | +100-150ms | +10-40ms |
| **CPU en servidor** | Alta (decode/encode) | Baja (passthrough) |
| **Procesos** | 2 procesos | 1 proceso |
| **Configuración** | Compleja | Simple |
| **Puertos en local** | ❌ Requiere NAT | ✅ No requiere |

## Uso

### En la EC2 (Servidor Repetidor)

```bash
# Instalar Redis (config server)
sudo apt-get install redis-server

# Configurar Redis para aceptar conexiones remotas
sudo sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
sudo systemctl restart redis-server

# Iniciar el repetidor
openob <EC2_PUBLIC_IP> ec2-repeater transmission repeater -p 5004 -j 30
```

### En el Encoder (Local)

```bash
# Enviar audio al repetidor EC2
openob <EC2_PUBLIC_IP> encoder transmission tx <EC2_PUBLIC_IP> \
  -e pcm -r 48000 -j 60 -a alsa -d hw:0,0
```

### En el Decoder (Local)

```bash
# Recibir audio desde el repetidor EC2
openob <EC2_PUBLIC_IP> decoder transmission rx -a alsa -d hw:1,0
```

## Opciones del Modo Repeater

```bash
openob <config_host> <node_name> <link_name> repeater [options]
```

### Opciones disponibles:

- `-p, --port`: Puerto base para RTP (por defecto: 3000). RTCP usa port+1
- `-j, --jitter_buffer`: Tamaño del buffer de jitter en ms (por defecto: 30ms)
- `--peer PEER_ID ADDRESS`: Pre-registrar un peer (opcional)

### Ejemplos con opciones:

```bash
# Con puerto personalizado y jitter buffer de 20ms
openob 18.211.119.253 repeater transmission repeater -p 5004 -j 20

# Pre-registrando peers
openob 18.211.119.253 repeater transmission repeater \
  --peer encoder1 192.168.1.10:5004 \
  --peer decoder1 10.0.0.5:5004
```

## Configuración de Red (AWS EC2)

### Security Group

Abre los siguientes puertos en el Security Group de la EC2:

| Puerto | Tipo | Fuente | Descripción |
|--------|------|--------|-------------|
| 6379 | TCP | IPs de confianza | Redis (config server) |
| 5004 | UDP | 0.0.0.0/0 | RTP (audio) |
| 5005 | UDP | 0.0.0.0/0 | RTCP (control) |

**Nota de seguridad**: Limita el acceso a Redis (6379) solo a las IPs de tus endpoints. No lo expongas públicamente sin protección.

### Ejemplo con AWS CLI:

```bash
# Obtener el Security Group ID
SG_ID=$(aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

# Abrir Redis (solo desde IPs específicas)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 6379 \
  --cidr <YOUR_ENCODER_IP>/32

# Abrir RTP/RTCP (público)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol udp \
  --port 5004-5005 \
  --cidr 0.0.0.0/0
```

## Costos de Ancho de Banda

Con PCM 48kHz/16bit/stereo:

- **Bitrate**: ~1.536 Mbps por dirección
- **EC2 total**: ~3.072 Mbps (inbound + outbound)
- **Consumo**: ~1.15 GB/hora
- **Costo AWS** (aprox.): $0.09/hora (región us-east-1)

Con Opus 128kbps:

- **Bitrate**: 128 kbps por dirección
- **EC2 total**: 256 kbps
- **Consumo**: ~113 MB/hora
- **Costo AWS** (aprox.): $0.01/hora

## Flujo Completo de Configuración

### 1. Preparar EC2

```bash
# Conectar por SSH
ssh -i key.pem ubuntu@18.211.119.253

# Instalar dependencias
sudo apt-get update
sudo apt-get install -y redis-server python3-gst-1.0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  python3-pip

# Instalar OpenOB
sudo pip3 install openob  # o clonar repo e instalar desde source

# Configurar Redis
sudo sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
sudo systemctl restart redis-server
```

### 2. Configurar Security Group (ver arriba)

### 3. Iniciar Repeater en EC2

```bash
# Usando screen para mantener el proceso activo
screen -S openob-repeater

openob 18.211.119.253 ec2-repeater transmission repeater -p 5004 -j 30

# Presionar Ctrl+A, luego D para desconectar screen
```

### 4. Iniciar Encoder (máquina local)

```bash
openob 18.211.119.253 encoder transmission tx 18.211.119.253 \
  -e pcm -r 48000 -j 60 -a alsa -d hw:0,0
```

### 5. Iniciar Decoder (máquina remota)

```bash
openob 18.211.119.253 decoder transmission rx -a alsa -d hw:1,0
```

## Troubleshooting

### El repeater no recibe paquetes

1. Verificar que los puertos UDP estén abiertos en el Security Group
2. Verificar que el encoder esté enviando a la IP correcta
3. Revisar logs: `journalctl -f` o salida de consola

### Alta latencia

1. Reducir jitter buffer: `-j 20` o `-j 10`
2. Verificar latencia de red: `ping <EC2_IP>`
3. Usar Opus en lugar de PCM si el ancho de banda es limitado

### Peers no se registran

1. Verificar que Redis esté accesible desde los endpoints
2. Comprobar conectividad: `redis-cli -h <EC2_IP> ping`
3. Revisar configuración de firewall local

### Audio entrecortado

1. Aumentar jitter buffer: `-j 60` o `-j 80`
2. Verificar que no haya pérdida de paquetes: `mtr <EC2_IP>`
3. Considerar usar VPN (WireGuard) para mejor estabilidad

## Modo Alternativo: con VPN (Recomendado para producción)

Para máxima estabilidad, considera usar WireGuard VPN:

```bash
# En EC2: instalar WireGuard
sudo apt install wireguard

# Crear configuración VPN (ver documentación de WireGuard)
# Asignar IPs: EC2=10.200.0.1, Encoder=10.200.0.2, Decoder=10.200.0.3

# Luego usar IPs de VPN en lugar de IPs públicas
openob 10.200.0.1 repeater transmission repeater -p 5004
```

## Servicios Systemd (Arranque Automático)

### Archivo: `/etc/systemd/system/openob-repeater.service`

```ini
[Unit]
Description=OpenOB Repeater Service
After=network.target redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/usr/local/bin/openob 18.211.119.253 ec2-repeater transmission repeater -p 5004 -j 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Activar servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable openob-repeater
sudo systemctl start openob-repeater
sudo systemctl status openob-repeater
```

## Monitoreo

### Ver logs en tiempo real:

```bash
# Si usas systemd
sudo journalctl -u openob-repeater -f

# Si usas screen
screen -r openob-repeater
```

### Verificar peers conectados:

Los logs del repeater mostrarán cuando los peers se registren:

```
[INFO] Registered peer encoder: RTP=203.0.113.45:5004, RTCP=203.0.113.45:5005
[INFO] Registered peer decoder: RTP=198.51.100.67:5004, RTCP=198.51.100.67:5005
```

## Limitaciones Conocidas

1. **NAT Simétrica**: En redes con NAT simétrica (~8% de ISPs), puede ser necesario usar VPN
2. **Descubrimiento de peers**: Actualmente requiere pre-registro via Redis o argumentos CLI
3. **Sin encriptación**: Los paquetes RTP no están cifrados. Considera usar VPN o SRTP en producción
4. **IPv4 únicamente**: No soporta IPv6 en la versión actual

## Próximas Mejoras

- [ ] Descubrimiento automático de peers via paquetes de registro
- [ ] Soporte para SRTP (RTP seguro)
- [ ] Interfaz web para monitoreo de peers
- [ ] Métricas de latencia y calidad en tiempo real
- [ ] Soporte para más de 2 peers (multicast passthrough)
- [ ] IPv6 support

## Soporte

Para reportar bugs o sugerir mejoras, crea un issue en:
https://github.com/JamesHarrison/openob/issues
