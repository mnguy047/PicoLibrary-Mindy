# FeedbackStats.py - stores satisfaction votes

class FeedbackStats:
    def __init__(self):
        self._happy_count = 0
        self._unhappy_count = 0
        self._happy_streak = 0

    def get_total_count(self):
        return self._happy_count + self._unhappy_count

    def get_light_level(self):
        return round(self.calculate_percentage() * 8 / 100)

    def calculate_percentage(self):
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return self._happy_count * 100 / total

    def add_happy(self):
        self._happy_count += 1
        self._happy_streak += 1

    def add_unhappy(self):
        self._unhappy_count += 1
        self._happy_streak = 0

    def reset(self):
        self._happy_count = 0
        self._unhappy_count = 0
        self._happy_streak = 0

    def get_happy_streak(self):
        return self._happy_streak
