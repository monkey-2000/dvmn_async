import asyncio
import curses
import random
import re
import time
from curses_tools import read_controls, draw_frame, get_frame_size
from itertools import cycle as cycle
import os
from statistics import mean as mean

TIC_TIMEOUT = 0.1
ANIMATION_FOLDER = 'files'
SPACESHIP_VEL_MUL_ROW = 10
SPACESHIP_VEL_MUL_COL = 10


class NoFrameFile(Exception):
    pass

class EventLoopCommand:
    def __await__(self):
        return (yield self)


class CoroutineParams(EventLoopCommand):
    def __init__(self, new_pos=None):
        self.spaceship_pos = new_pos


def calc_delay(time):
    return int(time/TIC_TIMEOUT)


async def sleep(sleep_frames=1):
    for _ in range(sleep_frames):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*'):
    """star animation"""
    while True:

        rand_delay = random.randint(0, 1000) * 0.01
        await sleep(calc_delay(rand_delay))

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(calc_delay(2))

        canvas.addstr(row, column, symbol)
        await sleep()

        await sleep(calc_delay(0.3))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep()

        await sleep(calc_delay(0.5))

        canvas.addstr(row, column, symbol)
        await sleep()

        await sleep(calc_delay(0.3))


async def fire(canvas,
               start_row,
               start_column,
               rows_speed=-0.3,
               columns_speed=0,
               symbols=['*', 'O', ' ']):
    """Display animation of gun shot. Direction and speed can be specified."""

    symbols = cycle(symbols)

    cur_s = next(symbols)

    start_row, start_column = get_corrected_position(cur_s, canvas,
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


def get_corrected_position(obj, canvas, obj_start_row, obj_start_col, frame_borders={'row': 1, 'col': 1}):
    """text pos (moving obj) validation: text must be in a frame"""
    rows_in_obj, columns_in_obj = get_frame_size(obj)

    max_row, max_col = canvas.getmaxyx()

    centre_obj_position = {'row': mean([obj_start_row, obj_start_row + rows_in_obj]),
                     'col': mean([obj_start_col, obj_start_col + columns_in_obj])}

    half_obj = {'row': int(rows_in_obj/2),
                'col': int(columns_in_obj/2)}

    max_obj_centre_pos = {'row': max_row - frame_borders['row'],
               'col': max_col - frame_borders['col']}

    min_obj_centre_pos = {'row': frame_borders['row'],
                          'col': frame_borders['col']}


    obj_position = [obj_start_row, obj_start_col]

    ## check object position in row and col dimensions
    for i, dim in enumerate(centre_obj_position.keys()):

        if centre_obj_position[dim] < min_obj_centre_pos[dim]:
            obj_position[i] = min_obj_centre_pos[dim]

        elif centre_obj_position[dim] > max_obj_centre_pos[dim] :
            obj_position[i] = max_obj_centre_pos[dim] - half_obj[dim]

    return obj_position


async def animate_spaceship(canvas, start_row, start_column, frames):
    """Display animation of spaceship"""

    for frame in frames.copy():
        frames.extend([frame, frame])

    for frame in cycle(frames):
        draw_frame(canvas, start_row, start_column, frame)

        await CoroutineParams((start_row + 2, start_column + 2))

        draw_frame(canvas, start_row, start_column, frame, negative=True)


        row_direction, column_direction, key = read_controls(canvas)

        start_row += row_direction * SPACESHIP_VEL_MUL_ROW
        start_column += column_direction * SPACESHIP_VEL_MUL_COL

        start_row, start_column = get_corrected_position(frame, canvas,
                                                         start_row, start_column)


def load_frames(folder, key_word='sc'):
    """
    Load frames. Spaceship frames is default.
    :param folder: name of dir with frames in project dir
    :param key_word: pattern in searched frame filename
    :return: list of frames
    """
    pattern = f'\w*{key_word}\w*.txt'
    path_to_dir = os.path.join(os.getcwd(), folder)
    frame_paths = [
                os.path.join(path_to_dir, frame_file_name) for frame_file_name in
                os.listdir(path_to_dir) if re.fullmatch(pattern, frame_file_name)
                ]
    if frame_paths:
        frames = []
        for path_to_frame in frame_paths:
            with open(path_to_frame, 'r') as f:
                frames.append(f.read())
        return frames
    else:
        raise NoFrameFile('No frame files here')


def draw(canvas):
    """Draw frames"""
    try:
        spaceship_frames = load_frames(ANIMATION_FOLDER)
    except NoFrameFile:
        exit('Frame files not found in ANIMATION_FOLDER directory')

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

    coroutines.append(animate_spaceship(canvas, spaceship_row, spaceship_column, spaceship_frames))

    # ------draw frames------
    while coroutines:

        for i, coroutine in enumerate(coroutines.copy()):
            try:
                command = coroutine.send(None)
                try:
                    spaceship_row, spaceship_column = command.spaceship_pos
                except AttributeError:
                    pass

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
