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


class Logger:
    """logging"""

    def __init__(self, file_name='logs'):
        self.logger = self._logger(file_name)

    def _logger(self, file_name):
        logger = logging.getLogger(file_name)
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(f'{file_name}.log')
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
        return logger


LOG = Logger()


class EventLoopCommand:
    def __await__(self):
        return (yield self)


class CoroutineParams(EventLoopCommand):
    def __init__(self, seconds, new_pos=None):
        self.sleep_seconds = seconds
        self.spaceship_pos = new_pos


def calc_dely(time):
    return int(time/TIC_TIMEOUT)


async def blink(canvas, row, column, symbol='*'):
    """star animation"""
    while True:

        rand_dely = random.randint(0, 1000) * 0.01
        for _ in range(calc_dely(rand_dely)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)

        for _ in range(calc_dely(2)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for _ in range(calc_dely(0.3)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        for _ in range(calc_dely(0.5)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for _ in range(calc_dely(0.3)):
            await asyncio.sleep(0)


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
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), next(symbols))
    await asyncio.sleep(0)
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
            await CoroutineParams(0, (start_row + 2, start_column + 2))

        draw_frame(canvas, start_row, start_column, frame, negative=True)


        row_direction, column_direction, key = read_controls(canvas)

        start_row += row_direction * SPACESHIP_VEL_MUL_ROW
        start_column += column_direction * SPACESHIP_VEL_MUL_COL

        LOG.logger.debug(f'start_column,{start_column}, start_row {start_row}')

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
            # LOG.logger.debug(f'spaceship_pos{row}, {column}')


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
    sleeping_coroutines = [[0, coroutine] for coroutine in coroutines]
    while sleeping_coroutines:

        for timeout, coroutine in sleeping_coroutines:
            LOG.logger.debug(f'timeout,{timeout}, coroutine {coroutine}')

        sleeping_coroutines = [[timeout - TIC_TIMEOUT, coroutine]
                               for timeout, coroutine in sleeping_coroutines]

        # divide coroutine on an active and sleeping
        active_coroutines = [[timeout, coroutine] for timeout, coroutine in sleeping_coroutines
                             if timeout <= 0]
        sleeping_coroutines = [[timeout, coroutine] for timeout, coroutine in sleeping_coroutines
                               if timeout > 0]

        for _, coroutine in active_coroutines:
            try:
                command = coroutine.send(None)
                seconds_to_sleep = get_sleep_command(command)
                spaceship_position = get_pos_from_command(command)
                if spaceship_position:
                    spaceship_row, spaceship_column = spaceship_position
                # LOG.logger.debug(f'coroutine,{coroutine}')
            except StopIteration:
                if seconds_to_sleep:
                    sleeping_coroutines.append([seconds_to_sleep, fire(canvas, spaceship_row,
                                                                       spaceship_column)])
                else:
                    sleeping_coroutines.append([0, fire(canvas, spaceship_row,
                                                        spaceship_column)])
                continue  # выкидываем истощившуюся корутины

            if seconds_to_sleep:
                sleeping_coroutines.append([seconds_to_sleep, coroutine])
            else:
                sleeping_coroutines.append([0, coroutine])

        curses.curs_set(False)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
