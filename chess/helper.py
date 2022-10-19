def pos_inc(pos: tuple[int, int], inc: tuple[int, int]):
    return pos[0]+inc[0], pos[1]+inc[1]

def check_grid(pos: tuple[int, int]):
    return min(pos) >= 0 and max(pos) <= 7