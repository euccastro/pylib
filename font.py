import os

import pyglet

pyglet.font.add_file(os.path.join(os.path.dirname(__file__), 
                                  "Inconsolata.otf"))


class font:
    def __init__(self, name, points_from_pixels):
        self.name = name
        self.points_from_pixels = points_from_pixels

inconsolata = font("Inconsolata",
                   lambda h: int(round(h*.7)))
default = inconsolata

