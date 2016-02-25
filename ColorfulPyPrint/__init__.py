# -*- coding: UTF-8 -*-
from __future__ import print_function

from ._Beep import beep
from ._ColorfulPrint import Fore
from ._logtime import logtime

__author__ = 'Aploium'
__version__ = '0.2.2'
__all__ = ['infoprint', 'dbgprint', 'warnprint', 'errprint', 'importantprint', 'apoutput_set_verbose_level',
           'apoutput_current_verbose_level']

PRINT_TYPE_INFO = 0
PRINT_TYPE_DEBUG = 1
PRINT_TYPE_WARN = 2
PRINT_TYPE_ERROR = 3
PRINT_TYPE_IMPORTANT_NOTICE = 4

TIME_LEVEL_NONE = 0
TIME_LEVEL_TIME = 1
TIME_LEVEL_FULL = 2

O_TIME_LEVEL = TIME_LEVEL_TIME
O_VERBOSE_LEVEL = 1


def _printr(output, other_inputs, printtype=PRINT_TYPE_INFO, timelevel=O_TIME_LEVEL, is_beep=False):
    # Time Section
    if timelevel == TIME_LEVEL_NONE:
        section_time = ''
    elif timelevel == TIME_LEVEL_FULL:
        section_time = '[' + logtime(is_print_date=True) + '] '
    else:
        section_time = '[' + logtime(is_print_date=False) + '] '

    # Type&Color Section
    if printtype == PRINT_TYPE_INFO:
        section_color = Fore.GREEN
        section_type = '[INFO] '
    elif printtype == PRINT_TYPE_DEBUG:
        section_color = Fore.LIGHTBLUE_EX
        section_type = '[DEBUG] '
    elif printtype == PRINT_TYPE_WARN:
        section_color = Fore.YELLOW
        section_type = '[WARNING] '
    elif printtype == PRINT_TYPE_ERROR:
        section_color = Fore.RED
        section_type = '[ERROR] '
    elif printtype == PRINT_TYPE_IMPORTANT_NOTICE:
        section_color = Fore.LIGHTMAGENTA_EX
        section_type = '[IMPORTANT] '
    else:
        section_color = ''
        section_type = ''

    # Finally Print
    print(section_color + section_time + section_type, end='')
    try:
        print(output, end='')
        if other_inputs:
            for item in other_inputs:
                print(' ', end='')
                print(item, end='')
    except Exception as e:
        print(Fore.RED + 'PRINT ERROR: ', e)
    print(Fore.RESET)
    if is_beep:
        try:
            beep()
        except:
            pass


def apoutput_set_verbose_level(verbose_level=1):
    global O_VERBOSE_LEVEL
    O_VERBOSE_LEVEL = verbose_level


def apoutput_current_verbose_level():
    global O_VERBOSE_LEVEL
    return O_VERBOSE_LEVEL


def _handle_kwargs(v, timelevel, is_beep, kwargs):
    if 'v' not in kwargs:
        kwargs['v'] = v
    if 'timelevel' not in kwargs:
        kwargs['timelevel'] = timelevel
    if 'is_beep' not in kwargs:
        kwargs['is_beep'] = is_beep
    return kwargs['v'], kwargs['timelevel'], kwargs['is_beep']


def infoprint(output, *other_inputs, **kwargs):
    v, timelevel, is_beep = _handle_kwargs(1, O_TIME_LEVEL, False, kwargs)
    if v <= O_VERBOSE_LEVEL:
        _printr(output, other_inputs, printtype=PRINT_TYPE_INFO, timelevel=timelevel, is_beep=is_beep)


def dbgprint(output, *other_inputs, **kwargs):
    v, timelevel, is_beep = _handle_kwargs(3, O_TIME_LEVEL, False, kwargs)
    if v <= O_VERBOSE_LEVEL:
        _printr(output, other_inputs, printtype=PRINT_TYPE_DEBUG, timelevel=timelevel, is_beep=is_beep)


def warnprint(output, *other_inputs, **kwargs):
    v, timelevel, is_beep = _handle_kwargs(2, O_TIME_LEVEL, False, kwargs)
    if v <= O_VERBOSE_LEVEL:
        _printr(output, other_inputs, printtype=PRINT_TYPE_WARN, timelevel=timelevel, is_beep=is_beep)


def errprint(output, *other_inputs, **kwargs):
    v, timelevel, is_beep = _handle_kwargs(0, O_TIME_LEVEL, False, kwargs)
    if v <= O_VERBOSE_LEVEL:
        _printr(output, other_inputs, printtype=PRINT_TYPE_ERROR, timelevel=timelevel, is_beep=is_beep)


def importantprint(output, *other_inputs, **kwargs):
    v, timelevel, is_beep = _handle_kwargs(0, O_TIME_LEVEL, True, kwargs)
    if v <= O_VERBOSE_LEVEL:
        _printr(output, other_inputs, printtype=PRINT_TYPE_IMPORTANT_NOTICE, timelevel=timelevel, is_beep=is_beep)
