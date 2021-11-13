from datetime import datetime
from threading import Thread

import cv2


class VideoStream:

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.vout = cv2.VideoWriter()

    def start(self):
        Thread(target=self.update).start()
        self.vout.open(f'Videos/match_{datetime.now().strftime("%Y-%m-%d_%H:%M")}.mov',
                       cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 30, (800, 600), True)

    def update(self):
        while not self.stopped:
            self.grabbed, self.frame = self.stream.read()
            self.vout.write(self.frame)

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.vout.release()
