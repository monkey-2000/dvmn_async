#https://github.com/nobbynobbs/devman-async-python-1


"""obstacle class, animations and factory"""

import asyncio
import uuid

from curses_tools import draw_frame
from time_tools import sleep


class Obstacle():
    """cosmic garbage"""

    def __init__(self, row, column, row_size=1, column_size=1, uid=None):
        self.row = row
        self.column = column
        self.row_size = row_size
        self.column_size =column_size
        self.uid = uid

    def get_bounding_box_frame(self):
        """increment box size to compensate obstacle movement"""
        rows, columns = self.row_size + 1, self.column_size + 1
        return "\n".join(_get_bounding_box_lines(rows, columns))

    def get_bounding_box_corner_pos(self):
        """top left corner"""
        return self.row - 1, self.column - 1

    def dump_bounding_box(self):
        """left top corner and bbox frame itself"""
        row, column = self.get_bounding_box_corner_pos()
        return row, column, self.get_bounding_box_frame()

    def has_collision(
        self, obj_corner_row, obj_corner_column, obj_size_rows=1, obj_size_columns=1
    ):
        """Determine if collision has occured. Return True or False."""
        return has_collision(
            (self.row, self.column),
            (self.row_size, self.column_size),
            (obj_corner_row, obj_corner_column),
            (obj_size_rows, obj_size_columns),
        )

    def move_to(self, row, column):
        self.row = row
        self.column = column


def _get_bounding_box_lines(rows, columns):
    """yield bounding box line by line"""
    yield " " + "-" * columns + " "
    for _ in range(rows):
        yield "|" + " " * columns + "|"
    yield " " + "-" * columns + " "


async def show_obstacles(canvas, obstacles):
    """Display bounding boxes of every obstacle in a list"""

    while True:
        boxes = []

        for obstacle in obstacles:
            boxes.append(obstacle.dump_bounding_box())

        for row, column, frame in boxes:
            draw_frame(canvas, row, column, frame)

        await asyncio.sleep(0)

        for row, column, frame in boxes:
            draw_frame(canvas, row, column, frame, negative=True)


def _is_point_inside(
    corner_row, corner_column, size_rows, size_columns, point_row, point_row_column
):
    rows_flag = corner_row <= point_row < corner_row + size_rows
    columns_flag = corner_column <= point_row_column < corner_column + size_columns

    return rows_flag and columns_flag


def has_collision(obstacle_corner, obstacle_size, obj_corner, obj_size=(1, 1)):
    """Determine if collision has occured. Return True or False."""

    opposite_obstacle_corner = (
        obstacle_corner[0] + obstacle_size[0] - 1,
        obstacle_corner[1] + obstacle_size[1] - 1,
    )

    opposite_obj_corner = (
        obj_corner[0] + obj_size[0] - 1,
        obj_corner[1] + obj_size[1] - 1,
    )

    return any(
        [
            _is_point_inside(*obstacle_corner, *obstacle_size, *obj_corner),
            _is_point_inside(*obstacle_corner, *obstacle_size, *opposite_obj_corner),
            _is_point_inside(*obj_corner, *obj_size, *obstacle_corner),
            _is_point_inside(*obj_corner, *obj_size, *opposite_obstacle_corner),
        ]
    )


def find_obstracles(obstracles, uid):

    for ind, obstracle in enumerate(obstracles):
        if obstracle.uid == uid:
            return ind
    return -1


def generate_obstracle_uid():
    # generate uid for new obstracle
    return uuid.uuid4().hex
