# Based on code from https://github.com/WereCatf/pytimedinput, with the original author claiming this license:
'''MIT License

Copyright (c) 2020 WereCatf

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import sys
import time
from typing import Tuple, Union

if(sys.platform == "win32"):
    import msvcrt
    import ctypes
    from ctypes import wintypes
    def checkStdin():
        return msvcrt.kbhit()
    def readStdin():
        return msvcrt.getwch()
    def getStdoutSettings():
        savedConsoleSettings = wintypes.DWORD()
        kernel32 = ctypes.windll.kernel32
        # The Windows standard handle -11 is stdout
        kernel32.GetConsoleMode(kernel32.GetStdHandle(-11), ctypes.byref(savedConsoleSettings))
        return savedConsoleSettings
    def setStdoutSettings(savedConsoleSettings):
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), savedConsoleSettings)
    def enableStdoutAnsiEscape():
        kernel32 = ctypes.windll.kernel32
        # Enable ANSI escape sequence parsing
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
else:
    import select
    import tty
    import termios
    def checkStdin():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    def readStdin():
        return sys.stdin.read(1)
    def getStdoutSettings():
        return termios.tcgetattr(sys.stdin)
    def setStdoutSettings(savedConsoleSettings):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, savedConsoleSettings)
    def enableStdoutAnsiEscape():
        # Should be enabled by default under Linux (and OSX?), just set cbreak-mode
        tty.setcbreak(sys.stdin.fileno(), termios.TCSADRAIN)


def GetKey(timeout: int, allowCharacters: str = "") -> str:
    """Wait for the user to press a single key out of an optional list of allowed ones.

    Args:
        timeout (int, required): How many seconds to wait for input.
        allowCharacters (str, optional): Which characters the user is allowed to enter. Defaults to "", ie. any character.

    Returns:
        str: Which key the user pressed, None if the input timed out.
    """

    if(not sys.__stdin__.isatty()):
        raise RuntimeError("timedKey() requires an interactive shell, cannot continue.")

    savedConsoleSettings = getStdoutSettings()
    enableStdoutAnsiEscape()

    timeStart = time.time()

    user_input = None
    # Do a try/finally here, so we always restore savedConsoleSettings.
    # Otherwise the user terminal get messed up if the user does ctrl-c
    # to break, and characters that are typed do not appear after we exit.
    try:
        # This appears to busy wait!  Seems like it should do a sleep,
        # even if only briefly, and only if timeout is large!
        while(True):
            time_elapsed = time.time() - timeStart
            if(time_elapsed >= timeout):
                break
            time_remaining = timeout - time_elapsed
            if time_remaining > 0.010:
                time.sleep(min(time_remaining * 0.5, 0.1))
            if(checkStdin()):
                c = readStdin()
                if(len(allowCharacters) == 0 or c in allowCharacters):
                    user_input = c
                    break
    finally:
        setStdoutSettings(savedConsoleSettings)
    return user_input
