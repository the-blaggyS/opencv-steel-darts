import cv2
import math

from server.classes import CalibrationData, Image


def draw_board(image: Image, calibration_data: CalibrationData) -> None:
    for ring_radius in calibration_data.ring_radii:
        cv2.circle(image, calibration_data.center_dartboard, ring_radius, color=(255, 255, 255), thickness=1)
    for sector in range(20):
        cv2.line(image, calibration_data.center_dartboard,
                 (int(calibration_data.center_dartboard[0] + calibration_data.ring_radii[5] * math.cos((sector + 0.5) * calibration_data.sector_angle)),
                  int(calibration_data.center_dartboard[1] + calibration_data.ring_radii[5] * math.sin((sector + 0.5) * calibration_data.sector_angle))),
                 color=(255, 255, 255), thickness=1)
