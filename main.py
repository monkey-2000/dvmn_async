import asyncio
import curses
import random
import time
from curses_tools import *
from itertools import cycle as cycle
import os
from statistics import median as median
import logging

TIC_TIMEOUT = 0.1
ANIMATION_FOLDER = 'files'
SPACESHIP_VEL_MUL_ROW = 10
SPACESHIP_VEL_MUL_COL = 10


class EventLoopCommand:
    def __await__(self):
        return (yield self)


class CoroutineParams(EventLoopCommand):
    def __init__(self, new_pos=None):
        self.spaceship_pos = new_pos


def calc_dely(time):
    return int(time/TIC_TIMEOUT)


async def sleep(sleep_frames=1):
    for _ in range(sleep_frames):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*'):
    """star animation"""
    while True:

        rand_dely = random.randint(0, 1000) * 0.01
        await sleep(calc_dely(rand_dely))


        canvas.addstr(row, column, symbol, curses.A_DIM)

        await sleep(calc_dely(2))

        canvas.addstr(row, column, symbol)
        await sleep()

        await sleep(calc_dely(0.3))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep()

        await sleep(calc_dely(0.5))

        canvas.addstr(row, column, symbol)
        await sleep()

        await sleep(calc_dely(0.3))


async def fire(canvas,
               start_row,
               start_column,
               rows_speed=-0.3,
               columns_speed=0,
               symbols=['*', 'O', ' ']):
    """Display animation of gun shot. Direction and speed can be specified."""
    if type(symbols) is list:
        symbols = cycle(symbols)
    cur_s = next(symbols)

    start_row, start_column = is_pos_correct(cur_s, canvas,
                                             start_row, start_column)

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), cur_s)
    await sleep()

    canvas.addstr(round(row), round(column), next(symbols))
    await sleep()
    canvas.addstr(round(row), round(column), next(symbols))

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1
    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def get_star_pos(size):
    """get random star position"""
    pos = []
    for dim in size:
        pos.append(random.randint(1, dim - 1))
    return pos


def is_pos_correct(text, canvas, t_row, t_col, frame_borders={'row': 2, 'col': 2}):
    """text pos (moving obj) validation: text must be in a frame"""
    rows_in_symb, columns_in_symb = get_frame_size(text)
    max_row, max_col = canvas.getmaxyx()

    frame_size = {'row': max_row,
                  'col': max_col}

    mean_position = {'row': median([t_row, t_row + rows_in_symb]),
                     'col': median([t_col, t_col + columns_in_symb])}

    ans_pos = [t_row, t_col]
    for i, dimension in enumerate(mean_position.keys()):
        if mean_position[dimension] < frame_borders[dimension]:
            ans_pos[i] = frame_borders[dimension] + 1
        elif mean_position[dimension] > frame_size[dimension] - frame_borders[dimension]:
            ans_pos[i] = frame_size[dimension] - 2 * (frame_borders[dimension] + 1)

    return ans_pos


async def animate_spaceship(canvas, start_row, start_column, frames):
    """Display animation of spaceship"""
    for frame in cycle(frames):
        draw_frame(canvas, start_row, start_column, frame)

        for i in range(2):
            await CoroutineParams((start_row + 2, start_column + 2))

        draw_frame(canvas, start_row, start_column, frame, negative=True)


        row_direction, column_direction, key = read_controls(canvas)

        start_row += row_direction * SPACESHIP_VEL_MUL_ROW
        start_column += column_direction * SPACESHIP_VEL_MUL_COL

        start_row, start_column = is_pos_correct(frame, canvas,
                                                 start_row, start_column)


def load_frames(folder, key_word='sc'):
    """
    Load frames. Spaceship frames is default.
    :param folder: name of dir with frames in project dir
    :param key_word: pattern in searched frame filename
    :return: list of frames
    """
    path_to_dir = os.path.join(os.getcwd(), folder)
    frame_paths = [
                os.path.join(path_to_dir, frame_file_name) for frame_file_name in
                os.listdir(path_to_dir) if key_word in frame_file_name
                ]
    frames = []
    for path_to_frame in frame_paths:
        with open(path_to_frame, 'r') as f:
            frames.append(f.read())
    return frames


def get_sleep_command(command):
    """
    :param command: CoroutineParams()
    :return: seconds to sleep value or None
    """
    if command:
        seconds_to_sleep = command.sleep_seconds
        return seconds_to_sleep


def get_pos_from_command(command):
    if command:
        if command.spaceship_pos:
            row, column = command.spaceship_pos
            return row, column


def draw(canvas):
    """Draw frames"""
    curses.window.nodelay(canvas, True)
    win_size = curses.window.getmaxyx(canvas)

    coroutines = []
    # ------stars-------
    num_stars = random.randint(5, 6)

    for _ in range(num_stars):
        row, column = get_star_pos(win_size)
        star_style = random.choice('+*.:')
        coroutines.append(blink(canvas, row, column, star_style))

    # ------spacecraft and fire------
    spaceship_row, spaceship_column = win_size[0] / 2, win_size[1] / 2
    coroutines.append(fire(canvas, spaceship_row + 2, spaceship_column + 2))

    spaceship_frames = load_frames(ANIMATION_FOLDER)
    coroutines.append(animate_spaceship(canvas, spaceship_row, spaceship_column, spaceship_frames))

    # ------draw frames------
    while coroutines:

        for i, coroutine in enumerate(coroutines.copy()):
            try:
                command = coroutine.send(None)
                spaceship_position = get_pos_from_command(command)
                if spaceship_position:
                    spaceship_row, spaceship_column = spaceship_position

            except StopIteration:
                coroutines.remove(coroutine)
                coroutines.append(fire(canvas, spaceship_row, spaceship_column))
                continue

        curses.curs_set(False)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
