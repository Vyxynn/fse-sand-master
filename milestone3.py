import RPi.GPIO as GPIO
import time
import subprocess

mp3_process = None
MP3_FILE = "/home/pi/fse-sand/pipe.mp3"

tilt1_start = None
tilt2_start = None

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
    buzzer_off()

    GPIO.setup(TILT1_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(TILT2_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(PIR_GPIO, GPIO.IN)


def distance():
    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.LOW)
    time.sleep(0.000002)

    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIGGER_GPIO, GPIO.LOW)

    timeout = time.monotonic() + 0.04

    # Wait for the echo pulse to start.
    while GPIO.input(ULTRASONIC_ECHO_GPIO) == GPIO.LOW:
        if time.monotonic() > timeout:
            return None

    start_time = time.monotonic()

    # Wait for the echo pulse to finish.
    while GPIO.input(ULTRASONIC_ECHO_GPIO) == GPIO.HIGH:
        if time.monotonic() > timeout:
            return None

    end_time = time.monotonic()

    duration = end_time - start_time
    return duration * 34300 / 2


def get_tilt1():
    return GPIO.input(TILT1_GPIO)


def get_tilt2():
    return GPIO.input(TILT2_GPIO)


def get_motion():
    return GPIO.input(PIR_GPIO)


def buzzer_on():
    # The buzzer is active-low.
    GPIO.output(BUZZER_GPIO, GPIO.LOW)


def buzzer_off():
    GPIO.output(BUZZER_GPIO, GPIO.HIGH)


def startup_sound():
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
        if mp3_process.poll() is None:
            mp3_process.terminate()

        mp3_process = None


def loop():
    global tilt1_start, tilt2_start

    while True:
        dis = distance()
        tilt1 = get_tilt1()
        tilt2 = get_tilt2()
        motion = get_motion()

        # Use a larger activation distance when motion is detected.
        if motion == GPIO.HIGH:
            alert_distance = 50
        else:
            alert_distance = 30

        distance_alarm = (
            dis is not None and dis < alert_distance
        )

        # The tilt switches use pull-up resistors, so LOW means active.
        tilt1_active = tilt1 == GPIO.LOW
        tilt2_active = tilt2 == GPIO.LOW

        now = time.monotonic()

        # Each tilt switch must remain continuously active for five seconds.
        # Its timer resets immediately when the switch becomes inactive.
        if tilt1_active:
            if tilt1_start is None:
                tilt1_start = now
        else:
            tilt1_start = None

        if tilt2_active:
            if tilt2_start is None:
                tilt2_start = now
        else:
            tilt2_start = None

        tilt1_alarm = (
            tilt1_start is not None
            and now - tilt1_start >= 5
        )

        tilt2_alarm = (
            tilt2_start is not None
            and now - tilt2_start >= 5
        )

        tilt_alarm = tilt1_alarm or tilt2_alarm

        # The buzzer turns off when neither alarm condition is active.
        buzzer_alarm = distance_alarm or tilt_alarm

        if buzzer_alarm:
            buzzer_on()
        else:
            buzzer_off()

        # MP3 playback is controlled only by the distance alarm.
        update_mp3(distance_alarm)

        if dis is None:
            print("Distance: No echo received")
        else:
            print(f"Distance: {dis:.2f} cm")

        print("Tilt 1 active:", tilt1_active)
        print("Tilt 2 active:", tilt2_active)
        print("Motion:", motion)
        print("Alert distance:", alert_distance, "cm")
        print("Distance alarm:", distance_alarm)
        print("Tilt alarm:", tilt_alarm)
        print("Buzzer alarm:", buzzer_alarm)
        print("====================")

        time.sleep(0.1)


def destroy():
    global mp3_process

    if mp3_process is not None:
        if mp3_process.poll() is None:
            mp3_process.terminate()

        mp3_process = None

    buzzer_off()
    GPIO.cleanup()


if __name__ == "__main__":
    setup()

    try:
        startup_sound()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
