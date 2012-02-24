from __future__ import division

import math
from pyglet.gl import *

def draw_circle(x, y, radius, divisions=32):
    _draw_round_thing(GL_POLYGON, x, y, radius, divisions)

def draw_circumference(x, y, radius, divisions=32):
    _draw_round_thing(GL_LINE_LOOP, x, y, radius, divisions)

def _draw_round_thing(mode, x, y, radius, divisions):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(radius, radius, radius)
    dl = getattr(draw_circle, 'dl', None)
    if dl is None:
        dl = draw_circle.dl = glGenLists(1)
        glNewList(dl, GL_COMPILE_AND_EXECUTE)
        glBegin(mode)
        for x in xrange(divisions):
            angle = (x/divisions) * math.pi * 2
            glVertex2f(math.cos(angle), math.sin(angle))
        glEnd()
        glPopMatrix()
        glEndList()
    else:
        glCallList(dl)

def draw_rectangle(x, y, w, h):
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x+w, y)
    glVertex2f(x+w, y+h)
    glVertex2f(x, y+h)
    glEnd()
