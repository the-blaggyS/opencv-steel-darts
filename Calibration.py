import math
import os
import pickle
from time import sleep

import cv2
import numpy as np

from Classes import CalibrationData
from Draw import draw_board
from VideoCapture import VideoStream

original_image = np.empty_like


def calibrate(cam, mount):
    calibration_data_file = {
        'right': 'tmp/calibration_data_r.pkl',
        'left': 'tmp/calibration_data_l.pkl'
    }

    try:
        cam.start()
        sleep(1)
        calibration_image = cam.read()
        cam.stop()
    except Exception as e:
        print('Could not init cam')
        print(e)
        return

    global original_image
    original_image = calibration_image

    is_calibrated = False
    calibration_data = CalibrationData()

    while not is_calibrated:
        if os.path.isfile(calibration_data_file[mount]):  # if calibration data exists
            calibration_data = read_calibration_data(calibration_data_file[mount])
            if confirm_calibration(calibration_data, calibration_image.copy()):
                is_calibrated = True
        if not is_calibrated:  # if no calibration data exists or current wasn't accepted
            calibration_data = start_calibration_process(calibration_image.copy(), calibration_data)
            if calibration_data:
                with open(calibration_data_file[mount], 'wb') as calibration_file:
                    pickle.dump(calibration_data, calibration_file, 0)
                is_calibrated = True

    return calibration_data


def start_calibration_process(image, calibration_data):
    # 13/6: 0 | 6/10: 1 | 10/15: 2 | 15/2: 3 | 2/17: 4 | 17/3: 5 | 3/19: 6 | 19/7: 7 | 7/16: 8 | 16/8: 9 |
    # 8/11: 10 | 11/14: 11 | 14/9: 12 | 9/12: 13 | 12/5: 14 | 5/20: 15 | 20/1: 16 | 1/18: 17 | 18/4: 18 | 4/13: 19
    # top, bottom, left, right
    # 12/9, 2/15, 8/16, 13/4
    calibration_data = manipulate_transformation_points(image, calibration_data)

    cv2.destroyAllWindows()

    cv2.imshow('Confirm Calibration', original_image)
    user_input = cv2.waitKey(0)
    if user_input == ord('\r'):
        cv2.destroyAllWindows()
        return calibration_data
    else:
        return None


def confirm_calibration(calibration_data, image):
    transformed_image = cv2.warpPerspective(image.copy(), calibration_data.transformation_matrix, (800, 800))
    overlaid_image = draw_board(transformed_image, calibration_data)

    cv2.imshow('Confirm Calibration', overlaid_image)

    user_input = cv2.waitKey(0)
    cv2.destroyAllWindows()
    return user_input == ord('\r')  # enter


def read_calibration_data(file_name):
    try:
        with open(file_name, 'rb') as calibration_file:
            calibration_data = pickle.load(calibration_file)
    except EOFError as e:
        print(e)

    calibration_data.transformation_matrix = np.array(calibration_data.transformation_matrix)
    return calibration_data


def manipulate_transformation_points(image, calibration_data):

    def nothing(x):
        pass

    slider_count = 500

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)

    for i in range(4):
        for j, xy in enumerate(['x', 'y']):
            cv2.createTrackbar(f'p{i+1}_{xy}', 'image', 0, slider_count, nothing)
            cv2.setTrackbarPos(f'p{i+1}_{xy}', 'image', int(slider_count/2) + calibration_data.offsets[i][j])

    while True:
        offsets = []
        for i in range(4):
            offsets.append([])
            for xy in ['x', 'y']:
                offsets[i].append(cv2.getTrackbarPos(f'p{i+1}_{xy}', 'image') - int(slider_count/2))

        transformation_matrix, transformed_image = transformation(image.copy(), calibration_data, *offsets)
        cv2.imshow('image', transformed_image)

        user_input = cv2.waitKey(1) & 0xFF
        if user_input == 27:  # escape
            break

    calibration_data.offsets = offsets
    calibration_data.transformation_matrix = transformation_matrix
    return calibration_data


def transformation(image, calibration_data, p1, p2, p3, p4):
    points = calibration_data.points
    new_points = list(map(lambda p: destination_point(p, calibration_data),  calibration_data.dst_points))

    # create transformation matrix
    src = np.array([(points[0][0] + p1[0], points[0][1] + p1[1]), (points[1][0] + p2[0], points[1][1] + p2[1]),
                    (points[2][0] + p3[0], points[2][1] + p3[1]), (points[3][0] + p4[0], points[3][1] + p4[1])],
                   np.float32)
    dst = np.array(new_points, np.float32)
    transformation_matrix = cv2.getPerspectiveTransform(src, dst)

    image = cv2.warpPerspective(image, transformation_matrix, (800, 800))
    image = draw_board(image, calibration_data)

    for point in new_points:
        cv2.circle(image, list(map(int, point[:2])), 2, (255, 255, 0), 2, 4)

    return transformation_matrix, image


def destination_point(i, calibration_data):
    dst_point = [
        (calibration_data.center_dartboard[0] + calibration_data.ring_radius[5] * math.cos((0.5 + i) * calibration_data.sector_angle)),
        (calibration_data.center_dartboard[1] + calibration_data.ring_radius[5] * math.sin((0.5 + i) * calibration_data.sector_angle))
    ]
    return dst_point


if __name__ == '__main__':
    print('Welcome to darts!')
    cam_r = VideoStream(src=1)
    cam_r.start()
    calibrate(cam_r, mount='right')
