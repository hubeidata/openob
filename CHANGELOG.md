## 1.0.0-repeater - 2025-09-30

### Added - Modo Repeater (Passthrough)

* **Nueva funcionalidad principal**: Modo repeater que permite usar OpenOB como repetidor RTP sin decodificar/encodear
  * Forwarding de RTP y RTCP sin procesamiento de codec
  * Latencia reducida ~50-60% vs modo RX+TX tradicional
  * Uso de CPU reducido ~75% en el servidor
  * Compatible con NAT (los endpoints se conectan saliente)

* **Nuevos archivos**:
  * `openob/rtp/repeater.py`: Clase RTPRepeater con pipeline passthrough
  * `REPEATER_MODE.md`: Documentación completa (450+ líneas)
  * `README_REPEATER.md`: Quick start guide
  * `EXAMPLES.md`: 6 casos de uso detallados
  * `setup_ec2_repeater.sh`: Script de instalación automática para EC2
  * `test_repeater_installation.py`: Script de verificación de instalación
  * `openob-repeater.service`: Archivo systemd
  * `IMPLEMENTATION_SUMMARY.md`: Resumen técnico

* **Modificaciones**:
  * `openob/node.py`: Soporte para modo 'repeater'
  * `bin/openob`: Nuevo subparser con opciones -p, -j, --peer
  * `openob/audio_interface.py`: Manejo de modo repeater

### Performance Improvements

* Latencia: 120-200ms (RX+TX) → 65-115ms (Repeater)
* CPU usage: 40-60% (RX+TX) → 5-15% (Repeater) en EC2 t3.micro

### Documentation

* ~1,500 líneas de documentación
* Guías de configuración AWS/EC2
* Scripts de automatización
* Troubleshooting comprehensivo

---

## 4.0.0-dev

* Upgraded GStreamer libraries to ^1.0
* Added Python 3 compatability

## 3.1

* Improved command line interface (Jonty Sewell)
* Bugfix for PCM mode operation (Jonty Sewell)

## 3.0.3

* Packaging bugfixes

## 3.0.0

* Released

## 3.0.0a1

* Refactored the Manager into Node, LinkConfig, AudioInterface and Logger classes
* Refactored logging to use Python's logging framework
* Removed audio level feedback on the command line
* Moved configuration into objects for shared and node-specific (audio interface) values
* Removed PulseAudio element support (except through the 'auto' interface type)
* Removed variable size input queue, since this was an attempt to fix the audiorate related glitches but made no difference
* Removed CELT support; only Opus is now supported for compressed audio
* Removed colorama dependency
* Enabled support for disabling automatic connection under JACK (Chris Roberts)
* Added support for asking the audio interface for a sample rate (Chris Roberts)

## 2.3.6

* Fixed level messages reporting incorrect channel counts

## 2.3.5

* Added multicast support (Jonty Sewell)
* Added automatic audio interface selection support (Jonty Sewell)

## 2.3.4

* Minor bugfix

## 2.3.3

* Added support for Opus features:

    * Discontinuous transmission
    * In-band Forward Error Correction (and loss % assumption)
    * Frame size selection

## <2.3.3

* Check the git changelog for these changes.
