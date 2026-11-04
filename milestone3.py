import RPi.GPIO as GPIO
import time
import subprocess

mp3_process = None
MP3_FILE = "/home/pi/fse-sand/pipe.mp3"

tilt_start = None

# Ultrasonic distance sensor
ULTRASONIC_TRIGGER_GPIO = 16
ULTRASONIC_ECHO_GPIO = 18

# Buzzer
BUZZER_GPIO = 17

# Tilt switches
TILT1_GPIO = 22
TILT2_GPIO = 21

# PIR sensor
PIR_GPIO = 24


def setup():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(ULTRASONIC_TRIGGER_GPIO, GPIO.OUT)
    GPIO.setup(ULTRASONIC_ECHO_GPIO, GPIO.IN)
    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.LOW)

    GPIO.setup(BUZZER_GPIO, GPIO.OUT)
    GPIO.output(BUZZER_GPIO, GPIO.HIGH)

    GPIO.setup(TILT1_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(TILT2_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(PIR_GPIO, GPIO.IN)


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


def get_motion():
    return GPIO.input(PIR_GPIO)


def buzzer_on():
    GPIO.output(BUZZER_GPIO, GPIO.LOW)


def buzzer_off():
    GPIO.output(BUZZER_GPIO, GPIO.HIGH)


def on():
    buzzer_on()
    time.sleep(0.3)
    buzzer_off()
    time.sleep(0.1)

    for _ in range(3):
        buzzer_on()
        time.sleep(0.05)
        buzzer_off()
        time.sleep(0.05)


def update_mp3(play_audio):
    global mp3_process

    if play_audio:
        if mp3_process is None or mp3_process.poll() is not None:
            mp3_process = subprocess.Popen(
                ["mpg123", "-q", MP3_FILE]
            )
    elif mp3_process is not None:
        mp3_process.terminate()
        mp3_process = None


def loop():
    global tilt_start

    while True:
        dis = distance()
        tilt1 = get_tilt1()
        tilt2 = get_tilt2()
        motion = get_motion()

        # If the PIR detects motion, activate at 30 cm.
        # Otherwise, activate at 5 cm.
        if motion == 1:
            alert_distance = 50
        else:
            alert_distance = 30

        distance_alarm = (
            dis is not None and dis < alert_distance
        )

        # Activate the tilt alarm after five seconds.
        if tilt1 == 1 or tilt2 == 1:
            if tilt_start is None:
                tilt_start = time.monotonic()

            tilt_alarm = time.monotonic() - tilt_start >= 5
        else:
            tilt_start = None
            tilt_alarm = False

        # The buzzer sounds for either distance or tilt alarm.
        if distance_alarm or tilt_alarm:
            buzzer_on()
        else:
            buzzer_off()

        # MP3 alarm is controlled by distance and PIR state.
        update_mp3(distance_alarm)

        if dis is None:
            print("No echo received")
        else:
            print(f"Distance: {dis:.2f} cm")

        print("Tilt 1:", tilt1)
        print("Tilt 2:", tilt2)
        print("Motion:", motion)
        print("Alert distance:", alert_distance, "cm")
        print("====================")

        time.sleep(0.5)


def destroy():
    global mp3_process

    if mp3_process is not None:
        mp3_process.terminate()
        mp3_process = None

    buzzer_off()
    GPIO.cleanup()


if __name__ == "__main__":
    setup()

    try:
        on()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
