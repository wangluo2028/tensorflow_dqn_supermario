#!/usr/bin/env python
__author__ = 'justinarmstrong'

"""
This is an attempt to recreate the first level of
Super Mario Bros for the NES.
"""

import sys
import pygame as pg
from data.main import main
from data.env import Env
import cProfile


if __name__=='__main__':
    env = Env()
    main(env)
    pg.quit()
    sys.exit()