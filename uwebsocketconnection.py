import hashlib
import base64

class uWebSocketConnection():

    def ws_header(self, byte0, byte1):
        self.fin = (byte0 >> 7) & 1
        self.rsv1 = (byte0 >> 6) & 1
        self.rsv2 = (byte0 >> 5) & 1
        self.rsv3 = (byte0 >> 4) & 1
        self.opcode = byte0 & 0xf

        self.has_mask = (byte1 >> 7) & 1
        self.size = byte1 & 0x7f

    def send(self, message):
        packet = chr((1 << 7) | (0 << 6) | (0 << 5) | (0 << 4) | 1)
        packet += chr( 0 | len(message))
        packet += message
        self.raw_send(packet)

    def parse_packet(self):

        # get the header
        while len(self.queue) < 2:
            data = self.raw_recv()
            if not data:
                return None
            self.queue += data

        self.ws_header(ord(self.queue[0]), ord(self.queue[1]))
        self.queue = self.queue[2:]
        if self.has_mask == 1:
            while len(self.queue) < 4:
                data = self.raw_recv()
                if not data:
                    return None
                self.queue += data 
            # get the mask
            self.mask = self.queue[:4]
            self.queue = self.queue[4:]

        while len(self.queue) <  self.size:
            data = self.raw_recv()
            if not data:
                return None
            self.queue += data

        self.payload = self.queue[:self.size]
        self.queue = self.queue[self.size:]

        if self.has_mask:
            unmasked = bytearray(self.payload)
            mask = map(ord, self.mask)
            for i in range(self.size):
                unmasked[i] = unmasked[i] ^ mask[i%4] 
            return unmasked

        return self.payload
        

    def receiver(self):
        self.raw_send(self.headers)
        while True:
            message = self.parse_packet()
            if message is None:
                return
            self.onmessage(message)

    def handshake(self):
        sha1 = hashlib.sha1()
        sha1.update(self.environ['HTTP_SEC_WEBSOCKET_KEY'] + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
        sec_key = base64.b64encode(sha1.digest())

        return ("""%s 101 WebSocket Protocol Handshake\r
Upgrade: WebSocket\r
Connection: Upgrade\r
Sec-WebSocket-Origin: %s\r
Sec-WebSocket-Accept: %s\r\n\r\n""" % (self.environ['SERVER_PROTOCOL'], self.environ['HTTP_ORIGIN'], sec_key))

    def run(self):
        import socket
        self.socket = socket.fromfd(self.fd, socket.AF_INET, socket.SOCK_STREAM)
        self.receiver()

    def raw_send(self, data):
        self.socket.send(data)

    def raw_recv(self):
        return self.socket.recv(self.bufsize)

    def __init__(self, environ, fd):
        self.environ = environ
        self.fd = fd
        self.headers = self.handshake()
        self.queue = ''
        self.bufsize = 4096
        self.run()

class uGeventWebSocketConnection(uWebSocketConnection):

    def run(self):
        import gevent
        import gevent.socket
        self.socket = gevent.socket.fromfd(self.fd, gevent.socket.AF_INET, gevent.socket.SOCK_STREAM)
        self.runner = gevent.spawn(self.receiver)
        gevent.joinall([self.runner])

class uGreenWebSocketConnection(uWebSocketConnection):


    def run(self):
        self.receiver()
        

    def raw_recv(self):
        import uwsgi
        uwsgi.wait_fd_read(self.fd)
        uwsgi.suspend()
        return uwsgi.recv(self.fd, self.bufsize)

    def raw_send(self, data):
        import uwsgi
        uwsgi.send(self.fd, str(data))

