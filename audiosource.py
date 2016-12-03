import pyaudio
import threading

import audiofilter

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
DEV_NAME = "USB Audio Device"


class AudioSource(threading.Thread):

  def __init__(self):
    super(AudioSource, self).__init__()
    self.daemon = True
    self.stopped = threading.Event()
    self.audio_started = threading.Event()

    self.lock = threading.Lock()
    self.listeners = list()

  def init_audio(self):
    self.filt = audiofilter.AudioFilter(samples_per_sec=RATE / CHUNK)

    audio = pyaudio.PyAudio()
    device_index = (
        x for x in range(audio.get_device_count())
        if DEV_NAME in audio.get_device_info_by_index(x)['name']).next()

    print "Opening audio device %s" % audio.get_device_info_by_index(
        device_index)
    self.stream = audio.open(
        format=FORMAT,
        input_device_index=device_index,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK)
    print "Stream started."
    self.audio_started.set()

  def stop_audio(self):
    self.stream.stop_stream()
    print "Stream terminated."

  def stop(self):
    self.stopped.set()
    self.join()

  def add_listener(self, listener):
    with self.lock:
      self.listeners.append(listener)

  def remove_listener(self, listener):
    with self.lock:
      self.listeners.remove(listener)

  def run(self):
    self.init_audio()
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

      pdata = self.filt.process(data)
      if pdata is None:
        continue

      # Broadcast to listeners.
      with self.lock:
        for listener in self.listeners:
          listener(pdata)

    self.stop_audio()
