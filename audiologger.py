import wave


class AudioLogger(object):

  def __init__(self, filt):
    self.filt = filt

  def open(self):
    self.wv = wave.open('testoutput.wav', 'wb')
    self.wv.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))

  def close(self):
    self.wv.close()

  def on_new_audio(self, data):
    if not self.filt.is_silent():
      self.wv.writeframes(data)
