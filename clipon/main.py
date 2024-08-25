import evdev
import os
import time
import logging

os.environ["LIBCAMERA_LOG_LEVELS"] = "*:3"
logging.getLogger("picamera2").setLevel(logging.WARNING)
start = time.time()

from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder

picam = None
for i in range(10):
    try:
        picam = Picamera2()
        break
    except IndexError:
        print("Camera not found, retrying...")
        time.sleep(2)

if picam is None:
    print("Failed to initialize the camera after multiple attempts.")
    exit(1)
print("Setup in", str(time.time() - start), "seconds")

os.system("echo none | sudo tee /sys/class/leds/ACT/trigger > /dev/null 2>&1")
os.system("echo 0 | sudo tee /sys/class/leds/ACT/brightness > /dev/null 2>&1")
device = None
recording = False
ledon = False
switchtime = 0
encoder = H264Encoder(bitrate=10000000)
for i in range(20):
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for blue in devices:
		if "Ambertronix Consumer Control" == blue.name:
			device = blue
			print("Found device")
			break
	if device is not None:
		break
	if device is None:
		print("Didn't find device")
		time.sleep(2)
if device is None:
	print("Couldn't find the device")
	exit()
while True:
    if len(device.active_keys()) == 1:
        print("Button pressed")
        if not recording:
            os.system("echo 1 | sudo tee /sys/class/leds/ACT/brightness > /dev/null 2>&1")
            t = time.localtime()
            current_time = time.strftime("%Y-%m-%d_%H-%M-%S", t)
            print("Recording at", current_time)
            starttime = time.time()
            filename = "/home/pi/Desktop/clipon/files/" + str(current_time) + ".h264"
            picam.start_recording(encoder, filename)
            recording = True
        else:
            picam.stop_recording()
            os.system("echo 0 | sudo tee /sys/class/leds/ACT/brightness > /dev/null 2>&1")
            recording = False
            print("Stopped recording of " + str(round(10 * (time.time() - starttime)) / 10) + " sec")
            os.system("ffmpeg -r 30 -i " + filename + " -vcodec copy " + filename[:-5] + ".mp4 > /dev/null 2>&1")
            os.remove(filename)
    if not recording:
        if switchtime == 0:
            switchtime = 20000
            if ledon:
                os.system("echo 0 | sudo tee /sys/class/leds/ACT/brightness > /dev/null 2>&1")
            else:
                os.system("echo 1 | sudo tee /sys/class/leds/ACT/brightness > /dev/null 2>&1")
            ledon = not ledon
        else:
            switchtime -= 1
    if recording and time.time() - starttime > 60:
        picam.stop_recording()
        os.system("echo 0 | sudo tee /sys/class/leds/ACT/brightness > /dev/null 2>&1")
        print("Stopped recording because of 60 sec timeout")
        recording = False
        os.system("ffmpeg -r 30 -i " + filename + " -vcodec copy " + filename[:-5] + ".mp4")
        os.remove(filename)
