"""
DrawingPanel.py — notebook/Google Colab compatible edition

A lightweight inline replacement for the Tkinter-based DrawingPanel used by
Building Python Programs materials.  It keeps the introductory drawing API
familiar while rendering with Pillow and IPython display instead of opening a
desktop window.

Designed for Jupyter Notebook and Google Colab.
"""

from PIL import Image, ImageDraw, ImageFont
import time
import math


class Color:
    """Small compatibility helper for common DrawingPanel color formats."""

    # Common classroom-friendly color names. Pillow also understands many names.
    BLACK = "black"
    WHITE = "white"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    PURPLE = "purple"
    PINK = "pink"
    GRAY = "gray"
    GREY = "grey"
    CYAN = "cyan"
    MAGENTA = "magenta"
    BROWN = "brown"
    LIGHT_BLUE = "lightblue"
    LIGHT_GRAY = "lightgray"
    DARK_GRAY = "darkgray"

    def __init__(self, *args):
        self.value = self.to_hex(*args)

    def __str__(self):
        return self.value

    @staticmethod
    def is_rgb(color):
        return (
            isinstance(color, (tuple, list))
            and len(color) == 3
            and all(isinstance(v, (int, float)) and 0 <= v <= 255 for v in color)
        )

    @staticmethod
    def is_hex(color):
        if not isinstance(color, str) or len(color) not in (4, 7) or not color.startswith("#"):
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_name(color):
        if not isinstance(color, str) or not color:
            return False
        try:
            Image.new("RGB", (1, 1), color)
            return True
        except Exception:
            return False

    @staticmethod
    def is_valid_color(color):
        return isinstance(color, Color) or Color.is_rgb(color) or Color.is_hex(color) or Color.is_name(color)

    @staticmethod
    def to_rgb(*args):
        if len(args) == 1:
            color = args[0]
            if isinstance(color, Color):
                color = str(color)
            if Color.is_rgb(color):
                return tuple(int(v) for v in color)
            img = Image.new("RGB", (1, 1), color)
            return img.getpixel((0, 0))
        if len(args) == 3:
            return tuple(int(v) for v in args)
        raise ValueError("invalid color")

    @staticmethod
    def to_hex(*args):
        r, g, b = Color.to_rgb(*args)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def to_name(*args):
        # For notebook use, a normalized hex value is a safe representation.
        return Color.to_hex(*args)

    @staticmethod
    def normalize_all_colors(options):
        for key in ("color", "fill", "outline"):
            if key in options and options[key] not in ("", None):
                options[key] = Color.to_hex(options[key])


class DrawingPanel:
    """
    Inline DrawingPanel for Jupyter/Colab.

    Coordinates match the original convention:
      x grows left -> right
      y grows top -> bottom

    Drawing methods automatically refresh the notebook display when auto_show
    is True (the default). For many drawing operations, pass auto_show=False
    and call panel.show() once at the end.
    """

    def __init__(self, width=500, height=500, background="white",
                 auto_show=True, **options):
        self._width = int(width)
        self._height = int(height)
        self._background = background
        self._outline = "black"
        self._fill = "black"
        self._stroke = 1
        self._font = None
        self._title = "DrawingPanel"
        self._visible = True
        self._resizable = False
        self._x = 0
        self._y = 0
        self._mouse_x = 0
        self._mouse_y = 0
        self._auto_show = auto_show
        self._display_handle = None

        self._image = Image.new("RGB", (self._width, self._height), background)
        self._draw = ImageDraw.Draw(self._image)
        if self._auto_show:
            self.show()

    # ---------- notebook display ----------

    def _refresh(self):
        if not self._visible or not self._auto_show:
            return
        self.show()

    def show(self):
        """Displays or refreshes the panel inline beneath the notebook cell."""
        self._visible = True
        try:
            from IPython.display import display
            if self._display_handle is None:
                self._display_handle = display(self._image.copy(), display_id=True)
            else:
                self._display_handle.update(self._image.copy())
        except Exception:
            # Outside IPython, save()/image can still be used.
            pass
        return self

    def display(self):
        return self.show()

    def close(self):
        """Hides future automatic refreshes. There is no desktop window to close."""
        self._visible = False

    def is_visible(self):
        return self._visible

    @staticmethod
    def is_headless():
        return True

    # ---------- helpers ----------

    def _color(self, color, default):
        return default if color in ("", None) else color

    def _line_width(self, options):
        return int(float(options.get("width", self._stroke)))

    def _outline_fill(self, color, options, filled=False):
        default = self._fill if filled else self._outline
        chosen = self._color(color, default)
        if filled:
            fill = options.get("fill", chosen)
            outline = options.get("outline", fill)
        else:
            outline = options.get("outline", chosen)
            fill = options.get("fill", None)
        return outline, fill

    def _coords(self, coords):
        if len(coords) == 1 and isinstance(coords[0], (list, tuple)):
            first = coords[0]
            if first and isinstance(first[0], (list, tuple)):
                return [tuple(p) for p in first]
            coords = tuple(first)

        coords = list(coords)
        if coords and isinstance(coords[-1], str) and Color.is_valid_color(coords[-1]):
            coords = coords[:-1]

        if coords and isinstance(coords[0], (list, tuple)):
            return [tuple(p) for p in coords]
        if len(coords) % 2:
            raise ValueError("must pass an even number of coordinates")
        return [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]

    # ---------- drawing ----------

    def clear(self):
        self._image = Image.new("RGB", (self._width, self._height), self._background)
        self._draw = ImageDraw.Draw(self._image)
        self._refresh()

    def draw_line(self, x1, y1, x2, y2, color="", **options):
        color = options.get("fill", self._color(color, self._outline))
        self._draw.line((x1, y1, x2, y2), fill=color, width=self._line_width(options))
        self._refresh()

    def draw_rect(self, x, y, w, h, color="", **options):
        outline, fill = self._outline_fill(color, options, False)
        self._draw.rectangle((x, y, x + w, y + h), outline=outline, fill=fill,
                             width=self._line_width(options))
        self._refresh()

    def draw_rectangle(self, x, y, w, h, color="", **options):
        self.draw_rect(x, y, w, h, color, **options)

    def fill_rect(self, x, y, w, h, color="", **options):
        outline, fill = self._outline_fill(color, options, True)
        self._draw.rectangle((x, y, x + w, y + h), fill=fill, outline=outline,
                             width=self._line_width(options))
        self._refresh()

    def fill_rectangle(self, x, y, w, h, fill="", color="", **options):
        # Original library uses fill as the first color argument for this alias.
        chosen = fill if fill not in ("", None) else color
        self.fill_rect(x, y, w, h, chosen, **options)

    def draw_oval(self, x, y, w, h, color="", **options):
        outline, fill = self._outline_fill(color, options, False)
        self._draw.ellipse((x, y, x + w, y + h), outline=outline, fill=fill,
                           width=self._line_width(options))
        self._refresh()

    def fill_oval(self, x, y, w, h, color="", **options):
        outline, fill = self._outline_fill(color, options, True)
        self._draw.ellipse((x, y, x + w, y + h), fill=fill, outline=outline,
                           width=self._line_width(options))
        self._refresh()

    def draw_pixel(self, x, y, color="", **options):
        color = self._color(color, self._outline)
        if 0 <= int(x) < self._width and 0 <= int(y) < self._height:
            self._image.putpixel((int(x), int(y)), Color.to_rgb(color))
        self._refresh()

    def draw_polyline(self, *coords, **options):
        raw = list(coords)
        color = self._outline
        if raw and isinstance(raw[-1], str) and Color.is_valid_color(raw[-1]):
            color = raw.pop()
        points = self._coords(tuple(raw))
        if len(points) >= 2:
            self._draw.line(points, fill=options.get("fill", color),
                            width=self._line_width(options))
        self._refresh()

    def draw_polygon(self, *coords, **options):
        raw = list(coords)
        color = self._outline
        if raw and isinstance(raw[-1], str) and Color.is_valid_color(raw[-1]):
            color = raw.pop()
        points = self._coords(tuple(raw))
        if len(points) >= 2:
            self._draw.polygon(points, fill=options.get("fill", None),
                               outline=options.get("outline", color))
        self._refresh()

    def fill_polygon(self, *coords, **options):
        raw = list(coords)
        color = self._fill
        if raw and isinstance(raw[-1], str) and Color.is_valid_color(raw[-1]):
            color = raw.pop()
        points = self._coords(tuple(raw))
        if len(points) >= 2:
            fill = options.get("fill", color)
            self._draw.polygon(points, fill=fill,
                               outline=options.get("outline", fill))
        self._refresh()

    def draw_arc(self, x, y, w, h, start_angle, extent, color="", **options):
        color = self._color(color, self._outline)
        # Pillow angles increase clockwise in image coordinates. This conversion
        # approximates Tkinter's visual convention.
        start = -start_angle
        end = -(start_angle + extent)
        start, end = min(start, end), max(start, end)
        self._draw.arc((x, y, x + w, y + h), start=start, end=end,
                       fill=options.get("outline", color),
                       width=self._line_width(options))
        self._refresh()

    def fill_arc(self, x, y, w, h, start_angle, extent, color="", **options):
        color = self._color(color, self._fill)
        start = -start_angle
        end = -(start_angle + extent)
        start, end = min(start, end), max(start, end)
        fill = options.get("fill", color)
        self._draw.pieslice((x, y, x + w, y + h), start=start, end=end,
                            fill=fill, outline=options.get("outline", fill))
        self._refresh()

    def draw_string(self, text, x, y, color="", font="", **options):
        color = options.get("fill", self._color(color, self._outline))
        pil_font = None
        # A Pillow font object can be passed directly for advanced notebook use.
        if isinstance(font, ImageFont.ImageFont):
            pil_font = font
        self._draw.text((x, y), str(text), fill=color, font=pil_font)
        self._refresh()

    def draw_image(self, filename, x=0, y=0, w=0, h=0, **options):
        img = filename if isinstance(filename, Image.Image) else Image.open(filename)
        img = img.convert("RGB")
        if w > 0 and h > 0:
            img = img.resize((int(w), int(h)))
        self._image.paste(img, (int(x), int(y)))
        self._refresh()

    # ---------- image / pixels ----------

    @property
    def image(self):
        return self._image

    def get_pixel_color_rgb(self, x, y):
        return self._image.getpixel((int(x), int(y)))

    def get_pixel(self, x, y):
        return self.get_pixel_color_rgb(x, y)

    def get_pixel_color(self, x, y):
        return Color.to_hex(self.get_pixel_color_rgb(x, y))

    def get_pixels(self):
        return [[self.get_pixel_color_rgb(x, y)
                 for y in range(self._height)]
                for x in range(self._width)]

    def get_pixel_colors(self):
        return [[self.get_pixel_color(x, y)
                 for y in range(self._height)]
                for x in range(self._width)]

    @property
    def pixels(self):
        return self.get_pixels()

    @property
    def pixel_colors(self):
        return self.get_pixel_colors()

    # ---------- saving ----------

    def save(self, filename):
        self._image.save(filename)

    def save_as(self, filename):
        self.save(filename)

    # ---------- properties / setters ----------

    @property
    def width(self):
        return self._width

    def get_width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def get_height(self):
        return self._height

    @property
    def size(self):
        return (self._width, self._height)

    def get_size(self):
        return self.size

    def set_size(self, width, height):
        width, height = int(width), int(height)
        new_img = Image.new("RGB", (width, height), self._background)
        new_img.paste(self._image.crop((0, 0, min(width, self._width),
                                       min(height, self._height))), (0, 0))
        self._width, self._height = width, height
        self._image = new_img
        self._draw = ImageDraw.Draw(self._image)
        self._refresh()

    def set_width(self, width):
        self.set_size(width, self._height)

    def set_height(self, height):
        self.set_size(self._width, height)

    @property
    def background(self):
        return self._background

    def get_background(self):
        return self._background

    def set_background(self, color):
        old = self._image
        self._background = color
        self._image = Image.new("RGB", (self._width, self._height), color)
        self._image.paste(old)
        self._draw = ImageDraw.Draw(self._image)
        self._refresh()

    @property
    def color(self):
        return self._outline

    @color.setter
    def color(self, value):
        self._outline = value

    def get_color(self):
        return self._outline

    def set_color(self, color):
        self._outline = color

    @property
    def fill_color(self):
        return self._fill

    @fill_color.setter
    def fill_color(self, value):
        self._fill = value

    def get_fill_color(self):
        return self._fill

    def set_fill_color(self, color):
        self._fill = color

    @property
    def stroke(self):
        return self._stroke

    @stroke.setter
    def stroke(self, value):
        self._stroke = int(value)

    @property
    def stroke_width(self):
        return self._stroke

    def get_stroke(self):
        return self._stroke

    def get_stroke_width(self):
        return self._stroke

    def set_stroke(self, width):
        self._stroke = int(width)

    def set_stroke_width(self, width):
        self.set_stroke(width)

    @property
    def title(self):
        return self._title

    def get_title(self):
        return self._title

    def set_title(self, title):
        self._title = str(title)

    @property
    def resizable(self):
        return False

    def is_resizable(self):
        return False

    def set_resizable(self, value):
        # Notebook output is not a desktop window.
        self._resizable = False

    def sleep(self, ms):
        time.sleep(ms / 1000.0)

    # Desktop-window methods retained as harmless compatibility no-ops.
    def center(self):
        pass

    def set_location(self, x, y):
        self._x, self._y = x, y

    def get_location(self):
        return (self._x, self._y)

    def set_visible(self, visible):
        self._visible = bool(visible)
        if self._visible:
            self.show()

    def set_status(self, text):
        pass

    def message(self, text, title=""):
        print(text)

    def add_key_listener(self, function, event_type="press"):
        raise NotImplementedError("Keyboard listeners are not supported in inline Colab/Jupyter output.")

    def add_mouse_listener(self, function, event_type="click"):
        raise NotImplementedError("Mouse listeners are not supported in inline Colab/Jupyter output.")

    def animate(self, delay, func):
        while self.is_visible():
            self.sleep(delay)
            func()
