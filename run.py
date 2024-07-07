import cv2
import numpy as np
import pyautogui
import win32gui
import time
import random
import copy
from PIL import Image
import keyboard
import win32process

class Timer():
    last_time: float

class Button():
    hwnd: any
    top_left: tuple
    width: int
    height: int
    show: tuple
    confi: float
    stable: bool

    def __init__(self):
        self.hwnd = None
        self.top_left = None
        self.width = None
        self.height = None
        self.show = None
        self.stable = False
    
    @property
    def value(self):
        return self.confi
    
    @value.setter
    def value(self, new_confi):
        self.confi = round(new_confi, 4)

def find_window_by_title(title):
    def callback(hwnd, extra):
        if title in win32gui.GetWindowText(hwnd):
            extra.append(hwnd)
    hwnd_list = []
    win32gui.EnumWindows(callback, hwnd_list)
    return hwnd_list[0] if hwnd_list else None

def find_window_by_process(process_name):
    hwnd_list = []
    def callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != "":
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                _, found_process_name = win32process.GetModuleFileNameEx(pid, 0)
            except win32process.error:
                found_process_name = None
            if found_process_name and found_process_name.lower() == process_name.lower():
                hwnd_list.append(hwnd)
        return True
    win32gui.EnumWindows(callback, hwnd_list)
    return hwnd_list[0] if hwnd_list else None

def capture_window(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    screenshot = pyautogui.screenshot()

    img = screenshot.crop((left, top, right, bottom))
    
    return img #, screenshot

def match_template(window_img, template_img, threshold=0.6):
    window_img_cv = cv2.cvtColor(np.array(window_img), cv2.COLOR_RGB2BGR)
    template_img_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2BGR)
    
    res = cv2.matchTemplate(window_img_cv, template_img_cv, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= threshold:
        return max_loc, template_img_cv.shape[1], template_img_cv.shape[0], max_val
    else:
        return None, None, None, max_val
    
def ticknow():
    st = round(time.time(), 3)
    return st

def click_random_in_region(button, tick, sig):
    if time.time() - tick('press') >= 0.01:
        rect = (0, 0)# win32gui.GetWindowRect(button.hwnd)
        abs_x = rect[0] + button.top_left[0] + random.randint(0, button.width - 1)
        abs_y = rect[1] + button.top_left[1] + random.randint(0, button.height - 1)
        pyautogui.click(abs_x, abs_y)
        tick('press', True)
        print(f"Click @{sig} ({abs_x - rect[0]} {abs_y - rect[1]})")

def newpress(sig, tick: Timer, hwnd):
    if time.time() - tick('press') >= 0.2:
        keyboard.press(sig)
        keyboard.release(sig)
        print(f"{sig} pressed!")
        tick('press', True)

def appear_then_press(template: Image.Image, img: Image.Image, button: Button, sig, tick):
    tl, *_ = match_template(img, template)
    if tl:
        newpress(sig, tick, button.hwnd)
        # click_random_in_region(button, tick, sig)

def ergotic(templates, img, button, tick):
    sigs = ['left', 'right', 'up', 'down']
    for i, template in enumerate(templates):
        appear_then_press(template, img, button, sigs[i%4], tick)
     
def id_timer():
    # return id's last use time
    timers = {}

    def timer(id, clear = False):
        if id in timers:
            last_time = timers[id]
            if clear:
                timers[id] = time.time()
            return last_time
        else:
            timers[id] = time.time()
            return 0

    return timer

def slowprt(now, id: int, interval: int, message: str):
    if time.time() - now(id) >= interval:
        print(message)
        now(id, True)

def newcrop(img: Image.Image, button: Button):
    new_image = img.crop((button.top_left[0], button.top_left[1], button.top_left[0] + button.width, button.top_left[1] + button.height))
    return new_image

def button_eval(button: Button, nan: tuple):
    if nan[0]:
        button.top_left = nan[0]
        button.width = nan[1]
        button.height = nan[2]
    button.confi = nan[3]

def button_stable(button: Button, img: Image.Image, template: Image.Image):
    # judge if button location is stable
    top_left, *_ = match_template(img, template)
    if not top_left:
        return False
    if top_left != button.top_left:
        return False
    return True

def button_lock_on(button: Button, img: Image.Image, template: Image.Image, hwnd):
    # assure button is stable after first run
    if not button.top_left:
        # this block only load once when button first show
        button.hwnd = hwnd
        button_eval(button, match_template(img, template))
    else:
        if not button.stable:
            if button_stable(button, img, template):
                button.stable = True
            else:
                button.top_left = None
        if button.stable:
            crop_window = newcrop(img, button)
            button.show, _, _, button.confi = match_template(crop_window, template)

def fishing(hwnd, templates, threshold = 0.5):
    mask_image = [
        Image.open(img)
        for img in templates[0]
    ]
    icons = templates[1] + templates[2]
    icon_image = [
        Image.open(img)
        for img in icons
    ]
    flag = False
    now = id_timer()
    init = Timer()
    init.last_time = -40
    idfy_area = Button()
    buffer_area = Button()
    pause = Button()
    endtime = Button()

    while 1:
        if not hwnd:
            break

        window_img = capture_window(hwnd)

        button_lock_on(endtime, window_img, mask_image[2], hwnd)
        if endtime.show:
            continue

        button_lock_on(pause, window_img, mask_image[0], hwnd)

        if pause.stable and pause.show:
            if not flag:
                slowprt(now, 1, 2, f"Find area: {pause.top_left}, Width: {pause.width}, Hight: {pause.height}, Fishing Game Detected")

            button_lock_on(idfy_area, window_img, mask_image[1], hwnd)

            if idfy_area.stable and not buffer_area.stable:
                # modify for screenshot latency, press latency, etc.
                buffer_area = copy.copy(idfy_area)
                buffer_area.top_left = (idfy_area.top_left[0] - 0, idfy_area.top_left[1])
                buffer_area.width = idfy_area.width + 0

            if idfy_area.show or flag:
                # 1. game started 2. game in progress
                if idfy_area.show and not flag:
                    # 1. this block only load once when fishing start
                    print(">>>>>>>>>>>>>>>>Fishing Game Start<<<<<<<<<<<<<<<<")
                    init.last_time = time.time()
                    flag = True
                    # flag means game started
                if flag:
                    if time.time() - init.last_time <= 30:
                        crop_buffer = newcrop(window_img, buffer_area)
                        ergotic(icon_image, crop_buffer, idfy_area, now)
                    else:
                        # now timeout, exit process
                        flag = False
        else:
            slowprt(now, 2, 2, f"Fishing Not Running {round(pause.confi, 3)}")

def main():
    window_title = "NIKKE"
    # process_name = 'nikke.exe'
    ui = ['paused.png','click_area.png','end.png']
    blue_icon = ['bleft.png','bright.png','bup.png','bdown.png']
    yellow_icon = ['yleft.png','yright.png','yup.png','ydown.png']
    templates = [ui, blue_icon, yellow_icon]
    
    hwnd = find_window_by_title(window_title)
    # hwnd = find_window_by_process(process_name)
    if hwnd:
        print(f"Find Window: {hwnd}")
        fishing(hwnd, templates)
    else:
        print("Game not running")

if __name__ == "__main__":
    main()