from __future__ import division

from copy import deepcopy

import stackless

import yaml
import pyglet
from pyglet.window import key
from pyglet.gl import *

from la import vec2

import font


over = None
focus = None
debug_over = False
debug_navigate = False
# The hierarchy of windows that we are navigating. 
navigating = []

keyboard_events = ['on_key_press',
                   'on_key_release',
                   'on_text',
                   'on_text_motion',
                   'on_text_motion_select']
def activate(w):
    global focus
    if focus is not None:
        focus.on_deactivate()
    focus = w
    w.on_activate()

def on_window_remove(w):
    global focus
    if focus is w:
        focus = None
    del navigating[1:]

def run_window(name, parent, kw=None):
    d = yaml.load(file(name+".yaml"))
    d.update(kw or {})
    root = window_from_dicttree(d)
    parent.add_child(root)
    ret = root.run()
    parent.remove_child(root)
    return ret

class window:
    """
    A window is a region of the screen that can handle input events and draw
    itself.

    Windows are organized in a hierarchy, where each window can have any
    number of children.  By default (as defined in rec_mouse_event_handler),
    to handle a mouse event for a screen position (x, y), we traverse this
    hierarchy depth-first to find a window that is 'enabled' and claims
    ('inside') to contain point (x, y).

    We draw in a similarly hierarchical manner.

    As a convenience, we assume the general case of rectangular windows
    arranged within the parent's borders.  Special cases must provide dummy
    layout interface.

    As another convenience, a window provides a run() method, which will block
    until some other tasklet calls its return_(x) method, and return x.
    """

    default_ret = True
    enabled = False

    def __init__(self, 
                 rect=None, 
                 layout=None,
                 name=None, 
                 id=None, 
                 enabled=None):
        self.name = name or self.__class__.__name__
        self.rect = rect
        if layout:
            self._layout = layout
        self.children = []
        self.templates = {}
        self.was_inside = True
        self.id = id
        if enabled is not None:
             self.enabled = enabled

    def find_template(self, id_):
        if id_ in self.templates:
            return self, self.templates[id_]
        else:
            for child in self.children:
                parent, builder = child.find_template(id_)
                if builder:
                    return parent, builder
        return None, None

    def find_window(self, id_):
        if id_ == getattr(self, 'id', None):
            return self
        for child in self.children:
            ret = child.find_window(id_)
            if ret:
                return ret
        return None

    def find_absolute_rect(self):
        # XXX: Hack.
        # This should be cheaper.  This is a known issue in the stable
        # version of ui.py.
        def get_left_bottom(w):
            if w is self:
                return self.rect.left, self.rect.bottom
            for child in w.children:
                left, bottom = get_left_bottom(child)
                if left is not None:
                    return left + w.rect.left, bottom + w.rect.bottom
            return None, None
        left, bottom = get_left_bottom(desktop)
        return irect(left, bottom, self.rect.width, self.rect.height)

    def _layout(s, rect, self, parent):
        return self.rect, rect

    def layout(self, rect, parent):
        my_rect, rest = self._layout(rect, self, parent)
        if my_rect != self.rect:
            if (self.rect is None
                or (my_rect.width, my_rect.height)
                    != (self.rect.width, self.rect.height)):
                self.on_resize(my_rect)
            self.rect = my_rect
            self.layout_children()
        return rest

    def on_resize(self, new_rect):
        pass

    def layout_children(self):
        child_rest = irect(0, 0, self.rect.width, self.rect.height)
        for child in self.children:
            child_rest = child.layout(child_rest, self)

    def inside(self, x, y):
        return self.rect.contains(x, y)

    def rec_draw(self):
        if not self.rect:
            return
        glPushMatrix()
        glTranslatef(self.rect.left, self.rect.bottom, 0)
        self.draw()
        for child in reversed(self.children):
            child.rec_draw()
        def draw_rectangle(margin):
            w = self.rect.width - (margin+1)
            h = self.rect.height - (margin+1)
            pyglet.graphics.draw(4, GL_LINE_LOOP, ('v2i', 
                    (margin, margin, w, margin, w, h, margin, h)))
        if debug_over and over is self:
            glColor3f(1.0, 0.0, 1.0)
            draw_rectangle(1)
        if debug_navigate and navigating and navigating[-1] is self:
            glColor3f(1.0, 1.0, 1.0)
            draw_rectangle(0)
        glPopMatrix()

    def draw(self):
        pass
    
    def rec_mouse_event_handler(name):
        rec_name = 'rec_mouse_' + name
        on_name = 'on_mouse_' + name
        def handle(self, x, y, *args, **kw):
            global over
            for child in self.children:
                if child.enabled:
                    cx = x - child.rect.left
                    cy = y - child.rect.bottom
                    if (child.inside(x, y)
                        and getattr(child, rec_name)(cx, cy, *args, **kw)):
                        if over is None:
                            over = child
                        return True
            else:
                return getattr(self, on_name)(x, y, *args, **kw)
        handle.__name__ = rec_name
        return handle

    for name in ['drag', 'motion', 'leave', 'press', 'release']:
        locals()['rec_mouse_' + name] = rec_mouse_event_handler(name)
        locals()['on_mouse_' + name] = (
                lambda self, *args, **kw: self.default_ret)

    for name in keyboard_events:
        locals()[name] = lambda *args: None

    del name, rec_mouse_event_handler

    # I decorate mouse motion handling to implement window mouse enter and exit.
    _base_rec_mouse_motion = rec_mouse_motion

    def rec_mouse_motion(self, x, y, dx, dy):
        for child in self.children:
            if child.was_inside and not child.inside(x, y):
                child.rec_mouse_leave(x, y)
        for child in self.children:
            if child.was_inside and child.inside(x, y):
                break
        else:
            for child in self.children:
                if not child.was_inside and child.inside(x, y):
                    child.was_inside = True
                    child.on_mouse_enter(x, y)
                    break
        return self._base_rec_mouse_motion(x, y, dx, dy)

    def rec_mouse_leave(self, x, y):
        # This was originally meant as a pyglet event handler, but it proved
        # necessary to propagate recursively the leave events generated in
        # rec_mouse_motion, lest granchildren be oblivious to the mouse
        # leaving them.
        if self.was_inside:
            self.on_mouse_leave(x, y)
            self.was_inside = False
            for child in self.children:
                if child.enabled:
                    child.rec_mouse_leave(x, y)

    def on_mouse_enter(self, x, y):
        pass

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def run(self):
        self.ch = stackless.channel()
        return self.ch.receive()

    def return_(self, val=None):
        self.ch.send(val)

    def add_child(self, child):
        self.children.append(child)
        self.layout_children()

    def remove_child(self, child):
        self.children.remove(child)
        self.layout_children()
        on_window_remove(child)

    def set_namespace(self, ns):
        """
        If this window was created from a dicttree, this is called as soon as the
        namespace of descendant ids is built, shortly after window creation.

        Subclasses of window may want to maintain a reference to this namespace
        or do some other initialization at this point.
        """
        pass

class text_view(window):

    def __init__(self, *args, **kw):
        fontname = pop_if_in(kw, 'font') or 'default'
        text = pop_if_in(kw, 'text') or ""
        color = pop_if_in(kw, 'color') or [.5, .5, .5, 1.]
        window.__init__(self, *args, **kw)
        self.font = getattr(font, fontname)
        self.text = text
        self.set_color(color)
        if self.rect:
            self.on_resize(self.rect)

    def set_color(self, color):
        self.color = [int(round(comp * 255)) for comp in color]
        if len(self.color) == 3:
            self.color.append(255)


class label(text_view):
    def set_text(self, text):
        self.text = text
        if hasattr(self, 'label'):
            self.label.text = text

    def set_color(self, color):
        text_view.set_color(self, color)
        if hasattr(self, 'label'):
            self.label.color = self.color

    def on_resize(self, new_rect):
        self.label = pyglet.text.Label(
                self.text,
                font_name=self.font.name,
                font_size=self.font.points_from_pixels(new_rect.height),
                x=new_rect.width//2,
                y=new_rect.height//2,
                color=self.color,
                anchor_x='center',
                anchor_y='center'
                )
    def draw(self):
        self.label.draw()

class edit(text_view):
    #XXX: Bug, ao resizar non lembra o estado do caret, seleson, etc.

    enabled = True

    def __init__(self, *args, **kw):
        self.maxlen = pop_if_in(kw, 'maxlen') or 20
        text_view.__init__(self, *args, **kw)

    def on_resize(self, new_rect):
        if hasattr(self, 'doc'):
            text = self.doc.text
        else:
            text = self.text
        if hasattr(self, 'caret'):
            position, mark = self.caret.position, self.caret.mark
        else:
            position = len(text)
            mark = None
        self.doc = pyglet.text.document.UnformattedDocument(text)
        self.doc.set_style(0, 0,
                dict(font_name=self.font.name,
                     font_size=self.font.points_from_pixels(new_rect.height),
                     color=self.color)
                )
        self.pyglet_layout = pyglet.text.layout.IncrementalTextLayout(self.doc,
                                                               new_rect.width,
                                                               new_rect.height)
        self.pyglet_layout.x = new_rect.width // 2
        self.pyglet_layout.y = new_rect.height // 2
        self.pyglet_layout.anchor_x = 'left'
        self.pyglet_layout.anchor_y = 'center'
        self.caret = pyglet.text.caret.Caret(self.pyglet_layout,
                                             color=self.color[:3])
        self.caret.position = position
        self.caret.mark = mark

    def on_text(self, char):
        if char == '\r':
            if self.doc.text:
                #self.caret.delete()
                self.on_enter(self.doc.text)
        elif len(self.doc.text) < self.maxlen:
            self.caret.on_text(char)

    def on_enter(self, text):
        pass

    def on_activate(self):
        print "Now I would show caret."

    def on_deactivate(self):
        print "Now I would hide caret."

    def on_text_motion(self, motion):
        # XXX: Bug in pyglet, content_width never shrinks to accomodate for
        # deleted text.
        if motion in [key.MOTION_BACKSPACE, key.MOTION_DELETE]:
            self.pyglet_layout.content_width = 0
        self.caret.on_text_motion(motion)

    def on_text_motion_select(self, *etc):
        self.caret.on_text_motion_select(*etc)

    def draw(self):
        self.pyglet_layout.x = (self.rect.width 
                                - self.pyglet_layout.content_width) // 2
        self.pyglet_layout.draw()

class button(window):

    enabled = True

    hilite_color = 1., 1., 1. 
    lolite_color = .3, .3, 1.

    def __init__(self, *args, **kw):
        label_ = label(font='default', 
                       color=self.lolite_color,
                       text=kw.pop('label'),
                       layout=fill_layout())
        callback = pop_if_in(kw, 'callback')
        window.__init__(self, *args, **kw)
        self.children.append(label_)
        self.label = label_
        self.callback = callback

    def init_label_y_if_necessary(self):
        #XXX!
        if not hasattr(self, 'press_y'):
            self.release_y = self.label.label.y
            self.press_y = self.label.label.y - int(self.label.label.content_height * .1)

    def on_mouse_enter(self, *etc):
        self.label.set_color(self.hilite_color)

    def on_mouse_leave(self, *etc):
        self.label.set_color(self.lolite_color)

    #XXX: Check that these actually work and make sense for all types of
    #     pyglet and ui layouts.
    def on_mouse_press(self, *etc):
        self.init_label_y_if_necessary()
        self.label.label.y = self.press_y
        self.callback()

    def on_mouse_release(self, *etc):
        self.init_label_y_if_necessary()
        self.label.label.y = self.release_y

class _desktop(window):
    enabled = True
    def __init__(self, pyglet_window):
        window.__init__(self, 
                        irect(0, 
                              0,
                              pyglet_window.width,
                              pyglet_window.height),
                        layout=fill_layout(),
                        name='desktop')
        handlers = dict(('on_' + name[len('rec_'):], getattr(self, name))
                        for name in dir(self)
                        if name.startswith('rec_'))
        pyglet_window.push_handlers(**handlers)

    def rec_mouse_motion(*args, **kw):
        global over
        over = None
        return window.rec_mouse_motion(*args, **kw)

    def rec_resize(self, width, height):
        self.layout(irect(0, 0, width, height), None)

    # Prevent exit on ESC.
    def rec_key_press(self, *args):
        return pyglet.event.EVENT_HANDLED

    def rec_draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        window.rec_draw(self)


class rect(object):

    def __init__(self, left, bottom, width, height):
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height

    def contains(self, x, y):
        return (self.left <= x < self.right
                and self.bottom <= y < self.top)

    def get_right(self):
        return self.left + self.width
    right = property(get_right)

    def get_top(self):
        return self.bottom + self.height
    top = property(get_top)

    def get_center(self):
        return vec2(self.left + self.width / 2,
                    self.bottom + self.height / 2)
    center = property(get_center)

    def __repr__(self):
        return "rect(left=%s, bottom=%s, width=%s, height=%s)" % (
                self.left, self.bottom, self.width, self.height)

    def __iter__(self):
        yield self.left, self.bottom
        yield self.right, self.bottom
        yield self.right, self.top
        yield self.left, self.top

    def __eq__(self, other):
        return (isinstance(other, rect)
                and self.left == other.left
                and self.bottom == other.bottom
                and self.width == other.width
                and self.height == other.height)

class irect(rect):
    def __init__(self, left, bottom, width, height):
        rect.__init__(self, *(int(round(x)) 
                              for x in [left, bottom, width, height]))
    def get_center(self):
        return rect.get_center(self).map(round).map(int)
    center = property(get_center)

def layout_dict(rect, window, parent):
    ret = rect.__dict__.copy()
    ret['self'] = window
    ret['parent'] = parent
    return ret

class fill_layout:
    def __call__(self, r, s, p):
        return r, r

class push_layout:
    def __init__(self, thickness_expr):
        self.thickness_expr = thickness_expr
    def __call__(self, r, s, p):
        thickness = int(eval(self.thickness_expr, layout_dict(r, s, p)))
        return self.get_rects(r, thickness)

class left_layout(push_layout):
    def get_rects(self, r, width):
        return (irect(r.left, r.bottom, width, r.height),
                irect(r.left + width, r.bottom, r.width - width, r.height))

class right_layout(push_layout):
    def get_rects(self, r, width):
        return (irect(r.right - width, r.bottom, width, r.height),
                irect(r.left, r.bottom, r.width - width, r.height))

class bottom_layout(push_layout):
    def get_rects(self, r, height):
        return (irect(r.left, r.bottom, r.width, height),
                irect(r.left, r.bottom + height, r.width, r.height - height))

class top_layout(push_layout):
    def get_rects(self, r, height):
        return (irect(r.left, r.top - height, r.width, height),
                irect(r.left, r.bottom, r.width, r.height - height))

class center_layout:
    def __init__(self, width_expr, height_expr):
        self.width_expr = width_expr
        self.height_expr = height_expr
    def __call__(self, r, s, p):
        env = layout_dict(r, s, p)
        width = int(eval(self.width_expr, env))
        height = int(eval(self.height_expr, env))
        return (irect(r.left + (r.width-width)//2, 
                      r.bottom + (r.height-height)//2, 
                      width, 
                      height),
                r)

def pop_if_in(dict, key):
    if key in dict:
        return dict.pop(key)
    else:
        return None

class layer(window):
    """
    A layer is a fullscreen passive container for other windows.

    It is used to organize event handling and drawing order.
    """
    enabled = True
    default_ret = False
    _layout = fill_layout()

    def inside(self, *whatever):
        return True

class drag_layer(layer):
    #XXX: This doesn't always work right.  Icons are sometimes left behind.
    def __init__(self, **kw):
        grabber = kw.pop('grabber')
        layer.__init__(self, **kw)
        self.grabber = grabber
    def rec_mouse_drag(self, *etc):
        return self.grabber.rec_mouse_drag(*etc)
    def rec_mouse_release(self, x, y, *etc):
        desktop.children.remove(self)
        self.grabber.on_end_drag(x, y)
        del self.grabber

def start_drag(w):
    desktop.children.insert(0, drag_layer(grabber=w))
    desktop.layout_children()

def window_from_dicttree(d):
    classpath = pop_if_in(d, 'class')
    if classpath:
        modname, classname = classpath.split('.')
        cls = getattr(__import__(modname), classname)
    else:
        cls = window
    layout = pop_if_in(d, 'layout')
    if layout:
        layout_list = layout.split(" ")
        layout_class = globals()[layout_list[0] + "_layout"]
        d['layout'] = layout_class(*layout_list[1:])
    children = pop_if_in(d, 'children') or []
    w = cls(**d)
    def template_builder(d):
        def build(**extra):
            dd = deepcopy(d)
            dd.update(extra)
            return window_from_dicttree(dd)
        return build
    for childdict in children:
        if pop_if_in(childdict, 'template'):
            template_id = childdict.pop('id')
            assert template_id not in w.templates
            w.templates[template_id] = template_builder(childdict) 
        else:
            w.children.append(window_from_dicttree(childdict))
    return w

def init(pyglet_window):
    global desktop
    desktop = _desktop(pyglet_window)
    def text_handler(name):
        def handle(*args):
            if focus is not None:
                return getattr(focus, name)(*args)
        return handle
    pyglet_window.push_handlers(**dict((name, text_handler(name))
                                       for name in keyboard_events))
    navigating.append(desktop)
    pressed = set()

    @pyglet_window.event
    def on_key_press(k, mods):
        pressed.add(k)
        refresh_mode()
        if mods & key.MOD_CTRL:
            if k == key.UP:
                if len(navigating)>1:
                    navigating.pop()
                    print_info(navigating[-1])
                else:
                    print "Already at root."
            if k == key.DOWN:
                if navigating[-1].children:
                    new = navigating[-1].children[0]
                    print_info(new)
                    navigating.append(new)
                else:
                    print "Window has no children."
            if k in [key.LEFT, key.RIGHT]:
                if len(navigating) > 1:
                    direction = -1 if key.LEFT else +1
                    siblings = navigating[-2].children
                    if len(siblings) > 1:
                        new = siblings[
                                ((siblings.index(navigating[-1]) + direction)
                                 % len(siblings))]
                        print_info(new)
                        navigating[-1] = new
                    else:
                        print "Window has no siblings."
                else:
                    print "Desktop has no siblings."

    @pyglet_window.event
    def on_key_release(k, mods):
        pressed.remove(k)
        refresh_mode()

    def refresh_mode():
        global debug_navigate
        global debug_over
        debug_over = debug_navigate = (key.LCTRL in pressed 
                                       or key.RCTRL in pressed)

    def print_info(w):
        print
        print "id:", w.id
        print "name:", w.name
        print "class:", w.__class__.__name__
        print "enabled:", w.enabled

