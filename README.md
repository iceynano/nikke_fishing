# How to use

**ONLY PC** ~~of course you can get mobile version, just boring modification~~

Fisrt check your settings page, it should looks like below: (just screen mode and graphic ratio!)

By the way, my desktop resolution is 1920x1080, so if you could just use the resolution👈

now script support other resolution, but **1080p** and settings below is still better, script now need time to initiate zoom factor to adapt window, so you may find first game would fail: it's ok, next game would be fine, or you can handle to exit fishing manually then reload.

![settings](https://github.com/iceynano/nikke_fishing/blob/main/settings.png)

**NOTICE: DO NOT MODIFY GAME RESOLUTION WHEN CODE RUNNING**

## Steps

1. if you want install manually, just running `pip install -r requirements.txt`. (if you use venv or other virtual env, I bet you are good at this)  

    if you use release package, just unzip it then double click `start script.bat`, it would auto install requirements to folder under script.

2. run the py file **AS ADMIN** if you install manually, I guess it would be fine if you install requirements properly.

3. go to the fishing area and click twice button, script would help you press ⬆⬆⬇⬇⬅⬅➡➡ (only this! do not expect more.)

4. you could just keep code running when in game, it would only press button when fishing game running, but remember quit script if you do not use it.

5. I guess nothing.

6. If you find code runs badly, I have left extra funcs in script, fork and modify code as you like, I rarely read issues. (For long response time, try moddify number in [L287](https://github.com/iceynano/nikke_fishing/blob/4973795cc146055ed41ca677107ed89e07f2e331/run.py#L287))

7. USE AT YOUR OWN RISK, if you got banned, I would be glad to advise you play games that don't constrain the use of scripts. 

**NOTICE: KEEP GAME RUNNING FOREGROUND AND WINDOW NO OBSTRUCTED WHEN YOU WANT IT FISHING**

## Dev branch feature

now script on dev branch has support semi-automatic click, you just need to click one fishing spot in game and wait script woeking, then click next fishing spot as work complete.  

however, it doesn't support scale yet, so it could only work at default setting above. by the way, the performance of script has improved, now fishing won't fail when start first time.

for user still in use main branch, comment out the code L273 would be helpful. if you want to experience dev branch, download dev branch source code and do mannual install with steps above, or just unzip it to cover files in release package folder, then running `python loop_run.py` in console.bat.

## Demo

https://github.com/iceynano/nikke_fishing/assets/34570144/fcb82298-8344-4e6b-832d-6bc271f0a970

## Demo in dev

https://github.com/iceynano/nikke_fishing/assets/34570144/f733f396-d5b3-4fd0-b5c8-68bdc0f7b3f5

