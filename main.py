import random
import pyautogui as pag
import pytesseract
import time
import os
import json
from gen_curve import get_curve
import concurrent.futures

from utils import clean_string, get_centre_pos, get_centre_pos_from_box, get_distance, get_left_top_width_height, get_pos_in_area, preprocess

SAFE_EDGE = (2350, 580)
SENSITIVITY_POS = ((1595, 280), (1695, 310))
CHANGE_HERO_POS = ((2165, 625), (2490, 680))
HERO_NAME_POS = ((2170, 555), (2485, 600))
OPTIONS_BTN_POS = ((1170, 700), (1750, 765))
CONTROLS_BTN_POS = ((425, 85), (600, 125))
LOCATE_CONFIDENCE = 0.6
TWEENS = [pag.easeInQuad, pag.easeOutQuad, pag.easeInOutQuad]
TYPING_INTERVAL = 0.25

class ScreenController:
    def __init__(self, human):
        """
        Initialize a ScreenController object.

        :param human: A flag indicating whether the controller should simulate human-like behavior.
        :type human: bool
        :return: None
        """
        self.human = human

    def click_in_area(self, area):
        """
        Generate a random position within a given area, move the cursor to that position, click on it, and wait for a random
        time interval to simulate human-like clicking behavior.

        :param area: A tuple of two tuples, each containing the (x, y) coordinates of the top-left and bottom-right corners
                     of the rectangular area.
        :type area: tuple
        :return: None
        """
        pos = get_pos_in_area(area)
        self.move_to_pos(pos)
        pag.click()

    def click_on_pos(self, pos):
        """
        Move the cursor to the given position and click on it while waiting for a random time interval to simulate human-like
        clicking behavior.

        :param pos: A tuple containing the (x, y) coordinates of the position to click on.
        :type pos: tuple
        :return: None
        """
        self.move_to_pos(pos)
        pag.click()

    def move_to_pos(self, pos):
        """
        Move the cursor to the given position.

        :param pos: A tuple containing the (x, y) coordinates of the position to move to.
        :type pos: tuple
        :return: None
        """
        if self.human:
            start_pos = pag.position()
            distance = get_distance(start_pos, pos)
            num_points = int(distance // 50)
            curve = get_curve(start_pos, pos, num_points)
            self.move_along_curve(curve)
        pag.moveTo(pos, duration=random.uniform(0.01, 0.02), tween=random.choice(TWEENS))
    
    def move_along_curve(self, curve):
        """
        Move the cursor along the specified curve.

        :param curve: A list of (x, y) coordinates representing the curve.
        :type curve: list
        :return: None
        """

        for i, (x, y) in enumerate(curve):
            # todo - tinker with how we travel along the curve
            if i % random.randint(1, 3) == 0: 
                pag.moveTo(x, y, duration=random.uniform(0.005, 0.05))

    def get_text_from_position(self, pos, preprocess=False):
        """
        Extract text from a given position on the screen using Tesseract OCR engine.

        :param pos: A tuple of 2 tuples representing the top-left and bottom-right corners of the rectangular area on the screen.
        :type pos: tuple
        :param preprocess: Whether to preprocess the screenshot before performing OCR. Defaults to False.
        :type preprocess: bool
        :return: The text extracted from the specified position on the screen, cleaned and formatted.
        :rtype: str
        """
        area = get_left_top_width_height(pos)
        img = self.get_cropped_screenshot(area, preprocess)
        text = pytesseract.image_to_string(img)
        return clean_string(text)

    def get_cropped_screenshot(self, area, do_preprocess):
        """
        Get a cropped screenshot of a specified area on the screen.

        :param area: A tuple of integers representing the area to capture in the format (left, top, width, height).
        :type area: tuple
        :param do_preprocess: A flag indicating whether to preprocess the captured image before returning.
        :type do_preprocess: bool
        :return: A PIL.Image object representing the captured screenshot.
        :rtype: PIL.Image

        Notes:
        - The area should be specified in screen coordinates.
        - If do_preprocess is True, the captured image will be preprocessed using the preprocess function before returning.
        """
        img = pag.screenshot(region=area)
        if do_preprocess:
            img = preprocess(img)
        return img

class HeroManager:
    def __init__(self, human):
        """
        Initialize a HeroManager object.

        :param human: A flag indicating whether the manager should simulate human-like behavior.
        :type human: bool
        :return: None
        """
        self.ctrl = ScreenController(human)

    def get_hero_data_locations(self, screenshot):
        """
        Get the locations of hero data from the given screenshot.

        :param screenshot: The screenshot to analyze.
        :type screenshot: PIL.Image
        :return: A list of dictionaries containing hero data, including name, sensitivity, and filepath.
        :rtype: list
        """
        data = []
        filenames = [os.path.join("heroes", filename) for filename in os.listdir("heroes")]
        
        # use threading to speed up the process of finding the location for each hero card
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for img_path in filenames:
                futures.append(executor.submit(self.get_hero_card_location, img_path, screenshot))
            
            for future in concurrent.futures.as_completed(futures):
                # we can start capturing the settings for hero cards we have already located,
                # while others are still being located.
                # this speeds up execution significantly.
                hero_img_path, location = future.result()
                self.ctrl.click_on_pos(location)
                pos = get_pos_in_area(CHANGE_HERO_POS)

                # use threading to speed up the process of capturing the hero settings
                # this grabs the hero settings using OCR
                # and in parallel, it starts moving the cursor back to the required button
                # so we can return to the hero page screen as soon as possible
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    # get the sensitivity settings using OCR
                    hero_data_future = executor.submit(self.get_hero_data)
                    # move the cursor to the CHANGE_HERO button
                    move_cursor_future = executor.submit(self.ctrl.move_to_pos, pos)
                    sensitivity, hero_name = hero_data_future.result()
                    move_cursor_future.result()
                
                pag.click(pos)

                data.append(
                    {"name": hero_name, "sensitivity": sensitivity, "filepath": hero_img_path}
                )
                print(hero_name, sensitivity)
        
        return data

    def get_hero_card_location(self, hero_img_path, screenshot):
        """
        Get the location of a hero card within the given screenshot.

        :param hero_img_path: The path to the hero image file.
        :type hero_img_path: str
        :param screenshot: The screenshot to search for the hero card.
        :type screenshot: PIL.Image
        :return: A tuple containing the hero image path and the center coordinates of the hero card.
        :rtype: tuple
        """
        hero_card = pag.locate(hero_img_path, screenshot, confidence=LOCATE_CONFIDENCE)
        if not hero_card:
            print("BAD!")
            return {}
        centre = get_centre_pos_from_box(hero_card)
        
        return hero_img_path, centre

    def get_hero_data(self):
        """
        Get hero sensitivity and name from the current screen position.

        :return: A tuple containing the hero sensitivity and name.
        :rtype: tuple
        """
        sensitivity = self.ctrl.get_text_from_position(SENSITIVITY_POS, True)
        hero_name = self.ctrl.get_text_from_position(HERO_NAME_POS)
        return sensitivity, hero_name

    def get_all_heroes_screenshot(self):
        """
        Take a screenshot of the screen showing all the heroes.

        :return: The screenshot of all the heroes.
        :rtype: PIL.Image
        """
        # this function assumes the user has pressed "ESC" after loading up their overwatch client
        # todo - press ESC yourself you lazy script
        
        # Click the 'Options' button
        self.ctrl.click_in_area(OPTIONS_BTN_POS)
        # Click the 'Controls' button
        self.ctrl.click_in_area(CONTROLS_BTN_POS)
        # Click the 'Change Hero' button
        self.ctrl.click_in_area(CHANGE_HERO_POS)
        # Move the cursor to a safe position to ensure no hero cards are highlighted
        self.ctrl.move_to_pos(SAFE_EDGE)
        # sleep so we take a screenshot of the correct page
        time.sleep(1)
        return pag.screenshot()

    def set_hero_sensitivities(self, data):
        """
        Set the sensitivities for the heroes using the provided data.

        :param data: The hero data containing sensitivity, filepath, and name.
        :type data: list
        :return: None
        """

        all_heroes_img = self.get_all_heroes_screenshot()

        for hero in data:
            hero_card = pag.locate(
                hero["filepath"], all_heroes_img, confidence=LOCATE_CONFIDENCE
            )
            if not hero_card:
                # todo - handle heroes that cant be found (try them again afterwards?)
                print("BAD!", hero["filepath"])
                continue

            print(hero["filepath"])
            # click on the hero card
            centre = get_centre_pos_from_box(hero_card)
            self.ctrl.click_on_pos(centre)

            # click on the sensitivity settings box
            sens_centre = get_centre_pos(*get_left_top_width_height(SENSITIVITY_POS))
            self.ctrl.click_on_pos(sens_centre)

            # select the current sensitivity to ensure it is overridden
            pag.keyDown("ctrl")
            pag.press("a")
            pag.keyUp("ctrl")

            # input the desired sensitivity
            pag.write(hero["sensitivity"], interval=TYPING_INTERVAL)
            pag.press("enter")

            # click to return to the 'Change Hero' page
            self.ctrl.click_in_area(CHANGE_HERO_POS)

def get_sensitivity_data(human_movement=True):
    """Get sensitivity data for all heroes.

    Returns:
        A list of dictionaries where each dictionary contains the following keys:
        - name: the name of the hero (str)
        - sensitivity: the sensitivity of the hero (float)
        - filepath: the filepath to the hero's image (str)
    """
    data = []
    mgr = HeroManager(human_movement)
    all_heroes_img = mgr.get_all_heroes_screenshot()
    
    data = mgr.get_hero_data_locations(all_heroes_img)

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
    mgr = HeroManager(human_movement)
    mgr.set_hero_sensitivities(data)
    
def save_settings_to_json(filename, human_movement):
    data = get_sensitivity_data(human_movement)
    with open(filename, "w+") as fn:
        json.dump(data, fn)

def load_settings_from_json(filename, human_movement):
    with open(filename, "r") as fn:
        data = json.load(fn)
    set_sensitivity_data(data, human_movement)

if __name__ == "__main__":
    # todo - implement a GUI
    # currently you need to comment and uncomment as necessary
    save_settings_to_json("settings.json", False)
    # load_settings_from_json("settings.json", False)
