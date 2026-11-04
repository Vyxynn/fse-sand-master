import RPi.GPIO as GPIO
import time
import sys
from enum import Enum

tilt_start = None

# Ultrasonic distance sensor
ULTRASONIC_TRIGGER_GPIO = 16
ULTRASONIC_ECHO_GPIO = 18

# Buzzer
BUZZER_GPIO = 17

# Tilt switch
TILT1_GPIO = 22
TILT2_GPIO = 21


def setup():
    GPIO.setmode(GPIO.BCM)

    # Ultrasonic setup
    GPIO.setup(ULTRASONIC_TRIGGER_GPIO, GPIO.OUT)
    GPIO.setup(ULTRASONIC_ECHO_GPIO, GPIO.IN)
    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.LOW)

    # Buzzer setup
    GPIO.setup(BUZZER_GPIO, GPIO.OUT)
    GPIO.output(BUZZER_GPIO, GPIO.HIGH)
    
    # Tilt setup
    GPIO.setup(TILT1_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(TILT2_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def distance():
    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.LOW)
    time.sleep(0.000002)

    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.LOW)

    timeout = time.time() + 0.04

    while GPIO.input(ULTRASONIC_ECHO_GPIO) == GPIO.LOW:
        if time.time() > timeout:
            return None

    time1 = time.time()

    while GPIO.input(ULTRASONIC_ECHO_GPIO) == GPIO.HIGH:
        if time.time() > timeout:
            return None

    time2 = time.time()

    duration = time2 - time1
    return duration * 34300 / 2
    
def get_tilt1():
    return GPIO.input(TILT1_GPIO)
	
def get_tilt2():
    return GPIO.input(TILT2_GPIO)


def buzzer_on():
    GPIO.output(BUZZER_GPIO, GPIO.LOW)


def buzzer_off():
    GPIO.output(BUZZER_GPIO, GPIO.HIGH)


def beep(duration):
    buzzer_on()
    time.sleep(duration)
    buzzer_off()
    time.sleep(duration)


def on():
    buzzer_on()
    time.sleep(0.3)
    buzzer_off()
    time.sleep(0.1)

    buzzer_on()
    time.sleep(0.05)
    buzzer_off()
    time.sleep(0.05)

    buzzer_on()
    time.sleep(0.05)
    buzzer_off()
    time.sleep(0.05)

    buzzer_on()
    time.sleep(0.05)
    buzzer_off()


def loop():
    global tilt_start

    while True:
        dis = distance()
        tilt1 = get_tilt1()
        tilt2 = get_tilt2()

        if dis is None:
            print("No echo received")
            buzzer_off()
        else:
            print(dis, "cm")

            if dis < 5:
                buzzer_on()
            elif dis < 30:
                beep_interval = (dis - 5) / 50.0
                beep(beep_interval)
            else:
                buzzer_off()

        print("tilt1", tilt1)
        print("tilt2", tilt2)

        if tilt1 == 1 or tilt2 == 1:
            if tilt_start is None:
                tilt_start = time.monotonic()

            if time.monotonic() - tilt_start >= 5:
                buzzer_on()
        else:
            tilt_start = None

        time.sleep(0.05)


def destroy():
    buzzer_off()
    GPIO.cleanup()


if __name__ == "__main__":
    setup()

    try:
        on()
        loop()
    except KeyboardInterrupt:
        destroy()
