"""На экране звезду обозначаем одним символом *.
Со временем её яркость меняется от тусклой до самой яркой."""
#
import curses
import asyncio
import time


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
    #print(time_to_sleep.seconds)
    time.sleep(time_to_sleep.seconds)


def draw(canvas):
    row, column = (5, 20)
    d_col = 10
    TIC_TIMEOUT = 0.1

    coroutines = []

    for i in range(5):
        coroutines.append(blink(canvas, row, column + d_col * i))

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
