import wave
import speak


class AudioLogger(object):

  def __init__(self, filt):
    self.filt = filt
    self.silent = True

  def open(self):
    self.wv = wave.open('testoutput.wav', 'wb')
    self.wv.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))

    self.wv.writeframes(speak.speak_rec_header())

  def close(self):
    self.wv.close()

  def on_new_audio(self, data):
    if not self.filt.is_silent():
      if self.silent:
        self.silent = False
        self.wv.writeframes(speak.speak_msg_header())
        print '[LOGGER] New header written.'
      self.wv.writeframes(data)
    else:
      self.silent = True
