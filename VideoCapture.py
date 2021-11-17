from threading import Thread

import cv2


class VideoStream:

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        self.stopped = False
        Thread(target=self.update).start()

    def update(self):
        while not self.stopped:
            self.grabbed, self.frame = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
