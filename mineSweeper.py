import random
import logging
import sys
import time
logging.basicConfig(level=logging.INFO)
import pygame
from pygame.locals import *


game_cfg = {
    "width": 40,
    "height": 25,
    "num_mine": 200
}


show_cfg = {
    "width": 1200,
    "height": 750,
    "topleft": (50, 50),
    "block_size": 25,
    "line_width": 1,
    "font": "arial",
    "font_size": 16,
    }

color_cfg = {
    "psudo": (150, 150, 150),
    " ": (127, 127, 127),
    "X": (127, 127, 127),
    # "X": (255, 255, 255),
    "F": (255, 0, 0),
    "W": (255, 255, 0),
    "?": (40, 200, 0),
    "!": (40, 200, 0),
    "B": (200, 200, 200),
    "number": (0, 0, 255),
    "1": (0, 0, 255),
    "2": (0, 255, 0),
    "3": (255, 0, 0),
    "4": (0, 255, 255),
    "5": (0, 127, 127),
    "6": (0, 0, 255),
    "7": (0, 0, 255),
    "8": (0, 0, 255),
}


class MineModelBoard():
    '''
    All possible status:
         : unrevealed block
        X: hidden mine
        F: flagged mine
        W: wrong flagged mine
        ?: mine marked as ?
        !: none-mine marked as ?
        B: blank
        1-8: Number of mines around
    Possible action:
        Reset: /
        left-click: one_block_sweep
        right-click: flag/?/unmark
        both-click:
            for a digit, if not all its neighbour mines are flagged, show the
            neighbor of it; else, sweep all its unflagged neighbors, which might
            cause fail
    Show:
        board
        time
        mine-remains

    TODO:
        how about change block to block class?
    '''
    def __init__(self, width, height, num_mine):
        self.h = height
        self.w = width
        self.num_mine = num_mine
        self._reset()

    def _reset(self):
        self.board = [[" "] * self.w for i in range(self.h)]
        mines = random.sample(list(range(self.h * self.w)), self.num_mine)
        for idx in mines:
            x, y = idx // self.h, idx % self.h
            self._set(x, y, "X")
        self.curr_mine = self.num_mine
        self.curr_eval = 0

    ### inner function ###
    # in getter and setter, x and y are swiped for the real x-axis and y-axis
    # for all other application, simply use normal order of x, y and call
    # getter and setter
    def _get(self, x, y):
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            logging.debug("get %s %s %s" % (x, y, self.board[y][x]))
            return self.board[y][x]
        return None

    def _set(self, x, y, mark):
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            self.board[y][x] = mark
            logging.debug("set %s %s %s" % (x, y, mark))
            return True
        return False

    def _get_neighbors(self, x, y):
        res = []
        for i, j in [(x-1, y-1), (x-1, y), (x-1, y+1),
                     (x, y-1), (x, y+1),
                     (x+1, y-1), (x+1, y), (x+1, y+1)]:
            if self._get(i, j):
                res.append((i, j, self._get(i, j)))
        return res

    def _get_num_mines(self, x, y):
        neighbor = self._get_neighbors(x, y)
        return sum([1 if block[2] in ["X", "F", "?"] else 0
                    for block in neighbor])
        # block: tuple(x, y, mark)
        # "X", "F", "?" are mines

    def _get_num_flagged_blocks(self, x, y):
        neighbor = self._get_neighbors(x, y)
        return sum([1 if block[2] in ["F", "W", "?", "!"] else 0
                    for block in neighbor])
        # block: tuple(x, y, mark)
        # "F", "W", "?", "!" are marked blocks

    ### user interact ###
    def left_click(self, x, y):
        if self._get(x, y) is None:
            logging.info("click out of board")
            return
        if self._get(x, y) == "X":
            return True
        if self._get(x, y) != " ":
            logging.info("try to sweep a marked block.")
            return
        is_lose = self.one_block_sweep(x, y)
        if is_lose:
            return True

    def right_click(self, x, y):
        # TODO: deal with key error
        mark = self._get(x, y)
        if mark == "F":
            self.curr_mine += 1
        dct = {" ": "W",
               "X": "F",
               "W": "!",
               "F": "?",
               "!": " ",
               "?": "X"}
        self._set(x, y, dct.get(mark, mark))
        if self._get(x, y) == "F":
            self.curr_mine -= 1

    def both_click(self, x, y):
        # also count ? mark as flagged
        # TODO: for wrong flag, mark wrong flagged blocks (which is the
        # corresponded wrong flagged block?)
        if self._get(x, y) not in "12345678":
            logging.info("both click only for number blocks")
            return
        if self._get_num_flagged_blocks(x, y) >= int(self._get(x, y)):
            for new_x, new_y, mark in self._get_neighbors(x, y):
                if mark not in ["F", "W", "?", "!"]:
                    is_lose = self.one_block_sweep(new_x, new_y)
                    if is_lose:
                        return True
        else:
            for new_x, new_y, mark in self._get_neighbors(x, y):
                if mark in [" ", "X"]:
                    self.psudo_click(new_x, new_y)

    def psudo_click(self, x, y):
        # TODO: do this in V part
        logging.info("not enough flagged mines around (%s, %s)" % (x, y))
        pass

    def win(self):
        print(self.output())
        print("win")
        pass

    def loss(self):
        print(self.output())
        print("loss")
        pass

    def reset(self):
        pass

    def output(self):
        def hidden(row):
            res = []
            dct = {"X": " ", "W": "F", "!": "?"}
            for c in row:
                res.append(dct.get(c, c))
            return res
        col_separator = '\n' + '-' * (2 * self.w + 1) + '\n'
        s = col_separator.join(['|'.join([''] + hidden(row) + [''])
                                for row in self.board])
        return s

    ### logic ###
    def one_block_sweep(self, x, y):
        if self._get(x, y) == "X":
            return True
        if self._get(x, y) != " ":
            return
        if self._get_num_mines(x, y) == 0:
            self._set(x, y, "B")
            self.curr_eval += 1
            for new_x, new_y, _ in self._get_neighbors(x, y):
                is_lose = self.one_block_sweep(new_x, new_y)
                if is_lose:
                    return True
        else:
            self._set(x, y, str(self._get_num_mines(x, y)))
            self.curr_eval += 1

    ### run ###
    def operation_onestep(self, op, x, y):
        if op == "left_click":
            is_lose = self.left_click(x, y)
            if is_lose:
                return "lose"
            if self.curr_eval + self.num_mine == self.h * self.w:
                return "win"
        elif op == "right_click":
            self.right_click(x, y)
        elif op == "both_click":
            is_lose = self.both_click(x, y)
            if is_lose:
                return "lose"
            if self.curr_eval + self.num_mine == self.h * self.w:
                return "win"
        else:
            logging.debug("illegal op")
        return ""

    def run_input(self):
        def parse_input(s):
            s = s.split()
            if len(s) not in [2, 3]:
                logging.info("unsupported op")
                return
            if len(s) == 2:
                op = "left_click"
                x, y = s
            else:
                op, x, y = s
            op_dict = {"left_click": ["l", "lc", "left"],
                       "right_click": ["r", "rc", "right"],
                       "both_click": ["b", "bc", "both"]}
            for key, val in op_dict.items():
                if key == op:
                    break
                if op in val:
                    op = key
                    break
            print(op, x, y)
            x, y = int(x) - 1, int(y) - 1
            return op, x, y

        while True:
            print(self.output())
            s = input()
            if s == "q":
                return
            if s == "r":
                # TODO: reset
                return
            op, x, y = parse_input(s)
            res = self.operation_onestep(op, x, y)
            if res == "win":
                self.win()
                break
            elif res == "lose":
                self.loss()
                break
            elif res == "":
                pass
            else:
                logging.debug("unexpected step result")


class MineControlBoard(MineModelBoard):
    def _axis_2_grid(self, x, y):
        x = (x - show_cfg["topleft"][0]) // show_cfg["block_size"]
        y = (y - show_cfg["topleft"][1]) // show_cfg["block_size"]
        return x, y

    def click(self, x, y, button):
        # get board pos from camvass pos
        x, y = self._axis_2_grid(x, y)
        if button == 1:
            self.left_click(y, x)
        elif button == 3:
            self.right_click(y, x)
        else:
            pass  # TODO


class MineViewBoard(MineControlBoard):
    def _draw_block(self, x, y, mark=None):
        if mark is not None:
            c = mark
        else:
            c = self._get(x, y)
            if c is None:
                return
        top = show_cfg["topleft"][0] + x * show_cfg["block_size"]
        left = show_cfg["topleft"][1] + y * show_cfg["block_size"]
        fill_size = show_cfg["block_size"] - show_cfg["line_width"]
        if c in "12345678":
            number = c
            c = "B"
        else:
            number = None
        color = color_cfg.get(c, (0, 0, 0))

        rect = Rect(left, top, fill_size, fill_size)
        pygame.draw.rect(self.screen, color, rect)
        if number:
            text_surface = my_font.render(number, True, color_cfg.get(number, color_cfg["number"]))
            self.screen.blit(text_surface, (left + 6, top + 6))  # TODO: calc 4

    def _draw_board(self):
        for x in range(self.w):
            for y in range(self.h):
                self._draw_block(x, y)

    def create_screen(self, width, height, full_screen=0):
        self.screen = pygame.display.set_mode((width, height), full_screen, 32)

    def screen_run(self, fps=60):
        while True:
            time.sleep(1.0 / fps)
            self._draw_board()
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    self.click(event.pos[0],
                               event.pos[1],
                               event.button)
            


if __name__ == "__main__":
    pygame.init()
    b = MineViewBoard(game_cfg["height"], game_cfg["width"], game_cfg["num_mine"])
    my_font = pygame.font.SysFont(show_cfg["font"], show_cfg["font_size"])
    b.create_screen(show_cfg["width"], show_cfg["height"])
    b.screen_run()
