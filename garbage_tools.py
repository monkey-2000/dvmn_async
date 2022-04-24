import random


class EventLoopCommand:
    def __await__(self):
        return (yield self)


class GarbageCoroutineParams(EventLoopCommand):
    def __init__(self, new_pos=None):
        self.garbage_pos = new_pos



def get_garbage_column(size):
    """get random garbage column position"""
    dim = size[1]
    column = random.randint(1, dim - 1)
    return column


def crate_new_garbage_frame_list(garbage_frames, garbage_num_max=None):
    """"""
    if not garbage_num_max:
        garbage_num = random.randint(3)
    else:
        print(garbage_num_max)
        garbage_num = random.randint(0, garbage_num_max)

    garbage_list = []
    for _ in range(garbage_num):
        garbage_list.append(random.choice(garbage_frames))
    return garbage_list
