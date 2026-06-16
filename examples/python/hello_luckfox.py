import os
import platform
import sys

print("Hello from Python on Luckfox PicoCalc")
print("user id:", os.getuid())
print("python:", sys.version.split()[0])
print("machine:", platform.machine())
