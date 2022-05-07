import asyncio
import dataclasses

from curses_tools import draw_frame
from global_constants import TIC_TIMEOUT


@dataclasses.dataclass
class TimeFlow:

    current_year: int

    async def run(self, year_in_seconds):
        while True:
            await sleep(calc_delay(year_in_seconds))
            self.current_year += 1

    async def show_year_box(self, canvas, nlines=10, ncols=10):

        year_window = canvas.derwin(nlines, ncols, 0, 0)
        while True:
            canvas.addstr(0, 0, f'{self.current_year} year')
            await sleep()
            canvas.addstr(0, 0, ' ')

def calc_delay(time):
    return int(time / TIC_TIMEOUT)


async def sleep(sleep_frames=1):
    for _ in range(sleep_frames):
        await asyncio.sleep(0)