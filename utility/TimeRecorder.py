import pickle
import time

class TimeRecorder:
    def __init__(self, path: str, splits: list = []):
        """Constructor

        :param path: Path to save results to, with no extension
        :type path: str
        :param splits: name of splits, defaults to []
        :type splits: list, optional
        """
        self.time_start = None
        self.time_end = None
        self.current_splits = []
        self.records = []
        self.path = path
        self.splits = splits

    def start(self):
        self.time_start = time.time()

    def split(self):
        self.current_splits.append(time.time() - self.time_start)
        self.time_start = time.time()
    
    def end(self):
        self.time_end = time.time()
        self.current_splits.append(self.time_end - self.time_start)
        self.records.append(self.current_splits)
        self.current_splits = []
    
    def export(self):
        with open(self.path + ".pkl", "wb") as file:
            pickle.dump(self, file)
