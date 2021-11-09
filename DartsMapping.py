import math

import cv2
import numpy as np

from Classes import DartDef


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

    dart_info = DartDef()

    # find the magnitude and angle of the dart
    vx = dart_loc[0] - width / 2
    vy = height / 2 - dart_loc[1]

    # reference angle for atan2 conversion
    ref_angle = 81

    dart_info.magnitude = math.sqrt(math.pow(vx, 2) + math.pow(vy, 2))
    dart_info.angle = math.fmod(((math.atan2(vy, vx) * 180 / math.pi) + 360 - ref_angle), 360)

    angle_diff_mul = int(dart_info.angle / 18)

    dart_info_base = [20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10, 6, 13, 4, 18, 1]
    try:
        dart_info.base = dart_info_base[angle_diff_mul]
    except IndexError:
        dart_info.base = -1

    # Calculating multiplier (and special cases for Bull's Eye):
    for i in range(0, len(calibration_data.ring_radius)):
        # Find the ring that encloses the dart
        if dart_info.magnitude <= calibration_data.ring_radius[i]:
            if i == 0:  # Double Bull's Eye
                dart_info.base = 25
                dart_info.multiplier = 2
            elif i == 1:  # Single Bull's Eye
                dart_info.base = 25
                dart_info.multiplier = 1
            elif i == 3:  # Triple
                dart_info.multiplier = 3
            elif i == 5:  # Double
                dart_info.multiplier = 2
            elif i == 2 or i == 4:  # Single
                dart_info.multiplier = 1
            break
    else:  # miss
        print('miss', dart_info.magnitude)
        dart_info.base = 0
        dart_info.multiplier = 0

    return dart_info
