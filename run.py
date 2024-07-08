import cv2
import numpy as np
import pyautogui
import win32gui
import time
import copy
from PIL import Image
import keyboard

GLSCALE = 1

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

# def find_window_by_process(process_name):
#     # didn't work. need to adjust.
#     hwnd_list = []
#     def callback(hwnd, hwnd_list):
#         if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != "":
#             _, pid = win32process.GetWindowThreadProcessId(hwnd)
#             try:
#                 _, found_process_name = win32process.GetModuleFileNameEx(pid, 0)
#             except win32process.error:
#                 found_process_name = None
#             if found_process_name and found_process_name.lower() == process_name.lower():
#                 hwnd_list.append(hwnd)
#         return True
#     win32gui.EnumWindows(callback, hwnd_list)
#     return hwnd_list[0] if hwnd_list else None

def capture_window(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    screenshot = pyautogui.screenshot()

    img = screenshot.crop((left, top, right, bottom))
    
    return img

def slowprt(now, id: int, interval: int, message: str):
    if time.time() - now(id) >= interval:
        print(message)
        now(id, True)

def newcrop(img: Image.Image, button: Button):
    new_image = img.crop((button.top_left[0], button.top_left[1], button.top_left[0] + button.width, button.top_left[1] + button.height))
    return new_image

def scale_try(image, template):
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    template = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)
    template_height, template_width = template.shape[:2]

    scale_start = 0.5
    scale_end = 2.0
    scale_step = 0.1

    best_scale = None
    best_val = float('inf')

    for scale in np.arange(scale_start, scale_end, scale_step):
        scaled_template = cv2.resize(template, (int(round(template_width * scale, 0)), int(round(template_height * scale, 0))))
        result = cv2.matchTemplate(image, scaled_template, cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)
        
        if min_val < best_val:
            best_val = min_val
            best_scale = scale

    return best_scale
     
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

def match_template(window_img, template_img, threshold=0.6):
    window_img_cv = cv2.cvtColor(np.array(window_img), cv2.COLOR_RGB2BGR)
    if GLSCALE == 1:
        template_img_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2BGR)
    else:
        template_img_cv = template_img
    res = cv2.matchTemplate(window_img_cv, template_img_cv, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= threshold:
        return max_loc, template_img_cv.shape[1], template_img_cv.shape[0], max_val
    else:
        return None, None, None, max_val

def scale_template(template, scale):
    template = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)
    template_height, template_width = template.shape[:2]
    scaled_template = cv2.resize(template, (int(round(template_width * scale, 0)), int(round(template_height * scale, 0))))
    return scaled_template

def cv_confirm(button: Button, flag: bool, img, template):
    # determine whether need to scale templates
    # stupid code, I have no better idea
    global GLSCALE
    if flag and button.confi >= 0.4:
        if button.confi <= 0.7 and GLSCALE == 1:
            # :if button not far from template, or it just didn't show in window
            temp_scale = scale_try(img, template)
            if temp_scale >= 0.7 and round(temp_scale, 1) != 1:
                # scale 
                GLSCALE = round(temp_scale, 2)
                test_value = match_template(img, scale_template(template, temp_scale))
                # print(GLSCALE, test_value[3])
                if test_value[3] <= 0.7:
                    GLSCALE = 1
        else:
            flag = False
    return flag

# def click_random_in_region(button, tick, sig):
#     if time.time() - tick('press') >= 0.01:
#         rect = win32gui.GetWindowRect(button.hwnd)
#         abs_x = rect[0] + button.top_left[0] + random.randint(0, button.width - 1)
#         abs_y = rect[1] + button.top_left[1] + random.randint(0, button.height - 1)
#         pyautogui.click(abs_x, abs_y)
#         tick('press', True)
#         print(f"Click @{sig} ({abs_x - rect[0]} {abs_y - rect[1]})")

def newpress(sig, tick: Timer, hwnd):
    if time.time() - tick('press') >= 0.2:
        keyboard.press(sig)
        keyboard.release(sig)
        print(f"{sig} pressed!")
        tick('press', True)

def appear_then_press(template: Image.Image, img: Image.Image, button: Button, sig, tick):
    tl, _, _, confi = match_template(img, template)
    if tl:
        newpress(sig, tick, button.hwnd)

def ergotic(templates, img, button, tick):
    sigs = ['left', 'right', 'up', 'down']
    for i, template in enumerate(templates):
        appear_then_press(template, img, button, sigs[i%4], tick)

def button_eval(button: Button, nan: tuple):
    if nan[0]:
        button.top_left = nan[0]
        button.width = nan[1]
        button.height = nan[2]
    button.confi = nan[3]

def button_stable(button: Button, img: Image.Image, template: Image.Image, threshold = 0.6):
    # determine if button location is stable
    top_left, *_ = match_template(img, template, threshold)
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

    def fl(file):
        return 'assets\\' + file

    mask_image = [
        Image.open(fl(img))
        for img in templates[0]
    ]
    icons = templates[1] + templates[2]
    icon_image = [
        Image.open(fl(img))
        for img in icons
    ]

    cv = False
    # flag for templates whether converted
    flag = False
    # flag for determine whether in fishing
    need_cv = True
    # flag for scale template
    now = id_timer()
    # tool to debug time cost
    init = Timer()
    # determine if fishing time out
    init.last_time = -40

    idfy_area = Button()
    buffer_area = Button()
    pause = Button()
    endtime = Button()

    while 1:
        if not hwnd:
            break

        if GLSCALE != 1 and not cv:
            # template broken detected, now scale templates
            cv_mask_image = [
                scale_template(template, GLSCALE)
                for template in mask_image
            ]
            mask_image.clear()
            mask_image = copy.copy(cv_mask_image)

            cv_icon_image = [
                scale_template(template, GLSCALE)
                for template in icon_image
            ]
            icon_image.clear()
            icon_image = copy.copy(cv_icon_image)
            cv = True

        window_img = capture_window(hwnd)

        button_lock_on(endtime, window_img, mask_image[2], hwnd)
        if endtime.show:
            continue

        button_lock_on(pause, window_img, mask_image[0], hwnd)

        need_cv = cv_confirm(pause, need_cv, window_img, mask_image[0])

        if pause.stable and pause.show:
            if not flag:
                slowprt(now, 1, 5, f"Find area: {pause.top_left}, Width: {pause.width}, Hight: {pause.height}, Fishing Game Detected")

            button_lock_on(idfy_area, window_img, mask_image[1], hwnd)

            if idfy_area.stable and not buffer_area.stable:
                # modify for screenshot latency, press latency, etc.
                buffer_area = copy.copy(idfy_area)
                if buffer_area.stable:
                    buffer_area.top_left = (idfy_area.top_left[0] - 0, idfy_area.top_left[1])
                    buffer_area.width = idfy_area.width - 0
        
            need_cv = cv_confirm(idfy_area, need_cv, window_img, mask_image[1])

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
                        ergotic(icon_image, crop_buffer, buffer_area, now)
                    else:
                        # now timeout, exit process
                        print(">>>>>>>>>>>>>>>>Fishing Game End<<<<<<<<<<<<<<<<")
                        flag = False
        else:
            if flag:
                print(">>>>>>>>>>>>>>>>Fishing Game End<<<<<<<<<<<<<<<<")
            flag = False
            slowprt(now, 2, 10, f"Fishing Not Running")

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