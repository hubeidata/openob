import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
Gst.init(None)

import socket
from openob.logger import LoggerFactory

class RTPReceiver(object):

    def __init__(self, node_name, link_config, audio_interface):
        """Sets up a new RTP receiver"""
    
        self.link_config = link_config
        self.audio_interface = audio_interface
        self.node_name = node_name

        self.logger_factory = LoggerFactory()
        self.logger = self.logger_factory.getLogger('node.%s.link.%s.%s' % (node_name, self.link_config.name, self.audio_interface.mode))
        self.logger.info('Creating reception pipeline')

        # Publish this decoder's IP to Redis for repeater discovery
        self._publish_decoder_address()

        self.build_pipeline()

    def _publish_decoder_address(self):
        """Publish this decoder's IP address to Redis so the repeater can find it"""
        try:
            # Get local IP address (the one used to connect to Redis)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Connect to Redis server to determine which local IP we're using
                s.connect((self.link_config.redis_host, 6379))
                local_ip = s.getsockname()[0]
            finally:
                s.close()
            
            # Publish to Redis with node name as key
            key_prefix = 'openob:%s:%s' % (self.link_config.name, self.node_name)
            self.link_config.redis.set('%s:receiver_host' % key_prefix, local_ip)
            self.link_config.redis.set('%s:port' % key_prefix, str(self.link_config.port))
            self.link_config.redis.set('%s:type' % key_prefix, 'decoder')
            
            # Set expiration time (TTL) of 60 seconds - will be refreshed periodically
            self.link_config.redis.expire('%s:receiver_host' % key_prefix, 60)
            self.link_config.redis.expire('%s:port' % key_prefix, 60)
            self.link_config.redis.expire('%s:type' % key_prefix, 60)
            
            self.logger.info('Published decoder address to Redis: %s:%s (TTL: 60s)' % (local_ip, self.link_config.port))
            
            # Schedule periodic refresh of the registration
            GLib.timeout_add_seconds(30, self._refresh_decoder_registration, key_prefix, local_ip)
            
            # Also send a UDP registration/keepalive to the repeater so it can learn
            # the decoder's public endpoint (works behind NAT without port-forwarding).
            try:
                # Create a lightweight UDP socket for registration packets
                self._reg_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Non-blocking and short timeout
                self._reg_socket.settimeout(0.5)

                # Send an initial registration immediately
                GLib.idle_add(self._send_registration)

                # Schedule periodic registration every 20 seconds to keep NAT mapping
                GLib.timeout_add_seconds(20, self._send_registration)
            except Exception as e:
                self.logger.debug('Could not create registration socket: %s' % e)
        except Exception as e:
            self.logger.warning('Could not publish decoder address to Redis: %s' % e)

    def _refresh_decoder_registration(self, key_prefix, local_ip):
        """Refresh decoder registration in Redis to keep it alive"""
        try:
            # Check if still connected
            if hasattr(self, 'pipeline') and self.pipeline:
                self.link_config.redis.expire('%s:receiver_host' % key_prefix, 60)
                self.link_config.redis.expire('%s:port' % key_prefix, 60)
                self.link_config.redis.expire('%s:type' % key_prefix, 60)
                return True  # Continue periodic refresh
            return False  # Stop refresh
        except Exception as e:
            self.logger.debug('Could not refresh decoder registration: %s' % e)
            return True  # Try again next time

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.logger.info('Listening for stream on %s:%i' % (self.link_config.receiver_host, self.link_config.port))

    def _send_registration(self):
        """Send a small UDP registration packet to the repeater so it can
        learn the decoder's external IP:port and start forwarding to it.

        Returns True to keep the GLib timeout active.
        """
        try:
            # Target is the configured receiver_host/port (usually the repeater)
            target_host = self.link_config.get('receiver_host') or self.link_config.redis_host
            target_port = int(self.link_config.get('port') or self.link_config.port)

            # Build a simple registration message including node name
            msg = ('OPENOB_REGISTER:%s' % self.node_name).encode('utf-8')

            if hasattr(self, '_reg_socket') and self._reg_socket:
                try:
                    # Use sendto with hostname (will resolve)
                    self._reg_socket.sendto(msg, (target_host, target_port))
                    self.logger.debug('Sent registration to %s:%s' % (target_host, target_port))
                except Exception as e:
                    self.logger.debug('Failed to send registration packet: %s' % e)
        except Exception as e:
            self.logger.debug('Registration helper error: %s' % e)

        # Keep the timeout active
        return True

    def loop(self):
        try:
            self.main_loop = GLib.MainLoop()
            self.main_loop.run()
        except Exception as e:
            self.logger.exception('Encountered a problem in the MainLoop, tearing down the pipeline: %s' % e)
            self.pipeline.set_state(Gst.State.NULL)

    def build_pipeline(self):
        self.pipeline = Gst.Pipeline.new('rx')
        
        self.started = False
        bus = self.pipeline.get_bus()
        
        self.transport = self.build_transport()
        self.decoder = self.build_decoder()
        self.output = self.build_audio_interface()

        self.pipeline.add(self.transport)
        self.pipeline.add(self.decoder)
        self.pipeline.add(self.output)
        self.transport.link(self.decoder)
        self.decoder.link(self.output)

        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def build_audio_interface(self):
        self.logger.debug('Building audio output bin')
        bin = Gst.Bin.new('audio')

        # Audio output
        if self.audio_interface.type == 'auto':
            sink = Gst.ElementFactory.make('autoaudiosink')
        elif self.audio_interface.type == 'alsa':
            sink = Gst.ElementFactory.make('alsasink')
            sink.set_property('device', self.audio_interface.alsa_device)
        elif self.audio_interface.type == 'jack':
            sink = Gst.ElementFactory.make('jackaudiosink')
            if self.audio_interface.jack_auto:
                sink.set_property('connect', 'auto')
            else:
                sink.set_property('connect', 'none')
            sink.set_property('name', self.audio_interface.jack_name)
            sink.set_property('client-name', self.audio_interface.jack_name)
            if self.audio_interface.jack_port_pattern:
                sink.set_property('port-pattern', self.audio_interface.jack_port_pattern)
        elif self.audio_interface.type == 'test':
            sink = Gst.ElementFactory.make('fakesink')

        bin.add(sink)
        
        # Audio resampling and conversion
        resample = Gst.ElementFactory.make('audioresample')
        resample.set_property('quality', 9)
        bin.add(resample)

        convert = Gst.ElementFactory.make('audioconvert')
        bin.add(convert)

        # Our level monitor, also used for continuous audio
        level = Gst.ElementFactory.make('level')
        level.set_property('message', True)
        level.set_property('interval', 1000000000)
        bin.add(level)

        resample.link(convert)
        convert.link(level)
        level.link(sink)

        bin.add_pad(Gst.GhostPad.new('sink', resample.get_static_pad('sink')))

        return bin

    def build_decoder(self):
        self.logger.debug('Building decoder bin')
        bin = Gst.Bin.new('decoder')

        # Decoding and depayloading
        if self.link_config.encoding == 'opus':
            decoder = Gst.ElementFactory.make('opusdec', 'decoder')
            decoder.set_property('use-inband-fec', True)  # FEC
            decoder.set_property('plc', True)  # Packet loss concealment
            depayloader = Gst.ElementFactory.make(
                'rtpopusdepay', 'depayloader')
        elif self.link_config.encoding == 'pcm':
            depayloader = Gst.ElementFactory.make(
                'rtpL16depay', 'depayloader')
        else:
            self.logger.critical('Unknown encoding type %s' % self.link_config.encoding)
        
        bin.add(depayloader)

        bin.add_pad(Gst.GhostPad.new('sink', depayloader.get_static_pad('sink')))

        if 'decoder' in locals():
            bin.add(decoder)
            depayloader.link(decoder)
            bin.add_pad(Gst.GhostPad.new('src', decoder.get_static_pad('src')))
        else:
            bin.add_pad(Gst.GhostPad.new('src', depayloader.get_static_pad('src')))

        return bin

    def build_transport(self):
        self.logger.debug('Building RTP transport bin')
        bin = Gst.Bin.new('transport')

        caps = self.link_config.get('caps').replace('\\', '')
        udpsrc_caps = Gst.Caps.from_string(caps)
        
        # Where audio comes in
        udpsrc = Gst.ElementFactory.make('udpsrc', 'udpsrc')
        udpsrc.set_property('port', self.link_config.port)
        udpsrc.set_property('caps', udpsrc_caps)
        udpsrc.set_property('timeout', 3000000000)
        if self.link_config.multicast:
            udpsrc.set_property('auto_multicast', True)
            udpsrc.set_property('multicast_group', self.link_config.receiver_host)
            self.logger.info('Multicast mode enabled')
        bin.add(udpsrc)

        rtpbin = Gst.ElementFactory.make('rtpbin', 'rtpbin')
        rtpbin.set_property('latency', self.link_config.jitter_buffer)
        rtpbin.set_property('autoremove', True)
        rtpbin.set_property('do-lost', True)
        bin.add(rtpbin)

        udpsrc.link_pads('src', rtpbin, 'recv_rtp_sink_0')

        valve = Gst.ElementFactory.make('valve', 'valve')
        bin.add(valve)
        
        bin.add_pad(Gst.GhostPad.new('src', valve.get_static_pad('src')))
        # Attach callbacks for dynamic pads (RTP output) and busses
        rtpbin.connect('pad-added', self.rtpbin_pad_added)

        return bin

    # Our RTPbin won't give us an audio pad till it receives, so we need to
    # attach it here
    def rtpbin_pad_added(self, obj, pad):
        valve = self.transport.get_by_name('valve')
        rtpbin = self.transport.get_by_name('rtpbin')

        # Unlink first.
        rtpbin.unlink(valve)
        # Relink
        rtpbin.link(valve)

    def on_message(self, bus, message):
        if message.type == Gst.MessageType.ELEMENT:
            struct = message.get_structure()
            if struct != None:
                if struct.get_name() == 'level':
                    if self.started is False:
                        self.started = True
                        if len(struct.get_value('peak')) == 1:
                            self.logger.info('Receiving mono audio transmission')
                        else:
                            self.logger.info('Receiving stereo audio transmission')
                    else:
                        if len(struct.get_value('peak')) == 1:
                            self.logger.debug('Level: %.2f', struct.get_value('peak')[0])
                        else:
                            self.logger.debug('Levels: L %.2f R %.2f' % (struct.get_value('peak')[0], struct.get_value('peak')[1]))

                if struct.get_name() == 'GstUDPSrcTimeout':
                    # Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'rx-graph')                    
                    # Only UDP source configured to emit timeouts is the audio input
                    self.logger.critical('No data received for 3 seconds!')
                    if self.started:
                        self.logger.critical('Shutting down receiver for restart')
                        self.pipeline.set_state(Gst.State.NULL)
                        self.main_loop.quit()
        return True


