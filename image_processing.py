import math


def compute_flare_intensity(x, y, max_x, max_y, props, ratio):
    delta_x = (x / max_x) - props.posx
    delta_y = (y / max_y) - props.posy

    dist = math.sqrt((delta_x ** 2) + (delta_y ** 2) / ratio)
    return max(props.flare_size - dist, 0.0)
