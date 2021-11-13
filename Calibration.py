import math
import os
import pickle

import cv2
import numpy as np

from Classes import CalibrationData, Ellipse, Line
from Draw import draw_board, draw_line
from MathFunctions import intersect_line_circle
from VideoCapture import VideoStream

original_image = np.empty_like


def calibrate(cam, mount):
    calibration_data_file = {
        'right': 'tmp/calibration_data_r.pkl',
        'left': 'tmp/calibration_data_l.pkl'
    }

    try:
        calibration_image = cam.read()
    except Exception as e:
        print('Could not init cam')
        print(e)
        return

    global original_image
    original_image = calibration_image

    is_calibrated = False
    calibration_data = None

    while not is_calibrated:
        if os.path.isfile(calibration_data_file[mount]):  # if calibration data exists
            calibration_data = restore_calibration_from_file(calibration_data_file[mount], calibration_image.copy())
            if calibration_data:  # if user confirmed loaded calibration data
                is_calibrated = True
            else:  # if cam needs new calibration
                os.remove(calibration_data_file[mount])
        else:  # if no calibration data exists
            calibration_data = start_calibration_process(calibration_image.copy())
            if calibration_data:
                with open(calibration_data_file[mount], 'wb') as calibration_file:
                    pickle.dump(calibration_data, calibration_file, 0)
                is_calibrated = True

    return calibration_data


def start_calibration_process(calibration_image):
    pre_processed_image = pre_process_calibration_image(calibration_image.copy())
    calibration_data = CalibrationData()
    calibration_data.points = get_transformation_points(pre_processed_image)

    # 13/6: 0 | 6/10: 1 | 10/15: 2 | 15/2: 3 | 2/17: 4 | 17/3: 5 | 3/19: 6 | 19/7: 7 | 7/16: 8 | 16/8: 9 |
    # 8/11: 10 | 11/14: 11 | 14/9: 12 | 9/12: 13 | 12/5: 14 | 5/20: 15 | 20/1: 16 | 1/18: 17 | 18/4: 18 | 4/13: 19
    # top, bottom, left, right
    # 12/9, 2/15, 8/16, 13/4
    calibration_data.dst_points = [12, 2, 18, 8]
    calibration_data.transformation_matrix = manipulate_transformation_points(calibration_image, calibration_data)

    cv2.destroyAllWindows()

    cv2.imshow('Confirm Calibration', original_image)
    user_input = cv2.waitKey(0)
    if user_input == ord('\r'):
        cv2.destroyAllWindows()
        return calibration_data
    else:
        return None


def restore_calibration_from_file(file_name, calibration_image):
    try:
        with open(file_name, 'rb') as calibration_file:
            calibration_data = pickle.load(calibration_file)

        calibration_data.transformation_matrix = np.array(calibration_data.transformation_matrix)

        transformed_image = cv2.warpPerspective(calibration_image.copy(), calibration_data.transformation_matrix, (800, 800))
        overlaid_image = draw_board(transformed_image, calibration_data)

        cv2.imshow('Confirm Calibration', overlaid_image)

        user_input = cv2.waitKey(0)
        if user_input == ord('\r'):  # enter
            cv2.destroyAllWindows()
            return calibration_data
        else:
            cv2.destroyAllWindows()
            return None

    except EOFError as e:
        print(e)


def pre_process_calibration_image(rgb_image):
    hsv_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2HSV)
    cv2.imshow('HSV', hsv_image)

    kernel = np.ones((5, 5), np.float32) / 25
    blurred_image = cv2.filter2D(hsv_image, -1, kernel)
    cv2.imshow('Blurred', blurred_image)

    _, _, image_brightness = cv2.split(blurred_image)
    cv2.imshow('Brightness', image_brightness)

    _, binary_image = cv2.threshold(image_brightness, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imshow('Binary', binary_image)

    kernel = np.ones((5, 5), np.uint8)
    closed_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
    cv2.imshow('Morphological Closing', closed_image)

    return closed_image


def get_transformation_points(image):
    ellipse = find_ellipse(image.copy())
    cv2.ellipse(original_image, (ellipse.x, ellipse.y), (ellipse.a, ellipse.b), ellipse.angle, 0, 360, (0, 255, 0), 2)
    cv2.imshow('Selected Ellipse', original_image)

    edged_image = auto_canny(image)
    cv2.imshow('Edged Image', edged_image)

    lines = find_sector_lines(edged_image)
    for line in lines:
        draw_line(original_image, line)
    cv2.imshow('Selected Sector Lines', original_image)

    M = ellipse2circle(ellipse)
    intersectp_s = get_ellipse_line_intersection(ellipse, M, lines)
    for point in intersectp_s:
        cv2.circle(original_image, list(map(int, point[:2])), 3, (255, 0, 0), 2, 8)
    cv2.imshow('Calculated Intersections', original_image)
    cv2.waitKey(0)

    return intersectp_s


def find_ellipse(image):
    ellipses = []

    contours, _ = cv2.findContours(image, 1, 2)
    contours = sorted(contours, key=lambda cnt: cv2.contourArea(cnt), reverse=True)

    tmp_image = original_image.copy()

    for contour in contours:
        try:
            ellipse = cv2.fitEllipse(contour)
            cv2.ellipse(tmp_image, ellipse, (0, 255, 0), 2)
        except Exception:
            continue

        x, y = ellipse[0]
        a, b = ellipse[1]
        angle = ellipse[2]

        ellipses.append(Ellipse(int(a/2), int(b/2), int(x), int(y), int(angle)))

    cv2.imshow('Found Ellipses', tmp_image)
    cv2.waitKey(0)

    while True:
        for ellipse in ellipses:
            tmp_image = original_image.copy()
            cv2.ellipse(tmp_image, (ellipse.x, ellipse.y), (ellipse.a, ellipse.b), ellipse.angle, 0.0, 360.0,
                        (0, 255, 0), 2)
            cv2.imshow('Is this the outer double ring?', tmp_image)

            user_input = cv2.waitKey(0)
            if user_input == ord('\r'):
                return ellipse


def ellipse2circle(ellipse):
    angle = ellipse.angle * math.pi / 180
    x = ellipse.x
    y = ellipse.y
    a = ellipse.a
    b = ellipse.b

    # build transformation matrix http://math.stackexchange.com/questions/619037/circle-affine-transformation
    R1 = np.array([[math.cos(angle), math.sin(angle), 0], [-math.sin(angle), math.cos(angle), 0], [0, 0, 1]])
    R2 = np.array([[math.cos(angle), -math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]])

    T1 = np.array([[1, 0, -x], [0, 1, -y], [0, 0, 1]])
    T2 = np.array([[1, 0, x], [0, 1, y], [0, 0, 1]])

    D = np.array([[1, 0, 0], [0, a / b, 0], [0, 0, 1]])

    M = T2.dot(R2.dot(D.dot(R1.dot(T1))))

    return M


def find_sector_lines(image):

    lines = cv2.HoughLines(image, 1, np.pi / 80, 100, 100)
    lines = [Line(*line[0]) for line in lines]

    tmp_image = original_image.copy()
    for line in lines:
        draw_line(tmp_image, line)

    cv2.imshow('Found Lines', tmp_image)
    cv2.waitKey(0)

    degree_diff = lambda a, b: abs(abs(a % np.pi - b % np.pi) - np.pi/2)

    min_diff_lines = []

    for line1 in lines:
        for line2 in lines:

            if min_diff_lines:
                diff = degree_diff(line1.theta, line2.theta)
                min_diff = degree_diff(min_diff_lines[0].theta, min_diff_lines[1].theta)

                if diff < min_diff:
                    min_diff_lines = [line1, line2]
            else:
                min_diff_lines = [line1, line2]

    return min_diff_lines


def get_ellipse_line_intersection(ellipse, M, lines):
    center_ellipse = (ellipse.x, ellipse.y)
    circle_radius = ellipse.a
    M_inv = np.linalg.inv(M)

    # find line circle intersection and use inverse transformation matrix to transform it back to the ellipse
    intersectp_s = []
    for line in lines:
        line_p1 = M.dot(np.transpose(np.hstack([line.p1, 1])))
        line_p2 = M.dot(np.transpose(np.hstack([line.p2, 1])))
        inter1, inter_p1, inter2, inter_p2 = intersect_line_circle(np.asarray(center_ellipse), circle_radius,
                                                                   np.asarray(line_p1), np.asarray(line_p2))
        if inter1 and inter2:
            inter_p1 = M_inv.dot(np.transpose(np.hstack([inter_p1, 1])))
            inter_p2 = M_inv.dot(np.transpose(np.hstack([inter_p2, 1])))
            intersectp_s.append(inter_p1)
            intersectp_s.append(inter_p2)

    return intersectp_s


def manipulate_transformation_points(image, calibration_data):

    def nothing(x):
        pass

    slider_count = 200

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.createTrackbar('ts1', 'image', 0, 20, nothing)
    cv2.createTrackbar('tx1', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ty1', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ts2', 'image', 0, 20, nothing)
    cv2.createTrackbar('tx2', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ty2', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ts3', 'image', 0, 20, nothing)
    cv2.createTrackbar('tx3', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ty3', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ts4', 'image', 0, 20, nothing)
    cv2.createTrackbar('tx4', 'image', 0, slider_count, nothing)
    cv2.createTrackbar('ty4', 'image', 0, slider_count, nothing)
    cv2.setTrackbarPos('ts1', 'image', 10)
    cv2.setTrackbarPos('tx1', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ty1', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ts2', 'image', 10)
    cv2.setTrackbarPos('tx2', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ty2', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ts3', 'image', 10)
    cv2.setTrackbarPos('tx3', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ty3', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ts4', 'image', 10)
    cv2.setTrackbarPos('tx4', 'image', int(slider_count / 2))
    cv2.setTrackbarPos('ty4', 'image', int(slider_count / 2))

    while True:
        ts1 = cv2.getTrackbarPos('ts1', 'image')
        tx1 = cv2.getTrackbarPos('tx1', 'image') - int(slider_count / 2)
        ty1 = cv2.getTrackbarPos('ty1', 'image') - int(slider_count / 2)
        ts2 = cv2.getTrackbarPos('ts2', 'image')
        tx2 = cv2.getTrackbarPos('tx2', 'image') - int(slider_count / 2)
        ty2 = cv2.getTrackbarPos('ty2', 'image') - int(slider_count / 2)
        ts3 = cv2.getTrackbarPos('ts3', 'image')
        tx3 = cv2.getTrackbarPos('tx3', 'image') - int(slider_count / 2)
        ty3 = cv2.getTrackbarPos('ty3', 'image') - int(slider_count / 2)
        ts4 = cv2.getTrackbarPos('ts4', 'image')
        tx4 = cv2.getTrackbarPos('tx4', 'image') - int(slider_count / 2)
        ty4 = cv2.getTrackbarPos('ty4', 'image') - int(slider_count / 2)

        calibration_data.dst_points = [ts1, ts2, ts3, ts4]
        transformation_matrix, transformed_image = transformation(image.copy(), calibration_data, tx1, ty1, tx2, ty2, tx3, ty3, tx4, ty4)
        cv2.imshow('image', transformed_image)

        user_input = cv2.waitKey(1) & 0xFF
        if user_input == 27:  # escape
            break

    return transformation_matrix


def transformation(image, calibration_data, tx1, ty1, tx2, ty2, tx3, ty3, tx4, ty4):
    points = calibration_data.points
    new_points = list(map(lambda p: destination_point(p, calibration_data),  calibration_data.dst_points))

    # create transformation matrix
    src = np.array([(points[0][0] + tx1, points[0][1] + ty1), (points[1][0] + tx2, points[1][1] + ty2),
                    (points[2][0] + tx3, points[2][1] + ty3), (points[3][0] + tx4, points[3][1] + ty4)],
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


def auto_canny(image):
    sigma = 0.33
    v = np.median(image)
    lower = int(max(0, (1 - sigma) * v))
    upper = int(min(255, (1 + sigma) * v))
    edged_image = cv2.Canny(image, lower, upper)
    return edged_image


if __name__ == '__main__':
    print('Welcome to darts!')
    cam_r = VideoStream(src=1).start()
    calibrate(cam_r, mount='right')
