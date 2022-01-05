import cv2
import math
import numpy as np

from server.classes import CalibrationData, Dart, Point


def get_transformed_location(location: Point, calibration_data: CalibrationData) -> Point:
    # transform only the hit point with the saved transformation matrix
    dart_loc = cv2.perspectiveTransform(np.array([[location]]), calibration_data.transformation_matrix)
    transformed_dart_loc = dart_loc.reshape(1, -1)[0]
    return Point.cast(transformed_dart_loc)


# Returns dartThrow (score, multiplier, angle, magnitude) based on x,y location
def get_dart_region(dart_loc: Point, calibration_data: CalibrationData) -> Dart:
    frame = calibration_data.image_shape

    # find the magnitude and angle of the dart
    vx = dart_loc[0] - frame.width / 2
    vy = frame.height / 2 - dart_loc[1]

    # reference angle for atan2 conversion
    ref_angle = 81

    magnitude = math.sqrt(math.pow(vx, 2) + math.pow(vy, 2))
    angle = math.fmod(((math.atan2(vy, vx) * 180 / math.pi) + 360 - ref_angle), 360)

    angle_diff_mul = int(angle / 18)

    dart_base = [20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10, 6, 13, 4, 18, 1]
    try:
        base = dart_base[angle_diff_mul]
    except IndexError:
        base = -1

    # Calculating multiplier (and special cases for Bull's Eye):
    for i in range(0, len(calibration_data.ring_radii)):
        # Find the ring that encloses the dart
        if magnitude <= calibration_data.ring_radii[i]:
            if i == 0:  # Double Bull's Eye
                base = 25
                multiplier = 2
            elif i == 1:  # Single Bull's Eye
                base = 25
                multiplier = 1
            elif i == 3:  # Triple
                multiplier = 3
            elif i == 5:  # Double
                multiplier = 2
            else:  # Single
                multiplier = 1
            break
    else:  # miss
        print('miss', magnitude)
        base = 0
        multiplier = 0

    return Dart(base, multiplier, magnitude, angle)
