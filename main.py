import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket

import threading
import time

import sys

import pyaudio
import numpy as np

import collections

CHUNK = 1024

class PeriodicWriter(threading.Thread):
    def __init__(self, ws):
        super(PeriodicWriter, self).__init__()
        self.ws = ws
        self.daemon = True
        self.stopped = threading.Event()
        self.count = 1

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 48000

        DEV_NAME = "USB Audio Device"

        audio = pyaudio.PyAudio()

        device_index = (x for x in range(audio.get_device_count()) if DEV_NAME in audio.get_device_info_by_index(x)['name']).next()

        print "Found audio device %s" % audio.get_device_info_by_index(device_index)

# start Recording
        self.stream = audio.open(format=FORMAT, input_device_index=device_index, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
        print "recording..."

        PEAK_HSEC = 1.0

        h_framelen = RATE / CHUNK
        self.peakq = collections.deque(maxlen=h_framelen)

        # How fast gain can be adjusted.
        self.gain = 1.0
        self.gain_rate = 0.5 / (RATE / CHUNK)

        # Drop gain faster
        self.gain_neg = 5

    def stop(self):
        self.stopped.set()

    def run(self):

        # TODO: support multiple consumers.

        imod = 0

        while not self.stopped.is_set():
            try:
                data = self.stream.read(CHUNK)
            except IOError as err:
                # TODO: track errors
                print 'IOError: %s' % err
                continue

            if data is None:
                print 'Error: empty read.'
                continue

            ndata = np.fromstring(data, np.int16)
            peak = np.abs(ndata).max()

            # Don't transmit this packet if it's silent.
            if peak < 20:
                continue

            # Boost gain based on PEAK_HSEC
            self.peakq.append(peak)

            #peak_avg = sum(self.peakq) / len(self.peakq)
            peak_avg = max(self.peakq)

            gain = float(2**15-1) / float(peak_avg)
            gain = min(gain, 10)

            # Smooth out changes in gain
            if gain > self.gain:
                self.gain += self.gain_rate
            else:
                self.gain -= self.gain_rate * self.gain_neg
            gain = self.gain

            # Hard limiter.
            gain = min(gain, float(2**15-1) / peak)

            ndata = (ndata * gain).clip(min=-2**15, max=2**15-1).astype(np.int16)
            data = ndata.tostring()

            print str(gain)

            if self.ws.is_open:
                self.ws.write_message(data, binary=True)
                self.count += 1

        print 'Stop stream.'
        self.stream.stop_stream()



class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print 'new connection'
        self.is_open = True
        self.t = PeriodicWriter(self)
        self.t.start()

    def on_message(self, message):
        print 'message received: %s' % message
        # Reverse Message and send it back
        print 'sending back message: %s' % message[::-1]
        self.write_message(message[::-1])

    def on_close(self):
        print 'connection closed'
        self.is_open = False
        self.t.stop()
        self.t.join()

    def check_origin(self, origin):
        return True

application = tornado.web.Application([
    (r'/ws', WSHandler),
])


if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8080)
    myIP = socket.gethostbyname(socket.gethostname())
    print '*** Websocket Server Started at %s***' % myIP
    tornado.ioloop.IOLoop.instance().start()
