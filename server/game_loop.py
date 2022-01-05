import csv
import os
from threading import Thread
from time import sleep
from typing import Any, Callable, Dict, List

from server.calibration import read_calibration_data
from server.classes import CalibrationData, CancellationToken, Dart
from server.darts_recognition import get_dart
from server.video_capture import VideoStream


class GameLoop:
    cam: VideoStream = VideoStream(src=1)
    calibration_data: CalibrationData = read_calibration_data('../tmp/calibration_data.pkl')
    cancellationToken: CancellationToken
    subscribers: List[Callable[[Dart], None]] = []

    def __init__(self):
        self.subscribers.append(log_dart)

    def add_subscriber(self, subscriber: Callable[[Dart], None]) -> None:
        self.subscribers.append(subscriber)

    def start(self) -> None:
        self.cancellationToken = CancellationToken()
        self.cam.start(); sleep(1)
        print('start')
        Thread(target=self.run, daemon=True).start()

    def stop(self) -> None:
        self.cancellationToken.cancel()

    def run(self) -> None:
        while not self.cancellationToken.is_cancelled:
            dart = get_dart(self.cam, self.calibration_data, self.cancellationToken)
            [subscriber(dart) for subscriber in self.subscribers]
            if not dart: sleep(5)


def log_dart(dart: Dart) -> None:
    darts_log = '../tmp/darts_log2.csv'

    def write_csv(dart_dict: Dict[str, Any], header: bool = False):
        field_names: List[str] = ['id', 'date', 'base', 'multiplier', 'loc_x', 'loc_y']
        with open(darts_log, 'a') as csv_file:
            csv_writer = csv.DictWriter(csv_file, field_names)
            if header: csv_writer.writeheader()
            csv_writer.writerows([dart_dict])

    if dart: write_csv(dart.asdict(), header=(not os.path.isfile(darts_log)))


if __name__ == '__main__':
    game_loop = GameLoop()
    game_loop.start()
