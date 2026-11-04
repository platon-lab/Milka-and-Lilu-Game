"""Песочница + сюжет. Запуск: python main.py"""
import os
import random

import pygame

from sim import World, COLORS, EMPTY, SAND, WATER, STONE, ACID, FIRE, POWDER, OIL, METAL
from entities import Animal
from story import Story

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")

COLS, ROWS = 150, 92          # размер поля в клетках
TOOLBAR_H = 58
FPS = 30
MAX_PETS_EACH = 4
BRUSH_SIZES = [1, 2, 3, 5, 8]
DOG_H, CAT_H = 9, 11          # высота животных в клетках

TOOLS = [
    ("Песок", SAND), ("Вода", WATER), ("Камень", STONE), ("Кислота", ACID),
    ("Нефть", OIL), ("Порох", POWDER), ("Огонь", FIRE), ("Металл", METAL),
    ("Ластик", EMPTY), ("Пёс", "dog"), ("Кот", "cat"),
]
UTILS = [("Кисть", "brush"), ("Очистить", "clear"), ("Меню", "menu")]

BG = (10, 11, 16)
BTN = (45, 50, 68)
BTN_ACTIVE = (230, 200, 90)
BTN_BORDER = (90, 95, 115)


def asset_path(name):
    """Ищем файл в папке assets/, а если её нет — рядом с main.py."""
    for folder in (ASSETS, BASE_DIR):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    return None


def load_img(name):
    return pygame.image.load(asset_path(name)).convert_alpha()


def load_font(size):
    path = asset_path("font.ttf")
    if path:
        return pygame.font.Font(path, size)
    return pygame.font.SysFont("arial,dejavusans,sans", size)


def draw_button(surf, rect, label, font, active=False, swatch=None):
    pygame.draw.rect(surf, BTN_ACTIVE if active else BTN, rect, border_radius=8)
    pygame.draw.rect(surf, BTN_BORDER, rect, 2, border_radius=8)
    if swatch is not None:
        pygame.draw.rect(surf, swatch, (rect.x + 6, rect.y + 6, 10, 10), border_radius=3)
    color = (20, 20, 20) if active else (245, 245, 245)
    txt = font.render(label, True, color)
    surf.blit(txt, txt.get_rect(center=rect.center))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Песочница")
        self.screen = pygame.display.set_mode((960, 600), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = load_font(18)
        self.small = load_font(14)
        self.tb_font = load_font(13)
        self.big = load_font(40)
        self.dog_img = load_img("dog.png")
        self.cat_img = load_img("cat.png")

        self.world = World(COLS, ROWS)
        self.grid_surf = pygame.Surface((COLS, ROWS))
        self.state = "menu"           # menu | sandbox | story
        self.story = None
        self.tool = SAND
        self.brush = 2
        self.running = True
        self.layout()

    # ----- раскладка -----
    def layout(self):
        self.screen = pygame.display.get_surface()
        self.sw, self.sh = self.screen.get_size()
        self.canvas_h = self.sh - TOOLBAR_H
        self.cell = max(2, min(self.sw // COLS, self.canvas_h // ROWS))
        self.ox = (self.sw - COLS * self.cell) // 2
        self.oy = (self.canvas_h - ROWS * self.cell) // 2

        items = [("tool", v, lbl) for lbl, v in TOOLS] + [(k, None, lbl) for lbl, k in UTILS]
        bw = (self.sw - 8) // len(items)
        self.toolbar = []
        for i, (kind, val, label) in enumerate(items):
            rect = pygame.Rect(4 + i * bw + 2, self.sh - TOOLBAR_H + 6, bw - 4, TOOLBAR_H - 12)
            self.toolbar.append((rect, kind, val, label))

        mw, mh = min(360, self.sw - 40), 60
        mx = self.sw // 2 - mw // 2
        self.menu_buttons = [
            (pygame.Rect(mx, self.sh // 2 - 20, mw, mh), "story", "Сюжетный режим"),
            (pygame.Rect(mx, self.sh // 2 + 60, mw, mh), "sandbox", "Песочница"),
            (pygame.Rect(mx, self.sh // 2 + 140, mw, mh), "quit", "Выход"),
        ]

    # ----- питомцы -----
    def spawn_pets(self, world):
        world.animals = [
            Animal(world, "dog", self.dog_img, COLS // 2 - 12, ROWS, DOG_H),
            Animal(world, "cat", self.cat_img, COLS // 2 + 6, ROWS, CAT_H),
        ]

    def spawn_at(self, pos):
        gx, gy = self.grid_pos(pos)
        if gx is None:
            return
        kind = self.tool
        if sum(1 for a in self.world.animals if a.kind == kind) >= MAX_PETS_EACH:
            return
        if kind == "dog":
            a = Animal(self.world, "dog", self.dog_img, gx, max(1, gy), DOG_H)
        else:
            a = Animal(self.world, "cat", self.cat_img, gx, max(1, gy), CAT_H)
        self.world.animals.append(a)

    # ----- режимы -----
    def start_sandbox(self):
        self.world.clear()
        self.story = None
        self.state = "sandbox"

    def start_story(self):
        self.world = World(COLS, ROWS)
        self.story = Story(self.world, self.spawn_pets)
        self.state = "story"

    # ----- ввод -----
    def grid_pos(self, pos):
        gx = (pos[0] - self.ox) // self.cell
        gy = (pos[1] - self.oy) // self.cell
        if 0 <= gx < COLS and 0 <= gy < ROWS:
            return gx, gy
        return None, None

    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False
        elif ev.type == pygame.VIDEORESIZE:
            self.layout()
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            if self.state == "menu":
                self.running = False
            else:
                self.state = "menu"
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.on_click(ev.pos)

    def on_click(self, pos):
        if self.state == "menu":
            for rect, action, _ in self.menu_buttons:
                if rect.collidepoint(pos):
                    if action == "story":
                        self.start_story()
                    elif action == "sandbox":
                        self.start_sandbox()
                    elif action == "quit":
                        self.running = False
            return

        if pos[1] >= self.canvas_h:
            for rect, kind, val, _ in self.toolbar:
                if rect.collidepoint(pos):
                    self.use_tool(kind, val)
                    break
            return

        if self.story and self.story.dialog_active:
            self.story.click()
            return

        if isinstance(self.tool, str):
            self.spawn_at(pos)

    def use_tool(self, kind, val):
        if kind == "tool":
            self.tool = val
        elif kind == "brush":
            i = BRUSH_SIZES.index(self.brush)
            self.brush = BRUSH_SIZES[(i + 1) % len(BRUSH_SIZES)]
        elif kind == "clear":
            if self.state == "sandbox":
                self.world.clear()
            else:
                self.world.clear_grid()   # в сюжете питомцев не трогаем
        elif kind == "menu":
            self.state = "menu"

    # ----- обновление -----
    def update(self, dt):
        if self.state not in ("sandbox", "story"):
            return
        if self.story:
            self.story.update(self.world)
        self.world.step()
        for a in self.world.animals:
            a.update(dt)

        blocked = self.story is not None and self.story.dialog_active
        if pygame.mouse.get_pressed()[0] and not blocked and isinstance(self.tool, int):
            pos = pygame.mouse.get_pos()
            if pos[1] < self.canvas_h:
                gx, gy = self.grid_pos(pos)
                if gx is not None:
                    self.world.paint(gx, gy, self.brush, self.tool)

    # ----- отрисовка -----
    def render_grid(self):
        s = self.grid_surf
        s.fill(COLORS[EMPTY])
        g = self.world.g
        for y in range(ROWS):
            row = g[y]
            for x in range(COLS):
                t = row[x]
                if t:
                    s.set_at((x, y), COLORS[t])

    def draw(self):
        scr = self.screen
        scr.fill(BG)
        if self.state == "menu":
            self.draw_menu()
            return

        ox, oy = self.ox, self.oy
        if self.world.shake > 0.5:
            ox += random.randint(-3, 3)
            oy += random.randint(-3, 3)
        self.render_grid()
        scaled = pygame.transform.scale(self.grid_surf, (COLS * self.cell, ROWS * self.cell))
        scr.blit(scaled, (ox, oy))

        for a in self.world.animals:
            a.draw(scr, self.cell, ox, oy, self.small)

        if self.story:
            self.story.draw(scr, self.font, self.small, self.sw)
        else:
            hint = self.small.render("Рисуй мышкой или пальцем. Esc — меню.", True, (150, 155, 170))
            scr.blit(hint, (12, 10))

        self.draw_toolbar()

    def draw_toolbar(self):
        pygame.draw.rect(self.screen, (24, 26, 36), (0, self.canvas_h, self.sw, TOOLBAR_H))
        for rect, kind, val, label in self.toolbar:
            if kind == "tool":
                active = (val == self.tool)
                swatch = COLORS.get(val) if isinstance(val, int) else None
                draw_button(self.screen, rect, label, self.tb_font, active, swatch)
            elif kind == "brush":
                draw_button(self.screen, rect, f"Кисть {self.brush}", self.tb_font)
            else:
                draw_button(self.screen, rect, label, self.tb_font)

    def draw_menu(self):
        scr = self.screen
        title = self.big.render("ПЕСОЧНИЦА", True, (240, 210, 120))
        scr.blit(title, title.get_rect(center=(self.sw // 2, self.sh // 2 - 110)))
        sub = self.font.render("Сюжет о заводе, двух питомцах и очень много песка", True, (170, 175, 190))
        scr.blit(sub, sub.get_rect(center=(self.sw // 2, self.sh // 2 - 60)))
        for rect, _, label in self.menu_buttons:
            draw_button(scr, rect, label, self.font)

    # ----- главный цикл -----
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                self.handle_event(ev)
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
