import collections
import csv
from datetime import datetime, timedelta
from itertools import groupby

import cv2
import math
import numpy as np
from dateutil import parser
from matplotlib import pyplot as plt
from pyheatmap.heatmap import HeatMap

from server.classes import CalibrationData
from server.draw import draw_board


def read_log():
    darts_log = 'tmp/darts_log.csv'
    with open(darts_log, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows = [row for row in csv_reader]
    return rows


def today(darts):
    return [dart for dart in darts if parser.parse(dart['date']).date() == datetime.today().date()]


def last_game(darts):
    return [dart for dart in darts if dart['game_id'] == darts[-1]['game_id']]


def last_n(darts, n):
    return darts[-n:]


def new_setup(darts):
    return [dart for dart in darts if parser.parse(dart['date']) >= parser.parse('2021-12-24')]


def heatmap_per_day(darts):
    correctly_detected_darts = [dart for dart in darts if dart['correctly_detected'] == 'True']
    darts_per_day_iterator = groupby(correctly_detected_darts, key=lambda dart: parser.parse(dart['date']).date())
    darts_per_day = {date: list(darts_of_day) for date, darts_of_day in darts_per_day_iterator}

    x_dates = []
    y_diff = []
    y_avg = []

    for date, darts in darts_per_day.items():
        generate_heatmap(list(darts), name=str(date))
        diff = sum([math.sqrt((400 - float(dart['loc_x']))**2 + (196 - float(dart['loc_y']))**2) for dart in darts]) / len(darts)
        x_dates.append(date)
        y_diff.append(diff)
        print(date, diff)
        avg = sum([int(dart['multiplier']) * int(dart['base']) for dart in darts]) / len(darts) * 3
        y_avg.append(avg)

    plt.plot(x_dates, y_diff)
    plt.show()
    plt.plot(x_dates, y_avg)
    plt.show()

    # darts_per_game_iterator = groupby(darts, key=itemgetter('game_id'))
    # darts_per_game = {game: list(darts_of_game) for game, darts_of_game in darts_per_game_iterator}
    #
    # x_games = []
    # y_avg = []
    #
    # for game, darts in darts_per_game.items():
    #     if len(darts) < 15: continue
    #     avg = sum([int(dart['multiplier']) * int(dart['base']) for dart in darts]) / len(darts) * 3
    #     date = parser.parse(darts[0]['date']).date()
    #     x_games.append(date.strftime('%d.%m'))
    #     y_avg.append(avg)
    #
    # plt.plot(x_games, y_avg, marker='o', linestyle='None')
    # plt.show()


def generate_map():
    image = np.zeros((800, 800, 3), dtype='uint8')
    draw_board(image, CalibrationData(image.shape))
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
    my_sum = 0
    for dart in darts:
        my_sum += int(dart['base']) * int(dart['multiplier'])
    avg = my_sum / len(darts)
    print(avg * 3)


def draw_darts_map(darts):
    darts_map = generate_map()
    for dart in darts:
        draw_dart(darts_map, dart['loc_x'], dart['loc_y'])
    cv2.imwrite('../tmp/darts_map.jpg', darts_map)


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
    total_playing_time = 0
    first_dart_of_game = darts[0]
    for idx, dart in enumerate(darts):
        if dart['game_id'] != first_dart_of_game['game_id']:
            # Calculate playing time of game
            last_dart_of_game = darts[idx-1]
            start_time_of_game = parser.parse(first_dart_of_game['date'])
            end_time_of_game = parser.parse(last_dart_of_game['date'])
            duration_of_game = (end_time_of_game - start_time_of_game).total_seconds()
            total_playing_time += duration_of_game
            # Start new game
            first_dart_of_game = dart
    print(timedelta(seconds=total_playing_time))
    print(timedelta(seconds=(parser.parse(darts[-1]['date'])-parser.parse(darts[0]['date'])).total_seconds()).days)
    print(timedelta(seconds=total_playing_time) / max(timedelta(seconds=(parser.parse(darts[-1]['date'])-parser.parse(darts[0]['date'])).total_seconds()).days, 1))


def generate_heatmap(darts, name=''):
    data = [(int(float(dart['loc_x'])), int(float(dart['loc_y']))) for dart in darts]
    print(len(data))

    darts_map = generate_map()
    cv2.imwrite('../tmp/base.jpg', darts_map)

    heatmap = HeatMap(data, base='tmp/base.jpg', width=800, height=800)
    heatmap.clickmap(save_as=f'tmp/hit{name}.png')
    heatmap.heatmap(save_as=f'tmp/heat{name}.png')


def main(darts):
    darts = new_setup(darts)

    count_scores(last_game(darts))
    count_scores(today([dart for dart in darts if dart['multiplier'] == '3']))
    average(last_game(darts))
    average(today(darts))
    draw_darts_map(last_game(darts))
    correctly_detected(last_game(darts))
    correctly_detected(today(darts))
    correctly_detected(darts)
    calculate_playing_time(today(darts))
    calculate_playing_time(darts)
    count_scores(today([dart for dart in darts if int(dart['base']) in (5, 20, 1) and dart['correctly_detected'] == 'True']))
    # draw_darts_map(today([dart for dart in darts if int(dart['base']) in (5, 20, 1) and dart['correctly_detected'] == 'True']))
    generate_heatmap(last_game([dart for dart in darts if dart['correctly_detected'] == 'True']))  # if int(dart['base']) != 0 and
    draw_darts_map(darts)
    heatmap_per_day(read_log())


if __name__ == '__main__':
    darts_dict = read_log()
    main(darts_dict)
