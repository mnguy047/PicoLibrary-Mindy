# FeedbackController.py - the seven states from the UML Statechart
import time
from StateModel import StateModel
from Lights import RED, GREEN, YELLOW, CYAN, BLUE, ORANGE, PURPLE, WHITE

WELCOME = 0
LOADING = 1
SELECTION = 2
HAPPY = 3
UNHAPPY = 4
CELEBRATION = 5
ALARM = 6

class FeedbackController:
    def __init__(self, display, light_strip, buzzer, sensor,
                 btn_green, btn_red, btn_manager, timer, stats):
        self._display = display
        self._strip = light_strip
        self._buzzer = buzzer
        self._stats = stats
        self._timer = timer
        self._loading_step = 0
        self._loading_start = 0
        self._alarm_on = True
        self._last_alarm_toggle = 0

        # StateModel controls all seven states.
        self._model = StateModel(7, self, debug=True)
        self._model.addSensor(sensor)
        self._model.addButton(btn_green)
        self._model.addButton(btn_red)
        self._model.addButton(btn_manager)
        self._model.addTimer(timer)

        for event in ("happy_done", "feedback_ok", "streak_reached",
                      "feedback_below_threshold"):
            self._model.addCustomEvent(event)

        # Transitions from the completed Statechart.
        for source, event, target in (
            (WELCOME, "uss_trip", LOADING),
            (LOADING, "timer_timeout", SELECTION),
            (SELECTION, "timer_timeout", WELCOME),
            (SELECTION, "green_press", HAPPY),
            (SELECTION, "red_press", UNHAPPY),
            (HAPPY, "happy_done", WELCOME),
            (HAPPY, "streak_reached", CELEBRATION),
            (HAPPY, "feedback_below_threshold", ALARM),
            (UNHAPPY, "feedback_ok", WELCOME),
            (UNHAPPY, "feedback_below_threshold", ALARM),
            (CELEBRATION, "timer_timeout", WELCOME),
            (ALARM, "manager_press", WELCOME),
            (ALARM, "green_press", WELCOME),
        ):
            self._model.addTransition(source, [event], target)

    def stateEntered(self, state, event):
        if state == WELCOME:
            self._timer.cancel()
            self._strip.off()
            self._buzzer.stop()
            self._display.clear()
            self._display.showText("Welcome!", 0, 0)
            self._display.showText("Step closer!", 1, 0)

        elif state == LOADING:
            self._display.clear()
            self._display.showText("Getting ready!", 0, 0)
            self._strip.off()
            self._loading_step = 0
            self._loading_start = time.ticks_ms()
            self._timer.start(2)

        elif state == SELECTION:
            self._display.clear()
            self._display.showText("Rate your visit", 0, 0)
            self._display.showText("Green :) Red :(", 1, 0)
            for i in range(8):
                self._strip.setPixel(i, GREEN if i < 4 else YELLOW, show=False)
            self._strip.show()
            self._timer.start(5)

        elif state == HAPPY:
            self.recordVote(event)
            self.showMood("happy")
            self._timer.start(2)

        elif state == UNHAPPY:
            self.recordVote(event)
            self.showMood("unhappy")
            self._timer.start(2)

        elif state == CELEBRATION:
            self._display.clear()
            self._display.showText("3 Happy Votes!", 0, 0)
            self._display.showText("Great job!", 1, 0)
            colors = (RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)
            for i in range(8):
                self._strip.setPixel(i, colors[i], show=False)
            self._strip.show()
            self._buzzer.beep(700, 120)
            self._buzzer.beep(900, 120)
            self._timer.start(3)

        elif state == ALARM:
            self._display.clear()
            self._display.showText("Call Manager!", 0, 0)
            self._display.showText("Happy: {:.0f}%".format(
                self._stats.calculate_percentage()), 1, 0)
            self._strip.setColor(RED)
            self._buzzer.play(700)
            self._alarm_on = True
            self._last_alarm_toggle = time.ticks_ms()

    def stateLeft(self, state, event):
        if state in (LOADING, SELECTION, HAPPY, UNHAPPY, CELEBRATION):
            self._strip.off()
        if state == SELECTION:
            self._timer.cancel()
        if state == ALARM:
            self._strip.off()
            self._buzzer.stop()
            if event == "green_press":
                self._stats.reset()

    def stateDo(self, state):
        if state == LOADING:
            elapsed = time.ticks_diff(time.ticks_ms(), self._loading_start)
            target = min(8, elapsed // 250)
            while self._loading_step < target:
                self._strip.setPixel(self._loading_step, CYAN)
                self._loading_step += 1

        elif state == ALARM:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_alarm_toggle) >= 300:
                self._last_alarm_toggle = now
                self._alarm_on = not self._alarm_on
                if self._alarm_on:
                    self._strip.setColor(RED)
                    self._buzzer.play(700)
                else:
                    self._strip.off()
                    self._buzzer.stop()

    def stateEvent(self, state, event):
        # Called after the two-second response timer expires.
        if event != "timer_timeout" or state not in (HAPPY, UNHAPPY):
            return False

        total = self._stats.get_total_count()
        percentage = self._stats.calculate_percentage()
        streak = self._stats.get_happy_streak()
        if total >= 5 and percentage < 30:
            self._model.processEvent("feedback_below_threshold")
        elif state == HAPPY and streak > 0 and streak % 3 == 0:
            self._model.processEvent("streak_reached")
        elif state == HAPPY:
            self._model.processEvent("happy_done")
        else:
            self._model.processEvent("feedback_ok")
        return True

    def recordVote(self, event):
        if event == "green_press":
            self._stats.add_happy()
        elif event == "red_press":
            self._stats.add_unhappy()

    def showMood(self, vote):
        self._display.clear()
        if vote == "happy":
            self._display.showText("Thank you!", 0, 0)
            self._strip.setColor(GREEN)
        else:
            self._display.showText("We'll do better!", 0, 0)
            self._strip.setColor(YELLOW)
        self._display.showText("Happy: {:.0f}%".format(
            self._stats.calculate_percentage()), 1, 0)

    def run(self):
        self._model.run(delay=0.1)

    def stop(self):
        self._model.stop()
        self._strip.off()
        self._buzzer.stop()
