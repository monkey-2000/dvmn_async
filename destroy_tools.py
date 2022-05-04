import asyncio
import curses

from curses_tools import draw_frame, get_frame_size

EXPLOSION_FRAMES = [
    """\
           (_)
       (  (   (  (
      () (  (  )
        ( )  ()
    """,
    """\
           (_)
       (  (   (
         (  (  )
          )  (
    """,
    """\
            (
          (   (
         (     (
          )  (
    """,
    """\
            (
              (
            (
    """,
]


async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in EXPLOSION_FRAMES:

        draw_frame(canvas, corner_row, corner_column, frame)

        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(0)


async def show_game_over(canvas):

    from main import load_frames, ANIMATION_FOLDER

    game_over_frame = load_frames(ANIMATION_FOLDER, key_word='game_over')[0]

    win_size = curses.window.getmaxyx(canvas)
    rows_in_text, columns_in_text = get_frame_size(game_over_frame)
    row_centre, column_centre = win_size[0] / 2, win_size[1] / 2
    row = max(
        0, row_centre - rows_in_text//2
    )
    column  = max(
        0, column_centre - columns_in_text//2
    )

    while True:
        draw_frame(canvas, row, column, game_over_frame)
        await asyncio.sleep(0)
