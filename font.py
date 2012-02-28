import pyglet

pyglet.font.add_file("jawbhard.ttf")


class font:
    def __init__(self, name, points_from_pixels):
        self.name = name
        self.points_from_pixels = points_from_pixels

jawbhard = font("Jawbreaker Hard BRK",
                lambda h: int(round(h*.7)))

