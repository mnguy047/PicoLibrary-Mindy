"""
# main.py
# Entry point for the ISM6106 Lab 4 IoT CRM System (Option B) on Raspberry Pi Pico 2 W
# Author: Mindy Nguyen
"""

from Log import *
from Net import Net
from Button import Button
from Displays import LCDDisplay
from LightStrip import LightStrip
from Lights import RED
from CRMController import CRMController


def main():
    """
    Initialize hardware peripherals using existing PicoLibrary wiring, load Wi-Fi
    credentials from secrets.py (git-ignored), and start CRMController in Option B mode.

    Pin Assignments (verified against diagram.json):
    - LCD 1602 (I2C): GP0 (SDA), GP1 (SCL)
    - NeoPixel Strip (8 LEDs): GP2 (DIN)
    - Next Button (active-low, no IRQ): GP16
    - Select Button (active-low, no IRQ): GP17
    """
    # Suppress INFO-level polling logs inside Button.isPressed() so numbered sequence
    # print statements remain clean and readable in the console.
    Log.level = ERROR

    try:
        from secrets import WIFI_SSID, WIFI_PASSWORD
    except ImportError:
        WIFI_SSID = ""
        WIFI_PASSWORD = None

    lcd = LCDDisplay(sda=0, scl=1)
    lights = LightStrip(pin=2, name="CRMStrip", numleds=8, brightness=0.5)
    net = Net()
    next_btn = Button(16, "Next", handler=None, lowActive=True)
    select_btn = Button(17, "Select", handler=None, lowActive=True)

    if not WIFI_SSID:
        print("Error: Create secrets.py with WIFI_SSID and WIFI_PASSWORD before running.")
        lcd.clear()
        lcd.showText("Missing secrets", 0, 0)
        lcd.showText("Add secrets.py", 1, 0)
        lights.setColor(RED)
        return

    controller = CRMController(
        net=net,
        lcd=lcd,
        lights=lights,
        nextButton=next_btn,
        selectButton=select_btn,
        ssid=WIFI_SSID,
        password=WIFI_PASSWORD,
    )
    controller.start(False)


if __name__ == "__main__":
    main()
