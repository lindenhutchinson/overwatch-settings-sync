import ctypes
import matplotlib.pyplot as plt
import random


def get_monitor_resolution():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_screen_xy(cart_x, cart_y):
    width, height = get_monitor_resolution()
    screen_x = cart_x + (width / 2)
    screen_y = -cart_y + (height / 2)
    return (screen_x, screen_y)


def get_cart_xy(screen_x, screen_y):
    width, height = get_monitor_resolution()
    cart_x = screen_x - (width / 2)
    cart_y = -(screen_y - (height / 2))
    return (cart_x, cart_y)


def recta(x1, y1, x2, y2):
    if x1 == x2:
        x2 += 1
    if y1 == y2:
        y2 += 1

    a = (y1 - y2) / (x1 - x2)
    b = y1 - a * x1
    return (a, b)


def get_curve(start_pos, end_pos, num_points):
    xa, ya = get_cart_xy(*start_pos)
    xc, yc = get_cart_xy(*end_pos)

    if xa < xc:
        xb = random.randint(xa, xc)
    else:
        xb = random.randint(xc, xa)

    if ya < yc:
        yb = random.randint(ya, yc)
    else:
        yb = random.randint(yc, ya)

    (x1, y1, x2, y2) = (xa, ya, xb, yb)
    (a1, b1) = recta(xa, ya, xb, yb)
    (a2, b2) = recta(xb, yb, xc, yc)
    points = []

    for i in range(0, num_points):
        if x1 == x2:
            continue
        else:
            (a, b) = recta(x1, y1, x2, y2)
        x = i * (x2 - x1) / num_points + x1
        y = a * x + b
        points.append(get_screen_xy(x, y))
        x1 += (xb - xa) / num_points
        y1 = a1 * x1 + b1
        x2 += (xc - xb) / num_points
        y2 = a2 * x2 + b2
    return points


if __name__ == "__main__":
    start = (100, 100)
    end = (200, 200)

    curve = get_curve(start, end, 1000)
    plt.plot(curve)
    plt.show()
