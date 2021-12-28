import time

import cv2
import numpy as np

from DartsMapping import get_dart_region, get_transformed_location
from MathFunctions import dist

DEBUG = True
dbg_next_image = [[]]
dbg_diff_image = [[]]


def get_darts(cam_r, calibration_data_r, breaker):
    global dbg_next_image
    global dbg_diff_image

    print(f'\n### Dart {breaker} ###')

    min_threshold = 300
    max_threshold = 30_000

    image_r, rgb_r = get_gray(cam_r)

    while True:
        time.sleep(0.1)

        # check if dart hit the board
        next_image_r, _ = get_gray(cam_r)
        binary_diff_r = get_binary_diff(image_r, next_image_r)
        num_changed_pixels = cv2.countNonZero(binary_diff_r)

        # num of changed pixels indicates dart
        if min_threshold < num_changed_pixels < max_threshold and breaker != -1:
            # wait for camera vibrations
            time.sleep(0.2)

            # filter noise
            next_image_r, next_rgb_r = get_gray(cam_r)
            diff_image_r = get_blurred_diff(image_r, next_image_r)
            dbg_next_image = cv2.cvtColor(next_image_r, cv2.COLOR_GRAY2RGB)

            # get corners
            corners_r = get_corners(diff_image_r)

            # dart detected?
            if corners_r.size < 40 or corners_r.size == 640 * 2:
                print("Dart not detected (pre-processing)")
                print('corners:', len(corners_r))
                continue

            # filter corners
            # close_corners_r = filter_corners_of_flight(corners_r)
            close_corners_r = corners_r
            corners_on_line_r = filter_corners_on_line(close_corners_r)

            # dart detected?
            if corners_on_line_r.size < 1:
                print("Dart not detected (post-processing)")
                print('corners:', len(corners_on_line_r))
                if DEBUG:
                    # copy debug images
                    dbg_diff_image = diff_image_r.copy()
                    # draw all different corners
                    dbg_draw_corners(corners_r, close_corners_r, corners_on_line_r)
                    # write debug images
                    cv2.imwrite(f'tmp/dbg_dart{breaker}.jpg', dbg_diff_image)
                    cv2.imwrite(f'tmp/dbg_corners{breaker}.jpg', dbg_next_image)
                continue

            # check if it was really a dart
            _, binary_diff_r = cv2.threshold(diff_image_r, 60, 255, 0)
            if cv2.countNonZero(binary_diff_r) > max_threshold:
                print('Player entered zone', cv2.countNonZero(binary_diff_r))
                break

            # get final darts location
            location_of_dart_r = get_real_location(corners_on_line_r, 'right')
            transformed_location_r = get_transformed_location(*location_of_dart_r, calibration_data_r)
            dart_info_r = get_dart_region(transformed_location_r, calibration_data_r)

            # with two cams: the decision has to be made here
            dart_info = dart_info_r
            dart_info.location = transformed_location_r

            print("Dart detected")
            print(f'{dart_info.multiplier}x{dart_info.base}')

            if DEBUG:
                # copy debug images
                dbg_diff_image = diff_image_r.copy()
                # draw all different corners
                dbg_draw_corners(corners_r, close_corners_r, corners_on_line_r)
                # draw darts location
                cv2.circle(dbg_next_image, location_of_dart_r.ravel(), 1, (255, 0, 255), 1)
                cv2.circle(dbg_next_image, location_of_dart_r.ravel(), 20, (255, 0, 255), 1)
                # mark dart on test image
                cv2.circle(dbg_diff_image, location_of_dart_r.ravel(), 10, (255, 255, 255), 1, 8)
                # write debug images
                cv2.imwrite(f'tmp/dbg_dart{breaker}.jpg', dbg_diff_image)
                cv2.imwrite(f'tmp/dbg_corners{breaker}.jpg', dbg_next_image)

            return dart_info

        # missed dart
        elif num_changed_pixels <= min_threshold:
            if num_changed_pixels > 0:
                print(num_changed_pixels)
            image_r = next_image_r
            continue

        # if player enters zone - break loop
        elif num_changed_pixels >= max_threshold:
            print('Player entered zone')
            print(num_changed_pixels)
            break


def get_gray(cam):
    image = cam.read()
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return gray_image, image


def get_binary_diff(image, next_image):
    diff_image = cv2.absdiff(image, next_image)
    blurred_image = cv2.GaussianBlur(diff_image, (5, 5), 0)
    blurred_image = cv2.bilateralFilter(blurred_image, 9, 75, 75)
    _, binary_diff_image = cv2.threshold(blurred_image, 60, 255, 0)
    return binary_diff_image


def get_diff(image, next_image):
    diff_image = cv2.absdiff(image, next_image)
    return diff_image


def get_blurred_diff(image, next_image):
    # create diff image
    diff_image = cv2.absdiff(image, next_image)
    # # filter noise from image distortions
    m = n = 5
    kernel = np.ones((m, n), np.float32) / (m * n)
    blurred_diff_image = cv2.filter2D(diff_image, -1, kernel)
    return blurred_diff_image


def get_corners(image):
    corners = cv2.goodFeaturesToTrack(image, 640, 0.0008, 1, mask=None, blockSize=3, useHarrisDetector=1, k=0.06)
    corners = corners[:, 0, :].astype(int)
    return corners


def line_frame_intersection(line, frame):
    def perp(a):
        b = np.empty_like(a)
        b[0] = -a[1]
        b[1] = a[0]
        return b

    def seg_intersect(a1, da, b1, db):
        dp = a1 - b1
        dap = perp(da)
        denom = np.dot(dap, db)
        num = np.dot(dap, dp)
        return (num / denom.astype(float)) * db + b1

    rows, cols = frame

    rect_lines = [
        # vx, vy, x0, y0
        [1, 0, 0, 0],
        [1, 0, 0, cols - 1],
        [0, 1, 0, 0],
        [0, 1, rows - 1, 0]
    ]

    points = []

    for rect_line in rect_lines:
        px, py = seg_intersect(np.array([rect_line[2], rect_line[3]]), np.array([rect_line[0], rect_line[1]]),
                               np.array([line[2], line[3]]), np.array([line[0], line[1]])).astype(int)
        if rect_line[0] and 0 <= px < rows or rect_line[1] and 0 <= py < cols:
            points.append((px, py))

    if len(points) != 2:
        print(points)

    return points


def filter_corners_on_line(corners):
    line = cv2.fitLine(corners, cv2.DIST_WELSCH, 0, 0.1, 0.1).ravel()
    p1, p2 = line_frame_intersection(line, (800, 600))

    corners_to_filter_out = []
    for idx, corner in enumerate(corners):
        # check distance to fitted line, only draw corners within certain range
        distance = dist(*p1, *p2, *corner)
        if distance > 20:
            corners_to_filter_out.append(idx)

    cv2.line(dbg_next_image, p1, p2, (127, 0, 127))  # debug

    corners_final = np.delete(corners, [corners_to_filter_out], axis=0)  # delete corners to form new array
    return corners_final


def filter_corners_of_flight(corners):
    lowest = corners[np.argmin(corners[:, 1], axis=0)]
    highest = corners[np.argmax(corners[:, 1], axis=0)]
    diff_y = highest[1] - lowest[1]
    mid_y = lowest[1] + 2 / 3 * diff_y

    corners_to_filter_out = []
    for idx, corner in enumerate(corners):
        corner_y = corner.ravel()[1]
        if corner_y > mid_y:
            corners_to_filter_out.append(idx)

    corners_without_flight = np.delete(corners, [corners_to_filter_out], axis=0)
    return corners_without_flight


def get_real_location(corners, mount):
    # if mount == "right":
    #     idx = np.argmax(corners[:, 0], axis=0)
    # else:
    #     idx = np.argmin(corners[:, 0], axis=0)
    idx = np.argmin(corners[:, 1], axis=0)
    return corners[idx]


def dbg_draw_corners(corners_, close_corners, corners_on_line):
    for corner in corners_[(corners_[:, None] != close_corners).any(-1).all(1)]:
        cv2.circle(dbg_next_image, corner.ravel(), 1, (255, 0, 0), 1)  # blue
    for corner in close_corners:
        cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 255, 0), 1)  # green
    for corner in corners_on_line:
        cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 0, 255), 1)  # red
