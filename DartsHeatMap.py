import collections
import csv

import cv2
import numpy as np

from Draw import draw_board


def read_log():
    darts_log = 'darts_log.csv'
    with open(darts_log, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows = [row for row in csv_reader]
    return rows


def generate_map():
    image = np.zeros((800, 800, 3), dtype='uint8')
    image = draw_board(image)
    return image


def draw_dart(image, x, y):
    cv2.circle(image, (int(float(x)), int(float(y))), 2, (0, 255, 0), 2, 8)
    cv2.circle(image, (int(float(x)), int(float(y))), 6, (0, 255, 0), 1, 8)


def count_scores(darts):
    counter = collections.Counter()
    for dart in darts:
        score = int(dart['base']) * int(dart['multiplier'])
        counter[score] += 1
    print(dict(sorted(counter.items(), key=lambda item: item[1], reverse=True)))
    print(len(darts))


def average(darts):
    sum = 0
    for dart in darts:
        sum += int(dart['base']) * int(dart['multiplier'])
    avg = sum / len(darts)
    print(avg)

    
if __name__ == '__main__':
    darts_dict = read_log()
    darts_map = generate_map()
    for dart in darts_dict:
        draw_dart(darts_map, dart['loc_x'], dart['loc_y'])
    cv2.imwrite('DartsHeatMap.jpg', darts_map)
    count_scores(darts_dict)
    average(darts_dict)
