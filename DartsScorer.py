from threading import Thread
from tkinter import *
from time import sleep

from Calibration import calibrate
from Classes import CalibrationData, GUIDef, Game, Player
from DartsRecognition import get_darts
from VideoCapture import VideoStream

cam_r = VideoStream(src=1).start()
calibration_data_r = CalibrationData()

game = Game()


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.minsize(width=800, height=600)
        self.pack()


# def detected_dart_callback(breaker, dart_base, dart_multiplier):
#
#     score = dart_base * dart_multiplier
#     game.get_current_player().score -= score
#
#     # update entry fields
#     if breaker == 1:
#         GUI.dart1entry.insert(10, str(score))
#     elif breaker == 2:
#         GUI.dart2entry.insert(10, str(score))
#     elif breaker == 3:
#         GUI.dart3entry.insert(10, str(score))
#
#     # update player score field
#     if game.current_player == 0:
#         GUI.e1.delete(0, 'end')
#         GUI.e1.insert(10, game.get_current_player().score)
#     elif game.current_player == 1:
#         GUI.e2.delete(0, 'end')
#         GUI.e2.insert(10, game.get_current_player().score)
#
#     # calculate final score
#     dart_entries = [GUI.dart1entry, GUI.dart2entry, GUI.dart3entry]
#     scores_sum = 0
#
#     for dart_entry in dart_entries:
#         score_str = dart_entry.get()
#         try:
#             score_int = int(score_str)
#         except ValueError:
#             score_int = 0
#         scores_sum += score_int
#
#     # update final score field
#     if game.get_current_player().score <= 1 or \
#        game.get_current_player().score == 0 and not dart_multiplier == 2:
#         GUI.finalentry.delete(0, 'end')
#         GUI.finalentry.insert(10, str(0))
#         game.get_current_player().score += scores_sum
#     else:
#         GUI.finalentry.delete(0, 'end')
#         GUI.finalentry.insert(10, scores_sum)


def game_on():
    player1 = Player('Lucas')
    game.players.append(player1)

    # player2 = Player('Player2')
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

    # t = Thread(target=get_darts, args=(cam_r, calibration_data_r, detected_dart_callback))
    t = Thread(target=game_loop)
    t.start()


def game_loop():
    while True:
        darts = []
        for dart in get_darts(cam_r, calibration_data_r):

            darts.append(dart)
            handle_event(darts)

        sleep(5)
        setup_next_round()


def handle_event(darts):
    latest_dart = darts[-1]
    score = latest_dart.base * latest_dart.multiplier

    # update player score
    game.get_current_player().score -= score

    # update entry fields
    if len(darts) == 1:
        gui.dart1entry.insert(10, str(score))
    elif len(darts) == 2:
        gui.dart2entry.insert(10, str(score))
    elif len(darts) == 3:
        gui.dart3entry.insert(10, str(score))

    # update player score field
    if game.current_player == 0:
        gui.e1.delete(0, 'end')
        gui.e1.insert(10, game.get_current_player().score)
    elif game.current_player == 1:
        gui.e2.delete(0, 'end')
        gui.e2.insert(10, game.get_current_player().score)

    # calculate final score
    score_sum = sum([dart.base * dart.multiplier for dart in darts])

    # update final score field
    if game.get_current_player().score > 1 or \
            game.get_current_player().score == 0 and latest_dart.multiplier == 2:
        gui.final_entry.delete(0, 'end')
        gui.final_entry.insert(10, score_sum)
    else:
        gui.final_entry.delete(0, 'end')
        gui.final_entry.insert(10, str(0))
        game.get_current_player().score += score_sum


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
        gui.e2.configure(bg='white')
    elif game.current_player == 1:
        gui.e2.configure(bg='light green')
        gui.e1.configure(bg='white')


def calibration_gui():
    global calibration_data_r
    calibration_data_r = calibrate(cam_r, 'right')


# correct dart score with binding -> press return to change
def dart_correction(event):
    # check if empty, on error write 0 to value of dart
    try:
        dart1 = int(eval(gui.dart1entry.get()))
    except ValueError:
        dart1 = 0
    try:
        dart2 = int(eval(gui.dart2entry.get()))
    except ValueError:
        dart2 = 0
    try:
        dart3 = int(eval(gui.dart3entry.get()))
    except ValueError:
        dart3 = 0

    new_final_score = dart1 + dart2 + dart3
    new_player_score = game.get_current_player().score - new_final_score
    game.get_current_player().score = new_player_score

    gui.final_entry.delete(0, 'end')
    gui.final_entry.insert(10, new_final_score)

    # check which player
    if game.current_player == 0:
        gui.e1.delete(0, 'end')
        gui.e1.insert(10, new_player_score)
    elif game.current_player == 1:
        gui.e2.delete(0, 'end')
        gui.e2.insert(10, new_player_score)


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

start_btn = Button(None, text="Game On!", fg="black", font="Helvetica 26 bold", command=game_on)
background.create_window(20, 20, window=start_btn, anchor='nw')

quit_btn = Button(None, text="QUIT", fg="black", font="Helvetica 26 bold", command=root.quit)
background.create_window(20, 300, window=quit_btn, anchor='nw')

# player labels and entry for total score
player1_label = Entry(root, font="Helvetica 32 bold", width=7)
player1_label.bind("<Return>", lambda: (game.players[0].set_name(player1_label.get())))
background.create_window(250, 20, window=player1_label, anchor='nw')
player1_label.insert(10, "Player 1")

player2_label = Entry(root, font="Helvetica 32 bold", width=7)
player2_label.bind("<Return>", lambda: (game.players[1].set_name(player2_label.get())))
background.create_window(400, 20, window=player2_label, anchor='nw')
player2_label.insert(10, "Player 2")

gui.e1 = Entry(root, font="Helvetica 44 bold", width=4)
background.create_window(250, 80, window=gui.e1, anchor='nw')
gui.e2 = Entry(root, font="Helvetica 44 bold", width=4)
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
