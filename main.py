# main.py - Satisfaction Kiosk for Raspberry Pi Pico W
from Displays import LCDDisplay
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from Sensors_advanced import UltrasonicSensor
from Button import Button
from Counters import SoftwareTimer
from FeedbackStats import FeedbackStats
from FeedbackController import FeedbackController

# GPIO: LCD 0/1, NeoPixels 2, Sonar 3/4,
# buzzer 15, Green 16, Red 17, Manager 18.

def main():
    lcd = LCDDisplay(sda=0, scl=1)
    strip = LightStrip(pin=2, numleds=8, brightness=0.5)
    buzzer = PassiveBuzzer(pin=15)
    sensor = UltrasonicSensor(trigger=3, echo=4, name="uss",
                              lowActive=True, threshold=10.0)
    green = Button(pin=16, name="green", lowActive=True)
    red = Button(pin=17, name="red", lowActive=True)
    manager = Button(pin=18, name="manager", lowActive=True)
    timer = SoftwareTimer(name="timer")
    stats = FeedbackStats()

    kiosk = FeedbackController(lcd, strip, buzzer, sensor,
                               green, red, manager, timer, stats)
    try:
        kiosk.run()
    finally:
        kiosk.stop()

if __name__ == "__main__":
    main()
