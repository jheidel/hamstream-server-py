import wave
import speak
import os
from datetime import datetime as dt

SAVE_DIR = "/home/pi/record/"


class AudioLogger(object):

  def __init__(self, filt):
    self.filt = filt
    self.silent = True

  def open(self):
    ts = dt.now().strftime("%Y%m%d-%H%M%S")
    fn = "audio_%s.wav" % ts
    self.wv = wave.open(os.path.join(SAVE_DIR, fn), 'wb')
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
