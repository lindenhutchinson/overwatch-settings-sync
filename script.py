import random
import pyautogui as pag
import cv2
import pytesseract
import ctypes
from PIL import Image
import numpy as np
import re
import time
import os
import json
from gen_curve import get_curve
import math
import concurrent.futures

SAFE_EDGE = (2350, 580)
SET_WIDTH = 2560
SET_HEIGHT = 1440
SENSITIVITY_POS = ((1595, 280), (1695, 310))
CHANGE_HERO_POS = ((2165, 625), (2490, 680))
HERO_NAME_POS = ((2170, 555), (2485, 600))
OPTIONS_BTN_POS = ((1170, 700), (1750, 765))
CONTROLS_BTN_POS = ((425, 85), (600, 125))
LOCATE_CONFIDENCE = 0.6
TWEENS = [pag.easeInQuad, pag.easeOutQuad, pag.easeInOutQuad]
TYPING_INTERVAL = 0.25


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


def get_cropped_screenshot(area, do_preprocess):
    """
    Get a cropped screenshot of a specified area on the screen.

    Args:
    area (tuple): A tuple of integers representing the area to capture in the format (left, top, width, height).
    do_preprocess (bool): A flag indicating whether to preprocess the captured image before returning.

    Returns:
    PIL.Image: A PIL.Image object representing the captured screenshot.

    Note:
    - The area should be specified in screen coordinates.
    - If do_preprocess is True, the captured image will be preprocessed using the preprocess function before returning.
    """
    img = pag.screenshot(region=area)
    if do_preprocess:
        img = preprocess(img)
    return img


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


def get_text_from_position(pos, preprocess=False):
    """
    Extracts text from a given position on the screen using Tesseract OCR engine.

    Args:
    pos (tuple): A tuple of 2 tuples representing the top-left and bottom-right corners of the rectangular area on the screen.
    preprocess (bool, optional): Whether to preprocess the screenshot before performing OCR. Defaults to False.

    Returns:
    str: The text extracted from the specified position on the screen, cleaned and formatted.
    """
    area = get_left_top_width_height(pos)
    img = get_cropped_screenshot(area, preprocess)
    text = pytesseract.image_to_string(img)
    return clean_string(text)


def click_in_area(area, human_movement):
    """
    This function generates a random position within a given area, moves the cursor to that position, clicks on it and
    waits for a random time interval to simulate a human-like clicking behaviour.

    Parameters:
    -----------
    area: tuple
        A tuple of two tuples, each containing the (x,y) coordinates of the top-left and bottom-right corners of the
        rectangular area.

    Returns:
    --------
    None
    """
    pos = get_pos_in_area(area)
    move_to_pos(pos, human_movement)
    pag.click()


def click_on_pos(pos, human_movement):
    """
    This function moves the cursor to the given position and clicks on it while waiting for a random time interval to
    simulate a human-like clicking behaviour.

    Parameters:
    -----------
    pos: tuple
        A tuple containing the (x,y) coordinates of the position to click on.

    Returns:
    --------
    None
    """
    move_to_pos(pos, human_movement)
    pag.click()


def move_along_curve(curve):
    for i, (x, y) in enumerate(curve):
        if i % random.randint(1, 3) == 0: 
            pag.moveTo(x, y, duration=random.uniform(0.005, 0.05))


def get_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))


def move_to_pos(pos, human_movement):
    if human_movement:
        start_pos = pag.position()
        distance = get_distance(start_pos, pos)
        num_points = int(distance // 50)
        curve = get_curve(start_pos, pos, num_points)
        move_along_curve(curve)
    pag.moveTo(pos, duration=random.uniform(0.01, 0.02), tween=random.choice(TWEENS))

def get_hero_data_locations(screenshot, human_movement):
    data = []
    filenames = [os.path.join("heroes", filename) for filename in os.listdir("heroes")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for img_path in filenames:
            futures.append(executor.submit(get_hero_card_location, img_path, screenshot))
        
        for future in concurrent.futures.as_completed(futures):
            hero_img_path, location = future.result()
            click_on_pos(location, human_movement)
            pos = get_pos_in_area(CHANGE_HERO_POS)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                hero_data_future = executor.submit(get_hero_data)
                move_cursor_future = executor.submit(move_to_pos, pos, human_movement)

                sensitivity, hero_name = hero_data_future.result()
                move_cursor_future.result()
            
            pag.click(pos)

            data.append(
                {"name": hero_name, "sensitivity": sensitivity, "filepath": hero_img_path}
            )
            print(hero_name, sensitivity)
    
    return data

def get_hero_card_location(hero_img_path, screenshot):
    hero_card = pag.locate(hero_img_path, screenshot, confidence=LOCATE_CONFIDENCE)
    if not hero_card:
        print("BAD!")
        return {}
    centre = get_centre_pos_from_box(hero_card)
    
    return hero_img_path, centre


def get_hero_data():
    sensitivity = get_text_from_position(SENSITIVITY_POS, True)
    hero_name = get_text_from_position(HERO_NAME_POS)
    return sensitivity, hero_name


def get_all_heroes_screenshot(human_movement):
    click_in_area(OPTIONS_BTN_POS, human_movement)
    click_in_area(CONTROLS_BTN_POS, human_movement)
    click_in_area(CHANGE_HERO_POS, human_movement)
    move_to_pos(SAFE_EDGE, human_movement)
    # sleep so we take a screenshot of the correct page
    time.sleep(1)
    return pag.screenshot()

def get_sensitivity_data(human_movement=True):
    """Get sensitivity data for all heroes.

    Returns:
        A list of dictionaries where each dictionary contains the following keys:
        - name: the name of the hero (str)
        - sensitivity: the sensitivity of the hero (float)
        - filepath: the filepath to the hero's image (str)
    """

    data = []

    all_heroes_img = get_all_heroes_screenshot(human_movement)
    
    data = get_hero_data_locations(all_heroes_img, human_movement)

    return data


def set_sensitivity_data(data, human_movement=True):
    """
    Sets the sensitivity data for the heroes specified in the data list.

    Args:
        data (list): A list of dictionaries containing hero data. Each dictionary should have
                     the following keys: 'name', 'sensitivity', and 'filepath'. 'name' is the
                     name of the hero, 'sensitivity' is a string representing the sensitivity
                     value, and 'filepath' is the file path of the hero image.

    Returns:
        None
    """
    all_heroes_img = get_all_heroes_screenshot(human_movement)

    for hero in data:
        hero_card = pag.locate(
            hero["filepath"], all_heroes_img, confidence=LOCATE_CONFIDENCE
        )
        if not hero_card:
            print("BAD!", hero["filepath"])
            continue
        print(hero["filepath"])
        centre = get_centre_pos_from_box(hero_card)
        click_on_pos(centre, human_movement)
        sens_centre = get_centre_pos(*get_left_top_width_height(SENSITIVITY_POS))
        click_on_pos(sens_centre, human_movement)
        pag.keyDown("ctrl")
        pag.press("a")
        pag.keyUp("ctrl")
        pag.write(hero["sensitivity"], interval=TYPING_INTERVAL)
        pag.press("enter")
        click_in_area(CHANGE_HERO_POS, human_movement)


def save_settings_to_json(filename, human_movement):
    data = get_sensitivity_data(human_movement)
    with open(filename, "w+") as fn:
        json.dump(data, fn)


def load_settings_from_json(filename, human_movement):
    with open(filename, "r") as fn:
        data = json.load(fn)
    set_sensitivity_data(data, human_movement)


if __name__ == "__main__":

    save_settings_to_json("settings.json", False)
    # load_settings_from_json("settings.json", False)
