
from os import path, devnull
import sys
import time
from collections import deque

import pyaudio
from pocketsphinx import *

nframes = 512 # 1/32 second
nmemory = 4 # number of frames for short term memory
muting = 0.2 # s stop listening after something was recognized
timeout = 1.0 # stop listening after this amount of silence
threshold = 10

class Processor():

	def __init__(self, keywordFile):
		pa = pyaudio.PyAudio()

		model_path = get_model_path()

		config = Decoder.default_config()
		config.set_string('-hmm', path.join(model_path, 'en-us'))
		config.set_string('-lm', path.join(model_path, 'en-us.lm.bin'))
		config.set_string('-dict', path.join(model_path, "cmudict-en-us.dict"))
		config.set_string("-logfn", devnull)

		self.decoder = Decoder(config)
		self.decoder.set_kws("keywords", keywordFile)
		self.decoder.set_search("keywords")

		self.microphone = pa.open(
				input=True,
				channels=1,
				rate=16000,
				format=pyaudio.paInt16,
				frames_per_buffer=nframes,
				start=False)

		self.active = False
		self.microphone.start_stream()
		self.buffer = bytearray(nframes)
		self.memory = deque(maxlen = nmemory)
		self.lastTrigger = 0

		self.callback = None

	def trigger_and_process(self):
		self.lastTrigger = time.time()
		if not self.active:
			print("?")
			self.decoder.start_utt()
			self.active = True

			for i in range(len(self.memory)):
				if self.process(self.memory[i]):
					break
		else:
			self.process(self.buffer)

	def sleep(self):
		if self.active:
			print("---")
			self.active = False
			self.decoder.end_utt()
			self.callback(None)

	def process(self, buf):
		self.decoder.process_raw(buf, False, False)
		hyp = self.decoder.hyp()
		if hyp:
			self.decoder.end_utt()
			print(hyp.hypstr)
			self.active = False
			self.microphone.stop_stream()
			if self.callback:
				self.callback(hyp.hypstr)
			time.sleep(muting)
			self.microphone.start_stream()
			return True
		else:
			return False

	def listen(self):
		self.memory.append(self.buffer)
		self.buffer = self.microphone.read(nframes)
		msbs = self.buffer[1::2]
		amp = max([a if a < 128 else 256-a for a in msbs])

		if amp > threshold:
			self.trigger_and_process()

		else:
			if time.time() > self.lastTrigger + timeout:
				self.sleep()
			elif self.active:
				self.process(self.buffer)
