
import sys
import time
import os
import json

from pydub import AudioSegment
from pydub.playback import play

from processor import Processor

if len(sys.argv) != 4:
	print("usage: " + sys.argv[0] + " wakeword keywordFile commandFile")
	quit()

path, wakeword, keywordFile, commandFile = sys.argv

with open(commandFile) as fid:
    commands = json.load(fid)

wake = AudioSegment.from_wav("sounds/87035_active.wav")
ok = AudioSegment.from_wav("sounds/320181_ok.wav")
nack = AudioSegment.from_wav("sounds/426888_error.wav")

proc = Processor(keywordFile)

awaiting = False
since = 0

def awaitCmd():
	global awaiting, since
	awaiting = True
	since = time.time()
	play(wake)

def cb(word):
	global awaiting, since
	if awaiting:
		awaiting = False
		if word and word in commands:
			play(ok)
			os.system(commands[word])
		else:
			play(nack)
	else:
		if word == wakeword:
			awaitCmd()

proc.callback = cb

while True:
	proc.listen()
	if awaiting and time.time() > since + 3.0:
		awaiting = False
		play(nack)
