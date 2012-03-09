from __future__ import division

import math
import numbers


class vec3:
    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    def normalize(self):
        return self / self.length()
    def inormalize(self):
        l = self.length()
        self.x /= l
        self.y /= l
        self.z /= l
    def length(self):
        return math.sqrt(self.length_sq())
    def length_sq(self):
        return self.x * self.x + self.y * self.y + self.z * self.z
    def __add__(self, other):
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self
    def __sub__(self, other):
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, x):
        return vec3(self.x * x, self.y * x, self.z * x)
    __rmul__ = __mul__
    def __div__(self, x):
        return vec3(self.x / x, self.y / x, self.z / x)
    __truediv__ = __div__
    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        elif i == 2:
            return self.z
        else:
            raise IndexError(i)
    def __cmp__(self, other):
        return cmp(tuple(self), tuple(other))
    def __repr__(self):
        return "vec3(%s, %s, %s)" % (self.x, self.y, self.z)

def cross(v, w):
    return vec3(v.y * w.z - v.z * w.y,
                v.z * w.x - v.x * w.z,
                v.x * w.y - v.y * w.x)

class mat22:
    def __init__(self, a11, a12, a21, a22):
        self.a11, self.a12, self.a21, self.a22 = a11, a12, a21, a22

    def __mul__(self, other):
        if isinstance(other, vec2):
            return vec2(self.a11 * other.x + self.a12 * other.y,
                        self.a21 * other.x + self.a22 * other.y)
        elif isinstance(other, numbers.Number):
            return mat22(self.a11 * other, 
                         self.a12 * other, 
                         self.a21 * other, 
                         self.a22 * other)
        else:
            raise NotImplementedError

    def __truediv__(self, other):
        if isinstance(other, numbers.Number):
            return mat22(self.a11 / other, 
                         self.a12 / other, 
                         self.a21 / other, 
                         self.a22 / other)
        else:
            raise NotImplementedError

class vec2:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError(i)

    def __setitem__(self, i, v):
        if i == 0:
            self.x = v
        elif i == 1:
            self.y = v
        else:
            raise IndexError(i)

    def become(self, other):
        self.x = other.x
        self.y = other.y

    def __neg__(self):
        return vec2(-self.x, -self.y)

    def length(self):
        return math.sqrt(self.length_sq())

    def length_sq(self):
        return self.x * self.x + self.y * self.y

    def truncated(self, max_length):
        """
        Return a vector in the same direction as me that has length
        min(max_length, length(x,y)).
        """
        l = self.length()
        if l <= max_length:
            return self.copy()
        else:
            return vec2(self.x * max_length / l, self.y * max_length / l)

    def normalized(self):
        return self / self.length()

    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __mul__(self, x):
        return vec2(self.x * x, self.y * x)
    __rmul__ = __mul__

    def __truediv__(self, x):
        return vec2(self.x / x, self.y / x)

    def __mod__(self, x):
        return vec2(self.x % x, self.y % x)

    def copy(self):
        return vec2(self.x, self.y)

    def __nonzero__(self):
        return bool(self.x or self.y)

    def __eq__(self, other):
        return (isinstance(other, vec2)
                and self.x == other.x
                and self.y == other.y)

    def __hash__(self):
        return hash((vec2, self.x, self.y))

    def normalized_if_not_zero(self):
        if self:
            return self.normalized()
        else:
            return self

    def __repr__(self):
        return "vec2(%s, %s)" % (self.x, self.y)

    def map(self, fn):
        return vec2(fn(self.x), fn(self.y))

def right_ortho(v):
    """
    Return a vector that is
     - same length as v
     - perpendicular to v
     - facing rightwards from the v direction.
    """
    return vec2(v.y, -v.x)

def left_ortho(v):
    """
    Return a vector that is
     - same length as v
     - perpendicular to v
     - facing leftwards from the v direction.
    """
    return vec2(-v.y, v.x)

def collision_response(p, v, q, d):
    """
    Return the closest point to p, along the line starting from p
    in the direction of the v vector, that dists d from the point q.

    We assume that there is indeed one solution, and that |p-q| > d.
    """
    qbase = p + dot((q - p), v) * v / (v.x * v.x + v.y * v.y)
    dist_from_base = math.sqrt(d * d - (q - qbase).length_sq())
    diff_from_base = v.normalized() * dist_from_base
    return closest(qbase + diff_from_base, qbase - diff_from_base, p)

def closest(a, b, p):
    """
    Return the point, among a or b, which is closest to p.
    """
    if (p-a).length_sq() < (p-b).length_sq():
        return a
    else:
        return b

def solve_quadratic(a, b, c):
    x = math.sqrt(b * b - 4 * a * c)
    a2 = 2 * a
    return ((-b + x) / a2, 
            ((-b - x) / a2))

def segment_to_point_distance(p, q, r):
    """
    Return the distance between the segment defined by endpoints p, q
    and the point r.
    """
    v = q - p
    vlen = v.length()
    u = v / vlen
    w = r - p
    projlen = dot(u, w)
    if projlen <= 0:
        return (r - p).length()
    elif projlen >= vlen:
        return (r - q).length()
    else: 
        # This is the same as
        #   line_to_point_distance(p, q - p, r)
        # but we have some parts already calculated.
        return (r - (p + u * projlen)).length() 

def line_to_point_distance(p, v, q):
    """
    Return the distance between the line that passes through point p in
    the direction of the v vector and the point q.
    """
    qbase = p + dot((q - p), v) * v / (v.x * v.x + v.y * v.y)
    return (q - qbase).length()

def dot(v, w):
    return v.x * w.x + v.y * w.y

dot2 = dot

def dot3(v, w):
    return v.x * w.x + v.y * w.y + v.z * w.z

def occlusion_angles(p, o, radius):
    """
    (left_angle, right_angle) from p to the tangent of the circle with center at o
    and the given radius.
    """
    po = o - p
    delta_angle = math.asin(radius/po.length())
    base_angle = math.atan2(po.y, po.x)
    return ((base_angle + delta_angle) % (math.pi * 2),
            (base_angle - delta_angle) % (math.pi * 2))


def closest_point_in_segment(p, a, b):
    ab = b - a
    t = max(0, min(1, dot(p - a, ab) / dot(ab, ab)))
    return a + t * ab


def test_closest_point_in_segment():
    import pyglet
    import draw_util
    from pyglet import gl
    
    w = pyglet.window.Window()

    line = []

    point = vec2(0, 0)

    @w.event
    def on_mouse_press(x, y, button, modifiers):
        if len(line) < 2:
            line.append(vec2(x, y))
        else:
            point.x = x
            point.y = y

    @w.event
    def on_draw():
        w.clear()
        gl.glBegin(gl.GL_POINTS)
        for ep in line:
            gl.glVertex2f(*ep)
        gl.glEnd()
        if len(line) == 2:
            gl.glBegin(gl.GL_LINES)
            gl.glVertex2f(*line[0])
            gl.glVertex2f(*line[1])
            gl.glEnd()
        if not (point.x == point.y == 0):
            closest = closest_point_in_segment(point, *line)
            gl.glBegin(gl.GL_POINTS)
            gl.glVertex2f(*closest)
            gl.glEnd()
            radius = (closest - point).length()
            draw_util.draw_circumference(point.x, point.y, radius)

    gl.glPointSize(4)
    pyglet.app.run()

def rotate(angle, v):
    sin = math.sin(angle)
    cos = math.cos(angle)
    return vec2(v.x * cos - v.y * sin,
                v.x * sin + v.y * cos)

def convex_hull(points):
    def is_left(p0, p1, p2):
        ret = ((p1.x - p0.x) * (p2.y - p0.y)
                - (p2.x - p0.x) * (p1.y - p0.y))
        if ret > 0:
            return 1
        elif ret < 0:
            return -1
        else:
            return 0
    def is_left_of_rightmost_lowest(p1, p2):
        return is_left(rightmost_lowest, p1, p2)
    rightmost_lowest = p0 = max(points, key=lambda p: (-p.y, p.x))
    points = points[:]
    points.remove(rightmost_lowest)
    points.sort(cmp=is_left_of_rightmost_lowest)
    for (p1, p2) in zip(points[:-1], points[1:]):
        if is_left(rightmost_lowest, p1, p2) == 0:
            if (p1 - p0).length_sq() > (p2 - p0).length_sq():
                points.remove(p2)
            else:
                points.remove(p1)
    points.insert(0, rightmost_lowest)
    stack = points[:2]
    for p in points[2:]:
        while True:
            if is_left(stack[-2], p, stack[-1]) > 0:
                break
            stack.pop()
        stack.append(p)
    stack.reverse()   
    return stack

def lerp(t, a, b):
    return a + t * (b-a)

if __name__ == '__main__':
    test_closest_point_in_segment()
