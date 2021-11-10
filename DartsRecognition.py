import time

import cv2
import numpy as np

from DartsMapping import get_dart_region, get_transformed_location
from MathFunctions import dist, closest_point


def get_darts(cam_r, calibration_data_r, count=3):

    breaker = 0

    min_threshold = 500
    max_threshold = 10_000

    image_r = get_gray(cam_r)

    while True:
        time.sleep(0.2)
        # check if dart hit the board
        next_image_r = get_gray(cam_r)
        binary_diff_r = get_binary_diff(image_r, next_image_r)

        num_changed_pixels = cv2.countNonZero(binary_diff_r)
        # if num_changed_pixels > 0:
        #     print(num_changed_pixels)

        if min_threshold < num_changed_pixels < max_threshold and breaker < count:
            # wait for camera vibrations
            time.sleep(0.5)

            print(f'\n### Dart {breaker+1} ###')

            # filter noise
            next_image_r = get_gray(cam_r)
            diff_image_r = get_diff(image_r, next_image_r)

            # get corners
            corners_r = get_corners(diff_image_r)

            dbg_diff_image = diff_image_r.copy()
            dbg_next_image = cv2.cvtColor(next_image_r, cv2.COLOR_GRAY2RGB)

            # dart outside?
            if corners_r.size < 40 or len(corners_r) == 640:
                print("dart not detected")
                continue

            # filter corners
            corners_filtered_r, mean = filter_corners(corners_r)
            mean = tuple(map(int, mean))
            cv2.rectangle(dbg_next_image, (mean[0]-180, mean[1]-120), (mean[0]+180, mean[1]+120), (255, 0, 0))

            # dart outside?
            if corners_filtered_r.size < 30:
                print("dart not detected")
                continue

            # find left and rightmost corners
            rows, cols = diff_image_r.shape[:2]
            corners_tmp, line_r = filter_corners_line(corners_filtered_r, rows, cols, cv2.DIST_WELSCH)
            cv2.line(dbg_next_image, *line_r, (127, 0, 127))
            corners_final_r, line_r = filter_corners_line(corners_tmp, rows, cols, cv2.DIST_HUBER)
            cv2.line(dbg_next_image, *line_r, (255, 0, 255))

            for corner in corners_r:
                cv2.circle(dbg_next_image, corner.ravel(), 1, (255, 0, 0))  # blue
            for corner in corners_filtered_r:
                cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 255, 0))  # green
            for corner in corners_final_r:
                cv2.circle(dbg_next_image, corner.ravel(), 1, (0, 0, 255))  # red

            _, binary_diff_r = cv2.threshold(diff_image_r, 60, 255, 0)

            # check if it was really a dart
            if cv2.countNonZero(binary_diff_r) > max_threshold * 2:
                print('threshold exceeded')
                continue

            # dart was found -> increase counter
            breaker += 1
            print("Dart detected")

            # get final darts location
            try:
                location_of_dart_r = get_real_location(corners_final_r, 'right')
                # map point to line
                location_of_dart_r = map_location_to_line((location_of_dart_r.item(0), location_of_dart_r.item(1)), line_r).astype(int)
                cv2.circle(dbg_next_image, location_of_dart_r.ravel(), 1, (255, 0, 255), 1)
                cv2.circle(dbg_next_image, location_of_dart_r.ravel(), 20, (255, 0, 255), 1)
                # check for the location of the dart with the calibration
                dart_loc_r = get_transformed_location(location_of_dart_r.item(0), location_of_dart_r.item(1), calibration_data_r)
                # detect region and score
                dart_info_r = get_dart_region(dart_loc_r, calibration_data_r)
                # mark dart on test image
                cv2.circle(dbg_diff_image, (location_of_dart_r.item(0), location_of_dart_r.item(1)), 10, (255, 255, 255), 2, 8)
            except AttributeError as e:
                print("Something went wrong in finding the darts location!")
                print(e)
                breaker -= 1
                continue

            dart_info = dart_info_r
            dart_info.location = dart_loc_r

            # print(dart_info.base, dart_info.multiplier)
            cv2.imwrite(f'dbg_dart{breaker}.jpg', dbg_diff_image)
            cv2.imwrite(f'dbg_corners{breaker}.jpg', dbg_next_image)

            yield dart_info

            # save new diff img for next dart
            image_r = next_image_r

        # missed dart
        elif cv2.countNonZero(binary_diff_r) <= min_threshold:
            image_r = next_image_r
            continue

        # if player enters zone - break loop
        elif cv2.countNonZero(binary_diff_r) >= max_threshold:
            print('Player entered zone')
            break


def get_gray(cam):
    image = cam.read()
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return gray_image


def get_binary_diff(image, next_image):
    diff_image = cv2.absdiff(image, next_image)
    blurred_image = cv2.GaussianBlur(diff_image, (5, 5), 0)
    blurred_image = cv2.bilateralFilter(blurred_image, 9, 75, 75)
    _, binary_diff_image = cv2.threshold(blurred_image, 60, 255, 0)
    return binary_diff_image


def get_diff(image, next_image):
    diff_image = cv2.absdiff(image, next_image)

    # filter noise from image distortions
    kernel = np.ones((3, 3), np.float32) / 9
    blurred_diff_image = cv2.filter2D(diff_image, -1, kernel)

    return blurred_diff_image


def get_corners(image):
    # number of features to track is a distinctive feature
    corners = cv2.goodFeaturesToTrack(image, 640, 0.0008, 0, mask=None, blockSize=3, useHarrisDetector=1, k=0.06)  # k=0.08
    print('corners:', len(corners))
    corners = corners[:, 0, :]
    corners = np.int0(corners)
    return corners


def filter_corners(corners):
    mean_corners = np.mean(corners, axis=0)
    mean_x, mean_y = mean_corners.ravel()

    corners_to_filter_out = []
    for idx, corner in enumerate(corners):
        corner_x, corner_y = corner.ravel()
        # filter noise to only get dart arrow
        if abs(mean_x - corner_x) > 180 or abs(mean_y - corner_y) > 120:
            corners_to_filter_out.append(idx)

    corners_new = np.delete(corners, [corners_to_filter_out], axis=0)  # delete corners to form new array
    return corners_new, (mean_x, mean_y)


def filter_corners_line(corners, rows, cols, dist_func):
    [vx, vy, x, y] = cv2.fitLine(corners, dist_func, 2.9 if dist_func == cv2.DIST_WELSCH else 0, 0.1, 0.1)  # 5.0 if dist_func == cv2.DIST_WELSCH else 0
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


def get_real_location(corners_final, mount):
    while True:
        if mount == "right":
            loc = np.argmax(corners_final[:, 0], axis=0)
        else:
            loc = np.argmin(corners_final[:, 0], axis=0)
        possible_loc = corners_final[loc]
        possible_loc_x = possible_loc.item(0)
        possible_loc_y = possible_loc.item(1)

        # check if dart location has neighbouring corners (if not -> continue)
        neighbours = 0
        corners_to_filter_out = []
        for idx, corner in enumerate(corners_final):
            if (corner == possible_loc).all():  # you're not your own neighbour
                corners_to_filter_out.append(idx)
                continue
            corner_x, corner_y = corner.ravel()
            distance = abs(possible_loc_x - corner_x) + abs(possible_loc_y - corner_y)
            if distance < 20:
                neighbours += 1

        if neighbours < 3:
            print("### used different location due to noise!")
            corners_final = np.delete(corners_final, [corners_to_filter_out], axis=0)  # delete corner w/o neighbours
            continue

        return possible_loc


def map_location_to_line(location_of_dart, line):
    point_on_line = closest_point(*line[0], *line[1], *location_of_dart)
    return point_on_line
