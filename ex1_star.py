"""На экране звезду обозначаем одним символом *.
Со временем её яркость меняется от тусклой до самой яркой."""
#
import curses
import asyncio
import random
import time
from _curses import window
import pdb
import logging

class EventLoopCommand:

    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):

    def __init__(self, seconds):
        self.seconds = seconds


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        await Sleep(2)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        await Sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        await Sleep(0.5)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        await Sleep(0.3)


def new_frame(coroutines, curses, canvas):
    for coroutine in coroutines.copy():
        coroutine.send(None)
        curses.curs_set(False)
        canvas.refresh()


def sleep_frame(coroutines):
    for coroutine in coroutines.copy():
        time_to_sleep = coroutine.send(None)
    # print(time_to_sleep.seconds)
    time.sleep(time_to_sleep.seconds)


def get_star_pos(size):
    x = random.randint(1, size[0]-1)
    y = random.randint(1, size[1]-1)
    return x, y


def draw(canvas):
    TIC_TIMEOUT = 0.1
    num_stars = random.randint(5, 100)
    coroutines = []
    win_size = window.getmaxyx(canvas)

    for _ in range(num_stars):
        row, column = get_star_pos(win_size)
        star_style = random.choice('+*.:')
        coroutines.append(blink(canvas, row, column, star_style))

    while True:
        for _ in range(4):
            new_frame(coroutines, curses, canvas)
            sleep_frame(coroutines)
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
#
# def draw(canvas, style, t):
#     row, column = (5, 20)
#     if style:
#         canvas.addstr(row, column, '*', style)
#     else:
#         canvas.addstr(row, column, '*')
#     canvas.refresh()
#     curses.curs_set(False)
#     time.sleep(t)
#
#
# if __name__ == '__main__':
#     curses.update_lines_cols()
#     while True:
#         curses.wrapper(draw, curses.A_DIM, 2)
#         curses.wrapper(draw, None, 0.3)
#         curses.wrapper(draw, curses.A_BOLD, 0.5)
#         curses.wrapper(draw, None, 0.3)
