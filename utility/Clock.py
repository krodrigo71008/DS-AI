import time
import numpy as np
from utility.GameTime import GameTime


class Clock:
    def __init__(self, start_time=0.):
        # time in seconds is supposed to be the time in seconds since the game started 
        # (for example, at the end of the first day this should be 480)
        self.time_in_seconds : float = start_time
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

    def start(self):
        self._last_time = time.time()

    def update(self):
        current_time = time.time()
        self.time_in_seconds += current_time - self._last_time
        self._last_dt = current_time - self._last_time
        self._last_time = current_time

    def dt(self) -> float:
        """Gives time that passed between current time in this clock and the previous update

        :return: passed time before last update
        :rtype: float
        """
        return self._last_dt

    def time(self) -> float:
        """Gives time in seconds

        :return: time in seconds
        :rtype: float
        """
        return self.time_in_seconds

    def raw_timestamp(self) -> float:
        """Gives timestamp in seconds

        :return: timestamp in seconds
        :rtype: float
        """
        return self._last_time

    # time_delta should be GameTime
    def time_from_now(self, time_delta: GameTime) -> float:
        """
        Calculates the point in time that is time_delta in the future from now

        :param time_delta: how much time in the future
        :type time_delta: GameTime
        :return: 'timestamp' representing the requested time
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


class ClockMock(Clock):
    def __init__(self, times_to_return : np.array):
        """A Clock implementation that returns preset times instead of the real times

        :param times_to_return: [0] is start time, [1] is _last_time, [2] onwards is times_to_return
        :type times_to_return: np.array
        :return: ClockMock instance
        :rtype: ClockMock
        """
        start_time = times_to_return[0]
        super().__init__(start_time)
        self.times_to_return = times_to_return
        self.current_time_index = 2
        self._last_time = times_to_return[1]

    def update(self):
        current_time = self.times_to_return[self.current_time_index]
        self.current_time_index += 1
        self.time_in_seconds += current_time - self._last_time
        self._last_dt = current_time - self._last_time
        self._last_time = current_time

    # start must not do anything since _last_time is already initialized in the constructor
    def start(self):
        pass

    def next_time(self):
        if self.current_time_index == len(self.times_to_return):
            return None
        return self.times_to_return[self.current_time_index]

class ClockRecorder(Clock):
    def __init__(self, start_time=0.):
        super().__init__(start_time)
        # time_records[0] is start_time, time_records[1] is initial _last_time (used to calculate dt), 2 and 
        # onwards are time measurements
        self.time_records = []
        self.time_records.append(start_time)
        self.time_records.append(self._last_time)

    def start(self):
        super().start()
        self.time_records[1] = self._last_time
    
    def update(self):
        current_time = time.time()
        self.time_records.append(current_time)
        self.time_in_seconds += current_time - self._last_time
        self._last_dt = current_time - self._last_time
        self._last_time = current_time
