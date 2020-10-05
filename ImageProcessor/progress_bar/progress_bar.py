import sys
import math


class ProgressBar:
    def __init__(self, max_count: int):
        self.counter: int = 0
        self.max_count: int = max_count

    def inc(self, step: int = 1):
        self.counter += step

    def update_max_count(self, step: int = 1):
        self.max_count += step

    def reset(self):
        self.counter = 0

    def show(self):
        progress: float = self.counter / self.max_count
        points_count: int = math.floor(progress * 25)
        sys.stdout.write(
            f"\rProgress: [{'#' * points_count}{'_' * (25 - points_count)}] "
            f"{str(round(progress * 10000) / 100)}%")
        sys.stdout.flush()
