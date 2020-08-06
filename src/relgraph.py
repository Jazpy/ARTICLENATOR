import itertools
import cairo
import math

class RelGraph:
  def __init__(self):
    self.vertices = set()
    self.edges    = dict()

  def link_articles(self, articles):
    for edge in itertools.combinations(articles, 2):
      self.vertices.add(edge[0].get_id())
      self.vertices.add(edge[1].get_id())

      k_tuple = (edge[0].get_id(), edge[1].get_id())
      self.edges[k_tuple] = self.edges.get(k_tuple, 0) + 1

  # Inner circle class for rendering
  class CairoCircle:
    def __init__(self, x, y, r=0.03):
      self.x = x
      self.y = y
      self.r = r

    def draw(self, ctx):
      ctx.arc(self.x, self.y, self.r, 0, 2 * math.pi)
      ctx.fill()

    def get_center(self):
      return (self.x, self.y)

  def cairo_render(self, pathname, side):
    if len(self.vertices) < 2:
      print('Not enough data available for rendering!')
      return

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, side, side)
    context = cairo.Context(surface)
    context.scale(side, side)

    # Create a circle for each vertex
    v_angle      = 0.0
    v_angle_step = (math.pi * 2.0) / float(len(self.vertices))
    circles = {}
    for i, v in enumerate(sorted(self.vertices)):
      x = 0.5 + (0.4 * math.cos(v_angle_step * i))
      y = 0.5 + (0.4 * math.sin(v_angle_step * i))
      circles[v] = self.CairoCircle(x, y)

    # Draw all edges
    for edge, weight in self.edges.items():
      # Get relevant circles
      c0 = circles[edge[0]]
      c1 = circles[edge[1]]

      # Get centers for circles
      c0_c = c0.get_center()
      c1_c = c1.get_center()

      # Draw the line
      curr_weight   = 0.001 * math.log(float(weight), 1.5)
      curr_darkness = 0.1 * math.log(float(weight), 2)
      context.set_line_width(curr_weight)
      context.set_source_rgba(0, 1.0 - curr_darkness, 0, 1)
      context.move_to(c0_c[0], c0_c[1])
      context.line_to(c1_c[0], c1_c[1])
      context.stroke()

    # Draw all circles
    context.set_source_rgb(0, 1, 0)
    context.set_line_width(0.01)
    for circle in circles.values():
      circle.draw(context)

    # Write PNG
    surface.write_to_png(f'{pathname}.png')
