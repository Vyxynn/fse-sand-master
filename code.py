from gpiozero import MotionSensor, DistanceSensor, Buzzer
from time import sleep

# BCM GPIO pin assignments
PIR_GPIO = 17
ULTRASONIC_TRIGGER_GPIO = 23
ULTRASONIC_ECHO_GPIO = 24
BUZZER_GPIO = 18

# Alarm settings
ALARM_DISTANCE_CM = 100
READ_INTERVAL_SECONDS = 0.25l

# Devices
pir = MotionSensor(PIR_GPIO)

distance_sensor = DistanceSensor(
    trigger=ULTRASONIC_TRIGGER_GPIO,
    echo=ULTRASONIC_ECHO_GPIO,
    max_distance=4
)

buzzer = Buzzer(BUZZER_GPIO)

try:
    print("Security system started. Press Ctrl+C to stop.")

    while True:
        motion_detected = pir.motion_detected
        distance_cm = distance_sensor.distance * 100

        # Alarm activates when motion is detected within the set distance
        alarm_active = (
            motion_detected
            and distance_cm <= ALARM_DISTANCE_CM
        )

        if alarm_active:
            buzzer.on()
            alarm_status = "ALARM"
        else:
            buzzer.off()
            alarm_status = "CLEAR"

        print(
            f"Motion: {'DETECTED' if motion_detected else 'None':<8} | "
            f"Distance: {distance_cm:6.1f} cm | "
            f"Alarm: {alarm_status}"
        )

        sleep(READ_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nSecurity system stopped.")

finally:
    buzzer.off()
