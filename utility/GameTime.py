class GameTime:
    def __init__(self, *args, **kwargs):
        if len(kwargs) != 1 or len(args) > 0:
            raise Exception("Wrong usage, use only one of the following named arguments: "
                            "seconds, minutes, days or non_winter_days.")
        if "seconds" in kwargs:
            if kwargs["seconds"] is None:
                self.infinite = True
            else:
                self.infinite = False
                self._seconds = kwargs["seconds"]
            self.exclude_winter = False
        elif "minutes" in kwargs:
            if kwargs["minutes"] is None:
                self.infinite = True
            else:
                self.infinite = False
                self._seconds = kwargs["minutes"]*60
            self.exclude_winter = False
        elif "days" in kwargs:
            if kwargs["days"] is None:
                self.infinite = True
            else:
                self.infinite = False
                self._seconds = kwargs["days"]*480
            self.exclude_winter = False
        elif "non_winter_days" in kwargs:
            if kwargs["non_winter_days"] is None:
                self.infinite = True
            else:
                self.infinite = False
                self._seconds = kwargs["non_winter_days"]*480
            self.exclude_winter = True

    def seconds(self):
        if not self.infinite:
            return self._seconds
        else:
            return None

    def minutes(self):
        if not self.infinite:
            return self._seconds/60
        else:
            return None

    def days(self):
        if not self.infinite:
            return self._seconds/480
        else:
            return None

    def __add__(self, other):
        aux = GameTime(seconds=self.seconds() + other.seconds())
        aux.exclude_winter = self.exclude_winter
        return aux

    def __sub__(self, other):
        aux = GameTime(seconds=self.seconds() - other.seconds())
        aux.exclude_winter = self.exclude_winter
        return aux

    def __mul__(self, number):
        aux = GameTime(seconds=self.seconds() * number)
        aux.exclude_winter = self.exclude_winter
        return aux

    def __truediv__(self, number):
        aux = GameTime(seconds=self.seconds() / number)
        aux.exclude_winter = self.exclude_winter
        return aux

    def __le__(self, other):
        return self.seconds() <= other.seconds()

    def __ge__(self, other):
        return self.seconds() >= other.seconds()

    def __gt__(self, other):
        return self.seconds() > other.seconds()

    def __lt__(self, other):
        return self.seconds() < other.seconds()
