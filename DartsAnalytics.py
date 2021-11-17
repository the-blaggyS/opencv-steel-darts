import collections
import csv
import time
from datetime import datetime

import cv2
import numpy as np
from dateutil import parser

from Draw import draw_board


def read_log():
    darts_log = 'tmp/darts_log.csv'
    with open(darts_log, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows = [row for row in csv_reader]
    return rows


def today(darts):
    return [dart for dart in darts if parser.parse(dart['date']).day == datetime.now().day]


def last_game(darts):
    return [dart for dart in darts if dart['game_id'] == darts[-1]['game_id']]


def last_n(darts, n):
    return darts[-n:]


def generate_map():
    image = np.zeros((800, 800, 3), dtype='uint8')
    image = draw_board(image)
    return image


def draw_dart(image, x, y):
    cv2.circle(image, (int(float(x)), int(float(y))), 2, (0, 255, 0), 2, 8)
    cv2.circle(image, (int(float(x)), int(float(y))), 6, (0, 255, 0), 1, 8)


def count_scores(darts):
    print('\n\n### Scores Dict ###')
    counter = collections.Counter()
    for dart in darts:
        score = int(dart['base']) * int(dart['multiplier'])
        counter[score] += 1
    print(dict(sorted(counter.items(), key=lambda item: item[1], reverse=True)))
    print(len(darts))


def average(darts):
    print('\n\n### Average ###')
    sum = 0
    for dart in darts:
        sum += int(dart['base']) * int(dart['multiplier'])
    avg = sum / len(darts)
    print(avg)


def draw_darts_map(darts):
    darts_map = generate_map()
    for dart in darts:
        draw_dart(darts_map, dart['loc_x'], dart['loc_y'])
    cv2.imwrite('tmp/darts_map.jpg', darts_map)


def correctly_detected(darts):
    print('\n\n### Correctly Detected ###')
    counter = 0
    correct = 0
    for dart in darts:
        cd = dart['correctly_detected']
        if cd == 'True':
            correct += 1
            counter += 1
        elif cd == 'False':
            counter += 1
    print('Correct:', correct)
    print('Total:', counter)
    print('Percent:', correct/counter)


def calculate_playing_time(darts):
    print('\n\n### Playing Time ###')
    playing_time = 0
    for i in range(len(darts)-1):
        dart1 = darts[i]
        dart2 = darts[i+1]
        dt1 = parser.parse(dart1['date'])
        dt2 = parser.parse(dart2['date'])
        dt_diff = (dt2 - dt1).total_seconds()
        if dt_diff < 2*60:
            playing_time += dt_diff
        else:
            playing_time += 30

    ty_res = time.gmtime(playing_time)
    res = time.strftime('%H:%M:%S', ty_res)
    print(res)


def main(darts):
    count_scores(last_game(darts))
    average(last_game(darts))
    draw_darts_map(last_game(darts))
    correctly_detected(last_game(darts))
    correctly_detected(today(darts))
    correctly_detected(darts)
    calculate_playing_time(today(darts))
    calculate_playing_time(darts)
    count_scores(today([dart for dart in darts if int(dart['base']) in (5, 20, 1) and dart['correctly_detected'] == 'True']))
    # draw_darts_map(today([dart for dart in darts if int(dart['base']) in (5, 20, 1) and dart['correctly_detected'] == 'True']))


if __name__ == '__main__':
    darts_dict = read_log()
    main(darts_dict)
