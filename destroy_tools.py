import asyncio
import curses

from curses_tools import draw_frame


async def explode(canvas, center_row, center_column):
    frames = ['1', '2']
    for frame in frames:
        draw_frame(canvas,  center_row, center_column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, center_row, center_column, frame, negative='True')


async def show_gameover(canvas):

    win_size = curses.window.getmaxyx(canvas)
    row, column = win_size[0] / 2, win_size[1] / 2
    while True:

        draw_frame(canvas, row, column, 'game_over')
        await asyncio.sleep(0)