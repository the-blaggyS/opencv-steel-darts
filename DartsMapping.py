import math

import cv2
import numpy as np

from Classes import Dart


def get_transformed_location(x_coord, y_coord, calibration_data):
    # transform only the hit point with the saved transformation matrix
    # ToDo: idea for second camera -> transform complete image and overlap both images to find dart location?
    dart_loc_temp = np.array([[x_coord, y_coord]], dtype="float32")
    dart_loc_temp = np.array([dart_loc_temp])
    dart_loc = cv2.perspectiveTransform(dart_loc_temp, calibration_data.transformation_matrix)
    new_dart_loc = tuple(dart_loc.reshape(1, -1)[0])

    return new_dart_loc


# Returns dartThrow (score, multiplier, angle, magnitude) based on x,y location
def get_dart_region(dart_loc, calibration_data):
    height = 800
    width = 800

    # find the magnitude and angle of the dart
    vx = dart_loc[0] - width / 2
    vy = height / 2 - dart_loc[1]

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
    for i in range(0, len(calibration_data.ring_radius)):
        # Find the ring that encloses the dart
        if magnitude <= calibration_data.ring_radius[i]:
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

    dart = Dart(base, multiplier, magnitude, angle)

    return dart
