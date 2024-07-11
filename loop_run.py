import cv2
import numpy as np
import pyautogui
import win32gui
import time
import copy
import random
from PIL import Image
import keyboard

GLSCALE = 1
GLASSETS = {}
CVED = False

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
    img: Image.Image
    no_scale: bool

    def __init__(self):
        self.hwnd = None
        self.top_left = None
        self.width = None
        self.height = None
        self.show = None
        self.stable = False
        self.no_scale = True
    
    @property
    def value(self):
        return self.confi
    
    @value.setter
    def value(self, new_confi):
        self.confi = round(new_confi, 4)

def assets_initial():
    """
    initial global assets
    """
    def fl(file):
        return 'assets\\' + file + '.png'
    for asset in GLASSETS:
        tmp_asset = {
            img: Image.open(fl(img))
            for img in GLASSETS[asset][0]
        }
        GLASSETS[asset][0].clear()
        GLASSETS[asset][0] = tmp_asset
        GLASSETS[asset].append({})

def scale_template():
    pass

def scale_asset(assets):
    """
    scale assets

    Args:
        assets (str): 
            name in GLASSETS
    """
    cv_asset = {
        asset: scale_template(asset, GLSCALE)
        for asset in GLASSETS[assets][0]
    }
    GLASSETS[assets][0].clear()
    GLASSETS[assets][0] = cv_asset

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
    """
    Args:
        id (int):
            use slowprt with same id means use the same timer, it's useful if you want print different message with same interval.
    """
    if time.time() - now(id) >= interval:
        print(message)
        now(id, True)

def newcrop(img: Image.Image, button: Button):
    new_image = img.crop((button.top_left[0], button.top_left[1], button.top_left[0] + button.width, button.top_left[1] + button.height))
    return new_image
 
def id_timer():
    """
    return id's last use time
    """
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

def match_template(window_img, template_img, innerscale=True, threshold=0.6):
    window_img_cv = cv2.cvtColor(np.array(window_img), cv2.COLOR_RGB2BGR)
    if not innerscale and GLSCALE != 1:
        template_img_cv = template_img
    else:
        template_img_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2BGR)
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
    """
    determine whether need to scale templates
    """
    # stupid code, I have no better idea

    def scale_try(image, template: Image.Image):
        """
        scale_try would try to find the possible zoom factor to adapt resolution in use, it would return the best factor could find
        """
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
            
    global GLSCALE
    if flag and button.confi >= 0.4:
        if button.confi <= 0.7 and GLSCALE == 1:
            # :if button not far from template, or it just didn't show in window
            temp_scale = scale_try(img, template)
            if round(temp_scale, 1) == 1: return False
            if temp_scale >= 0.7:
                # scale 
                GLSCALE = test_value
                test_value = match_template(img, scale_template(template, temp_scale), False)
                # print(GLSCALE, test_value[3])
                if test_value[3] <= 0.7:
                    GLSCALE = 1
        else:
            flag = False
    return flag

def click_random_in_region(button, tick, sig):
    """
    it click in a region where button located, the coordinate of window button based is used as origin
    """
    if time.time() - tick('click') >= 0.1:
        rect = win32gui.GetWindowRect(button.hwnd)
        abs_x = rect[0] + button.top_left[0] + random.randint(5, button.width - 10)
        abs_y = rect[1] + button.top_left[1] + random.randint(5, button.height - 10)
        pyautogui.click(abs_x, abs_y)
        tick('click', True)
        print(f"Click @{sig} ({abs_x - rect[0]} {abs_y - rect[1]})")

def newpress(sig, tick):
    """
    send press key event for specify sig
    """
    if time.time() - tick('press') >= 0.2:
        keyboard.press(sig)
        keyboard.release(sig)
        print(f"{sig} pressed!")
        tick('press', True)

def handle_multibutton(buttons, hwnd, now):
    """
    receive buttons and click them in order
    """
    def real_area(button: Button, sig: str):
        offset = 130 if sig == 'end' else (180 if sig == 'start' else 190) 
        button.width = 60 + offset
        return button
    
    for button in buttons:
        while 1:

            window_img = capture_window(hwnd)

            sig = button[1]
            button = button[0]
            button: Button
            button_lock_on(button, window_img, button.img, hwnd)
            if button.show:
                area2click = real_area(button, sig)
                click_random_in_region(area2click, now, sig)
                break

def handle_up_down():
    pass

def appear_then_press(template: Image.Image, img: Image.Image, button: Button, sig, tick):
    tl, *_= match_template(img, template, False)
    if tl:
        # if sig == 'up' or sig == 'down':
        #     handle_up_down(button.hwnd)
        #     return
        newpress(sig, tick)

def ergotic(templates, img, button, tick):
    """
    loop detect image to press corrrespnding key
    """
    sigs = ['left', 'right', 'up', 'down']
    for i, template in enumerate(templates):
        # appear_then_press(template, img, button, sigs[i%4], tick)
        tl, *_ = match_template(img, template, False)
        if tl:
            newpress(sigs[i%4], tick)

def button_eval(button: Button, nan: tuple):
    if nan[0]:
        button.top_left = nan[0]
        button.width = nan[1]
        button.height = nan[2]
    button.confi = nan[3]

def button_stable(button: Button, img: Image.Image, template: Image.Image, threshold=0.6):
    """
    determine if button location is stable
    """
    top_left, *_ = match_template(img, template, button.no_scale, threshold)
    if not top_left:
        return False
    if top_left != button.top_left:
        return False
    return True

def button_lock_on(button: Button, img: Image.Image, template: Image.Image, hwnd):
    """
    assure button is stable after first run
    """
    if not button.top_left:
        # this block only load once when button first show
        button.hwnd = hwnd
        button_eval(button, match_template(img, template, button.no_scale))
    else:
        if not button.stable:
            if button_stable(button, img, template):
                button.stable = True
            else:
                button.top_left = None
        if button.stable:
            crop_window = newcrop(img, button)
            button.show, _, _, button.confi = match_template(crop_window, template, button.no_scale)

def handle_up_down(hwnd):
    global GLSCALE
    bkp_scale = GLSCALE
    GLSCALE = 1
    flag = 1

    sig = 'esc'
    keyboard.press(sig)
    keyboard.release(sig)
    
    start = Image.open('assets\\start.png')
    end = Image.open('assets\\end.png')
    pause = Image.open('assets\\paused.png')

    def real_area(button: Button, sig: str):
        offset = 130 if sig == 'end' else 180
        button.width = 60 + offset
        return button
    
    now = id_timer()
    st = Button()
    ed = Button()

    while 1:
        if not hwnd:
            break

        window_img = capture_window(hwnd)
        if flag == 1:
            button_lock_on(ed, window_img, end, hwnd)
            if ed.show:
                ed = real_area(ed, 'end')
                click_random_in_region(ed, now, 'end')
                flag = 2
        if flag == 2:
            button_lock_on(st, window_img, start, hwnd)
            if st.show:
                st = real_area(st, 'start')
                click_random_in_region(st, now, 'start')
                flag = 3
        if flag == 3:
            if match_template(window_img, pause, False)[0]:
                GLSCALE = bkp_scale
                return
            button_lock_on(ed, window_img, end, hwnd)
            if ed.show:
                ed = real_area(ed, 'end')
                click_random_in_region(ed, now, 'end')
                flag = 4
        if flag == 4 and match_template(window_img, pause, False)[0]:
            GLSCALE = bkp_scale
            return

def handle_man_pause(img):
    template = GLASSETS['ui_button'][0]['mannual_pause']
    end = GLASSETS['ui_button'][1]['mannual_pause']
    end: Button
    img = newcrop(img, end)
    mp_show = match_template(img, template)[0]
    return True if mp_show else False

def handle_buoy(hwnd, target='GOLD'):
    buoy_flag = GLASSETS['ui_element'][0]['buoy_flag']
    bu_bt = GLASSETS['ui_element'][1]
    bu_bt['buoy_button'] = Button()
    bu_bt['buoy_button'].img = GLASSETS['ui_element'][0]['buoy_button']

    BLUE = (0, 173, 255)
    PURPLE = (207, 81, 255)
    GOLD = (255, 195, 51)
    recorded = False

    def colorsimi(a, b):
        if type(a).__name__ == 'tuple':
            r1, g1, b1 = a
            r2, g2, b2 = b
            rs = abs(r1 - r2); gs = abs(g1 - g2); bs = abs(b1 - b2)
            for simi in [rs, gs, bs]:
                if simi > 10: return False
            return True
        return False

    while 1:
        window_img = capture_window(hwnd)

        if handle_man_pause(window_img): return True

        button_lock_on(bu_bt['buoy_button'], window_img, bu_bt['buoy_button'].img, hwnd)

        if bu_bt['buoy_button'].show:
            if not recorded:
                left = bu_bt['buoy_button'].top_left[0] - 50
                right = bu_bt['buoy_button'].top_left[0] + bu_bt['buoy_button'].width + 50
                bottom = win32gui.GetWindowRect(hwnd)[3] - win32gui.GetWindowRect(hwnd)[1]
                k = (left, 0, right, bottom)
                recorded = True
            window_img = window_img.crop(k)

            buoy_coor = match_template(window_img, buoy_flag)[0]
            pixel_1 = window_img.getpixel((buoy_coor[0] - 10, buoy_coor[1]))
            pixel_2 = window_img.getpixel((buoy_coor[0] - 10, buoy_coor[1] + 20))

            for i, color in enumerate([BLUE, PURPLE, GOLD]):
                if colorsimi(pixel_1, color): pixel_1 = ['BLUE', 'PURPLE', 'GOLD'][i]
                if colorsimi(pixel_2, color): pixel_2 = ['BLUE', 'PURPLE', 'GOLD'][i]

            buoy_color = pixel_1 if type(pixel_1).__name__ == 'str' else pixel_2

            if buoy_color == target:
                now = id_timer()
                print(f"target @{target} found, now execute press")
                newpress('space', now)
                break

            if buoy_color == 'GOLD' and buoy_coor[1] > k[3] / 2:
                print(f"@{target} not found, fallback to default target")
                target == 'GOLD'

def fishing():
    pass

def handle_loop(hwnd, target):
    now = id_timer()
    
    # start = GLASSETS['ui_button'][0]['start']
    # end = GLASSETS['ui_button'][0]['end']
    # begin_fish = GLASSETS['ui_button'][0]['begin_fish']
    # mannual_pause = GLASSETS['ui_button'][0]['mannual_pause']

    if not GLASSETS['ui_button'][1]:
        start = Button()
        end = Button()
        begin_fish = Button()
        mannual_pause = Button()
        pause = Button()

        sub_dict = GLASSETS['ui_button'][0]
        end.img, start.img, begin_fish.img, mannual_pause.img = tuple([sub_dict[key] for key in sub_dict.keys()])
        pause.img = GLASSETS['ui_element'][0].get('paused')
    else:
        sub_dict = GLASSETS['ui_button'][1]
        end, start, begin_fish, mannual_pause = tuple([sub_dict[key] for key in sub_dict.keys()])
        pause = GLASSETS['ui_element'][1].get('paused')

    flag = 1
    mp_flag = False
    
    def real_area(button: Button, sig: str):
        offset = 130 if sig == 'end' else (180 if sig == 'start' else 190) 
        button.width = 60 + offset
        return button
    
    while 1:
        if not hwnd:
            break
        
        window_img = capture_window(hwnd)

        if mp_flag:
            print("/////mannual pause detected. now quit script./////")
            return

        if flag == 1:
            button_lock_on(start, window_img, start.img, hwnd)
            if start.show:
                start = real_area(start, 'start')
                GLASSETS['ui_button'][1]['start'] = start
                click_random_in_region(start, now, 'start')
                flag = 2
                end.stable = False
                end.show = None
                continue
        if flag == 2:
            back = False
            if match_template(window_img, pause.img, False)[0]:
                newpress('esc', now)
                back = True

            button_lock_on(end, window_img, end.img, hwnd)
            button_lock_on(mannual_pause, window_img, mannual_pause.img, hwnd)

            if end.show:
                end = real_area(end, 'end')
                GLASSETS['ui_button'][1]['end'] = end
                GLASSETS['ui_button'][1]['mannual_pause'] = mannual_pause
                flag = 3

                if back: newpress('esc', now); continue
                click_random_in_region(end, now, 'end')
                continue
        if flag == 3:
            button_lock_on(begin_fish, window_img, begin_fish.img, hwnd)
            button_lock_on(pause, window_img, pause.img, hwnd)
            if pause.show:
                GLASSETS['ui_element'][1]['paused'] = pause
            if begin_fish.show:
                GLASSETS['ui_button'][1]['begin_fish'] = begin_fish
                newpress('space', now)
                flag = 4
                continue
        if flag == 4:
            mp_flag = handle_buoy(hwnd, target)
            if mp_flag: continue

            k = ['ui_element','blue_icon','yellow_icon']
            templates = [GLASSETS[key] for key in k]
            mp_flag = handle_fishing(hwnd, templates)
            if mp_flag: continue

            flag = 5
            end.stable = False
            end.show = None
            continue
        if flag == 5:
            button_lock_on(end, window_img, end.img, hwnd)
            if end.show:
                click_random_in_region(end, now, 'end')
                flag = 1


def handle_fishing(hwnd, templates, threshold=0.5):

    # def fl(file):
    #     return 'assets\\' + file + '.png'

    # mask_image = [
    #     Image.open(fl(img))
    #     for img in templates[0]
    # ]
    # icons = templates[1] + templates[2]
    # icon_image = [
    #     Image.open(fl(img))
    #     for img in icons
    # ]
    def ft(dic):
        return [dic[0][key] for key in dic[0].keys()]

    mask_image = ft(templates[0])
    icon_image = ft(templates[1]) + ft(templates[2])
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

    idfy_area = Button(); idfy_area.no_scale = False; idfy_area.img = mask_image[1]
    buffer_area = Button()
    pause = GLASSETS['ui_element'][1]['paused']; pause.no_scale = False
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

        if handle_man_pause(window_img): return True

        button_lock_on(pause, window_img, mask_image[0], hwnd)

        need_cv = cv_confirm(pause, need_cv, window_img, mask_image[0])

        if pause.show:
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
                        print(">>>>>>>>>>>>>>>>>Fishing Game End<<<<<<<<<<<<<<<<<")
                        flag = False
        else:
            if flag:
                print(">>>>>>>>>>>>>>>>>Fishing Game End<<<<<<<<<<<<<<<<<")
                return
            flag = False
            slowprt(now, 2, 10, f"Fishing Not Running")

def main():
    window_title = "NIKKE"
    # process_name = 'nikke.exe'
    ui_element = ['paused','click_area','end','buoy_button','buoy_flag']
    ui_button = ['end','start','begin_fish','mannual_pause']
    bar = ['R_0_t','R_1_t','SR_t','SSR_t']
    blue_icon = ['bleft','bright','bup','bdown']
    yellow_icon = ['yleft','yright','yup','ydown']
    global GLASSETS
    GLASSETS = {'ui_element':[ui_element], 'ui_button':[ui_button], 'bar':[bar], 'blue_icon':[blue_icon], 'yellow_icon':[yellow_icon]}
    assets_initial()
    # templates = [ui, blue_icon, yellow_icon]
    
    hwnd = find_window_by_title(window_title)
    # hwnd = find_window_by_process(process_name)
    if hwnd:
        print(f"Find Window: {hwnd}")
        # fishing(hwnd, templates)
        handle_loop(hwnd, 'GOLD')
    else:
        print("Game not running")

if __name__ == "__main__":
    main()