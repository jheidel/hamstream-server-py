import Queue
import pyaudio
import threading

import audiofilter

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
DEV_NAME = "USB Audio Device"


class AudioClient(threading.Thread):

  def __init__(self, name, listener, filtered):
    super(AudioClient, self).__init__()
    self.daemon = True
    self.data_queue = Queue.Queue(maxsize=100)
    self.stopped = threading.Event()

    self.name = name
    self.listener = listener
    self.filtered = filtered

  def stop(self):
    self.stopped.set()

  def put(self, data):
    self.data_queue.put(data)

  def run(self):
    me = 'audio client [%s, filtered=%s]' % (self.name, self.filtered)
    print '[START] %s' % me
    while True:
      try:
        data = self.data_queue.get(block=True, timeout=1)
      except Queue.Empty:
        continue
      if self.stopped.is_set():
        break
      self.listener(data)
    print '[STOP] %s' % me


class AudioSource(threading.Thread):

  def __init__(self):
    super(AudioSource, self).__init__()
    self.daemon = True
    self.stopped = threading.Event()
    self.audio_started = threading.Event()

    self.lock = threading.Lock()
    self.listeners = list()
    self.error_count = 0

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

  def wait_started(self):
    self.audio_started.wait(10)

  def stop_audio(self):
    self.stream.stop_stream()
    print "Stream terminated."

  def stop(self):
    self.stopped.set()
    self.join()

  def add_listener(self, *args, **kwargs):
    client = AudioClient(*args, **kwargs)
    client.start()
    with self.lock:
      self.listeners.append(client)

  def remove_listener(self, listener):
    with self.lock:
      client = (x for x in self.listeners if x.listener == listener).next()
      self.listeners.remove(client)
    client.stop()

  def num_listeners(self):
    return len(self.listeners)

  def run(self):
    self.init_audio()
    while not self.stopped.is_set():
      try:
        data = self.stream.read(CHUNK)
      except IOError as err:
        # TODO: track errors
        print 'IOError: %s' % err
        self.error_count += 1
        continue
      if data is None:
        print 'Error: empty read.'
        self.error_count += 1
        continue

      pdata = self.filt.process(data)
      if pdata is None:
        continue

      # Broadcast to filtered listeners.
      with self.lock:
        for listener in self.listeners:
          if listener.filtered:
            listener.listener(pdata)
          else:
            listener.listener(data)

    self.stop_audio()
