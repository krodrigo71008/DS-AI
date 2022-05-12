import time
from utility.GameTime import GameTime


class Clock:
    def __init__(self, start_time=0):
        # time in seconds is supposed to be the time in seconds since the game started 
        # (for example, at the end of the first day this should be 480)
        self.time_in_seconds = start_time
        self._last_time = time.time()
        self._last_dt = None
        self.dusk_start = [8, 8, 9, 9, 9, 9, 10, 10, 10, 10,
                           10, 10, 10, 10, 10, 9, 9, 9, 9, 8,
                           8, 8, 7, 7, 7, 6, 6, 6, 6, 6,
                           6, 7, 7, 7, 8]
        self.night_start = [13, 13, 13, 13, 14, 14, 14, 14, 14, 14,
                            14, 14, 14, 14, 14, 14, 14, 13, 13, 13,
                            13, 13, 13, 12, 12, 12, 12, 12, 12, 12,
                            12, 12, 12, 13, 13]

    def update(self):
        current_time = time.time()
        self.time_in_seconds += current_time - self._last_time
        self._last_dt = current_time - self._last_time
        self._last_time = current_time

    def dt(self):
        return self._last_dt

    def time(self):
        return self.time_in_seconds

    # time_delta should be GameTime
    def time_from_now(self, time_delta: GameTime) -> float:
        """
        Calculates the point in time that is time_delta in the future from now

        :param time_delta: how much time in the future
        :type time_delta: GameTime
        :return: 'timestamp' representing
        :rtype: float
        """
        if time_delta.exclude_winter:
            answer = self.time()
            # autumn is 20 days, so each 20 non winter days is a year
            num_years = time_delta.days() // 20
            remainder = time_delta.days() - num_years * 20
            answer += GameTime(days=35*num_years).seconds()
            # using self because going a whole number of years into the future doesn't change season
            if self.season() == "Summer":
                if Clock(self.time() + GameTime(days=remainder).seconds()).season() == "Winter":
                    answer += GameTime(days=15).seconds()
                answer += GameTime(days=remainder).seconds()
            else:
                # winter is from 21 to 35, so this should calculate seconds until end of winter (rounded down)
                answer += GameTime(days=35).seconds()-Clock(remainder).seconds_from_year_start()
                answer += remainder
            return answer
        else:
            return self.time()+time_delta.seconds()

    def day(self):
        return int(self.time_in_seconds // 480) + 1

    def day_on_year(self):
        return (int(self.time_in_seconds // 480) % 35) + 1

    def seconds_from_year_start(self):
        return self.time_in_seconds % (35 * 480)

    def season(self):
        if (self.day() % 35) + 1 <= 20:
            return "Summer"
        else:
            return "Winter"

    # from segment 0 to segment 15
    def segment(self):
        current_seconds = self.time_in_seconds - self.day()*480
        return int(current_seconds // 30)

    def day_section(self):
        year_day = self.day_on_year()
        segment = self.segment()
        if segment < self.dusk_start[year_day]:
            return "Day"
        elif segment < self.night_start[year_day]:
            return "Dusk"
        else:
            return "Night"

