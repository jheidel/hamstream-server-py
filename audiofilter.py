import numpy as np
import collections
import time

SILENCE_THRESH = 20

# History of peak data (in seconds)
PEAK_HIST_SEC = 1.0

GAIN_PER_SEC = 0.5

# How much faster gain decays
GAIN_NEG_MULT = 5

MAX_GAIN = 10

# duration to consider silence.
SILENCE_SEC = 5.0


class AudioFilter(object):

  def __init__(self, samples_per_sec):
    hsize = PEAK_HIST_SEC * samples_per_sec
    self.peakq = collections.deque(maxlen=hsize)

    # Peak value of the last sample, between 0 and 100
    self.audio_level = 0

    self.gain = 1.0
    self.gain_rate = GAIN_PER_SEC / samples_per_sec

    self.last_update = time.time()

  def is_silent(self):
    return time.time() - self.last_update > SILENCE_SEC

  def process(self, data):
    ndata = np.fromstring(data, np.int16)
    peak = np.abs(ndata).max()
    self.audio_level = float(peak) / (2**15 - 1)

    # Don't transmit this packet if it's silent.
    if peak < SILENCE_THRESH:
      return None

    # Boost gain based on PEAK_HIST_SEC
    self.peakq.append(peak)

    #peak_avg = sum(self.peakq) / len(self.peakq)
    peak_avg = max(self.peakq)

    gain = float(2**15 - 1) / float(peak_avg)
    gain = min(gain, MAX_GAIN)

    # Smooth out changes in gain
    if gain > self.gain:
      self.gain += self.gain_rate
    else:
      self.gain -= self.gain_rate * GAIN_NEG_MULT
    gain = self.gain

    # Hard limiter.
    gain = min(gain, float(2**15 - 1) / peak)

    ndata = (ndata * gain).clip(min=-2**15, max=2**15 - 1).astype(np.int16)

    self.last_update = time.time()
    return ndata.tostring()
