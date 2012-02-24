from __future__ import division

from pyglet.gl import *

def set_unit_projection(width, height):
    "Centered at screen, smallest of (width, height) becomes 1."
    if width > height:
        proj_width = width / height
        proj_height = 1.0
    else:
        proj_height = height / width
        proj_width = 1.0
    glOrtho(-proj_width, proj_width,
            -proj_height, proj_height,
            -1.0, 1.0)

def set_raster_projection(width, height):
    """
    Good for displaying text (and images?).
    """
    glOrtho(0, width, 0, height, -1, 1)

def set_perspective_projection(width, height):
    gluPerspective(40.0, width/height, 0.1, 100.0)

def make_resize_handler(set_projection):
    def on_resize(width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, width, height)
        set_projection(width, height)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED
    return on_resize

class raster_projection_context:
    def __init__(self, window):
        self.window = window
    def __enter__(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        set_raster_projection(self.window.width, self.window.height)
    def __exit__(self, *etc):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
