

from machine import Pin, I2C, PWM
import utime as time
import neopixel


class LCDDisplay:
    """Tiny 16x2 PCF8574 I2C LCD driver for address 0x27."""

    def __init__(self):
        self.i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        found = self.i2c.scan()
        print("LCD I2C scan:", found)
        if 0x27 not in found:
            raise RuntimeError("LCD at 0x27 not found")
        self.address = 0x27
        self._backlight = 0x08
        self._last = [None, None]
        time.sleep_ms(50)
        for pause in (5, 1, 1):
            self._nibble(0x30)
            time.sleep_ms(pause)
        self._nibble(0x20)  # 4-bit interface
        self._command(0x28)  # 2 lines, 5x8 characters
        self._command(0x0C)  # display ON, cursor OFF
        self._command(0x06)  # increment cursor
        self._command(0x01)  # clear display
        time.sleep_ms(3)

    def _write(self, value):
        self.i2c.writeto(self.address, bytes([value | self._backlight]))

    def _nibble(self, value):
        self._write(value | 0x04)  # enable HIGH
        time.sleep_us(1)
        self._write(value & 0xFB)  # enable LOW
        time.sleep_us(50)

    def _send(self, value, register_select):
        self._nibble((value & 0xF0) | register_select)
        self._nibble(((value << 4) & 0xF0) | register_select)

    def _command(self, value):
        self._send(value, 0)

    def line(self, row, message):
        text = (str(message)[:16] + " " * 16)[:16]
        if text == self._last[row]:
            return
        self._command(0x80 if row == 0 else 0xC0)
        for ch in text:
            self._send(ord(ch), 1)
            time.sleep_ms(1)
        self._last[row] = text


class Calendar:
    def __init__(self, initially_available=True):
        self.available = initially_available

    def isAvailable(self):
        return self.available


class Employee:
    def __init__(self, name, title, department="", email="", phoneNumber="", availability="Available"):
        self.name = name
        self.title = title
        self.department = department
        self.email = email
        self.phoneNumber = phoneNumber
        self.availability = availability

    def getAvailability(self):
        return self.availability


class Administrator(Employee):
    def __init__(self, name, title, department="", email="", phoneNumber="", calendar=None):
        super().__init__(name, title, department, email, phoneNumber)
        self.calendar = calendar if calendar is not None else Calendar()

    def getAvailability(self):
        return "Available" if self.calendar.isAvailable() else "Busy"


class Faculty(Employee):
    def __init__(self, name, title, department="", email="", phoneNumber="", courses="", officeHours="", availability="Available"):
        super().__init__(name, title, department, email, phoneNumber, availability)
        self.courses = courses
        self.officeHours = officeHours


class Staff(Employee):
    pass


class StudentWorker(Employee):
    pass


class LightStrip:
    def __init__(self, pin=2, count=8):
        self.pixels = neopixel.NeoPixel(Pin(pin), count)
        self.count = count

    def setColor(self, rgb):
        for i in range(self.count):
            self.pixels[i] = rgb
        self.pixels.write()


class PassiveBuzzer:
    def __init__(self, pin=15):
        self.pwm = PWM(Pin(pin))
        self.pwm.duty_u16(0)

    def beep(self, frequency):
        self.pwm.freq(frequency)
        self.pwm.duty_u16(2500)
        time.sleep_ms(60)
        self.pwm.duty_u16(0)


class NamePlateView:
    def __init__(self, display, light_strip):
        self.display = display
        self.strip = light_strip

    def update(self, employee, show_office=False):
        self.display.line(0, employee.name)
        if isinstance(employee, Faculty):
            detail = ("Office:" + employee.officeHours) if show_office else ("Courses:" + employee.courses)
        else:
            detail = employee.title
        self.display.line(1, detail)
        status = employee.getAvailability()
        colors = {"Available": (0, 150, 0), "Away": (180, 130, 0), "Busy": (150, 0, 0)}
        self.strip.setColor(colors.get(status, (0, 0, 0)))
        print(employee.name, "|", detail, "|", status)


class NamePlate:
    def __init__(self, people, view, buzzer):
        self.people = people
        self.view = view
        self.buzzer = buzzer
        self.index = 0
        self.office = False
        self.updateDisplay()

    def updateDisplay(self):
        self.view.update(self.people[self.index], self.office)

    def nextEmployee(self):
        self.index = (self.index + 1) % len(self.people)
        self.office = False
        self.buzzer.beep(1200)
        self.updateDisplay()

    def previousEmployee(self):
        self.index = (self.index - 1) % len(self.people)
        self.office = False
        self.buzzer.beep(800)
        self.updateDisplay()

    def changeAvailability(self):
        employee = self.people[self.index]
        if isinstance(employee, Administrator):
            print("Administrator availability is calendar-controlled")
        else:
            cycle = {"Available": "Away", "Away": "Busy", "Busy": "Available"}
            employee.availability = cycle.get(employee.availability, "Available")
        self.updateDisplay()

    def toggleFacultyInfo(self):
        if isinstance(self.people[self.index], Faculty):
            self.office = not self.office
            self.updateDisplay()


def main():
    print("DYNAMIC NAMEPLATE STARTING")
    lcd = LCDDisplay()
    strip = LightStrip(pin=2, count=8)
    buzzer = PassiveBuzzer(pin=15)

    people = [
        Administrator("Dr. Jane Doe", "Dean of Eng.", "Admin", "jdoe@univ.edu", "x1001", Calendar(True)),
        Faculty("Prof. Turing", "CS Professor", "Computer Sci", "aturing@univ.edu", "x2048",
                courses="CS101,CS305", officeHours="MW 2-4PM"),
        Staff("Grace Hopper", "Lab Manager", "IT Services", "ghopper@univ.edu", "x3300", "Away"),
        StudentWorker("Alex Smith", "Student Asst.", "Helpdesk", "asmith@univ.edu", "x4410", "Busy"),
    ]

    controller = NamePlate(people, NamePlateView(lcd, strip), buzzer)
    buttons = [Pin(20, Pin.IN, Pin.PULL_UP), Pin(17, Pin.IN, Pin.PULL_UP), Pin(18, Pin.IN, Pin.PULL_UP)]
    last_states = [1, 1, 1]
    faculty_counter = 0
    print("READY: GP20=Previous, GP17=Next, GP18=Availability")

    # Poll buttons instead of using interrupts: no ISR timing errors,
    # no scheduling queue overflow, and LCD updates happen sequentially.
    while True:
        for i in range(3):
            state = buttons[i].value()
            if last_states[i] == 1 and state == 0:
                time.sleep_ms(20)  # debounce
                if buttons[i].value() == 0:
                    if i == 0:
                        controller.previousEmployee()
                    elif i == 1:
                        print("NEXT BUTTON PRESSED")
                        controller.nextEmployee()
                    else:
                        controller.changeAvailability()
                    faculty_counter = 0
            last_states[i] = buttons[i].value()

        time.sleep_ms(30)
        #faculty_counter += 1
        #if faculty_counter >= 80:  # approximately every 2.5 seconds
            #faculty_counter = 0
            #controller.toggleFacultyInfo()


if __name__ == "__main__":
    main()
