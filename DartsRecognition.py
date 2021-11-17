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

    min_threshold = 50
    max_threshold = 15_000

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

            # dart outside?
            if corners_r.size < 40 or len(corners_r) == 640:
                print("Dart not detected")
                continue

            # filter corners
            close_corners_r = filter_distant_corners(corners_r)

            # dart outside?
            if close_corners_r.size < 30:
                print("Dart not detected")
                continue

            # filter corners
            corners_on_line_r = filter_corners_on_line(close_corners_r)
            mask_center = get_real_location(corners_on_line_r, mount='right')
            # diff in mask based on rbg image
            diff_rgb_r = get_diff(rgb_r, next_rgb_r)
            diff_image_for_mask_r = cv2.cvtColor(diff_rgb_r, cv2.COLOR_RGB2GRAY)
            # get corners in mask
            mask = get_mask(mask_center)
            corners_in_mask = get_corners_in_mask(diff_image_for_mask_r, mask)

            # dart outside?
            if corners_in_mask is None:
                print('No corners in mask found')
                continue

            # check if it was really a dart
            _, binary_diff_r = cv2.threshold(diff_image_r, 60, 255, 0)
            if cv2.countNonZero(binary_diff_r) > max_threshold:
                print('Player entered zone', cv2.countNonZero(binary_diff_r))
                break

            # get final darts location
            location_of_dart_r = get_real_location(corners_in_mask, 'right')
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
                dbg_draw_corners(corners_r, close_corners_r, corners_on_line_r, corners_in_mask)
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
    # filter noise from image distortions
    m = n = 9
    kernel = np.ones((m, n), np.float32) / (m * n)
    blurred_image = cv2.filter2D(image, -1, kernel)
    blurred_next_image = cv2.filter2D(next_image, -1, kernel)
    # create diff image
    diff_image = cv2.absdiff(blurred_image, blurred_next_image)
    # # filter noise from image distortions
    # m = n = 5
    # kernel = np.ones((m, n), np.float32) / (m * n)
    # blurred_diff_image = cv2.filter2D(diff_image, -1, kernel)
    return diff_image


def get_corners(image):
    corners = cv2.goodFeaturesToTrack(image, 640, 0.001, 0, mask=None, blockSize=3, useHarrisDetector=1, k=0.06)
    print('corners:', len(corners))
    corners = corners[:, 0, :].astype(int)
    return corners


def get_mask(point):
    x, y = point
    mask_radius = 10
    mask = np.zeros(shape=(600, 800), dtype=np.uint8)
    cv2.circle(mask, (x, y), mask_radius, 1, cv2.FILLED)
    cv2.circle(dbg_next_image, (x, y), 10, (0, 255, 255))  # debug
    return mask


def get_corners_in_mask(image, mask):
    corners = cv2.goodFeaturesToTrack(image, 640, 0.05, 0, mask=mask, blockSize=3, useHarrisDetector=1, k=0.06)
    if corners is not None:
        print('corners:', len(corners))
        corners = corners[:, 0, :].astype(int)
    return corners


def filter_distant_corners(corners):
    # TODO: don't use mean, but something else to get where most of the points are
    mean_corners = np.mean(corners, axis=0)
    mean_x, mean_y = mean_corners.ravel()

    # debug
    cv2.rectangle(dbg_next_image, (int(mean_x)-150, int(mean_y)-100), (int(mean_x)+150, int(mean_y)+100), (255, 0, 0))

    corners_to_filter_out = []
    for idx, corner in enumerate(corners):
        corner_x, corner_y = corner.ravel()
        # filter noise to only get dart arrow
        if abs(mean_x - corner_x) > 150 or abs(mean_y - corner_y) > 100:
            corners_to_filter_out.append(idx)

    corners_new = np.delete(corners, [corners_to_filter_out], axis=0)
    return corners_new


def filter_corners_on_line(corners):
    rows, cols = (800, 600)

    corners_on_line, line1_r = _filter_corners_line(corners, rows, cols, cv2.DIST_WELSCH)
    corners_on_line, line2_r = _filter_corners_line(corners_on_line, rows, cols, cv2.DIST_HUBER)

    cv2.line(dbg_next_image, *line1_r, (127, 0, 127))  # debug
    cv2.line(dbg_next_image, *line2_r, (255, 0, 255))  # debug

    return corners_on_line


def _filter_corners_line(corners, rows, cols, dist_func):
    [vx, vy, x, y] = cv2.fitLine(corners, dist_func, 0, 0.1, 0.1)  # 5.0 if dist_func == cv2.DIST_WELSCH else 0
    left_y = int((-x * vy / vx) + y)
    right_y = int(((cols - x) * vy / vx) + y)

    corners_to_filter_out = []
    for idx, corner in enumerate(corners):
        corner_x, corner_y = corner.ravel()
        # check distance to fitted line, only draw corners within certain range
        distance = dist(0, left_y, cols - 1, right_y, corner_x, corner_y)
        if distance > 10:
            corners_to_filter_out.append(idx)

    corners_final = np.delete(corners, [corners_to_filter_out], axis=0)  # delete corners to form new array
    return corners_final, ((0, left_y), (cols-1, right_y))


def get_real_location(corners, mount):
    if mount == "right":
        idx = np.argmax(corners[:, 0], axis=0)
    else:
        idx = np.argmin(corners[:, 0], axis=0)

    return corners[idx]


def dbg_draw_corners(corners_, close_corners, corners_on_line, corners_in_mask):
    for corner in corners_[(corners_[:, None] != close_corners).any(-1).all(1)]:
        cv2.circle(dbg_next_image, corner.ravel(), 2, (255, 0, 0), 2)  # blue
    for corner in close_corners:
        cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 255, 0), 1)  # green
    for corner in corners_on_line:
        cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 0, 255), 1)  # red
    for corner in corners_in_mask:
        cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 255, 255), 1)  # yellow
