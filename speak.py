import subprocess
import wave
import StringIO
import audioop
from datetime import datetime as dt

ESPEAK = "/usr/bin/espeak"


def speak(txt):
  out = subprocess.check_output([ESPEAK, '--stdout', txt])
  wave_file = StringIO.StringIO(out)
  wv = wave.open(wave_file)
  frames = wv.readframes(wv.getnframes())
  resamp_frames = audioop.ratecv(frames, 2,
                                 wv.getnchannels(),
                                 wv.getframerate(), 48000, None)
  return resamp_frames[0]


def speak_rec_header():

  def suffix(d):
    return 'th' if 11 <= d <= 13 else {
        1: 'st',
        2: 'nd',
        3: 'rd'
    }.get(d % 10, 'th')

  def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

  return speak('Radio stream recording from %s' % custom_strftime('%B {S}, %Y',
                                                                  dt.now()))


def speak_msg_header():
  now = dt.now()
  return speak('%s %s' % (now.hour, now.minute))
