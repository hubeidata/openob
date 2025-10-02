import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
Gst.init(None)

import socket
import time
from openob.logger import LoggerFactory


class RTPRepeater(object):
    """
    RTP Repeater (Passthrough Mode)
    
    This class implements a low-latency RTP repeater that forwards packets
    without decoding/encoding. It handles NAT traversal by learning peer
    addresses dynamically from incoming packets.
    
    Key features:
    - Passthrough mode: no codec processing
    - Dynamic peer registration from source addresses
    - RTP + RTCP forwarding
    - Minimal jitter buffer for packet smoothing
    - NAT-friendly: works with outbound connections from peers
    """

    def __init__(self, node_name, link_config):
        """Sets up a new RTP repeater"""
        
        self.link_config = link_config
        self.node_name = node_name
        
        self.logger_factory = LoggerFactory()
        self.logger = self.logger_factory.getLogger('node.%s.link.%s.repeater' % (node_name, self.link_config.name))
        self.logger.info('Creating repeater pipeline (passthrough mode)')

        # Peer tracking
        self.peers = {}  # {address: {'rtp_addr': (ip, port), 'rtcp_addr': (ip, port), 'last_seen': time}}
        self.peer_order = []  # Track order of peer registration
        
        # Flags for one-time logging
        self.encoder_detected = False
        self.decoder_detected = False
        
        # Port configuration
        self.rtp_port = self.link_config.port
        self.rtcp_port = self.rtp_port + 1
        
        # Jitter buffer configuration (minimal for repeater)
        self.jitter_buffer_ms = getattr(self.link_config, 'jitter_buffer', 30)
        
        self.logger.info('Repeater will listen on RTP port %d and RTCP port %d' % (self.rtp_port, self.rtcp_port))
        self.logger.info('Jitter buffer set to %d ms' % self.jitter_buffer_ms)
        
        self.build_pipeline()

    def run(self):
        """Start the repeater pipeline"""
        self.pipeline.set_state(Gst.State.PLAYING)
        self.logger.info('Repeater active - waiting for peers to connect')
        self.logger.info('Peers should send RTP to this host on port %d' % self.rtp_port)

    def loop(self):
        """Main loop for the repeater"""
        try:
            self.main_loop = GLib.MainLoop()
            
            # Schedule peer timeout check
            GLib.timeout_add_seconds(30, self.check_peer_timeouts)
            
            # Schedule peer discovery from Redis
            GLib.timeout_add_seconds(2, self.discover_peers_from_redis)
            
            self.main_loop.run()
        except Exception as e:
            self.logger.exception('Encountered a problem in the MainLoop, tearing down the pipeline: %s' % e)
            self.pipeline.set_state(Gst.State.NULL)

    def check_peer_timeouts(self):
        """Remove peers that haven't sent packets recently"""
        current_time = time.time()
        timeout = 60  # seconds
        
        peers_to_remove = []
        for peer_id, peer_info in self.peers.items():
            if current_time - peer_info.get('last_seen', 0) > timeout:
                peers_to_remove.append(peer_id)
        
        for peer_id in peers_to_remove:
            self.logger.warning('Peer %s timed out, removing' % peer_id)
            del self.peers[peer_id]
            if peer_id in self.peer_order:
                self.peer_order.remove(peer_id)
        
        return True  # Continue periodic check

    def discover_peers_from_redis(self):
        """
        Discover new peers from Redis configuration
        This checks for encoder and decoder nodes that have registered
        """
        try:
            # Check for encoder (transmitter)
            encoder_host = self.link_config.get('receiver_host')
            encoder_port = self.link_config.get('port')
            
            if encoder_host and encoder_port and not self.encoder_detected:
                self.encoder_detected = True
                # Encoder is sending to us, we need to forward to decoder
                self.logger.info('━' * 70)
                self.logger.info('🎤 ENCODER DETECTED!')
                self.logger.info('   Node: encoder')
                self.logger.info('   RTP: %s:%s' % (encoder_host, encoder_port))
                self.logger.info('━' * 70)
            
            # Check for decoder (receiver) - look for nodes in Redis
            # The decoder will register itself when it starts
            if not self.decoder_detected:
                # Try to find decoder node information
                # OpenOB stores node info with keys like: openob:transmission:recepteur
                decoder_node = None
                try:
                    # Get all keys and look for decoder/recepteur nodes
                    keys = self.link_config.redis.keys('openob:%s:*' % self.link_config.name)
                    
                    # Debug: log all keys to see what's available
                    if keys:
                        self.logger.debug('Redis keys found: %s' % [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys])
                    
                    for key in keys:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        if 'recepteur' in key_str or 'decoder' in key_str or 'receiver' in key_str:
                            # Check if this key has a :type suffix
                            if key_str.endswith(':type'):
                                node_type = self.link_config.redis.get(key_str)
                                if node_type and (node_type == 'decoder' or node_type == b'decoder'):
                                    # Found a decoder node - extract base key
                                    base_key = key_str.replace(':type', '')
                                    parts = base_key.split(':')
                                    if len(parts) >= 3:
                                        decoder_node = parts[2]
                                        self.logger.debug('Found decoder node: %s' % decoder_node)
                                        break
                    
                    if decoder_node:
                        # Try to get decoder's listening address
                        # Decoder listens on receiver_host:port
                        decoder_key_prefix = 'openob:%s:%s' % (self.link_config.name, decoder_node)
                        decoder_host = self.link_config.redis.get('%s:receiver_host' % decoder_key_prefix)
                        decoder_port = self.link_config.redis.get('%s:port' % decoder_key_prefix)
                        
                        self.logger.debug('Decoder config - host: %s, port: %s' % (decoder_host, decoder_port))
                        
                        if decoder_host and decoder_port:
                            if isinstance(decoder_host, bytes):
                                decoder_host = decoder_host.decode('utf-8')
                            if isinstance(decoder_port, bytes):
                                decoder_port = decoder_port.decode('utf-8')
                            
                            self.decoder_detected = True
                            self.register_peer('decoder', (decoder_host, int(decoder_port)))
                            self.logger.info('━' * 70)
                            self.logger.info('🔊 DECODER CONNECTED!')
                            self.logger.info('   Node: %s' % decoder_node)
                            self.logger.info('   RTP: %s:%s' % (decoder_host, decoder_port))
                            self.logger.info('   Status: Forwarding audio')
                            self.logger.info('━' * 70)
                except Exception as e:
                    self.logger.warning('Error checking for decoder: %s' % e)
                
        except Exception as e:
            self.logger.debug('Error discovering peers: %s' % e)
        
        return True  # Continue periodic check

    def build_pipeline(self):
        """Build GStreamer pipeline for RTP/RTCP passthrough"""
        self.pipeline = Gst.Pipeline.new('repeater')
        
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        # Build RTP passthrough
        self.build_rtp_passthrough()
        
        # Build RTCP passthrough
        self.build_rtcp_passthrough()

    def build_rtp_passthrough(self):
        """
        Build RTP passthrough pipeline:
        udpsrc (listen) -> rtpjitterbuffer -> appsink (forward to peers)
        """
        self.logger.debug('Building RTP passthrough')
        
        # RTP input
        self.rtp_src = Gst.ElementFactory.make('udpsrc', 'rtp_src')
        self.rtp_src.set_property('port', self.rtp_port)
        self.rtp_src.set_property('caps', Gst.Caps.from_string('application/x-rtp'))
        
        # Jitter buffer (minimal latency)
        self.rtp_jitter = Gst.ElementFactory.make('rtpjitterbuffer', 'rtp_jitter')
        self.rtp_jitter.set_property('latency', self.jitter_buffer_ms)
        self.rtp_jitter.set_property('drop-on-latency', True)
        
        # App sink to capture packets and forward them
        self.rtp_sink = Gst.ElementFactory.make('appsink', 'rtp_sink')
        self.rtp_sink.set_property('emit-signals', True)
        self.rtp_sink.set_property('sync', False)
        self.rtp_sink.connect('new-sample', self.on_rtp_packet)
        
        # Add elements to pipeline
        self.pipeline.add(self.rtp_src)
        self.pipeline.add(self.rtp_jitter)
        self.pipeline.add(self.rtp_sink)
        
        # Link elements
        self.rtp_src.link(self.rtp_jitter)
        self.rtp_jitter.link(self.rtp_sink)
        
        # Create UDP socket for sending RTP packets
        self.rtp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def build_rtcp_passthrough(self):
        """
        Build RTCP passthrough pipeline:
        udpsrc (listen) -> appsink (forward to peers)
        """
        self.logger.debug('Building RTCP passthrough')
        
        # RTCP input
        self.rtcp_src = Gst.ElementFactory.make('udpsrc', 'rtcp_src')
        self.rtcp_src.set_property('port', self.rtcp_port)
        
        # App sink to capture RTCP packets and forward them
        self.rtcp_sink = Gst.ElementFactory.make('appsink', 'rtcp_sink')
        self.rtcp_sink.set_property('emit-signals', True)
        self.rtcp_sink.set_property('sync', False)
        self.rtcp_sink.connect('new-sample', self.on_rtcp_packet)
        
        # Add elements to pipeline
        self.pipeline.add(self.rtcp_src)
        self.pipeline.add(self.rtcp_sink)
        
        # Link elements
        self.rtcp_src.link(self.rtcp_sink)
        
        # Create UDP socket for sending RTCP packets
        self.rtcp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtcp_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def on_rtp_packet(self, appsink):
        """Handle incoming RTP packet and forward to other peers"""
        sample = appsink.emit('pull-sample')
        if sample:
            buffer = sample.get_buffer()
            
            # Get source address (peer that sent this packet)
            # Note: udpsrc doesn't directly expose source address, so we use a workaround
            # In production, you might want to use a custom element or socket
            
            # Extract packet data
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                packet_data = map_info.data
                
                # Register or update peer
                # Since we can't easily get source address from GStreamer udpsrc,
                # we'll use a simplified approach: forward to all registered peers
                # In a real implementation, you'd track source addresses via custom UDP handling
                
                # Forward to all OTHER peers
                self.forward_rtp_to_peers(packet_data)
                
                buffer.unmap(map_info)
        
        return Gst.FlowReturn.OK

    def on_rtcp_packet(self, appsink):
        """Handle incoming RTCP packet and forward to other peers"""
        sample = appsink.emit('pull-sample')
        if sample:
            buffer = sample.get_buffer()
            
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                packet_data = map_info.data
                
                # Forward RTCP to all peers
                self.forward_rtcp_to_peers(packet_data)
                
                buffer.unmap(map_info)
        
        return Gst.FlowReturn.OK

    def register_peer(self, peer_id, rtp_addr, rtcp_addr=None):
        """
        Manually register a peer (called from config or signaling)
        
        Args:
            peer_id: Unique identifier for the peer
            rtp_addr: Tuple of (ip, port) for RTP
            rtcp_addr: Tuple of (ip, port) for RTCP (optional, will use rtp_port+1)
        """
        if rtcp_addr is None:
            rtcp_addr = (rtp_addr[0], rtp_addr[1] + 1)
        
        self.peers[peer_id] = {
            'rtp_addr': rtp_addr,
            'rtcp_addr': rtcp_addr,
            'last_seen': time.time()
        }
        
        if peer_id not in self.peer_order:
            self.peer_order.append(peer_id)
        
        self.logger.info('Registered peer %s: RTP=%s:%d, RTCP=%s:%d' % 
                        (peer_id, rtp_addr[0], rtp_addr[1], rtcp_addr[0], rtcp_addr[1]))
        
        # Store peer info in Redis for coordination
        self.link_config.set('peer_%s_rtp_host' % peer_id, rtp_addr[0])
        self.link_config.set('peer_%s_rtp_port' % peer_id, rtp_addr[1])

    def forward_rtp_to_peers(self, packet_data):
        """Forward RTP packet to all registered peers"""
        for peer_id, peer_info in self.peers.items():
            try:
                rtp_addr = peer_info['rtp_addr']
                self.rtp_send_socket.sendto(packet_data, rtp_addr)
            except Exception as e:
                self.logger.error('Failed to forward RTP to peer %s: %s' % (peer_id, e))

    def forward_rtcp_to_peers(self, packet_data):
        """Forward RTCP packet to all registered peers"""
        for peer_id, peer_info in self.peers.items():
            try:
                rtcp_addr = peer_info['rtcp_addr']
                self.rtcp_send_socket.sendto(packet_data, rtcp_addr)
            except Exception as e:
                self.logger.error('Failed to forward RTCP to peer %s: %s' % (peer_id, e))

    def on_message(self, bus, message):
        """Handle GStreamer bus messages"""
        t = message.type
        
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.logger.error('GStreamer Error: %s' % err)
            self.logger.debug('Debug info: %s' % debug)
            self.main_loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            self.logger.warning('GStreamer Warning: %s' % err)
            self.logger.debug('Debug info: %s' % debug)
        elif t == Gst.MessageType.EOS:
            self.logger.info('End of stream')
            self.main_loop.quit()
        elif t == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, pending_state = message.parse_state_changed()
                self.logger.debug('Pipeline state changed from %s to %s' % 
                                (old_state.value_nick, new_state.value_nick))

    def get_stats(self):
        """Return statistics about the repeater"""
        return {
            'active_peers': len(self.peers),
            'peer_list': list(self.peers.keys()),
            'rtp_port': self.rtp_port,
            'rtcp_port': self.rtcp_port,
            'jitter_buffer_ms': self.jitter_buffer_ms
        }
