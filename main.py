import curses
import random
import time
from curses_tools import *
from itertools import cycle as cycle
import os
from statistics import median as median

TIC_TIMEOUT = 0.1
ANIMATION_FOLDER = 'files'


class EventLoopCommand:
    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):
    def __init__(self, seconds, new_pos=None):
        self.seconds = seconds
        self.new_pos = new_pos  ## position of fire


async def blink(canvas, row, column, symbol='*'):
    """star animation"""
    while True:
        await Sleep(random.randint(0, 1000) * 0.01)
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await Sleep(2)
        canvas.addstr(row, column, symbol)
        await Sleep(0)

        await Sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await Sleep(0)

        await Sleep(0.5)

        canvas.addstr(row, column, symbol)
        await Sleep(0)

        await Sleep(0.3)


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
    start_row, start_column = pos_correct(cur_s, canvas,
                                          [start_row, start_column])

    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), cur_s)
    await Sleep(0)

    canvas.addstr(round(row), round(column), next(symbols))
    await Sleep(0)
    canvas.addstr(round(row), round(column), next(symbols))

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1
    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await Sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def get_star_pos(size):
    """get random star position"""
    x = random.randint(1, size[0] - 1)
    y = random.randint(1, size[1] - 1)
    return x, y


def pos_correct(text, canvas, position, borders=[2, 2]):
    """chek correcting of text pos"""
    rows_in_symb, columns_in_symb = get_frame_size(text)
    max_row, max_col = canvas.getmaxyx()  #
    mpos = (median([position[0], position[0] + rows_in_symb]),
            median([position[1], position[1] + columns_in_symb]))

    ans_pos = position
    if mpos[0] < borders[0]:  #chekup rows
        ans_pos[0] = borders[0] + 1
    elif mpos[0] > max_row - borders[0]:
        ans_pos[0] = max_row - 2 * (borders[0] + 1)

    if mpos[1] < borders[1]:  #chekup cols
        ans_pos[1] = borders[1]
    elif mpos[1] > max_col - borders[1]:
        ans_pos[1] = max_col - 2 * (borders[1] + 1)
    return ans_pos


async def animate_spaceship(canvas, start_row, start_column, symbols):
    """spaceship frames"""
    sc = cycle(symbols)
    symbol = next(sc)
    while True:
        draw_frame(canvas, start_row, start_column, symbol)
        for i in range(2):
            await Sleep(0, (start_row + 2, start_column + 2))
        draw_frame(canvas, start_row, start_column, symbol, negative=True)
        symbol = next(sc)
        row_direction, column_direction, key = read_controls(canvas)

        start_row += row_direction
        start_column += column_direction

        [start_row, start_column
         ] = pos_correct(symbol, canvas,
                         [start_row, start_column])  ## check pos correct


def load_frames(folder, key_word='sc'):
    frs_path = os.path.join(os.getcwd(), folder)
    files = [
        os.path.join(frs_path, file) for file in os.listdir(frs_path)
        if 'sc' in file
    ]
    frs = []
    for file in files:
        with open(file, 'r') as f:
            frs.append(f.read())
    return frs


def draw(canvas):
    """Draw frames"""
    curses.window.nodelay(canvas, True)
    win_size = curses.window.getmaxyx(canvas)

    # ------stars-------
    num_stars = random.randint(5, 100)
    stars = []
    for _ in range(num_stars):
        row, column = get_star_pos(win_size)
        star_style = random.choice('+*.:')
        stars.append(blink(canvas, row, column, star_style))

    #### ------spacecraft and fire------
    start_row, start_column = win_size[0] / 2, win_size[1] / 2
    stars.append(fire(canvas, start_row + 2, start_column + 2))
    symbols = load_frames(ANIMATION_FOLDER)
    spacecraft = animate_spaceship(canvas, start_row, start_column, symbols)

    ### draw frames
    sleeping_stars = [[0, star] for star in stars]
    while sleeping_stars:
        sleeping_stars = [[timeout - TIC_TIMEOUT, star]
                          for timeout, star in sleeping_stars]

        # divide obj on an active and passive
        active_stars = [[timeout, star] for timeout, star in sleeping_stars
                        if timeout <= 0]
        sleeping_stars = [[timeout, star] for timeout, star in sleeping_stars
                          if timeout > 0]

        ##stars and fire
        for _, star in active_stars:
            try:
                sleep_command = star.send(None)
            except StopIteration:
                fr = fire(canvas, sc_info.new_pos[0], sc_info.new_pos[1])
                sleeping_stars.append([sc_info.seconds, fr])
                continue  # выкидываем истощившуюся корутины
            seconds_to_sleep = sleep_command.seconds
            sleeping_stars.append([seconds_to_sleep, star])
        ## spacecraft
        sc_info = spacecraft.send(None)
        curses.curs_set(False)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()

    curses.wrapper(draw)
