import itertools
import cairo
import math

class RelGraph:
  def __init__(self, concept):
    self.concept     = concept
    self.subconcepts = dict()
    self.edges       = []

  def link_concept(self, subconcept, articles):
    self.subconcepts[subconcept] = articles

  # Inner circle class for rendering
  class CairoCircle:
    def __init__(self, x, y, r, rgba, *,
      sat_txt_x=0.0, sat_txt_y=0.0, sat_txt='', sat_txt_size=0.0,
      txt='', txt_size=0.0):
      self.x    = x
      self.y    = y
      self.r    = r
      self.rgba = rgba

      self.sat_text_x    = sat_txt_x
      self.sat_text_y    = sat_txt_y
      self.sat_text      = sat_txt
      self.sat_text_size = sat_txt_size
      self.text          = txt
      self.text_size     = txt_size

    def draw_circle(self, ctx):
      ctx.set_source_rgba(*self.rgba)
      ctx.arc(self.x, self.y, self.r, 0, 2 * math.pi)
      ctx.fill()

      ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
      ctx.set_font_size(self.text_size)
      ctx.select_font_face("Arial",
        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      (_, _, t_w, t_h, _, _) = ctx.text_extents(self.text)
      ctx.move_to(self.x - (t_w / 2.0), self.y + (t_h / 2.0))
      ctx.show_text(self.text)

      ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
      ctx.set_font_size(self.sat_text_size)
      ctx.select_font_face("Arial",
        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      (_, _, t_w, t_h, _, _) = ctx.text_extents(self.sat_text)
      ctx.move_to(self.sat_text_x - (t_w / 2.0), self.sat_text_y + (t_h / 2.0))
      ctx.show_text(self.sat_text)

    def draw_text(self, ctx):
      ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
      ctx.set_font_size(self.text_size)
      ctx.select_font_face("Arial",
        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      (_, _, t_w, t_h, _, _) = ctx.text_extents(self.text)
      ctx.move_to(self.x - (t_w / 2.0), self.y + (t_h / 2.0))
      ctx.show_text(self.text)

      ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
      ctx.set_font_size(self.sat_text_size)
      ctx.select_font_face("Arial",
        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      (_, _, t_w, t_h, _, _) = ctx.text_extents(self.sat_text)
      ctx.move_to(self.sat_text_x - (t_w / 2.0), self.sat_text_y + (t_h / 2.0))
      ctx.show_text(self.sat_text)


    def get_center(self):
      return (self.x, self.y)

  def draw_edge(self, ctx, rgba, width, c0, c1):
    ctx.set_source_rgba(*rgba)
    ctx.set_line_width(width)

    # Get centers for circles
    c0_c = c0.get_center()
    c1_c = c1.get_center()

    # Draw the line
    ctx.move_to(c0_c[0], c0_c[1])
    ctx.line_to(c1_c[0], c1_c[1])
    ctx.stroke()

  def cairo_render(self, pathname, side):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, side, side)
    context = cairo.Context(surface)
    context.scale(side, side)

    # Main, sub, and article colors
    main_rgba      = (3.0 / 255.0,  121.0 / 255.0, 1.0,           1.0)
    sub_rgba       = (70.0 / 255.0, 3.0 / 255.0,   1.0,           1.0)
    art_rgba       = (3.0 / 255.0,  1.0,           137.0 / 255.0, 1.0)

    # Main and sub text sizes
    main_txts = 0.06
    sub_txts  = 0.015
    sat_txts  = 0.004

    # Main and sub branch widths
    main_width = 0.03
    sub_width  = 0.01

    # Main concept circle coordinates and radius
    main_x = 0.5
    main_y = 0.5
    main_r = 0.2

    # Space buffers around main and subconcepts
    main_b = 0.16
    sub_b  = 0.025

    # Minimum subconcept and article radii
    min_sub_r = 0.09
    min_art_r = 0.015

    # Create main concept circle
    circles   = {}
    circle_id = 0
    circles[circle_id] = self.CairoCircle(main_x, main_y, main_r,
      main_rgba, txt=self.concept, txt_size=main_txts)
    circle_id += 1

    # Create a circle for each subconcept
    sub_r          = min(min_sub_r, 3.3 * main_r / float(len(self.subconcepts)))
    con_angle_step = (math.pi * 2.0) / float(len(self.subconcepts))
    for i, (subconcept, articles) in enumerate(self.subconcepts.items()):
      # Append subconcept circle
      sub_x  = main_x + ((main_r + main_b) * math.cos(con_angle_step * i))
      sub_y  = main_y + ((main_r + main_b) * math.sin(con_angle_step * i))
      sub_id = circle_id
      circles[circle_id] = self.CairoCircle(sub_x, sub_y, sub_r,
        sub_rgba, txt=subconcept, txt_size=sub_txts)
      circle_id += 1

      # Link main and subconcept
      self.draw_edge(context, sub_rgba, main_width,
        circles[0], circles[sub_id])

      # Add articles around subconcept
      art_r          = min(min_art_r, 3.0 * sub_r / float(len(articles)))
      sub_angle_step = (math.pi * 2.0) / float(len(articles))
      for j, article in enumerate(articles):
        # Append article circle
        art_x  = sub_x + ((sub_r + sub_b) * math.cos(sub_angle_step * j))
        art_y  = sub_y + ((sub_r + sub_b) * math.sin(sub_angle_step * j))

        art_id = circle_id
        circles[circle_id] = self.CairoCircle(art_x, art_y, min_art_r,
          art_rgba, sat_txt_x=art_x, sat_txt_y=art_y,
          sat_txt=article.get_name() + str(article.get_year())[-2:],
          sat_txt_size=sat_txts)
        circle_id += 1

        # Link subconcept and article
        self.draw_edge(context, art_rgba, sub_width,
          circles[sub_id], circles[art_id])

    # Draw all circles
    for circle in circles.values():
      circle.draw_circle(context)
    for circle in circles.values():
      circle.draw_text(context)

    # Write PNG
    surface.write_to_png(f'{pathname}.png')
