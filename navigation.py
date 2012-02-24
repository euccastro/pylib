from __future__ import division

import pyglet
from pyglet.gl import *

import proj_util


yaw = 0.0
pitch = 0.0
dist = 5.0


def push_handlers(w):
    w.push_handlers(proj_util.make_resize_handler(
                        proj_util.set_perspective_projection),
                    on_mouse_drag,
                    on_mouse_scroll)

def on_mouse_drag(x, y, dx, dy, *etc):
    global yaw
    global pitch
    yaw -= dx
    pitch += dy
    pitch = max(-85.0, min(85.0, pitch))

def on_mouse_scroll(x, y, sx, d, *etc):
    global dist
    dist *= 1 + d / 10
    
def transform():
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -dist)
    glRotatef(-pitch, 1.0, 0.0, 0.0)
    glRotatef(-yaw, 0.0, 1.0, 0.0)

