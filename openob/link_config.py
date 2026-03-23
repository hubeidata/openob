import redis
import time
from openob.logger import LoggerFactory


class LinkConfig(object):

    """
        The LinkConfig class encapsulates link configuration. It's genderless;
        a TX node should be able to set up a new link and an RX node should be
        able (once the TX node has specified the port caps) to configure itself
        to receive the stream using the data and methods in this config.
    """

    def __init__(self, link_name, redis_host, max_retries=120, initial_delay=0.1, max_delay=5.0, socket_timeout=3.0):
        """
            Set up a new LinkConfig instance - needs to know the link name and
            configuration host. The redis_host can be host or host:port.

            max_retries: number of attempts before failing.
            initial_delay: first retry delay in seconds.
            max_delay: maximum exponential backoff delay.
            socket_timeout: redis socket connect/read timeout in seconds.
        """
        self.int_properties = ['port', 'jitter_buffer', 'opus_framesize', 'opus_complexity', 'bitrate', 'opus_loss_expectation']
        self.bool_properties = ['opus_dtx', 'opus_fec', 'multicast']
        self.link_name = link_name
        self.redis_host = redis_host
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.socket_timeout = socket_timeout
        self.logger_factory = LoggerFactory()
        self.logger = self.logger_factory.getLogger('link.%s.config' % self.link_name)
        self.logger.info("Connecting to configuration host %s" % self.redis_host)
        self.redis = None

        host = self.redis_host
        port = 6379
        if ':' in self.redis_host:
            try:
                host, port_str = self.redis_host.rsplit(':', 1)
                port = int(port_str)
            except ValueError:
                self.logger.warning("Invalid redis port in %s, using default 6379" % self.redis_host)
                host = self.redis_host
                port = 6379

        attempt = 0
        delay = self.initial_delay
        while attempt < self.max_retries:
            attempt += 1
            try:
                # Try a few constructor variants for broad redis-py compatibility.
                last_err = None
                client = None
                for variant in ("encoding", "charset", "minimal"):
                    try:
                        if variant == "encoding":
                            client = redis.StrictRedis(
                                host=host,
                                port=port,
                                encoding="utf-8",
                                decode_responses=True,
                                socket_connect_timeout=self.socket_timeout,
                                socket_timeout=self.socket_timeout,
                            )
                        elif variant == "charset":
                            client = redis.StrictRedis(
                                host=host,
                                port=port,
                                charset="utf-8",
                                decode_responses=True,
                                socket_connect_timeout=self.socket_timeout,
                                socket_timeout=self.socket_timeout,
                            )
                        else:  # "minimal" – no encoding kwargs at all
                            client = redis.StrictRedis(
                                host=host,
                                port=port,
                                socket_connect_timeout=self.socket_timeout,
                                socket_timeout=self.socket_timeout,
                            )
                        break
                    except TypeError as e:
                        # Parameter mismatch for this redis-py version – try next style.
                        last_err = e
                        client = None

                if client is None:
                    raise last_err or Exception("Unable to construct Redis client")

                self.redis = client
                self.redis.ping()
                self.logger.info("Connected to configuration host on attempt %d", attempt)
                return
            except Exception as e:
                self.logger.error(
                    "Unable to connect to configuration host (attempt %d/%d): %s",
                    attempt,
                    self.max_retries,
                    e,
                )
                if attempt >= self.max_retries:
                    self.logger.error("Reached maximum retries (%d), aborting.", self.max_retries)
                    raise
                time.sleep(delay)
                delay = min(self.max_delay, delay * 1.5)

    def blocking_get(self, key):
        """Get a value, blocking until it's not None if needed"""
        while True:
            value = self.get(key)
            if value is not None:
                self.logger.debug("Fetched (blocking) %s, got %s" % (key, value))
                return value
            time.sleep(0.1)

    def set(self, key, value):
        """Set a value in the config store"""
        scoped_key = self.scoped_key(key)

        if key in self.bool_properties:
            value = int(value)
        
        self.redis.set(scoped_key, value)
        self.logger.debug("Set %s to %s" % (scoped_key, value))
        return value

    def get(self, key):
        """Get a value from the config store"""
        scoped_key = self.scoped_key(key)
        value = self.redis.get(scoped_key)
        
        # Do some typecasting
        if key in self.int_properties:
            value = int(value)
        if key in self.bool_properties:
            value = (value == 'True')
        self.logger.debug("Fetched %s, got %s" % (scoped_key, value))
        return value

    def unset(self, key):
        scoped_key = self.scoped_key(key)
        self.redis.delete(scoped_key)
        self.logger.debug("Unset %s" % scoped_key)

    def __getattr__(self, key):
        """Convenience method to access get"""
        return self.get(key)

    def scoped_key(self, key):
        """Return an appropriate key name scoped to a link"""
        return ("openob:%s:%s" % (self.link_name, key))

    def set_from_argparse(self, opts):
        """Given an optparse object from bin/openob, configure this link"""
        self.set("name", opts.link_name)
        # jitter_buffer is a receiver-side concept (rtpbin latency), but this
        # value is stored in the shared config so either end can set it.
        if hasattr(opts, 'jitter_buffer'):
            self.set("jitter_buffer", opts.jitter_buffer)

        if opts.mode == "tx":
            self.set("port", opts.port)
            self.set("encoding", opts.encoding)
            self.set("bitrate", opts.bitrate)
            self.set("multicast", opts.multicast)
            self.set("input_samplerate", opts.samplerate)
            self.set("receiver_host", opts.receiver_host)
            self.set("opus_framesize", opts.framesize)
            self.set("opus_complexity", opts.complexity)
            self.set("opus_fec", opts.fec)
            self.set("opus_loss_expectation", opts.loss)
            self.set("opus_dtx", opts.dtx)

    def commit_changes(self, restart=False):
        """
            To be called after calls to set() on a running link to signal
            a reconfiguration event for that link. If restart is True, the link
            should simply terminate itself so it can be restarted with the new
            parameters. If restart is False, the link should set all parameters
            it can which do not involve a restart.
        """
        raise(NotImplementedError, "Link reconfiguration is not yet implemented")
