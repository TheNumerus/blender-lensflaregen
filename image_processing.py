import math


def compute_flare_intensity(x, y, max_x, max_y, props, ratio):
    delta_x = (x / max_x) - props.posx
    delta_y = (y / max_y) - props.posy

    dist = math.sqrt((delta_x ** 2) + ((delta_y / ratio) ** 2))
    return max(props.flare_size - dist, 0.0)


def draw_debug_cross(props):
    cross_color = [2.0, 0.0, 2.0, 1.0]
    thickness = 1
    length = 10

    max_x, max_y = props.image.size

    center_x = int(max_x * props.posx)
    center_y = int(max_y * props.posy)

    buffer = [0.0 for x in range(max_x * max_y * 4)]

    # draw horizontal line
    for y in range(max(center_y - thickness, 0), min(center_y + thickness, max_y)):
        for x in range(max(center_x - length, 0), min(center_x + length, max_x)):
            index = (x + y * max_x) * 4
            buffer[index:index+4] = cross_color

    # draw vertical line
    for y in range(max(center_y - length, 0), min(center_y + length, max_y)):
        for x in range(max(center_x - thickness, 0), min(center_x + thickness, max_x)):
            index = (x + y * max_x) * 4
            buffer[index:index+4] = cross_color

    props.image.pixels[:] = buffer