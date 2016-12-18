#!/usr/bin/env python

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import threading
import json
import signal
import time
from RPi import GPIO

import audiosource
import audiologger
import commands

PORT = 8080
STATS_INTERVAL = 1. / 15

GPIO_LED_PIN = 22


class PiFlasher(threading.Thread):

  def __init__(self):
    super(PiFlasher, self).__init__()
    self.stopped = threading.Event()

  def stop(self):
    self.stopped.set()
    self.join()

  def run(self):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(GPIO_LED_PIN, GPIO.OUT)
    while not self.stopped.is_set():
      GPIO.output(GPIO_LED_PIN, GPIO.HIGH)
      time.sleep(0.1)
      GPIO.output(GPIO_LED_PIN, GPIO.LOW)
      time.sleep(0.3)


class AudioClient(tornado.websocket.WebSocketHandler):

  def initialize(self, audio):
    super(AudioClient, self).initialize()
    self.audio = audio

  def open(self):
    print '[CONNECT] audio: %s' % self.request.remote_ip
    self.set_nodelay(True)
    self.audio.add_listener(
        name='stream %s' % self.request.remote_ip,
        listener=self.on_new_audio,
        filtered=True)

  def on_message(self, message):
    print 'audio message received: %s' % message

  def on_new_audio(self, data):
    try:
      self.write_message(data, binary=True)
    except Exception as err:
      print 'Socket audio write error: %s' % err

  def on_close(self):
    print '[DISCONNECT] audio: %s' % self.request.remote_ip
    self.audio.remove_listener(self.on_new_audio)


class StatsClient(tornado.websocket.WebSocketHandler):

  def initialize(self, audio):
    super(StatsClient, self).initialize()
    self.audio = audio
    self.stopped = threading.Event()

  def open(self):
    print '[CONNECT] stats: %s' % self.request.remote_ip
    self.set_nodelay(True)
    self.thread = threading.Thread(target=self.run)
    self.thread.daemon = True
    self.thread.start()

  def on_message(self, message):
    print 'stats message received: %s' % message

    # TODO: make this json
    if "shutdown" in message:
      commands.shutdown()

  def on_close(self):
    print '[DISCONNECT] stats: %s' % self.request.remote_ip
    self.stop()

  def stop(self):
    self.stopped.set()
    self.thread.join()

  def run(self):
    while not self.stopped.is_set():
      if self.audio.stopped.is_set():
        # TODO: a bit of a hack.
        break
      data = {
          'level': self.audio.filt.audio_level,
          'gain': self.audio.filt.gain,
          'aerrors': self.audio.error_count,
          'clients': self.audio.num_listeners(),
      }
      if not self.audio.filt.is_silent():
        self.write_message(json.dumps(data))
      self.stopped.wait(STATS_INTERVAL)


def main():
  audio = audiosource.AudioSource()
  audio.start()
  audio.wait_started()

  alogger = audiologger.AudioLogger(filt=audio.filt)
  alogger.open()
  audio.add_listener(
      name='wave_writer', listener=alogger.on_new_audio, filtered=False)

  # TODO timeout waiting for audio init.
  audio.audio_started.wait()

  application = tornado.web.Application([
      (r'/audio', AudioClient, {
          'audio': audio
      }),
      (r'/stats', StatsClient, {
          'audio': audio
      }),
  ])

  flasher = PiFlasher()
  flasher.start()

  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(PORT)
  my_ip = socket.gethostbyname(socket.gethostname())

  def server_shutdown(signum, stack):
    print 'Server shutdown'
    tornado.ioloop.IOLoop.instance().stop()

  signal.signal(signal.SIGINT, server_shutdown)
  signal.signal(signal.SIGTERM, server_shutdown)

  print '*** Websocket Server Started at %s***' % my_ip
  tornado.ioloop.IOLoop.instance().start()

  print 'graceful shutdown'
  flasher.stop()
  alogger.close()
  audio.stop()

  print 'exit'


if __name__ == "__main__":
  main()
