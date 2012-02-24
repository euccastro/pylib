from __future__ import division

import math

import pyglet
from pyglet.gl import *


def plot_2d(f, min_=-2, max_=2, ymin=None, ymax=None, xstep=None, ystep=None):
    w = pyglet.window.Window(resizable=True)

    @w.event
    def on_resize(width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        span = max_ - min_
        aspect = height / width
        halfvspan = span * aspect / 2
        ymin_, ymax_ = ymin, ymax
        if ymin is None:
            ymin_ = -halfvspan
        if ymax is None:
            ymax_ = halfvspan
        glOrtho(min_, max_,
                ymin_, ymax_, 
                -1, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        return pyglet.event.EVENT_HANDLED

    @w.event
    def on_mouse_motion(x, *etc):
        xv = min_ + (max_ - min_) * x / w.width
        yv = f(xv)
        print xv, "->", yv

    @w.event
    def on_draw():
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        span = max_ - min_
        pixel_size = span / w.width
        glBegin(GL_LINES)
        glColor3f(1.0, 0.0, 0.0)
        glVertex2f(-1000, 0)
        glVertex2f(1000, 0)
        for x in xrange(int(min_) - 1, int(max_) + 1):
            if x != 0:  
                glVertex2f(x, -0.2)
                glVertex2f(x, 0.2)
        glColor3f(0.0, 1.0, 0.0)
        glVertex2f(0, -1000)
        glVertex2f(0, 1000)
        for y in xrange(-10, 11):
            if y != 0:
                glVertex2f(-0.2, y)
                glVertex2f(0.2, y)
        glEnd()
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_LINE_STRIP)
        for i in xrange(int(span / pixel_size)):
            x = min_ + i * pixel_size
            y = f(x)
            glVertex2f(x, f(x))
        glEnd()
    pyglet.app.run()

if __name__ == '__main__':
    def gradient(x):
        return x
    def circle(x):
        if abs(x) >= 1:
            return 0
        else:
            return math.sqrt(1 - x * x)
    def smooth(x):
        if abs(x) >= 1:
            return 0
        x = 1 - abs(x)
        return 6 * x ** 4 - 15 * x ** 3 + 10 * x ** 2
    def circlex2(x):
        if abs(x) >= 1:
            return 0
        return 1 - x * x
    def _8t4xt(x):
        return 8 * circlex2(x) ** 4 * x
    def circlex4(x):
        return x ** 4 - 2 * x ** 2 + 1
    def circlex8(x):
        return x ** 8 - 4 * x ** 6 + 6 * x ** 4 - 4 * x ** 2 + 1 
    def circlex8_(x):
        return 8 * x ** 7 - 24 * x ** 5 + 20 * x ** 3 - 8 * x
    def circlex8__(x):
        return 56 * x ** 6 - 120 * x ** 4 + 60 * x ** 2 - 8
    def circlexramp(x):
        return circlex8(x) * x
    def circlexramp_(x):
        return 9 * x ** 8 - 28 * x ** 6 + 25 * x ** 5 - 12 * x ** 2 + 1
    def circlexramp__(x):
        return 72 * x ** 7 - 162 * x ** 5 + 125 * x ** 4 - 24 * x
    plot_2d(lambda(x): smooth(x) * x)
    #plot_2d(circlexramp__)#, ymin=-10, ymax=10)


