import csv
import os.path
import uuid
from datetime import datetime
from threading import Thread
from time import sleep
from tkinter import *

from Calibration import calibrate
from Classes import CalibrationData, GUIDef, Game, Player, Dart
from DartsRecognition import get_darts
from GameModes import *
from VideoCapture import VideoStream

cam_r = VideoStream(src=1)
calibration_data_r = CalibrationData()


def create_game():
    player_names = ['Lucas']
    players = [Player(name) for name in player_names]

    return Game(XX1(301, double_out=True), players)


game = create_game()


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.minsize(width=800, height=600)
        self.pack()


def start_game():
    global game
    game = create_game()

    gui.e1.configure(bg='light green')
    for score_field in score_fields:
        score_field.delete(0, 'end')
    for idx, player in enumerate(game.players):
        score_fields[idx].insert(10, player.score)
    for dart_entry in dart_entries:
        dart_entry.delete(0, 'end')
    gui.final_entry.delete(0, 'end')

    t = Thread(target=game_loop)
    t.start()


def game_loop():
    cam_r.start()
    sleep(1)  # time to init cam

    while not game.is_finished():
        game.get_current_player().turns.append([])
        current_turn = game.get_current_player().turns[-1]
        round_complete = False

        while not round_complete and game.is_running:
            dart = get_darts(cam_r, calibration_data_r, len(current_turn)+1)
            if dart is None:
                break
            else:
                current_turn.append(dart)
                update_entry_fields()
                round_complete = game.game_mode.is_turn_finished(game.get_current_player())

        update_final_score_field()

        # time to correct score detection
        # wait for player entering the zone
        _ = get_darts(cam_r, calibration_data_r, -1)

        update_player_score()
        log_dart()
        sleep(5)

        setup_next_round()
    cam_r.stop()


def update_entry_fields():
    current_turn = game.get_current_player().turns[-1]
    latest_dart = current_turn[-1]
    score = latest_dart.base * latest_dart.multiplier

    # update entry field
    dart_entries[len(current_turn)-1].insert(10, str(score))


def update_final_score_field():
    current_turn = game.get_current_player().turns[-1]
    score_sum = sum([dart.base * dart.multiplier for dart in current_turn])

    # check if turn was valid
    if not game.game_mode.is_turn_valid(game.get_current_player()):
        score_sum = 0

    # update final score field
    gui.final_entry.delete(0, 'end')
    gui.final_entry.insert(10, str(score_sum))


def update_player_score():
    current_turn = game.get_current_player().turns[-1]
    # check if turn was valid
    if game.game_mode.is_turn_valid(game.get_current_player()):
        # player score
        game.game_mode.update_player_score(game.get_current_player())
        update_player_score_field()


def update_player_score_field():
    score_field = score_fields[game.current_player]
    score_field.delete(0, 'end')
    score_field.insert(10, game.get_current_player().score)


def setup_next_round():
    # clear dart scores
    for dart_entry in dart_entries:
        dart_entry.delete(0, 'end')
    gui.final_entry.delete(0, 'end')

    game.next_player()

    # update ui
    score_field = score_fields[game.current_player]
    score_field.configure(bg='light green')
    score_field.configure(bg='black')


def log_dart():
    darts_log = 'tmp/darts_log.csv'

    def generate_dict(dart):
        return {
            'id': uuid.uuid4(),
            'date': datetime.now(),
            'game_id': game.id,
            'player_name': game.get_current_player().name,
            'base': dart.base,
            'multiplier': dart.multiplier,
            'loc_x': dart.location[0],
            'loc_y': dart.location[1],
            'correctly_detected': dart.correctly_detected
        }

    def write_csv(dart_dicts, header=False):
        field_names = ['id', 'date', 'game_id', 'player_name', 'base', 'multiplier', 'loc_x', 'loc_y',
                       'correctly_detected']
        with open(darts_log, 'a') as csv_file:
            csv_writer = csv.DictWriter(csv_file, field_names)
            if header:
                csv_writer.writeheader()
            csv_writer.writerows(dart_dicts)

    current_turn = game.get_current_player().turns[-1]
    write_csv([generate_dict(dart) for dart in current_turn], header=(not os.path.isfile(darts_log)))


# correct dart score with binding -> press return to change
def dart_correction(_):
    current_turn = game.get_current_player().turns[-1]
    for idx, entry in enumerate(dart_entries):

        if idx < len(current_turn):
            dart = current_turn[idx]
        else:
            dart = None

        try:
            base, multiplier = entry_to_dart(entry)
        except IndexError:
            continue

        if dart is None:
            dart = Dart(base, multiplier, -1, -1)
            current_turn.append(dart)
        elif base != dart.base or multiplier != dart.multiplier:
            dart.base = base
            dart.multiplier = multiplier
            dart.correctly_detected = False

    # update final score field
    score_sum = sum([dart.base * dart.multiplier for dart in current_turn])
    gui.final_entry.delete(0, 'end')
    gui.final_entry.insert(10, score_sum)


def entry_to_dart(entry):
    text = entry.get()
    multipliers = {'D': 2, 'T': 3}
    split = re.findall(r'\D+|\d+', text)
    if len(split) == 2:
        multiplier = multipliers[split[0]]
        base = int(split[1])
    else:
        multiplier = 1
        base = int(split[0])

    return base, multiplier


def stop_game():
    global game
    game = None
    cam_r.stop()


def calibration_gui():
    global calibration_data_r
    calibration_data_r = calibrate(cam_r, 'right')


root = Tk()
gui = GUIDef()

# Background Image
background = Canvas(root)
background.pack(expand=True, fill='both')

background_image = PhotoImage(file="Dartboard.gif")
background.create_image(0, 0, anchor='nw', image=background_image)

# Create Buttons
calibrate_btn = Button(None, text="Calibrate", fg="black", font="Helvetica 26 bold", command=calibration_gui)
background.create_window(20, 200, window=calibrate_btn, anchor='nw')

start_btn = Button(None, text="Game On!", fg="black", font="Helvetica 26 bold", command=start_game)
background.create_window(20, 20, window=start_btn, anchor='nw')

quit_btn = Button(None, text="QUIT", fg="black", font="Helvetica 26 bold", command=stop_game)
background.create_window(20, 300, window=quit_btn, anchor='nw')

# player labels and entry for total score
player1_label = Entry(root, fg='white', font="Helvetica 32 bold", width=7)
player1_label.bind("<Return>", lambda: (game.players[0].set_name(player1_label.get())))
background.create_window(250, 20, window=player1_label, anchor='nw')
player1_label.insert(10, game.players[0].name if len(game.players) >= 1 else "Player 1")

player2_label = Entry(root, fg='white', font="Helvetica 32 bold", width=7)
player2_label.bind("<Return>", lambda: (game.players[1].set_name(player2_label.get())))
background.create_window(400, 20, window=player2_label, anchor='nw')
player2_label.insert(10, game.players[1].name if len(game.players) >= 2 else "Player 2")

gui.e1 = Entry(root, fg='white', font="Helvetica 44 bold", width=4)
background.create_window(250, 80, window=gui.e1, anchor='nw')
gui.e2 = Entry(root, fg='white', font="Helvetica 44 bold", width=4)
background.create_window(400, 80, window=gui.e2, anchor='nw')
gui.e1.insert(10, "501")
gui.e2.insert(10, "501")

# dart throw scores
dart1label = Label(None, text="1.: ", font="Helvetica 20 bold")
background.create_window(300, 160, window=dart1label, anchor='nw')

gui.dart1entry = Entry(root, font="Helvetica 20 bold", width=3)
gui.dart1entry.bind("<Return>", dart_correction)
background.create_window(350, 160, window=gui.dart1entry, anchor='nw')

dart2label = Label(None, text="2.: ", font="Helvetica 20 bold")
background.create_window(300, 210, window=dart2label, anchor='nw')

gui.dart2entry = Entry(root, font="Helvetica 20 bold", width=3)
gui.dart2entry.bind("<Return>", dart_correction)
background.create_window(350, 210, window=gui.dart2entry, anchor='nw')

dart3label = Label(None, text="3.: ", font="Helvetica 20 bold")
background.create_window(300, 260, window=dart3label, anchor='nw')

gui.dart3entry = Entry(root, font="Helvetica 20 bold", width=3)
gui.dart3entry.bind("<Return>", dart_correction)
background.create_window(350, 260, window=gui.dart3entry, anchor='nw')

final_label = Label(None, text=" = ", font="Helvetica 20 bold")
background.create_window(300, 310, window=final_label, anchor='nw')

gui.final_entry = Entry(root, font="Helvetica 20 bold", width=3)
background.create_window(350, 310, window=gui.final_entry, anchor='nw')

dart_entries = [gui.dart1entry, gui.dart2entry, gui.dart3entry]
score_fields = [gui.e1, gui.e2]

app = Application(master=root)
app.mainloop()
root.destroy()
