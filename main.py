import os
import asyncio
import random
import re
import time
from statistics import mean as mean
from itertools import cycle as cycle

import curses

from curses_tools import read_controls, draw_frame, get_frame_size
from destroy_tools import explode, show_game_over
from game_scenario import get_garbage_delay_tics
from garbage_tools import get_garbage_column, crate_new_garbage_frame_array, get_max_garbage_amount_at_frame
from global_constants import TIC_TIMEOUT, START_YEAR, SECONDS_IN_YEAR, GUN_YEAR, \
    SPACESHIP_VEL_MUL_ROW, ANIMATION_FOLDER, DEBUG
from obstracles import Obstacle, find_obstracles, show_obstacles, generate_obstracle_uid
from physics import update_speed
from time_tools import sleep, calc_delay, TimeFlow

COROUTINES = []
OBSTRACLES = []
OBSTRACLES_IN_LAST_COLLISIONS = []


class NoFrameFile(Exception):
    pass


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


def find_collision_with_obstacle(row, column):
    """is spaceship shot or spaceship run into with obstacle"""
    for obstacle in OBSTRACLES:
        if obstacle.has_collision(row, column):
            OBSTRACLES_IN_LAST_COLLISIONS.append(obstacle)
            return True


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
    is_collision = False

    while 0 < row < max_row and 0 < column < max_column and not is_collision:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed
        is_collision = find_collision_with_obstacle(row, column)


def get_star_pos(size):
    """Get random star position."""
    pos = []
    for dim in size:
        pos.append(random.randint(1, dim - 1))
    return pos


def get_corrected_position(obj, canvas, obj_start_row, obj_start_col, frame_borders={'row': 1, 'col': 1}):
    """Text pos (moving obj) validation: text must be in a frame."""
    rows_in_obj, columns_in_obj = get_frame_size(obj)

    max_row, max_col = canvas.getmaxyx()

    centre_obj_position = {'row': mean([obj_start_row, obj_start_row + rows_in_obj]),
                           'col': mean([obj_start_col, obj_start_col + columns_in_obj])}

    half_obj = {'row': int(rows_in_obj / 2),
                'col': int(columns_in_obj / 2)}

    max_obj_centre_pos = {'row': max_row - frame_borders['row'],
                          'col': max_col - frame_borders['col']}

    min_obj_centre_pos = {'row': frame_borders['row'],
                          'col': frame_borders['col']}

    obj_position = [obj_start_row, obj_start_col]

    ## check object position in row and col dimensions
    for i, dim in enumerate(centre_obj_position.keys()):

        if centre_obj_position[dim] < min_obj_centre_pos[dim]:
            obj_position[i] = min_obj_centre_pos[dim]

        elif centre_obj_position[dim] > max_obj_centre_pos[dim]:
            obj_position[i] = max_obj_centre_pos[dim] - half_obj[dim]

    return obj_position


async def animate_spaceship(canvas, start_row, start_column, frames, time_flow):
    """Display animation of spaceship"""

    for frame in frames.copy():
        frames.extend([frame, frame])

    for frame in cycle(frames):
        draw_frame(canvas, start_row, start_column, frame)

        await sleep()

        draw_frame(canvas, start_row, start_column, frame, negative=True)

        row_direction, column_direction, is_space_pressed = read_controls(canvas)

        row_speed = row_direction * SPACESHIP_VEL_MUL_ROW
        column_speed = column_direction * SPACESHIP_VEL_MUL_ROW

        row_speed, column_speed = update_speed(row_speed, column_speed, row_direction,
                                               column_direction)

        start_row += row_speed
        start_column += column_speed

        start_row, start_column = get_corrected_position(frame, canvas,
                                                         start_row, start_column)

        # spaceship gun shot
        if is_space_pressed and time_flow.current_year >= GUN_YEAR:
            COROUTINES.append(fire(canvas, start_row + 2, start_column + 2))

        if find_collision_with_obstacle(start_row, start_column):
            break

    COROUTINES.append(show_game_over(canvas))


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.

     Column position will stay same, as specified on start.
     """
    rows_number, columns_number = canvas.getmaxyx()
    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    uid = generate_obstracle_uid()
    rows_size, columns_size = get_frame_size(garbage_frame)
    OBSTRACLES.append(Obstacle(row, column, rows_size, columns_size, uid))
    is_collision = False

    while row < rows_number and not is_collision:
        draw_frame(canvas, row, column, garbage_frame)

        await sleep()

        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed

        ind = find_obstracles(OBSTRACLES, uid)

        collision_obstracle_ind = find_obstracles(OBSTRACLES_IN_LAST_COLLISIONS, uid)
        if collision_obstracle_ind >= 0:
            is_collision = True
            OBSTRACLES_IN_LAST_COLLISIONS.remove(OBSTRACLES_IN_LAST_COLLISIONS[collision_obstracle_ind])
        else:
            OBSTRACLES[ind].move_to(row, column)

    OBSTRACLES.remove(OBSTRACLES[ind])
    if is_collision:
        await explode(canvas, row, column)


async def fill_orbit_with_garbage(frames, win_size, canvas, time_flow):
    """generate new garage"""

    while True:
        await sleep()

        garbage_num = get_max_garbage_amount_at_frame(time_flow.current_year)

        if garbage_num:
            new_garbage_frame_array = crate_new_garbage_frame_array(frames, garbage_num)
        else:
            new_garbage_frame_array = []

        for garbage_frame in new_garbage_frame_array:
            garbage_column = get_garbage_column(win_size)
            COROUTINES.append(fly_garbage(canvas, garbage_column, garbage_frame))

        if DEBUG:
            COROUTINES.append(show_obstacles(canvas, OBSTRACLES))

        delay_ticks = get_garbage_delay_tics(time_flow.current_year)
        delay_ticks = delay_ticks if delay_ticks else 0
        await sleep(delay_ticks)


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

    garbage_file_names = [
        'hubble', 'trash_small', 'duck',
        'lamp', 'trash_large', 'trash_small',
        'trash_xl'
    ]

    garbage_frames = []
    for garbage_file_name in garbage_file_names:
        try:
            garbage_frame = load_frames(ANIMATION_FOLDER, key_word=garbage_file_name)
        except NoFrameFile:
            exit(f'Frame files {garbage_file_name} not found in ANIMATION_FOLDER directory')
        else:
            garbage_frames.append(garbage_frame[0])

    curses.window.nodelay(canvas, True)
    win_size = curses.window.getmaxyx(canvas)

    # ------time-------
    timeflow = TimeFlow(current_year=START_YEAR)
    COROUTINES.extend([timeflow.run(SECONDS_IN_YEAR), timeflow.show_year_box(canvas)])

    # ------garbage-------
    COROUTINES.append(fill_orbit_with_garbage(garbage_frames, win_size, canvas, timeflow))
    # ------stars-------
    num_stars = random.randint(5, 6)

    for _ in range(num_stars):
        row, column = get_star_pos(win_size)
        star_style = random.choice('+*.:')
        COROUTINES.append(blink(canvas, row, column, star_style))

    # ------spacecraft------
    spaceship_row, spaceship_column = win_size[0] / 2, win_size[1] / 2
    COROUTINES.append(animate_spaceship(canvas, spaceship_row, spaceship_column, spaceship_frames, timeflow))

    # ------draw frames------
    while COROUTINES:

        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
                continue

        curses.curs_set(False)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
