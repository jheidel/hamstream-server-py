import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import threading
import json

import audiosource

PORT = 8080
STATS_INTERVAL = 0.05


class AudioClient(tornado.websocket.WebSocketHandler):

  def initialize(self, audio):
    super(AudioClient, self).initialize()
    self.audio = audio

  def open(self):
    print 'new connection'
    self.set_nodelay(True)
    self.audio.add_listener(self.on_new_audio)

  def on_message(self, message):
    print 'audio message received: %s' % message

  def on_new_audio(self, data):
    # TODO: make this non-blocking
    try:
      self.write_message(data, binary=True)
    except Exception as err:
      print 'Socket audio write error: %s' % err

  def on_close(self):
    print 'connection closed'
    self.audio.remove_listener(self.on_new_audio)


class StatsClient(tornado.websocket.WebSocketHandler):

  def initialize(self, audio):
    super(StatsClient, self).initialize()
    self.audio = audio
    self.stopped = threading.Event()

  def open(self):
    print 'new stats connection'
    self.set_nodelay(True)
    thread = threading.Thread(target=self.run)
    thread.daemon = True
    thread.start()

  def on_message(self, message):
    print 'stats message received: %s' % message

  def on_close(self):
    self.stopped.set()
    print 'stats connection closed'

  def run(self):
    while not self.stopped.is_set():
      data = {
          'level': self.audio.filt.audio_level,
          'gain': self.audio.filt.gain,
          'aerrors': self.audio.error_count,
      }
      if not self.audio.filt.is_silent():
        self.write_message(json.dumps(data))
      self.stopped.wait(STATS_INTERVAL)


def main():
  audio = audiosource.AudioSource()
  audio.start()

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

  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(PORT)
  my_ip = socket.gethostbyname(socket.gethostname())
  print '*** Websocket Server Started at %s***' % my_ip
  tornado.ioloop.IOLoop.instance().start()

  audio.stop()


if __name__ == "__main__":
  main()
