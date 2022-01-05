import time
from typing import Optional

import cv2
import numpy as np
import numpy.typing as npt

from server.classes import CalibrationData, CancellationToken, Dart, Frame, Image, Line, Point, VectorLine
from server.darts_mapping import get_dart_region, get_transformed_location
from server.math_functions import dist
from server.video_capture import VideoStream

DEBUG = True
dbg_next_image: Image
dbg_diff_image: Image


def get_dart(cam: VideoStream, calibration_data: CalibrationData, token: CancellationToken) -> Optional[Dart]:
    global dbg_next_image
    global dbg_diff_image

    min_threshold = 100
    max_threshold = 100_000

    max_corners = 2000

    image = get_gray(cam)

    while not token.is_cancelled:
        time.sleep(0.1)

        # check if dart hit the board
        next_image = get_gray(cam)
        binary_diff = get_binary_diff(image, next_image)
        num_changed_pixels = cv2.countNonZero(binary_diff)

        # num of changed pixels indicates dart
        if min_threshold < num_changed_pixels < max_threshold:
            # wait for camera vibrations
            time.sleep(0.2)

            # filter noise
            next_image = get_gray(cam)
            diff_image = get_blurred_diff(image, next_image)
            dbg_next_image = cv2.cvtColor(next_image, cv2.COLOR_GRAY2RGB)

            # get corners
            corners = get_corners(diff_image)

            # dart detected?
            if corners.size < 40 or corners.size == max_corners * 2:
                print("Dart not detected (pre-processing)")
                print('corners:', len(corners))
                continue

            # filter corners
            # close_corners_r = filter_corners_of_flight(corners_r)
            close_corners = filter_close_corners(corners)
            if close_corners.size == 0:
                print('Dart not detected (in-processing)')
                continue
            corners_on_line = filter_corners_on_line(close_corners, calibration_data.image_shape)

            # dart detected?
            if corners_on_line.size < 30:
                print("Dart not detected (post-processing)")
                print('corners:', len(corners_on_line))
                if DEBUG:
                    # copy debug images
                    dbg_diff_image = diff_image.copy()
                    # draw all different corners
                    dbg_draw_corners(corners, close_corners, corners_on_line)
                    # write debug images
                    cv2.imwrite(f'tmp/dbg_dart.jpg', dbg_diff_image)
                    cv2.imwrite(f'tmp/dbg_corners.jpg', dbg_next_image)
                continue

            # check if it was really a dart
            _, binary_diff = cv2.threshold(diff_image, 60, 255, 0)
            if cv2.countNonZero(binary_diff) > max_threshold:
                print('Player entered zone', cv2.countNonZero(binary_diff))
                break

            # get final darts location
            corners_with_neighbours = filter_corners_with_neighbours(corners_on_line)

            location_of_dart = get_real_location(corners_with_neighbours)
            transformed_location = get_transformed_location(location_of_dart, calibration_data)
            dart_info = get_dart_region(transformed_location, calibration_data)
            dart_info.location = transformed_location

            print("Dart detected")
            print(f'{dart_info.multiplier}x{dart_info.base}')

            if DEBUG:
                # copy debug images
                dbg_diff_image = diff_image.copy()
                # draw all different corners
                dbg_draw_corners(corners, close_corners, corners_on_line)
                # draw darts location
                cv2.circle(dbg_next_image, location_of_dart.astype(int), 1, color=(255, 0, 255), thickness=1)
                cv2.circle(dbg_next_image, location_of_dart.astype(int), 20, color=(255, 0, 255), thickness=1)
                # mark dart on test image
                cv2.circle(dbg_diff_image, location_of_dart.astype(int), 10, color=(255, 255, 255), thickness=1, lineType=8)
                # write debug images
                cv2.imwrite(f'tmp/dbg_dart.jpg', dbg_diff_image)
                cv2.imwrite(f'tmp/dbg_corners.jpg', dbg_next_image)

            return dart_info

        # missed dart
        elif num_changed_pixels <= min_threshold:
            if num_changed_pixels > 0:
                print(num_changed_pixels)
            image = next_image
            continue

        # if player enters zone - break loop
        elif num_changed_pixels >= max_threshold:
            print('Player entered zone')
            print(num_changed_pixels)
            break


def get_gray(cam: VideoStream) -> Image:
    image = cam.read()
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return gray_image


def get_binary_diff(image: Image, next_image: Image) -> Image:
    diff_image = cv2.absdiff(image, next_image)
    blurred_image = cv2.GaussianBlur(diff_image, (5, 5), 0)
    blurred_image = cv2.bilateralFilter(blurred_image, 9, 75, 75)
    _, binary_diff_image = cv2.threshold(blurred_image, 60, 255, 0)
    return binary_diff_image


def get_diff(image: Image, next_image: Image) -> Image:
    diff_image = cv2.absdiff(image, next_image)
    return diff_image


def get_blurred_diff(image: Image, next_image: Image) -> Image:
    # create diff image
    diff_image = cv2.absdiff(image, next_image)
    # # filter noise from image distortions
    m = n = 5
    kernel = np.ones((m, n), np.float32) / (m * n)
    blurred_diff_image = cv2.filter2D(diff_image, -1, kernel)
    return blurred_diff_image


def get_corners(image: Image) -> npt.NDArray[Point]:
    corners = cv2.goodFeaturesToTrack(image, 2000, 0.0008, 1, mask=None, blockSize=3, useHarrisDetector=1, k=0.06)
    corners = corners[:, 0, :]
    return corners


def line_frame_intersection(line: VectorLine, frame: Frame) -> Line:

    def seg_intersect(line1: VectorLine, line2: VectorLine) -> Point:
        diff = line1.support_vector - line2.support_vector
        line1_directional_vector_inv = line1.directional_vector.perp()
        denom = np.dot(line1_directional_vector_inv, line2.directional_vector)
        num = np.dot(line1_directional_vector_inv, diff)
        return (num / denom.astype(float)) * line2.directional_vector + line2.support_vector

    rect_lines = [
        # x0, y0, vx, vy
        VectorLine(Point(0, 0), Point(1, 0)),
        VectorLine(Point(0, frame.height - 1), Point(1, 0)),
        VectorLine(Point(0, 0), Point(0, 1)),
        VectorLine(Point(frame.width - 1, 0), Point(0, 1))
    ]

    points = []

    for rect_line in rect_lines:
        point = Point.cast(seg_intersect(rect_line, line).astype(int))
        if rect_line.directional_vector.x and 0 <= point.x < frame.width \
                or rect_line.directional_vector.y and 0 <= point.y < frame.height:
            points.append(point)

    if len(points) > 2:
        print(line)
        print(points)
        points = points[:2]

    return Line(*points)


def filter_close_corners(corners: npt.NDArray[Point]) -> npt.NDArray[Point]:
    diff_x = 150
    mean_corners = np.mean(corners, axis=0)
    mean_x, _ = mean_corners.ravel()

    left = Point(mean_x - diff_x, 0)
    right = Point(mean_x + diff_x, 1080)

    cv2.rectangle(dbg_next_image, left.astype(int), right.astype(int), color=(255, 0, 0))

    corners_to_filter_out = []
    for idx, corner in enumerate(map(Point.cast, corners)):
        # filter noise to only get dart arrow
        if not mean_x - diff_x < corner.x < mean_x + diff_x:
            corners_to_filter_out.append(idx)

    corners_new = np.delete(corners, [corners_to_filter_out], axis=0)
    return corners_new


def filter_corners_on_line(corners: npt.NDArray[Point], frame: Frame) -> npt.NDArray[Point]:
    line = cv2.fitLine(corners, cv2.DIST_WELSCH, 0, 0.1, 0.1).ravel()
    line = VectorLine(Point.cast(line[2:]), Point.cast(line[:2]))
    line = line_frame_intersection(line, frame)

    corners_to_filter_out = []
    for idx, corner in enumerate(map(Point.cast, corners)):
        # check distance to fitted line, only draw corners within certain range
        distance = dist(line, corner)
        if distance > 20:
            corners_to_filter_out.append(idx)

    cv2.line(dbg_next_image, line.p1, line.p2, color=(127, 0, 127))  # debug

    corners_new = np.delete(corners, [corners_to_filter_out], axis=0)  # delete corners to form new array
    return corners_new


def filter_corners_with_neighbours(corners: npt.NDArray[Point]) -> npt.NDArray[Point]:
    loc_idx = np.argmin(corners[:, 1], axis=0)
    loc = corners[loc_idx]

    neighbours = 0
    for idx, corner in enumerate(corners):
        if corner[1] - loc[1] < 40:
            neighbours += 1

    if neighbours < 3 and len(corners) > 1:
        print('skipped corner without neighbours')
        return filter_corners_with_neighbours(np.delete(corners, [loc_idx], axis=0))
    else:
        return corners


def get_real_location(corners: npt.NDArray[Point]) -> Point:
    idx = np.argmin(corners[:, 1], axis=0)
    return corners[idx]


def dbg_draw_corners(corners: npt.NDArray[Point], close_corners: npt.NDArray[Point], corners_on_line: npt.NDArray[Point]) -> None:
    for corner in corners[(corners[:, None] != close_corners).any(-1).all(1)]:
        cv2.circle(dbg_next_image, corner.astype(int), radius=1, color=(255, 0, 0), thickness=1)  # blue
    for corner in close_corners:
        cv2.circle(dbg_next_image, corner.astype(int), radius=1, color=(0, 255, 0), thickness=1)  # green
    for corner in corners_on_line:
        cv2.circle(dbg_next_image, corner.astype(int), radius=1, color=(0, 0, 255), thickness=1)  # red
