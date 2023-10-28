#!/usr/bin/env python3

"""
Generates a whole keyboard's worth of keycaps (and a few extras). Best way
to use this script is from within the `keycap_playground` directory.

.. bash::

    $ ./scripts/ergodox_ft_full.py --out /tmp/output_dir

.. note::

    Make sure you add the correct path to colorscad.sh if you want
    multi-material keycaps!

Fonts used by this script:
--------------------------

 * Gotham Rounded:style=Bold
 * Aharoni
 * Font Awesome 6 Free:style=Solid
"""

# stdlib imports
import os, sys
from pathlib import Path
import json
import argparse
from copy import deepcopy
from subprocess import getstatusoutput
import asyncio
import subprocess
from functools import partial
from typing import Sequence, Any
from asyncio import ensure_future
# 3rd party stuff
from colorama import Fore, Back, Style
from colorama import init as color_init
color_init()
# Our own stuff
from keycap import Keycap

# Change these to the correct paths in your environment:
OPENSCAD_PATH = Path("deps/OpenSCAD-2023.09.30.ai16393-x86_64.AppImage")
COLORSCAD_PATH = Path("deps/colorscad/colorscad.sh")

KEY_UNIT = 19.05 # Square that makes up the entire space of a key
BETWEENSPACE = 0.8 # Space between keycaps
FILE_TYPE = "3mf" # 3mf or stl

# BEGIN Async stuff
# Mostly copied from https://gist.github.com/anti1869/e02c4212ce16286ea40f
COMMANDS = []

#MAX_RUNNERS = 8
#SEM = asyncio.Semaphore(MAX_RUNNERS)

def run_command(cmd: str) -> str:
    """
    Run prepared behave command in shell and return its output.
    :param cmd: Well-formed behave command to run.
    :return: Command output as string.
    """
    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
            cwd=os.getcwd(),
        )

    except subprocess.CalledProcessError as e:
        output = e.output

    return output


# @asyncio.coroutine
async def run_command_on_loop(loop: asyncio.AbstractEventLoop, command: str) -> bool:
    """
    Run test for one particular feature, check its result and return report.
    :param loop: Loop to use.
    :param command: Command to run.
    :return: Result of the command.
    """
    async with SEM:
        runner = partial(run_command, command)
        output = await loop.run_in_executor(None, runner)
        await asyncio.sleep(1)  # Slowing a bit for demonstration purposes
        return output


@asyncio.coroutine
def run_all_commands(command_list: Sequence[str] = COMMANDS) -> None:
    """
    Run all commands in a list
    :param command_list: List of commands to run.
    """
    loop = asyncio.get_event_loop()
    fs = [run_command_on_loop(loop, command) for command in command_list]
    for f in asyncio.as_completed(fs):
        result = yield from f
        ensure_future(process_result(result))


@asyncio.coroutine
def process_result(result: Any):
    """
    Do something useful with result of the commands
    """
    print(result)

# END Async stuff

class ergodox_ft_base(Keycap):
    """
    Base keycap definitions for the riskeycap profile + our personal prefs.
    """
    def __init__(self, homing_dot=False, **kwargs):
        super().__init__(**kwargs,
            openscad_path=OPENSCAD_PATH,
            colorscad_path=COLORSCAD_PATH)
        self.render = ["keycap", "stem"]
        self.file_type = FILE_TYPE
        self.key_profile = "riskeycap"
        self.key_rotation = [110.1,0,0]
        self.wall_thickness = 0.45*2.7
        self.uniform_wall_thickness = True
        self.dish_thickness = 1.0 # Note: Not actually used
        self.dish_corner_fn = 40 # Save some rendering time
        self.polygon_layers = 4  # Ditto
        self.stem_height = 4
        self.stem_type = "round_cherry"
        self.stem_inset = -0.5
        self.stem_walls_inset = 0
        self.stem_inside_tolerance = 0.15
        self.stem_side_supports = [0,0,1,0]
        self.stem_locations = [[0,0,0]]
        # Because we do strange things we need legends bigger on the Z
        self.scale = [
            [1,1,3],
            [1,1,3],
        ]
        self.fonts = [
            "Gotham Rounded:style=Bold",
            "Gotham Rounded:style=Bold",
        ]
        self.font_sizes = [
            4.5, # Center
            3.5, # Front
        ]
        self.trans = [
            [0,-2.6,0], # Center
            [0,-2,2], # Front
        ]
        # Legend rotation
        self.rotation = [
            [-20,0,0], # Center
            [68,0,0], # Front
        ]
        # Homing dot (set homing_dot=True to enable)
        if homing_dot:
            self.homing_dot_length = 1.5
            self.homing_dot_width = 1.5
            self.homing_dot_x = 0
            self.homing_dot_y = -3
            self.homing_dot_z = -0.45
        self.postinit(**kwargs)

class ergodox_ft_wpm(ergodox_ft_base):
    """
    Same as regular but with smaller front legends
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[1] = 2

class ergodox_ft_icons(ergodox_ft_base):
    """
    For 1U with only icons
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fonts = [
            "Font Awesome 6 Free:style=Solid",
            "Font Awesome 6 Free:style=Solid",
        ]
        self.font_sizes = [
            5,
            3.9,
        ]

class ergodox_ft_icons_90top(ergodox_ft_icons):
    """
    For 1U with only icons, top icon rotated 90 degrees
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.rotation2 = [self.rotation[0], [0,0,0]]
        self.rotation[0] = [0,0,90]
        self.trans2 = [self.trans[0], [0,0,0]]
        self.trans[0] = [0,0,0]
        self.postinit(**kwargs_copy)

class ergodox_ft_pgupdn(ergodox_ft_icons):
    """
    For PgUp/PgDn (only icons, front rotated 90 degrees and slightly adjusted)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.font_sizes[1] = 3.7
        self.rotation2 = [[0,0,0], self.rotation[1]]
        self.rotation[1] = [0,0,90]
        self.trans2 = [[0,0,0], [0,-2,1.6]]
        self.trans[1] = [0,0,0]
        self.postinit(**kwargs_copy)

class ergodox_ft_front_icon(ergodox_ft_base):
    """
    For 1U with icon fronts (media keys, etc.)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fonts[1] = "Font Awesome 6 Free:style=Solid"
        self.font_sizes[1] = 3.9

class ergodox_ft_text(ergodox_ft_base):
    """
    Ctrl, Del, etc. need to be downsized a smidge.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.font_sizes[0] = 4
        self.postinit(**kwargs_copy)

class ergodox_ft_gem(ergodox_ft_base):
    """
    Same as base but in GEM profile
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.key_profile = "gem"
        self.key_rotation = [108.6,0,0]

class ergodox_ft_gem_front_icon(ergodox_ft_front_icon):
    """
    1U with icon front, but in GEM profile
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.key_profile = "gem"
        self.key_rotation = [108.6,0,0]

class ergodox_ft_multi(ergodox_ft_base):
    """
    For number row keys and others with multiple legends... ,./;'[]
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fonts = [
            "Gotham Rounded:style=Bold", # Left
            "Gotham Rounded:style=Bold", # Center
            "Gotham Rounded:style=Bold", # Right
            "Gotham Rounded:style=Bold", # Front
        ]
        self.font_sizes = [
            4.5, # Left
            4.5, # Center
            4.5, # Right
            3.5, # Front legend
        ]
        self.trans = [
            [-2.6,-2.6,0], # Left
            [0,-2.6,0], # Center
            [2.6,-2.6,0], # Right
            [0,-2,2], # F-key
        ]
        self.rotation = [
            [-20,0,0],
            [-20,0,0],
            [-20,0,0],
            [68,0,0],
        ]
        self.scale = [
            [1,1,3],
            [1,1,3],
            [1,1,3],
            [1,1,3],
        ]
        self.postinit(**kwargs)

class ergodox_ft_tilde(ergodox_ft_multi):
    """
    Tilde needs some changes because by default it's too small,
    and it has an icon front
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[0] = 6.5 # ` symbol
        self.font_sizes[2] = 5.5 # ~ symbol
        self.fonts[3] = "Font Awesome 6 Free:style=Solid"

class ergodox_ft_2(ergodox_ft_multi):
    """
    2 needs some changes based on the @ symbol
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale[2] = [0.85,1,1] # Squash it a bit

class ergodox_ft_3(ergodox_ft_multi):
    """
    3 needs some changes based on the # symbol (slightly too big)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[2] = 4.5 # # symbol

class ergodox_ft_5(ergodox_ft_multi):
    """
    5 needs some changes based on the % symbol (too big, too close to bar)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[2] = 4 # % symbol

class ergodox_ft_6(ergodox_ft_multi):
    """
    6 needs some changes based on the ^ symbol (too small, should be up high),
    also icon front
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[2] = 5.8 # ^ symbol
        self.trans[2] = [2.6,4.1,0]
        self.fonts[3] = "Font Awesome 6 Free:style=Solid"

class ergodox_ft_7(ergodox_ft_multi):
    """
    7 needs some changes based on the & symbol (it's too big)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[2] = 4.5 # & symbol

class ergodox_ft_8(ergodox_ft_multi):
    """
    8 needs some changes based on the tiny * symbol
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[2] = 8.5 # * symbol

class ergodox_ft_0(ergodox_ft_multi):
    """
    0 also needs some changes based on the tiny * symbol
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_sizes[3] = 6.6 # * symbol

class ergodox_ft_slash(ergodox_ft_multi):
    """
    /?, needs rotated Font Awesome front
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.fonts[3] = "Font Awesome 6 Free:style=Solid"
        self.font_sizes[3] = 3.9
        # Rotate front legend 90 degrees clockwise
        self.rotation2 = [[0,0,0], [0,0,0], [0,0,0], self.rotation[3]]
        self.rotation[3] = [0,0,-90]
        self.trans2 = [[0,0,0], [0,0,0], [0,0,0], self.trans[3]]
        self.trans[3] = [0,0,0]
        self.postinit(**kwargs_copy)

class ergodox_ft_1_5U(ergodox_ft_multi):
    """
    1.5U (with multiple legends)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs)
        self.key_length = KEY_UNIT*1.5-BETWEENSPACE
        self.key_rotation = [109.335,0,0]
        self.postinit(**kwargs_copy)

class ergodox_ft_1_5U_front_icon(ergodox_ft_1_5U):
    """
    For 1.5U with icon fronts (Esc, =+ and \|)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fonts[3] = "Font Awesome 6 Free:style=Solid"
        self.font_sizes[3] = 3.9

class ergodox_ft_dash(ergodox_ft_1_5U):
    """
    The dash (-) is fine but the underscore (_) needs minor repositioning.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trans[2] = [2.8,1.1,0] # _ needs to go down and to the right a bit
        self.scale[2] = [0.8,1,3] # Also needs to be squished a bit

class ergodox_ft_semicolon(ergodox_ft_1_5U):
    """
    The semicolon ends up being slightly higher than the colon but it looks
    better if the top dot in both is aligned.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trans[0] = [-2.6,2.1,0]
        self.trans[2] = [2.6,2.6,0]

class ergodox_ft_1_5UV(ergodox_ft_base):
    """
    The base for vertical 1.5U keycaps.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.key_width = KEY_UNIT*1.5-BETWEENSPACE
        self.key_rotation = [110.095,0,0]
        self.trans[1] = [0,0,-0.65]
        self.postinit(**kwargs_copy)

class ergodox_ft_lbracket(ergodox_ft_multi):
    """
    1.5U vertical left bracket, needs Font Awesome front
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.key_width = KEY_UNIT*1.5-BETWEENSPACE
        self.key_rotation = [110.095,0,0]
        self.fonts[3] = "Font Awesome 6 Free:style=Solid"
        self.font_sizes[3] = 3.9
        self.trans[3] = [0,0,-0.65]
        self.postinit(**kwargs_copy)

class ergodox_ft_rbracket(ergodox_ft_lbracket):
    """
    1.5U vertical right bracket, needs rotated Font Awesome front
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        # Rotate front legend 90 degrees clockwise
        self.rotation2 = [[0,0,0], [0,0,0], [0,0,0], self.rotation[3]]
        self.rotation[3] = [0,0,-90]
        self.trans2 = [[0,0,0], [0,0,0], [0,0,0], self.trans[3]]
        self.trans[3] = [0,0,0]
        self.postinit(**kwargs_copy)

class ergodox_ft_2UV_icon(ergodox_ft_base):
    """
    The base for 2U vertical keys with icon legends (Enter and Backspace)
    Hackishly using a rotated horizontal 2U key due to a stem support bug
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.key_length = KEY_UNIT*2-BETWEENSPACE
        self.key_rotation = [0,-110.095,90]
        self.stem_locations = [[0,0,0], [12,0,0], [-12,0,0]]
        self.rotation2 = self.rotation
        self.rotation = [[0,0,-90]]
        self.trans, self.trans2 = self.trans2, self.trans
        self.trans2[1] = [0,0,-2.8]
        self.fonts = ["Font Awesome 6 Free:style=Solid"]
        self.font_sizes = [5]
        self.stem_side_supports = [1,0,0,0]
        self.postinit(**kwargs_copy)

class ergodox_ft_enter(ergodox_ft_2UV_icon):
    """
    Enter key needs its icon rotated more
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        # Rotate "turn-down" 90 degrees further clockwise
        self.rotation = [[0,0,180]]
        self.postinit(**kwargs_copy)

class ergodox_ft_space(ergodox_ft_2UV_icon):
    """
    Using a rotated horizontal 2U key gives a "spacier" top surface
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs_copy = deepcopy(kwargs) # Because self.trans[0] updates in place
        self.key_length = KEY_UNIT*2-BETWEENSPACE
        self.dish_invert = True
        self.use_colorscad = False
        self.key_rotation = [0,-113.651,90]
        self.polygon_layers = 16 # For a smoother top
        self.postinit(**kwargs_copy)

KEYCAPS = [
    # Row 1
    ergodox_ft_1_5U_front_icon(name="l_esc", legends=[" ", "Esc", "", "\uf0e7"]),
    ergodox_ft_multi(name="l_1", legends=["1", "", "!", "F1"]),
    ergodox_ft_2(name="l_2", legends=["2", "", "@", "F2"]),
    ergodox_ft_3(name="l_3", legends=["3", "", "#", "F3"]),
    ergodox_ft_multi(name="l_4", legends=["4", "", "$", "F4"]),
    ergodox_ft_5(name="l_5", legends=["5", "", "%", "F5"]),
    ergodox_ft_tilde(name="l_tilde", legends=["`", "", "~", "\uf030"]),

    ergodox_ft_text(name="r_del", legends=["Del", "Ins"]),
    ergodox_ft_6(name="r_6", legends=["6", "", "^", "# \uf023"]),
    ergodox_ft_7(name="r_7", legends=["7", "", "&", "7"]),
    ergodox_ft_8(name="r_8", legends=["8", "", "*", "8"]),
    ergodox_ft_multi(name="r_9", legends=["9", "", "(", "9"]),
    ergodox_ft_0(name="r_0", legends=["0", "", ")", "*"]),
    ergodox_ft_1_5U_front_icon(name="r_equal", legends=["=", "", "+", "\uf0e7"]),

    # Row 2
    ergodox_ft_1_5U(name="l_tab", legends=[" ", "Tab", ""]),
    ergodox_ft_base(name="l_Q", legends=["Q", "F6"]),
    ergodox_ft_base(name="l_W", legends=["W", "F7"]),
    ergodox_ft_gem(name="l_W_gamer", legends=["W", "F7"]),
    ergodox_ft_base(name="l_E", legends=["E", "F8"]),
    ergodox_ft_base(name="l_R", legends=["R", "F9"]),
    ergodox_ft_base(name="l_T", legends=["T", "F10"]),
    ergodox_ft_lbracket(name="l_bracket", legends=["[", "", "{", "\uf55a"]),

    ergodox_ft_rbracket(name="r_bracket", legends=["]", "", "}", "\uf3be"]),
    ergodox_ft_wpm(name="r_Y", legends=["Y", "WPM 0"],),
    ergodox_ft_base(name="r_U", legends=["U", "4"]),
    ergodox_ft_base(name="r_I", legends=["I", "5"]),
    ergodox_ft_base(name="r_O", legends=["O", "6"]),
    ergodox_ft_base(name="r_P", legends=["P", "+"]),
    ergodox_ft_dash(name="r_dash", legends=["-", "", "_", "-"]),

    # Row 3
    ergodox_ft_1_5U_front_icon(name="l_bslash",
                               legends=["\\", "", "|", "\uf0a1 \uf023"]),
    ergodox_ft_front_icon(name="l_A", legends=["A", "\uf048"]),
    ergodox_ft_front_icon(name="l_S", legends=["S", "\uf027"]),
    ergodox_ft_front_icon(name="l_D", legends=["D", "\uf028"]),
    ergodox_ft_gem_front_icon(name="l_A_gamer", legends=["A", "\uf048"]),
    ergodox_ft_gem_front_icon(name="l_S_gamer", legends=["S", "\uf027"]),
    ergodox_ft_gem_front_icon(name="l_D_gamer", legends=["D", "\uf028"]),
    ergodox_ft_front_icon(name="l_F", legends=["F", "\uf051"],
                          homing_dot=True),
    ergodox_ft_front_icon(name="l_G", legends=["G", "\uf04b \uf04c"]),

    ergodox_ft_wpm(name="r_H", legends=["H", "WPM ^"]),
    ergodox_ft_base(name="r_J", legends=["J", "1"], homing_dot=True),
    ergodox_ft_base(name="r_K", legends=["K", "2"]),
    ergodox_ft_base(name="r_L", legends=["L", "3"]),
    ergodox_ft_semicolon(name="r_semicolon", legends=[";", "", ":", "="]),
    #ergodox_ft_1_5U(name="r_basic_quote", legends=["'", "", '"', "/"]),
    ergodox_ft_1_5U(name="r_quote", legends=["\u2019", "", "\u201d", "/"]),

    # Row 4
    ergodox_ft_1_5U(name="l_shift", legends=[" ", "Shift", "", ""]),
    ergodox_ft_front_icon(name="l_Z_bl", legends=["Z", "\uf0eb \uf205"]),
    ergodox_ft_front_icon(name="l_X_bl", legends=["X", "\uf0eb -"]),
    ergodox_ft_front_icon(name="l_C_bl", legends=["C", "\uf0eb +"]),
    ergodox_ft_front_icon(name="l_V_bl", legends=["V", "\uf0eb \uf2f1"]),
    ergodox_ft_base(name="l_Z", legends=["Z"]), # For non-backlit keyboards
    ergodox_ft_base(name="l_X", legends=["X"]), # For non-backlit keyboards
    ergodox_ft_base(name="l_C", legends=["C"]), # For non-backlit keyboards
    ergodox_ft_base(name="l_V", legends=["V"]), # For non-backlit keyboards
    ergodox_ft_base(name="l_B", legends=["B"]),
    ergodox_ft_1_5UV(name="l_fn", legends=["Fn"]),

    ergodox_ft_1_5UV(name="r_fn", legends=["Fn"]),
    ergodox_ft_wpm(name="r_N", legends=["N", "WPM"]),
    ergodox_ft_base(name="r_M", legends=["M", "0"]),
    ergodox_ft_multi(name="r_comma", legends=[",", "", "<", ","]),
    ergodox_ft_multi(name="r_period", legends=[".", "", ">", "."]),
    ergodox_ft_slash(name="r_slash", legends=["/", "", "?", "\uf149"]),
    ergodox_ft_1_5U(name="r_shift", legends=[" ", "Shift", "", ""]),

    # Row 5
    ergodox_ft_text(name="l_ctrl", legends=["Ctrl"]),
    ergodox_ft_front_icon(name="l_F3", legends=["F3", "\uf0d9"]),
    ergodox_ft_front_icon(name="l_F5", legends=["F5", "\uf0d7"]),
    ergodox_ft_front_icon(name="l_F11", legends=["F11", "\uf0d8"]),
    ergodox_ft_front_icon(name="l_F12", legends=["F12", "\uf0da"]),

    ergodox_ft_icons(name="r_left", legends=["\uf0d9"]),
    ergodox_ft_icons(name="r_down", legends=["\uf0d7"]),
    ergodox_ft_icons(name="r_up", legends=["\uf0d8"]),
    ergodox_ft_icons(name="r_right", legends=["\uf0da"]),
    ergodox_ft_text(name="r_ctrl", legends=["Ctrl"]),

    # Left thumb cluster
    ergodox_ft_pgupdn(name="l_pgup", legends=["\uf574", "\ue4c2"]),
    ergodox_ft_pgupdn(name="l_pgdn", legends=["\uf56d", "\ue4b8"]),
    ergodox_ft_space(name="l_space"),
    ergodox_ft_enter(name="l_enter", legends=["\uf3be"]),
    ergodox_ft_icons_90top(name="l_super", legends=["\uf197", "\uf0c9"]),
    ergodox_ft_text(name="l_alt", legends=["Alt"]),

    # Right thumb cluster
    ergodox_ft_icons_90top(name="r_home", legends=["\ue4c2", "\uf574"]),
    ergodox_ft_icons_90top(name="r_end", legends=["\ue4b8", "\uf56d"]),
    ergodox_ft_2UV_icon(name="r_backspace", legends=["\uf55a"]),
    ergodox_ft_space(name="r_space"),
    ergodox_ft_icons(name="r_compose", legends=["\uf5ad"],),
    ergodox_ft_text(name="r_alt", legends=["AltGr"], font_sizes=[3]),
]

def print_keycaps():
    """
    Prints the names of all keycaps in KEYCAPS.
    """
    print(Style.BRIGHT +
          f"Here's all the keycaps we can render:\n" + Style.RESET_ALL)
    keycap_names = ", ".join(a.name for a in KEYCAPS)
    print(f"{keycap_names}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render a full set of ergodox_ft keycaps.")
    parser.add_argument('-o', '--out',
        metavar='<filepath>', type=str, default=".",
        help='Where the generated files will go.')
    parser.add_argument('-j', '--jobs',
        metavar='<jobs>', type=int, default=8,
        help='How many simultaneous renders are allowed.')
    parser.add_argument('-f', '--force',
        required=False, action='store_true',
        help='Forcibly re-render keycaps even if they already exist.')
    parser.add_argument('-s', '--skip-colorscad',
        required=False, action='store_true',
        help='Avoid rendering with colorscad even if it is available (quicker, useful for testing)')
    parser.add_argument('-t', '--transparent',
        required=False, action='store_true',
        help='Render stem in legend color (for shine-through keycaps)')
    parser.add_argument('-l', '--legends',
        required=False, action='store_true',
        help=f'If True, generate a separate set of stl files for legends.')
    parser.add_argument('-k', '--keycaps',
        required=False, action='store_true',
        help='If True, prints out the names of all keycaps we can render.')
    parser.add_argument('names',
        nargs='*', metavar="name",
        help='Optional name of specific keycap you wish to render')
    args = parser.parse_args()
    SEM = asyncio.Semaphore(args.jobs)
    if len(sys.argv) == 1:
        parser.print_help()
        print("")
        print_keycaps()
        sys.exit(1)
    if args.keycaps:
        print_keycaps()
        sys.exit(1)
    if not os.path.exists(args.out):
        print(Style.BRIGHT +
              f"Output path, '{args.out}' does not exist; making it..."
              + Style.RESET_ALL)
        os.mkdir(args.out)
    print(Style.BRIGHT + f"Outputting to: {args.out}" + Style.RESET_ALL)
    if args.names: # Just render the specified keycaps
        matched = False
        for name in args.names:
            for keycap in KEYCAPS:
                if keycap.name.lower() == name.lower():
                    keycap.output_path = f"{args.out}"
                    matched = True
                    exists = False
                    if not args.force:
                        if os.path.exists(f"{args.out}/{keycap.name}.{keycap.file_type}"):
                            print(Style.BRIGHT +
                                f"{args.out}/{keycap.name}.{keycap.file_type} exists; "
                                f"skipping..."
                                + Style.RESET_ALL)
                            exists = True
                    if args.skip_colorscad:
                        keycap.use_colorscad = False
                    if args.transparent:
                        keycap.stem_color = "#505050"
                    if not exists:
                        print(Style.BRIGHT +
                            f"Rendering {args.out}/{keycap.name}.{keycap.file_type}..."
                            + Style.RESET_ALL)
                        print(keycap)
                        COMMANDS.append(str(keycap))
                    if args.legends:
                        keycap.name = f"{keycap.name}_legends"
                        # Change it to .stl since PrusaSlicer doesn't like .3mf
                        # for "parts" for unknown reasons...
                        keycap.file_type = "stl"
                        if os.path.exists(f"{args.out}/{keycap.name}.{keycap.file_type}"):
                            print(Style.BRIGHT +
                                f"{args.out}/{keycap.name}.{keycap.file_type} exists; "
                                f"skipping..."
                                + Style.RESET_ALL)
                            continue
                        print(Style.BRIGHT +
                            f"Rendering {args.out}/{keycap.name}.{keycap.file_type}..."
                            + Style.RESET_ALL)
                        print(keycap)
                        COMMANDS.append(str(keycap))
        if not matched:
            print(f"Cound not find a keycap named {name}")
    else:
        # First render the keycaps
        for keycap in KEYCAPS:
            keycap.output_path = f"{args.out}"
            if not args.force:
                if os.path.exists(f"{args.out}/{keycap.name}.{keycap.file_type}"):
                    print(Style.BRIGHT +
                        f"{args.out}/{keycap.name}.{keycap.file_type} exists; skipping..."
                        + Style.RESET_ALL)
                    continue
            if args.skip_colorscad:
                keycap.use_colorscad = False
            if args.transparent:
                keycap.stem_color = "#505050"
            print(Style.BRIGHT +
                f"Rendering {args.out}/{keycap.name}.{keycap.file_type}..."
                + Style.RESET_ALL)
            print(keycap)
            COMMANDS.append(str(keycap))
        # Next render the legends (for multi-material, non-transparent legends)
        if args.legends:
            for legend in KEYCAPS:
                if legend.legends == [""]:
                    continue # No actual legends
                legend.name = f"{legend.name}_legends"
                legend.output_path = f"{args.out}"
                legend.render = ["legends"]
                # Change it to .stl since PrusaSlicer doesn't like .3mf
                # for "parts" for unknown reasons...
                legend.file_type = "stl"
                if not args.force:
                    if os.path.exists(f"{args.out}/{legend.name}.{legend.file_type}"):
                        print(Style.BRIGHT +
                            f"{args.out}/{legend.name}.{legend.file_type} exists; skipping..."
                            + Style.RESET_ALL)
                        continue
                if args.skip_colorscad:
                    legend.use_colorscad = False
                if args.transparent:
                    legend.stem_color = "#505050"
                print(Style.BRIGHT +
                    f"Rendering {args.out}/{legend.name}.{legend.file_type}..."
                    + Style.RESET_ALL)
                print(legend)
                COMMANDS.append(str(legend))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_all_commands())
