import asyncio
import dataclasses

from curses_tools import draw_frame
from game_scenario import PHRASES
from global_constants import TIC_TIMEOUT


@dataclasses.dataclass
class TimeFlow:
    current_year: int

    async def run(self, year_in_seconds):
        while True:
            await sleep(calc_delay(year_in_seconds))
            self.current_year += 1

    async def show_year_box(self, canvas, nlines=10, ncols=None):

        if not ncols:
            _, ncols = canvas.getmaxyx()

        year_window = canvas.derwin(nlines, ncols, 0, 0)
        year_window.nodelay(True)
        while True:
            message_to_show = self.create_message_to_show()

            draw_frame(year_window, 0, 0, message_to_show)
            #year_window.addstr(0, 0, self.create_message_to_show())
            await sleep()

            year_window.refresh()
            draw_frame(year_window, 0, 0, message_to_show, negative=True)

    def create_message_to_show(self):
        year = f'{self.current_year} year'

        if self.current_year in PHRASES:
            return year + ': ' + PHRASES[self.current_year]
        else:
            return year


def calc_delay(time):
    return int(time / TIC_TIMEOUT)


async def sleep(sleep_frames=1):
    for _ in range(sleep_frames):
        await asyncio.sleep(0)
