from threading import Thread

import cv2

from server.classes import Image


class VideoStream:
    _stream: cv2.VideoCapture
    frame: Image
    stopped: bool = False

    def __init__(self, src: int = 0):
        self._stream = cv2.VideoCapture(src)
        _, frame = self._stream.read()
        self.frame = cv2.flip(frame, flipCode=-1)

    def start(self) -> None:
        self.stopped = False
        Thread(target=self._record).start()

    def stop(self) -> None:
        self.stopped = True

    def read(self) -> Image:
        return self.frame

    def _record(self) -> None:
        while not self.stopped:
            _, frame = self._stream.read()
            self.frame = cv2.flip(frame, flipCode=-1)
        self._stream.release()
