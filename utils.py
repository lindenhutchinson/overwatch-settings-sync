import random
import cv2
import ctypes
from PIL import Image
import numpy as np
import re
import math

SET_WIDTH = 2560
SET_HEIGHT = 1440


def preprocess(img):
    img = img.convert("RGB")

    # Convert the image to a NumPy array
    img_np = np.array(img)

    # Define the color codes to filter for
    color_codes = [
        (255, 255, 255),
    ]

    # Define the color similarity threshold
    threshold = 60  # Adjust this value to control the leeway in color matching

    # Filter for colors in the screenshot using NumPy operations
    filtered_mask = np.zeros_like(img_np[:, :, 0], dtype=bool)
    for color_code in color_codes:
        color_code_np = np.array(color_code)
        color_difference = np.sum(np.abs(img_np[:, :, :3] - color_code_np), axis=2)
        matches = color_difference <= threshold
        filtered_mask |= matches

    # Expand the filtered mask to have the same shape as the screenshot image array
    filtered_mask_expanded = np.expand_dims(filtered_mask, axis=2)
    filtered_mask_expanded = np.repeat(filtered_mask_expanded, 3, axis=2)

    # Create a filtered image using the filtered mask
    filtered_image_np = np.where(filtered_mask_expanded, img_np, 0)
    thres_img = cv2.threshold(filtered_image_np, 127, 255, cv2.THRESH_BINARY_INV)[1]

    return Image.fromarray(thres_img)


def get_left_top_width_height(pos):
    """
    Returns a tuple of four values representing the left, top, width, and height of a rectangle
    defined by the two corners of a rectangle given as the argument 'pos'.

    Args:
    pos (tuple): A tuple of two tuples, representing the top-left and bottom-right corners of a rectangle.

    Returns:
    tuple: A tuple of four integers representing the left, top, width, and height of the rectangle.

    Example:
    If pos = ((10, 20), (50, 80)), the function returns (10, 20, 40, 60), which represents a rectangle
    with top-left corner at (10, 20), width 40, and height 60.
    """
    l_x = pos[0][0]
    r_x = pos[1][0]

    l_y = pos[0][1]
    r_y = pos[1][1]

    return (l_x, l_y, r_x - l_x, r_y - l_y)


def get_monitor_resolution():
    """
    Returns the resolution of the primary monitor in pixels as a tuple (width, height).
    This function uses the `GetSystemMetrics()` function from the Windows user32.dll library,
    so it is only compatible with Windows operating systems.

    Returns:
    - tuple: A tuple of integers representing the width and height of the primary monitor's resolution.
    """
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_scalars():
    """
    Returns the scaling factors to fit the desired width and height
    (SET_WIDTH and SET_HEIGHT) into the user's monitor resolution.

    Returns:
    - w_scalar (float): The scaling factor for the width dimension.
    - h_scalar (float): The scaling factor for the height dimension.
    """
    u_width, u_height = get_monitor_resolution()

    w_scalar = SET_WIDTH / u_width
    h_scalar = SET_HEIGHT / u_height

    if u_width < SET_WIDTH:
        w_scalar = u_width / SET_WIDTH

    if u_height < SET_HEIGHT:
        h_scalar = u_height / SET_HEIGHT

    return w_scalar, h_scalar


def get_scaled_position(x, y):
    """
    Takes in the x and y coordinates and returns their scaled position on the user's screen, based on the user's monitor resolution and the desired width and height set in SET_WIDTH and SET_HEIGHT constants.

    Args:
        x (int): The x-coordinate of the position to be scaled.
        y (int): The y-coordinate of the position to be scaled.

    Returns:
        A tuple (x, y) containing the scaled position of the input coordinates on the user's screen.
    """
    w_scalar, h_scalar = get_scalars()

    x *= w_scalar
    y *= h_scalar

    return (x, y)


def get_scaled_pos(pos):
    """
    Scales the position of a rectangular region by the user's monitor resolution to ensure
    that the screenshot is taken with the same aspect ratio regardless of the user's screen resolution.

    Args:
        pos (tuple): A tuple of four coordinates (x1, y1, x2, y2) defining a rectangular region.

    Returns:
        list: A list of two tuples containing the scaled coordinates of the top-left and bottom-right corners
              of the rectangular region.
    """
    scaled_pos = []

    for corner in pos:
        corner_pos = get_scaled_position(*corner)
        scaled_pos.append(corner_pos)

    return scaled_pos


def clean_string(str):
    """
    Cleans a given string by removing all non-alphanumeric characters except for spaces and periods.

    Args:
    str (str): The string to be cleaned.

    Returns:
    str: The cleaned string.

    Example:
    >>> clean_string("Hi! This is a string with (a lot) of [punctuation] and $ymbols.")
    'Hi This is a string with a lot of punctuation and yymbols'
    """
    res = re.findall(r"([\d\w\s\.]+)\W", str)
    return res[0].strip("\n") if len(res) else ""


def get_pos_in_area(area):
    """
    Generate a random position within the given area.

    Args:
        area: A tuple containing two tuples representing the top-left and bottom-right corners
              of the area, respectively. Each corner is represented by a tuple of (x, y) coordinates.

    Returns:
        A tuple containing the x and y coordinates of the randomly generated position within the area.
    """
    x = random.randint(area[0][0], area[1][0])
    y = random.randint(area[0][1], area[1][1])
    return x, y


def get_centre_pos_from_box(box):
    """Calculate the center position of a bounding box object.

    Args:
        box (pyautogui.Box): A bounding box object.

    Returns:
        tuple: A tuple of the x and y coordinates of the center of the box.
    """
    return (box.left + box.width // 2, box.top + box.height // 2)


def get_centre_pos(left, top, width, height):
    """Calculate the center position of a rectangle given its coordinates.

    Args:
        left (int): The x-coordinate of the top-left corner of the rectangle.
        top (int): The y-coordinate of the top-left corner of the rectangle.
        width (int): The width of the rectangle.
        height (int): The height of the rectangle.

    Returns:
        tuple: A tuple of the x and y coordinates of the center of the rectangle.
    """
    return (left + width // 2, top + height // 2)


def get_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))


