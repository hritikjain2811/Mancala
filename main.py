import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex, platform
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.modalview import ModalView
from kivy.storage.dictstore import DictStore
from os.path import join, dirname
import random
import copy
import math
import sys


# Returns path containing content - either locally or in pyinstaller tmp file
def resourcePath():
    if hasattr(sys, '_MEIPASS'):
        return join(sys._MEIPASS)
    return join(dirname(__file__))


class Board(Widget):
    pass


class Field(ButtonBehavior, Widget):
    seeds = ListProperty([])
    is_ambar = BooleanProperty(False)
    color = ListProperty(get_color_from_hex('#26a69a80'))
    bg_color = ListProperty(get_color_from_hex('#26a69a00'))

    def __init__(self, **kwargs):
        super(Field, self).__init__(**kwargs)


class Seed(Widget):
    colors = [
        '#e53935',
        '#1e88e5',
        '#43a047',
        '#fdd835',
        '#ab47bc',
        '#8d6e63'
    ]
    color = StringProperty(colors[0])


class Btn(ButtonBehavior, Widget):
    text = StringProperty('btn')
    color = ListProperty(get_color_from_hex('#26a69a40'))
    text_color = ListProperty(get_color_from_hex('#26a69a'))

    def __init__(self, **kwargs):
        super(Btn, self).__init__(**kwargs)


class SoundBtn(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(SoundBtn, self).__init__(**kwargs)


class RotateBtn(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(RotateBtn, self).__init__(**kwargs)


class ScrollableLabel(ScrollView):
    text = StringProperty('Long text ...')


class ViewInfoBig(Widget):
    text = StringProperty('Long text ...')


class ViewInfo(Widget):
    text = StringProperty('...')


class ViewChoice(Widget):
    text = StringProperty('...')


class SelectBox(ButtonBehavior, Widget):
    text = StringProperty('mode')
    select = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SelectBox, self).__init__(**kwargs)


class ViewMode(Widget):
    text = StringProperty('...')


class MancalaApp(App):
    Window.clearcolor = get_color_from_hex('#000000')
    if platform in ['win', 'linux', 'mac']:
        icon = 'data/icon.png'
        title = 'Mancala'
        Window.size = (800, 480)
        Window.left = 100
        Window.top = 100

    board = ObjectProperty()
    fields = ListProperty([])
    seeds = ListProperty([])
    seed_size = ListProperty([64, 64])
    game_seeds = NumericProperty(48)  # 72
    temp_game_seeds = NumericProperty(48)
    player_AI = BooleanProperty(True)
    temp_player_AI = BooleanProperty(True)
    player_turn = NumericProperty(0)  # 1
    first_step = ListProperty([True, True])
    panel = ListProperty([])
    hand = ListProperty([])
    block = BooleanProperty(True)  # anti-multitouch ;)
    rotate_btn = ListProperty([])
    max_ambars = ListProperty([])
    temp_max_ambars = ListProperty([])
    ambars_AI = ListProperty([])
    board_row = NumericProperty(0)
    board_col = NumericProperty(0)

    store = ObjectProperty()
    save_matrix = []
    save_gameover = False
    save_player_turn = 0

    view_exit = None
    view_gameover = None
    view_new = None
    view_info = None
    view_rotate = None

    is_sound = BooleanProperty(True)
    sound_click = None
    sound_popup = None

    def on_start(self):
        self.board = self.root.ids.board
        self.seed_size = [(self.board.width - 9 * self.board.width / 80) / 8 / 4] * 2
        self.fields = [[self.root.ids.field00, self.root.ids.field01, self.root.ids.field02, self.root.ids.field03,
                        self.root.ids.field04, self.root.ids.field05, self.root.ids.field06],
                       [self.root.ids.field10, self.root.ids.field11, self.root.ids.field12, self.root.ids.field13,
                        self.root.ids.field14, self.root.ids.field15, self.root.ids.field16]]

        self.panel = [self.root.ids.panel1, self.root.ids.panel2]
        self.rotate_btn = [self.root.ids.rotate_btn1, self.root.ids.rotate_btn2]

        # sounds
        self.sound_click = SoundLoader.load('click.wav')
        self.sound_popup = SoundLoader.load('popup.wav')

        # exit dialog
        self.view_exit = ModalView(size_hint=(None, None), size=[self.board.height * 2, self.board.height * 1.25],
                                   auto_dismiss=False, background='data/background.png')
        self.view_exit.add_widget(ViewChoice(text='Exit the game?'))
        self.view_exit.children[0].ids.yes_btn.bind(on_release=self.stop)

        # game over dialog
        self.view_gameover = ModalView(size_hint=(None, None), size=[self.board.height * 2, self.board.height * 1.25],
                                       auto_dismiss=False, background='data/background.png')
        self.view_gameover.add_widget(ViewInfo(text='* GAME OVER *'))

        # new game dialog
        self.view_new = ModalView(size_hint=(None, None), size=[self.board.height * 2, self.board.height * 1.25],
                                  auto_dismiss=False, background='data/background.png')
        self.view_new.add_widget(ViewMode(text='Start new game?'))
        self.view_new.children[0].ids.yes_btn.bind(on_release=self.new_game)

        # rotate dialog
        self.view_rotate = ModalView(size_hint=(None, None), size=[self.board.height * 2, self.board.height * 1.25],
                                     auto_dismiss=False, background='data/background.png')
        self.view_rotate.add_widget(ViewChoice(text='Rotate the board?'))
        self.view_rotate.children[0].ids.yes_btn.bind(on_release=self.rotate_board)

        # info dialog
        self.view_info = ModalView(size_hint=(None, None), size=[self.board.height * 2, self.board.height * 1.25],
                                   auto_dismiss=False, background='data/background.png')
        self.view_info.add_widget(ViewInfoBig())

        # bind's
        Window.bind(on_key_down=self.on_key_down)
        if platform in ['win', 'linux', 'mac']: Window.bind(on_request_close=self.on_request_close)
        self.board.bind(size=Clock.schedule_once(self.resize, 0.150))

        # Android screen rotation ;)
        if platform == 'android':
            from jnius import autoclass
            ActivityInfo = autoclass('android.content.pm.ActivityInfo')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)

        # load data settings
        if platform in ['win', 'linux', 'mac']:  # desktop
            self.store = DictStore(join(self.user_data_dir, 'store.dat'))
        else:  # if platform in ['android', 'ios']
            self.store = DictStore('store.dat')  # android API 26+ без запроса разрешений доступа

        if self.store.exists('save_matrix'):
            self.game_seeds = self.store.get('game_seeds')['value']
            self.player_AI = self.store.get('player_AI')['value']
            self.is_sound = self.store.get('is_sound')['value']
            self.first_step = [True if self.store.get('first_step')['value'][0] == 1 else False,
                               True if self.store.get('first_step')['value'][1] == 1 else False]
            self.save_matrix = self.store.get('save_matrix')['value']
            self.save_gameover = self.store.get('save_gameover')['value']
            self.save_player_turn = self.store.get('save_player_turn')['value']

            if not self.save_gameover:
                self.load_game()
            else:
                self.start_game()

        else:
            self.start_game()

    def sound_move_play(self):
        sound_move = SoundLoader.load('move.wav')
        if sound_move: sound_move.play()

    def seed_pos(self, row, col):
        offset = self.board.width / 80
        x = random.randint(math.ceil(self.fields[row][col].x + offset),
                           math.ceil(
                               self.fields[row][col].x + self.fields[row][col].width - offset - self.seed_size[0]))
        y = random.randint(math.ceil(self.fields[row][col].y + offset),
                           math.ceil(
                               self.fields[row][col].y + self.fields[row][col].height - offset - self.seed_size[0]))

        return (x, y)

    def load_game(self):
        self.player_turn = self.save_player_turn
        self.seeds = [Seed(size_hint=(None, None), size=self.seed_size) for s in range(self.game_seeds)]

        for c in range(int(self.game_seeds / 12)):
            for s in range(12):
                self.seeds[12 * c + s].color = self.seeds[12 * c + s].colors[c]

        # save matrix
        seeds_index = [e for e in range(self.game_seeds)]
        moving = False

        for matrix_row in range(2):
            for matrix_col in range(7):
                for matrix_seeds in range(self.save_matrix[matrix_row][matrix_col]):
                    random_choice = random.choice(seeds_index)
                    random_index = seeds_index.pop(seeds_index.index(random_choice))
                    self.fields[matrix_row][matrix_col].seeds.append(self.seeds[random_index])
                    self.board.add_widget(self.seeds[random_index])
                    rand_pos = self.seed_pos(matrix_row, matrix_col)
                    anim = Animation(pos=rand_pos, duration=0.25, transition='linear')
                    anim.start(self.seeds[random_index])

                    if not moving:
                        moving = True
                        anim.bind(on_complete=self.after_start_game)

    def start_game(self):
        self.save_gameover = False
        self.first_step = [True, True]
        self.player_turn = 0 if random.randint(1, 100) <= 50 else 1
        self.seeds = [Seed(size_hint=(None, None), size=self.seed_size) for s in range(self.game_seeds)]

        for c in range(int(self.game_seeds / 12)):
            for s in range(12):
                self.seeds[12 * c + s].color = self.seeds[12 * c + s].colors[c]

        moving = False

        for i in range(int(self.game_seeds / 12)):
            for j in range(6):
                self.fields[0][j].seeds.append(self.seeds[j + 12 * i])
                self.fields[1][j + 1].seeds.append(self.seeds[j + 6 + 12 * i])
                self.board.add_widget(self.seeds[j + 12 * i])
                self.board.add_widget(self.seeds[j + 6 + 12 * i])

                rand_pos1 = self.seed_pos(0, j)
                rand_pos2 = self.seed_pos(1, j + 1)
                anim1 = Animation(pos=rand_pos1, duration=0.25, transition='linear')
                anim2 = Animation(pos=rand_pos2, duration=0.25, transition='linear')

                anim1.start(self.seeds[j + 12 * i])
                anim2.start(self.seeds[j + 6 + 12 * i])

                if not moving:
                    moving = True
                    anim2.bind(on_complete=self.after_start_game)

    def after_start_game(self, *args):
        self.turn(self.player_turn)

    def turn(self, player):
        # save
        self.save_matrix = [[len(self.fields[i][j].seeds) for j in range(7)] for i in range(2)]
        self.save_player_turn = player

        self.panel[player].text = 'Player ' + str(player + 1) + ' turn!'
        self.panel[1 if player == 0 else 0].text = 'Player ' + str(2 if player == 0 else 1)
        self.block = False
        if not self.player_AI or (player == 0 and self.player_AI):
            for field in self.fields[player]:
                field.disabled = False if not field.is_ambar and len(field.seeds) > 0 else True
            self.rotate_btn[player].disabled = False if ((self.first_step == [False, True] and player == 1) or (
                        self.first_step == [True, False] and player == 0)) and self.game_seeds == 72 else True
        elif player == 1 and self.player_AI:
            self.balda()

    def balda(self):
        select_fields = []
        for i in range(7):
            if not self.fields[1][i].is_ambar and len(self.fields[1][i].seeds) > 0:
                select_fields.append(i)

        is_rotate_disabled = False if self.first_step == [False, True] and self.game_seeds == 72 and len(
            self.fields[0][6].seeds) == 2 else True

        if not is_rotate_disabled and len(self.fields[0][6].seeds) > 1 and random.randint(1, 100) <= 50:
            self.rotate_btn[1].disabled = False
            self.rotate_btn[1].trigger_action(duration=0.25)

        elif self.first_step == [True, True] or random.randint(1,
                                                               100) <= 10:  # game first move random or 10% chance move random ;)
            rand_index = random.choice(select_fields)
            self.fields[1][rand_index].disabled = False
            self.fields[1][rand_index].trigger_action(duration=0.25)

        else:
            matrix = [[len(self.fields[i][j].seeds) for j in range(7)] for i in range(2)]
            self.minmaxAI(matrix)

    def minmaxAI(self, get_matrix):
        matrix = copy.deepcopy(get_matrix)  # copy list
        self.max_ambars = []
        self.temp_max_ambars = []
        self.ambars_AI = []
        self.moveAI(matrix)

        max_ambars_AI = []
        for e in self.ambars_AI:
            max_ambars_AI.append(max(e))

        sub_AI = []
        for s in max_ambars_AI:
            sub_AI.append(s - matrix[1][0])

        max_array = []
        for elem in self.max_ambars:
            max_array.append(max(elem))

        sub_Human = []
        for h in max_array:
            sub_Human.append(h - matrix[0][6])

        sub_AI_Human = []
        for a in range(len(sub_AI)):
            sub_AI_Human.append(sub_AI[a] - sub_Human[a])

        select_fields = []
        for i in range(6):
            if matrix[1][i + 1] > 0:
                select_fields.append(i + 1)

        max_AI = max(sub_AI_Human)

        if max_AI >= 0:  # MAXUP STRATEGY
            index_max = []
            for j in range(len(sub_AI_Human)):
                if sub_AI_Human[j] == max_AI:
                    index_max.append(j)
            rand_index = random.choice(index_max)

        else:  # MINMAX STRATEGY
            min_value = min(max_array)
            index_min = []
            for i in range(len(max_array)):
                if max_array[i] == min_value:
                    index_min.append(i)
            rand_index = random.choice(index_min)

        select_index = select_fields[rand_index]
        self.fields[1][select_index].disabled = False
        self.fields[1][select_index].trigger_action(duration=0.25)

    def moveAI(self, get_matrix, repeat=False):
        matrix = copy.deepcopy(get_matrix)  # copy list
        select_fields = []

        for i in range(6):
            if matrix[1][i + 1] > 0:
                select_fields.append(i + 1)

        for index in select_fields:
            result_bonus, result_matrix = self.move_analyze(matrix, 1, index)
            if result_bonus:
                if not repeat:
                    self.max_ambars.append([])
                    self.ambars_AI.append([])
                self.moveAI(result_matrix, True)
            else:  # moveHuman and search maxAmbar
                self.temp_max_ambars = []
                self.moveHuman(result_matrix)
                if repeat:
                    self.max_ambars[len(self.max_ambars) - 1] += self.temp_max_ambars
                    self.ambars_AI[len(self.ambars_AI) - 1] += [result_matrix[1][0]]
                if not repeat:
                    self.max_ambars.append(self.temp_max_ambars)
                    self.ambars_AI.append([result_matrix[1][0]])

    def moveHuman(self, get_matrix):
        matrix = copy.deepcopy(get_matrix)  # copy list
        select_fields = []
        maxAmbar = 0

        for i in range(6):
            if matrix[0][i] > 0:
                select_fields.append(i)

        for index in select_fields:
            result_bonus, result_matrix = self.move_analyze(matrix, 0, index)
            if result_bonus:
                self.moveHuman(result_matrix)
            elif result_matrix[0][6] >= maxAmbar:
                maxAmbar = result_matrix[0][6]

        self.temp_max_ambars.append(maxAmbar)

    def move_analyze(self, get_matrix, player, index):
        matrix = copy.deepcopy(get_matrix)  # copy list
        temp_hand = matrix[player][index]
        matrix[player][index] = 0

        row = player
        col = (index + 1) if player == 0 else (index - 1)

        while temp_hand > 0:
            temp_hand -= 1
            matrix[row][col] += 1

            # continue move
            if temp_hand > 0:
                # move self side
                if not ((row == 0 and col == 6) or (row == 1 and col == 0)) and row == player:
                    col = (col + 1) if player == 0 else (col - 1)

                # self ambar
                elif ((row == 0 and col == 6) or (row == 1 and col == 0)) and row == player:
                    row = (row + 1) if player == 0 else (row - 1)

                # move alien side
                elif not ((row == 0 and col + 1 == 6) or (row == 1 and col - 1 == 0)) and row != player:
                    col = (col - 1) if player == 0 else (col + 1)

                # alien ambar (before 1 step)
                elif ((row == 0 and col + 1 == 6) or (row == 1 and col - 1 == 0)) and row != player:
                    row = (row - 1) if player == 0 else (row + 1)
                    col = (col - 1) if player == 0 else (col + 1)

            # end move
            else:
                # get alien seeds
                if matrix[row][col] == 1 and row == player and not (
                        (row == 0 and col == 6) or (row == 1 and col == 0)) and \
                        matrix[(row + 1) if player == 0 else (row - 1)][(col + 1) if player == 0 else (col - 1)] > 0:
                    temp_hand = matrix[(row + 1) if player == 0 else (row - 1)][(col + 1) if player == 0 else (col - 1)]
                    matrix[(row + 1) if player == 0 else (row - 1)][(col + 1) if player == 0 else (col - 1)] = 0
                    temp_hand += 1
                    matrix[row][col] -= 1
                    # to ambar
                    matrix[0 if player == 0 else 1][6 if player == 0 else 0] += temp_hand
                    temp_hand = 0

                # game over
                elif (matrix[0][0] + matrix[0][1] + matrix[0][2] + matrix[0][3] + matrix[0][4] + matrix[0][5] == 0) or (
                        matrix[1][1] + matrix[1][2] + matrix[1][3] + matrix[1][4] + matrix[1][5] + matrix[1][6] == 0):
                    return (False, matrix)

                # bonus move
                elif ((row == 0 and col == 6) or (row == 1 and col == 0)):
                    return (True, matrix)

                # next player
                else:
                    return (False, matrix)

        return (False, matrix)

    def move(self, player, index):
        if not self.block:
            self.block = True
            self.first_step[player] = False
            self.panel[player].text = 'Player ' + str(player + 1) + ' move ...'

            for field in self.fields[player]:
                field.disabled = True

            self.rotate_btn[0].disabled = True
            self.rotate_btn[1].disabled = True

            self.hand = self.fields[player][index].seeds
            self.fields[player][index].seeds = []

            self.board_row = player
            self.board_col = (index + 1) if player == 0 else (index - 1)

            # Animation move
            self.anim_move()

    def anim_move(self):
        moving = False

        for seed in self.hand:
            rand_pos = self.seed_pos(self.board_row, self.board_col)
            anim = Animation(pos=rand_pos, duration=0.25, transition='linear')
            anim.start(seed)

            if not moving:
                moving = True
                anim.bind(on_complete=self.after_move)
                if self.is_sound: self.sound_move_play()

    def after_move(self, *args):
        if self.hand:
            temp_seed = self.hand.pop()
            self.fields[self.board_row][self.board_col].seeds.append(temp_seed)

            # continue move
            if len(self.hand) > 0:
                # move self side
                if not self.fields[self.board_row][self.board_col].is_ambar and self.board_row == self.player_turn:
                    self.board_col = (self.board_col + 1) if self.player_turn == 0 else (self.board_col - 1)

                # self ambar
                elif self.fields[self.board_row][self.board_col].is_ambar and self.board_row == self.player_turn:
                    self.board_row = (self.board_row + 1) if self.player_turn == 0 else (self.board_row - 1)

                # move alien side
                elif not self.fields[self.board_row][(self.board_col - 1) if self.player_turn == 0 else (
                        self.board_col + 1)].is_ambar and self.board_row != self.player_turn:
                    self.board_col = (self.board_col - 1) if self.player_turn == 0 else (self.board_col + 1)

                # alien ambar (before 1 step)
                elif self.fields[self.board_row][(self.board_col - 1) if self.player_turn == 0 else (
                        self.board_col + 1)].is_ambar and self.board_row != self.player_turn:
                    self.board_row = (self.board_row - 1) if self.player_turn == 0 else (self.board_row + 1)
                    self.board_col = (self.board_col - 1) if self.player_turn == 0 else (self.board_col + 1)

                # Animation move
                self.anim_move()

            # end move
            else:
                # get alien seeds
                if len(self.fields[self.board_row][
                           self.board_col].seeds) == 1 and self.board_row == self.player_turn and not \
                self.fields[self.board_row][self.board_col].is_ambar and len(
                        self.fields[(self.board_row + 1) if self.player_turn == 0 else (self.board_row - 1)][
                            (self.board_col + 1) if self.player_turn == 0 else (self.board_col - 1)].seeds) > 0:
                    self.hand = self.fields[(self.board_row + 1) if self.player_turn == 0 else (self.board_row - 1)][
                        (self.board_col + 1) if self.player_turn == 0 else (self.board_col - 1)].seeds
                    self.fields[(self.board_row + 1) if self.player_turn == 0 else (self.board_row - 1)][
                        (self.board_col + 1) if self.player_turn == 0 else (self.board_col - 1)].seeds = []
                    self.hand.append(self.fields[self.board_row][self.board_col].seeds[0])
                    self.fields[self.board_row][self.board_col].seeds = []
                    # to ambar
                    self.anim_to_ambar()

                # game over
                elif self.is_game_over():
                    self.game_over()

                # bonus move
                elif self.fields[self.board_row][self.board_col].is_ambar:
                    self.turn(self.player_turn)

                # next player
                else:
                    self.next_player()

    def anim_to_ambar(self):
        moving = False

        for seed in self.hand:
            rand_pos = self.seed_pos(self.player_turn, (6 if self.player_turn == 0 else 0))
            anim = Animation(pos=rand_pos, duration=0.25, transition='linear')
            anim.start(seed)

            if not moving:
                moving = True
                anim.bind(on_complete=self.after_ambar)
                if self.is_sound: self.sound_move_play()

    def after_ambar(self, *args):
        if self.hand:
            for seed in self.hand:
                self.fields[self.player_turn][6 if self.player_turn == 0 else 0].seeds.append(seed)
            self.hand = []

            if self.is_game_over():  # game over
                self.game_over()
            else:  # next player
                self.next_player()

    def next_player(self):
        self.player_turn = 1 if self.player_turn == 0 else 0
        self.turn(self.player_turn)

    def is_game_over(self):
        counter = [0, 0]

        for i in range(2):
            for field in self.fields[i]:
                counter[i] += len(field.seeds) if not field.is_ambar else 0

        if counter[0] == 0 or counter[1] == 0:
            return True
        else:
            return False

    def game_over(self):
        self.panel[0].text = 'Player 1'
        self.panel[1].text = 'Player 2'

        counter = [0, 0]

        for i in range(2):
            for field in self.fields[i]:
                counter[i] += len(field.seeds) if not field.is_ambar else 0

        if counter[0] == 0 and counter[1] == 0:
            # clear fields
            Clock.schedule_once(self.after_game_over, 0.25)
        else:
            # animation to ambar
            player = counter.index(max(counter[0], counter[1]))

            for field in self.fields[player]:
                if not field.is_ambar:
                    for seed in field.seeds:
                        self.hand.append(seed)
                    field.seeds = []

            self.anim_game_over(player)

    def anim_game_over(self, player):
        self.player_turn = player  # for select ambar in after_game_over()
        moving = False

        for seed in self.hand:
            rand_pos = self.seed_pos(player, (6 if player == 0 else 0))
            anim = Animation(pos=rand_pos, duration=0.25, transition='linear')
            anim.start(seed)

            if not moving:
                moving = True
                anim.bind(on_complete=self.after_game_over)
                if self.is_sound: self.sound_move_play()

    def after_game_over(self, *args):
        for seed in self.hand:
            self.fields[self.player_turn][6 if self.player_turn == 0 else 0].seeds.append(seed)
        self.hand = []

        sum1 = len(self.fields[0][6].seeds)
        sum2 = len(self.fields[1][0].seeds)

        winner = 'GAME DRAW!' if sum1 == sum2 else ('Player 1 WIN!' if sum1 > sum2 else 'Player 2 WIN!')

        self.panel[0].text = 'GAME DRAW' if sum1 == sum2 else ('Player 1 WIN!' if sum1 > sum2 else 'GAME OVER')
        self.panel[1].text = 'GAME OVER' if sum1 == sum2 else ('Player 2 WIN!' if sum2 > sum1 else 'GAME OVER')

        self.save_gameover = True
        self.view_gameover.children[0].text = winner + '\n\n' + str(sum1) + ' : ' + str(sum2)
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        self.view_gameover.open()

    def new_game(self, *args):
        self.game_seeds = self.temp_game_seeds
        self.player_AI = self.temp_player_AI

        for i in range(2):
            for field in self.fields[i]:
                field.seeds = []

        self.hand = []

        len_seeds = len(self.seeds)
        for i in range(len_seeds - 1, -1, -1):
            self.board.remove_widget(self.seeds[i])
            del self.seeds[i]

        self.panel[0].text = 'Player 1'
        self.panel[1].text = 'Player 2'

        self.start_game()

    def rotate_board(self, *args):
        if not self.block:
            self.block = True
            self.first_step[self.player_turn] = False
            self.panel[self.player_turn].text = 'The board rotates ...'

            for field in self.fields[self.player_turn]:
                field.disabled = True

            self.rotate_btn[0].disabled = True
            self.rotate_btn[1].disabled = True

            a = 6
            for b in range(7):
                temp1 = self.fields[0][b].seeds
                self.fields[0][b].seeds = []
                temp2 = self.fields[1][b + a].seeds
                self.fields[1][b + a].seeds = []
                self.fields[0][b].seeds = temp2
                self.fields[1][b + a].seeds = temp1
                temp1 = []
                temp2 = []
                a -= 2

            moving = False

            for i in range(2):
                for j, field in enumerate(self.fields[i]):
                    for seed in field.seeds:
                        rand_pos = self.seed_pos(i, j)
                        anim = Animation(pos=rand_pos, duration=0.5, transition='linear')
                        anim.start(seed)

                        if not moving:
                            moving = True
                            anim.bind(on_complete=self.after_rotate)

    def after_rotate(self, *args):
        self.next_player()

    def on_key_down(self, window, key, *args):
        if key in [27, 4]:  # ESC and BACK_BUTTON
            if self.is_sound and self.sound_popup: self.sound_popup.play()
            self.view_exit.open()
            return True

    def on_request_close(self, *args):
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        self.view_exit.open()
        return True

    def save_data(self):
        self.store.put('game_seeds', value=self.game_seeds)
        self.store.put('player_AI', value=self.player_AI)
        self.store.put('is_sound', value=self.is_sound)
        self.store.put('first_step', value=[0 if not self.first_step[0] else 1, 0 if not self.first_step[1] else 1])
        self.store.put('save_matrix', value=self.save_matrix)
        self.store.put('save_gameover', value=self.save_gameover)
        self.store.put('save_player_turn', value=self.save_player_turn)

    def resize(self, *args):
        self.seed_size = [(self.board.width - 9 * self.board.width / 80) / 8 / 4] * 2

        for i in range(2):
            for j, field in enumerate(self.fields[i]):
                for seed in field.seeds:
                    rand_pos = self.seed_pos(i, j)
                    anim = Animation(pos=rand_pos, duration=0.25, transition='linear')
                    anim.start(seed)

        # dialog's
        self.view_exit.size = [self.board.height * 2, self.board.height * 1.25]
        self.view_gameover.size = [self.board.height * 2, self.board.height * 1.25]
        self.view_new.size = [self.board.height * 2, self.board.height * 1.25]
        self.view_info.size = [self.board.height * 2, self.board.height * 1.25]
        self.view_rotate.size = [self.board.height * 2, self.board.height * 1.25]

    def on_pause(self):
        self.save_data()
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.save_data()
        sys.exit(0)  # for Android and other OS


if __name__ == '__main__':
    if platform in ['win', 'linux', 'mac']:  # desktop
        kivy.resources.resource_add_path(resourcePath())
    MancalaApp().run()