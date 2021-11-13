import csv
import os.path
import uuid
from datetime import datetime
from threading import Thread
from time import sleep
from tkinter import *

from Calibration import calibrate
from Classes import CalibrationData, GUIDef, Game, Player, DartDef
from DartsRecognition import get_darts
from VideoCapture import VideoStream

cam_r = VideoStream(src=1)
calibration_data_r = CalibrationData()

game = Game()
darts = []


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.minsize(width=800, height=600)
        self.pack()


def start_game():
    global game
    game = Game()

    player1 = Player('Lucas')
    player1_label.delete(0, 'end')
    player1_label.insert(10, player1.name)
    game.players.append(player1)

    # player2 = Player('Player2')
    # player2_label.delete(0, 'end')
    # player2_label.insert(10, player2.name)
    # game.players.append(player2)

    for player in game.players:
        player.score = game.start_score

    gui.e1.configure(bg='light green')

    gui.e1.delete(0, 'end')
    gui.e2.delete(0, 'end')
    gui.e1.insert(10, game.players[0].score)
    if len(game.players) == 2:
        gui.e2.insert(10, game.players[1].score)
    gui.final_entry.delete(0, 'end')
    gui.dart1entry.delete(0, 'end')
    gui.dart2entry.delete(0, 'end')
    gui.dart3entry.delete(0, 'end')

    t = Thread(target=game_loop)
    t.start()


def game_loop():
    global darts
    cam_r.start()

    while game.is_running:
        darts = []
        round_complete = False

        while not round_complete and game.is_running:
            dart = get_darts(cam_r, calibration_data_r, len(darts)+1)
            if dart is None:
                break
            else:
                darts.append(dart)
                round_complete = handle_event()

        update_final_score_field()

        # time to correct score detection
        # wait for player entering the zone
        _ = get_darts(cam_r, calibration_data_r, -1)

        update_player_score()
        log_dart()
        sleep(5)

        setup_next_round()
    cam_r.stop()


def handle_event():
    latest_dart = darts[-1]
    score = latest_dart.base * latest_dart.multiplier

    # update entry fields
    if len(darts) == 1:
        gui.dart1entry.insert(10, str(score))
    elif len(darts) == 2:
        gui.dart2entry.insert(10, str(score))
    elif len(darts) == 3:
        gui.dart3entry.insert(10, str(score))

    score_sum = sum([dart.base * dart.multiplier for dart in darts])
    new_score = game.get_current_player().score - score_sum
    return len(darts) == 3 or new_score < 2  # round finished after three darts or when score < 2


def update_final_score_field():
    score_sum = sum([dart.base * dart.multiplier for dart in darts])
    new_score = game.get_current_player().score - score_sum

    # update final score field
    if new_score > 1 or new_score == 0 and darts[-1].multiplier == 2:
        gui.final_entry.delete(0, 'end')
        gui.final_entry.insert(10, score_sum)
    else:
        gui.final_entry.delete(0, 'end')
        gui.final_entry.insert(10, str(0))


def update_player_score():
    score_sum = sum([dart.base * dart.multiplier for dart in darts])
    new_score = game.get_current_player().score - score_sum

    if new_score > 1 or new_score == 0 and darts[-1].multiplier == 2:
        score_sum = sum([dart.base * dart.multiplier for dart in darts])
        new_score = game.get_current_player().score - score_sum

        # player score
        game.get_current_player().score = new_score

        update_player_score_field()

        if game.get_current_player().score == 0:
            game.is_running = False


def update_player_score_field():
    if game.current_player == 0:
        gui.e1.delete(0, 'end')
        gui.e1.insert(10, game.get_current_player().score)
    elif game.current_player == 1:
        gui.e2.delete(0, 'end')
        gui.e2.insert(10, game.get_current_player().score)


def setup_next_round():
    # clear dart scores
    gui.final_entry.delete(0, 'end')
    gui.dart1entry.delete(0, 'end')
    gui.dart2entry.delete(0, 'end')
    gui.dart3entry.delete(0, 'end')

    game.next_player()

    # update ui
    if game.current_player == 0:
        gui.e1.configure(bg='light green')
        gui.e2.configure(bg='black')
    elif game.current_player == 1:
        gui.e2.configure(bg='light green')
        gui.e1.configure(bg='black')


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

    write_csv([generate_dict(dart) for dart in darts], header=(not os.path.isfile(darts_log)))


# correct dart score with binding -> press return to change
def dart_correction(_):
    for idx, entry in enumerate([gui.dart1entry, gui.dart2entry, gui.dart3entry]):
        if idx >= len(darts):
            darts.append(DartDef())
        dart = darts[idx]

        multipliers = {'D': 2, 'T': 3}
        input = entry.get()
        split = re.findall(r'\D+|\d+', input)
        if len(split) == 2:
            multiplier = multipliers[split[0]]
            base = int(split[1])
        else:
            multiplier = 1
            base = int(split[0])

        corrected_score = multiplier * int(base)
        original_score = dart.base * dart.multiplier
        if corrected_score != original_score:
            dart.base = corrected_score
            dart.multiplier = 1
            dart.correctly_detected = False

    # update final score field
    score_sum = sum([dart.base * dart.multiplier for dart in darts])
    gui.final_entry.delete(0, 'end')
    gui.final_entry.insert(10, score_sum)


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
player1_label.insert(10, "Player 1")

player2_label = Entry(root, fg='white', font="Helvetica 32 bold", width=7)
player2_label.bind("<Return>", lambda: (game.players[1].set_name(player2_label.get())))
background.create_window(400, 20, window=player2_label, anchor='nw')
player2_label.insert(10, "Player 2")

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

app = Application(master=root)
app.mainloop()
root.destroy()
