import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
Gst.init(None)

import socket
import time
import threading
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
        
        # Packet counters for statistics
        self.rtp_packet_count = 0
        self.rtcp_packet_count = 0
        
        # Port configuration
        self.rtp_port = self.link_config.port
        self.rtcp_port = self.rtp_port + 1
        
        # Jitter buffer configuration (minimal for repeater)
        self.jitter_buffer_ms = getattr(self.link_config, 'jitter_buffer', 30)
        
        self.logger.info('Repeater will listen on RTP port %d and RTCP port %d' % (self.rtp_port, self.rtcp_port))
        self.logger.info('Jitter buffer set to %d ms' % self.jitter_buffer_ms)
        
        # Clean up old peer registrations from Redis
        self._cleanup_old_peer_data()
        
        # Running flag for threads
        self.running = False
        
        self.build_sockets()

    def _cleanup_old_peer_data(self):
        """Clean up old peer registrations from previous sessions"""
        try:
            # Find all peer-related keys for this link
            pattern = 'openob:%s:*' % self.link_config.name
            keys = self.link_config.redis.keys(pattern)
            
            # Check which keys have TTL (active peers) vs no TTL (stale data)
            deleted_count = 0
            for key in keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                # Delete keys that look like peer registrations
                if any(x in key_str for x in [':receiver_host', ':port', ':type']):
                    # Check if it's a peer key (has node name like recepteur, emetteur, etc)
                    parts = key_str.split(':')
                    if len(parts) >= 3:
                        # Keep main transmission config, delete node-specific peer data
                        node_name = parts[2]
                        if node_name not in ['caps', 'encoding', 'bitrate', 'port', 
                                               'receiver_host', 'name', 'input_samplerate',
                                               'jitter_buffer', 'multicast', 'opus_complexity',
                                               'opus_dtx', 'opus_fec', 'opus_framesize',
                                               'opus_loss_expectation']:
                            # Check if key has TTL (active decoder)
                            ttl = self.link_config.redis.ttl(key_str)
                            if ttl == -1:  # No TTL = stale data from crashed process
                                self.link_config.redis.delete(key_str)
                                deleted_count += 1
                            elif ttl > 0:
                                # Active peer, keep it
                                self.logger.info('Found active peer data: %s (TTL: %ds)' % (key_str, ttl))
            
            if deleted_count > 0:
                self.logger.info('Cleaned up %d stale peer registration(s) from Redis' % deleted_count)
        except Exception as e:
            self.logger.warning('Could not cleanup old peer data: %s' % e)

    def build_sockets(self):
        """Build UDP sockets for RTP/RTCP passthrough (pure Python, no GStreamer)"""
        self.logger.info('Building UDP socket repeater (pure Python mode)')
        
        # RTP receive socket
        self.rtp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rtp_recv_socket.bind(('0.0.0.0', self.rtp_port))
        self.rtp_recv_socket.settimeout(0.1)  # 100ms timeout for clean shutdown
        
        # RTCP receive socket
        self.rtcp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtcp_recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rtcp_recv_socket.bind(('0.0.0.0', self.rtcp_port))
        self.rtcp_recv_socket.settimeout(0.1)
        
        # RTP send socket
        self.rtp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # RTCP send socket
        self.rtcp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtcp_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.logger.info('UDP sockets created: RTP=%d, RTCP=%d' % (self.rtp_port, self.rtcp_port))
        self.logger.info('Ready to receive and forward packets')

    def run(self):
        """Start the repeater (socket-based)"""
        self.running = True
        self.logger.info('Repeater active - waiting for peers to connect')
        self.logger.info('Peers should send RTP to this host on port %d' % self.rtp_port)
        
        # Start receiver threads
        self.rtp_thread = threading.Thread(target=self._rtp_receiver_thread, daemon=True)
        self.rtcp_thread = threading.Thread(target=self._rtcp_receiver_thread, daemon=True)
        
        self.rtp_thread.start()
        self.rtcp_thread.start()

    def _rtp_receiver_thread(self):
        """Thread that receives and forwards RTP packets"""
        self.logger.info('RTP receiver thread started')
        
        while self.running:
            try:
                data, addr = self.rtp_recv_socket.recvfrom(2048)
                
                # Count packets
                self.rtp_packet_count += 1
                
                # Detect encoder on first packet
                if not self.encoder_detected:
                    self.encoder_detected = True
                    encoder_host = self.link_config.get('receiver_host')
                    encoder_port = self.link_config.get('port')
                    self.logger.info('━' * 70)
                    self.logger.info('🎤 ENCODER DETECTED!')
                    self.logger.info('   Receiving from: %s:%d' % addr)
                    if encoder_host and encoder_port:
                        self.logger.info('   Expected: %s:%s' % (encoder_host, encoder_port))
                    self.logger.info('   Status: Active transmission')
                    if len(self.peers) > 0:
                        self.logger.info('   Forwarding to %d peer(s)' % len(self.peers))
                        self.logger.info('   🔴 AUDIO STREAMING NOW!')
                    else:
                        self.logger.info('   ⚠️  No decoders registered yet')
                    self.logger.info('━' * 70)
                
                # Log every 5000 packets (about every 100 seconds)
                if self.rtp_packet_count % 5000 == 0:
                    self.logger.info('📊 RTP: packet #%d, %d peer(s)' % (self.rtp_packet_count, len(self.peers)))
                
                # Forward to all peers
                self.forward_rtp_to_peers(data)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error('Error in RTP receiver: %s' % e)
        
        self.logger.info('RTP receiver thread stopped')

    def _rtcp_receiver_thread(self):
        """Thread that receives and forwards RTCP packets"""
        self.logger.info('RTCP receiver thread started')
        
        while self.running:
            try:
                data, addr = self.rtcp_recv_socket.recvfrom(2048)
                
                # Count packets
                self.rtcp_packet_count += 1
                
                # Forward to all peers
                self.forward_rtcp_to_peers(data)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error('Error in RTCP receiver: %s' % e)
        
        self.logger.info('RTCP receiver thread stopped')

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
        This checks for decoder nodes that have registered
        """
        try:
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
                            if self.encoder_detected:
                                self.logger.info('   Status: Receiving audio from encoder')
                                self.logger.info('   📡 Ready to forward packets')
                            else:
                                self.logger.info('   Status: Waiting for encoder...')
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
        udpsrc (listen) -> appsink (forward to peers)
        Note: Using direct path without jitterbuffer for immediate forwarding
        """
        self.logger.debug('Building RTP passthrough (direct mode)')
        
        # RTP input
        self.rtp_src = Gst.ElementFactory.make('udpsrc', 'rtp_src')
        self.rtp_src.set_property('port', self.rtp_port)
        self.rtp_src.set_property('caps', Gst.Caps.from_string('application/x-rtp'))
        
        self.logger.info('UDP source configured on port %d' % self.rtp_port)
        
        # App sink to capture packets and forward them
        self.rtp_sink = Gst.ElementFactory.make('appsink', 'rtp_sink')
        self.rtp_sink.set_property('emit-signals', True)
        self.rtp_sink.set_property('sync', False)
        self.rtp_sink.set_property('max-buffers', 1)  # Keep only latest buffer
        self.rtp_sink.set_property('drop', True)  # Drop old buffers
        self.rtp_sink.connect('new-sample', self.on_rtp_packet)
        
        # Add elements to pipeline
        self.pipeline.add(self.rtp_src)
        self.pipeline.add(self.rtp_sink)
        
        # Link elements directly (no jitterbuffer for now)
        self.rtp_src.link(self.rtp_sink)
        
        self.logger.info('RTP pipeline: udpsrc -> appsink (direct forwarding)')
        
        # Create UDP socket for sending RTP packets
        self.rtp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def on_rtp_probe(self, pad, info):
        """Probe callback to detect RTP packets at udpsrc level and forward them"""
        # Count packets
        self.rtp_packet_count += 1
        
        # Detect encoder on first RTP packet received  
        if not self.encoder_detected:
            self.encoder_detected = True
            encoder_host = self.link_config.get('receiver_host')
            encoder_port = self.link_config.get('port')
            self.logger.info('━' * 70)
            self.logger.info('🎤 ENCODER DETECTED!')
            self.logger.info('   Receiving RTP packets')
            if encoder_host and encoder_port:
                self.logger.info('   Expected from: %s:%s' % (encoder_host, encoder_port))
            self.logger.info('   Status: Active transmission')
            if len(self.peers) > 0:
                self.logger.info('   Forwarding to %d peer(s): %s' % (len(self.peers), ', '.join(self.peers.keys())))
                self.logger.info('   🔴 AUDIO STREAMING NOW!')
            else:
                self.logger.info('   ⚠️  No decoders registered yet')
            self.logger.info('━' * 70)
        
        # Log every 100 packets for monitoring (roughly every 2 seconds)
        if self.rtp_packet_count % 100 == 0:
            self.logger.info('📊 Probe active: packet #%d, %d peer(s)' % (self.rtp_packet_count, len(self.peers)))
        
        # Get buffer and forward
        probe_type = info.type
        buffer = None
        
        if probe_type & Gst.PadProbeType.BUFFER:
            buffer = info.get_buffer()
        elif probe_type & Gst.PadProbeType.BUFFER_LIST:
            # Handle buffer list
            buffer_list = info.get_buffer_list()
            if buffer_list and buffer_list.length() > 0:
                buffer = buffer_list.get(0)
        
        if buffer:
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                packet_data = map_info.data
                self.forward_rtp_to_peers(packet_data)
                buffer.unmap(map_info)
        
        return Gst.PadProbeReturn.OK

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
            # Count packets
            self.rtp_packet_count += 1
            
            # Detect encoder on first RTP packet received
            if not self.encoder_detected:
                self.encoder_detected = True
                encoder_host = self.link_config.get('receiver_host')
                encoder_port = self.link_config.get('port')
                self.logger.info('━' * 70)
                self.logger.info('🎤 ENCODER DETECTED!')
                self.logger.info('   Receiving RTP packets')
                if encoder_host and encoder_port:
                    self.logger.info('   Expected from: %s:%s' % (encoder_host, encoder_port))
                self.logger.info('   Status: Active transmission')
                if len(self.peers) > 0:
                    self.logger.info('   Forwarding to %d peer(s): %s' % (len(self.peers), ', '.join(self.peers.keys())))
                    self.logger.info('   🔴 AUDIO STREAMING NOW!')
                else:
                    self.logger.info('   ⚠️  No decoders registered yet')
                self.logger.info('━' * 70)
            
            # Log every 100 packets
            if self.rtp_packet_count % 100 == 0:
                self.logger.info('📊 Packet #%d received, %d peer(s)' % (self.rtp_packet_count, len(self.peers)))
            
            buffer = sample.get_buffer()
            
            # Extract packet data
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                packet_data = map_info.data
                
                # Forward to all registered peers
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
        # If no peers, nothing to do
        if len(self.peers) == 0:
            return
            
        # Log first successful forward
        if not hasattr(self, '_first_forward_logged'):
            self._first_forward_logged = True
            self._forward_count = 0
            self.logger.info('━' * 70)
            self.logger.info('📡 STARTING RTP FORWARDING')
            self.logger.info('   Packets/second: ~%d (48kHz stereo PCM)' % (48000 / 960))  # Approx for 20ms frames
            self.logger.info('   Forwarding to %d peer(s):' % len(self.peers))
            for peer_id, peer_info in self.peers.items():
                # Handle both old rtp_addr format and new host/port format
                if 'rtp_addr' in peer_info:
                    rtp_host, rtp_port = peer_info['rtp_addr']
                else:
                    rtp_host = peer_info['host']
                    rtp_port = peer_info['port']
                self.logger.info('   → %s at %s:%d' % (peer_id, rtp_host, rtp_port))
            self.logger.info('   🔴 AUDIO FLOWING!')
            self.logger.info('━' * 70)
        
        self._forward_count = getattr(self, '_forward_count', 0) + 1
        
        # Log every 50000 forwards (roughly every 1000 seconds / 16 minutes)
        if self._forward_count % 50000 == 0:
            self.logger.info('📊 Stats: Forwarded %d RTP packets to %d peer(s)' % (self._forward_count, len(self.peers)))
        
        for peer_id, peer_info in self.peers.items():
            try:
                # Handle both old rtp_addr format and new host/port format
                if 'rtp_addr' in peer_info:
                    rtp_addr = peer_info['rtp_addr']
                else:
                    rtp_addr = (peer_info['host'], peer_info['port'])
                
                bytes_sent = self.rtp_send_socket.sendto(packet_data, rtp_addr)
                # Update last_seen
                peer_info['last_seen'] = time.time()
            except Exception as e:
                self.logger.error('Failed to forward RTP to peer %s: %s' % (peer_id, e))

    def forward_rtcp_to_peers(self, packet_data):
        """Forward RTCP packet to all registered peers"""
        if len(self.peers) == 0:
            return
            
        # Log first forward for debugging
        if not hasattr(self, '_first_rtcp_forward_logged'):
            self._first_rtcp_forward_logged = True
            self.logger.info('Starting to forward RTCP packets to %d peer(s)' % len(self.peers))
        
        for peer_id, peer_info in self.peers.items():
            try:
                # Handle both old rtcp_addr format and new host/port format
                if 'rtcp_addr' in peer_info:
                    rtcp_addr = peer_info['rtcp_addr']
                else:
                    rtcp_addr = (peer_info['host'], peer_info['port'] + 1)
                
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
                # Log when pipeline reaches PLAYING state
                if new_state == Gst.State.PLAYING:
                    self.logger.info('Pipeline is now PLAYING - ready to receive packets')
        elif t == Gst.MessageType.ELEMENT:
            # Log element messages for debugging
            struct = message.get_structure()
            if struct:
                self.logger.debug('Element message: %s' % struct.to_string())

    def get_stats(self):
        """Return statistics about the repeater"""
        return {
            'active_peers': len(self.peers),
            'peer_list': list(self.peers.keys()),
            'rtp_port': self.rtp_port,
            'rtcp_port': self.rtcp_port,
            'jitter_buffer_ms': self.jitter_buffer_ms
        }
