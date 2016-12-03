import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket

import audiosource

PORT = 8080


class AudioClient(tornado.websocket.WebSocketHandler):
  # pylint: disable=too-many-public-methods

  def initialize(self, audio):
    super(AudioClient, self).initialize()
    self.audio = audio

  def open(self):
    print 'new connection'
    self.set_nodelay(True)
    self.audio.add_listener(self.on_new_audio)

  def on_message(self, message):
    print 'message received: %s' % message

  def on_new_audio(self, data):
    # TODO: make this non-blocking
    self.write_message(data, binary=True)

  def on_close(self):
    print 'connection closed'
    self.audio.remove_listener(self.on_new_audio)


def main():
  audio = audiosource.AudioSource()
  audio.start()

  # TODO timeout waiting for audio init.
  audio.audio_started.wait()

  application = tornado.web.Application([(r'/ws', AudioClient, {
      'audio': audio
  }),])

  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(PORT)
  my_ip = socket.gethostbyname(socket.gethostname())
  print '*** Websocket Server Started at %s***' % my_ip
  tornado.ioloop.IOLoop.instance().start()

  audio.stop()


if __name__ == "__main__":
  main()
