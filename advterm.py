#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Terminal like input, separating input line from scrolling output window
"""

import curses
import sys

try: 
# windows or dos 
    import msvcrt
    _use_msvc = True 
except ImportError: 
# assume unix 
    import tty, termios 
    _use_msvc = False 
    
_line = str()
_line_cb = None
_in_win = None
_out_win = None
_echo = None
_prefix = str()
_initialText = None
_running = True

def output(line, attr=0):
    ''' outputs text to log window '''
    if _out_win != None:
        _out_win.addstr(line, attr)
        _out_win.refresh()
        # needed to get cursor back on track
        _in_win.refresh()
    else:
        print(line)

def inputPrefix(prefix):
    ''' defines an input prefix '''
    global _prefix
    _prefix = prefix
    if _in_win != None:
        _in_win.clear()
        _in_win.addstr(_prefix, curses.A_BOLD)
        _in_win.addstr(_line)
        _in_win.refresh()

def sleep(secs):
    ''' sleeps given secs '''
    curses.napms(int(secs*1000))
    
def kill():
    ''' Stops input loop '''
    global _running
    _running = False
    
def getkey(): 
    ''' unix style get keypress in raw manner '''
    file = sys.stdin.fileno() 
    mode = termios.tcgetattr(file) 
    try: 
        tty.setraw(file, termios.TCSANOW) 
        ch = sys.stdin.read(1) 
    finally: 
        termios.tcsetattr(file, termios.TCSANOW, mode) 
    return ch 

def clear():
    ''' Clear windows '''
    curses.curs_set(1)
    curses.noecho()
    _in_win.clear()
    _in_win.addstr(_prefix, curses.A_BOLD)
    _in_win.addstr(_line)
    _out_win.clear()
    _out_win.refresh()
    _in_win.refresh()

def inputLoop(scr):
    ''' term setup and input loop '''
    
    global _in_win, _out_win, _line, _running
    
    scr.nodelay(0)
    curses.curs_set(1)
    curses.noecho()
    
    max_y, max_x = scr.getmaxyx()

    cy = max_y - 1
    
    _out_win = curses.newwin(max_y - 1, max_x, 0, 0)
    _out_win.scrollok(True)
    _out_win.setscrreg(0, max_y - 2)
    
    _in_win = curses.newwin(1, max_x, max_y - 1, 0)
    _in_win.clear()
    _in_win.addstr(_prefix, curses.A_BOLD)

    if _initialText != None:
        _out_win.addstr(_initialText, curses.A_BOLD)

    scr.move(cy, 0)
    
    _out_win.refresh()
    _in_win.refresh()

    
    # Do until exit
    _line = str()
    _running = True
    while _running:
        # Get input from user and flush the input buffer
        max_y, max_x = scr.getmaxyx()
        if _use_msvc:
            ch = msvcrt.getch()
        else:
            ch = getkey()
        
        if ord(ch) == 27:       # ESC
            _in_win.clear()
            _line = str()
        elif ord(ch) == 13:     # Return
            line = _line
            _line = str()
            if _echo:
                _out_win.addstr(line + "\n", curses.A_BOLD)
            _in_win.clear()
            _in_win.addstr(_prefix, curses.A_BOLD)
            _line_cb(line)
                
        elif ord(ch) == 127:    # Backspace
            if len(_line) >= 1:
                _line = _line[:-1]
                _in_win.clear()
                _in_win.addstr(_prefix, curses.A_BOLD)
                _in_win.addstr(_line)
                _in_win.move(0, len(_prefix + _line))
        elif ord(ch) == 3:      # Ctrl+C
            break
        elif ord(ch) < 32:      # crap characters
            pass
        else:
            if len(_prefix + _line) < max_x - 1: 
                _line += ch
                _in_win.clear()
                _in_win.addstr(_prefix, curses.A_BOLD)
                _in_win.addstr(_line)
                _in_win.move(0, len(_prefix + _line))
            

        _out_win.refresh()
        _in_win.refresh()

def startInput(linecallback, echo=False, initialText=None):
    ''' Start getting input until Ctrl+C is pressed '''
    global _line_cb, _echo, _initialText
    _line_cb = linecallback
    _echo = echo
    _initialText = initialText
    curses.wrapper(inputLoop)
