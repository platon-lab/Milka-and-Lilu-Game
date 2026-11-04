"""Питомцы: ходят по песку, падают, убегают от огня и кислоты.

Координаты в клетках: x — центр, y — уровень ног (низ), h — высота в клетках.
"""
import math
import random

import pygame

from sim import SAND, STONE, METAL, POWDER, FIRE, ACID

SOLID = (SAND, STONE, METAL, POWDER)
HAZARD = (FIRE, ACID)

GRAVITY = 40.0
WALK = 3.0
RUN = 7.0
JUMP = 13.0
HAZARD_DPS = 18.0
RESPAWN_AFTER = 6.0


class Animal:
    def __init__(self, world, kind, image, x, y, height_cells):
        self.world = world
        self.kind = kind
        self.name = "Бублик" if kind == "dog" else "Мурка"
        self.img = image
        self.h = float(height_cells)
        self.w = self.h * image.get_width() / image.get_height()
        self.home = (float(x), float(y))
        self.x = float(x)
        self.y = float(y)
        self.vy = 0.0
        self.dir = random.choice((-1, 1))
        self.hp = 100.0
        self.dead_time = 0.0
        self.scare = 0.0
        self.goal = None          # куда идти (используется в сюжете)
        self.idle = random.uniform(1.0, 3.0)
        self.pause = False
        self._cache = {}

    # ----- вспомогательное -----
    def _solid_at(self, px, py):
        return self.world.get(math.floor(px), math.floor(py)) in SOLID

    def _hazard_nearby(self):
        """Средняя x-координата рядом стоящих опасностей или None."""
        x0 = math.floor(self.x - self.w / 2) - 1
        x1 = math.floor(self.x + self.w / 2) + 1
        y0 = math.floor(self.y - self.h) - 1
        y1 = math.floor(self.y) + 1
        sx, n = 0.0, 0
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if self.world.get(xx, yy) in HAZARD:
                    sx += xx
                    n += 1
        return sx / n if n else None

    # ----- обновление -----
    def update(self, dt):
        if self.hp <= 0:
            self.dead_time += dt
            self._fall(dt)
            if self.dead_time >= RESPAWN_AFTER:
                self.hp = 100.0
                self.dead_time = 0.0
                self.x, self.y = self.home
                self.vy = 0.0
            return

        hz = self._hazard_nearby()
        if hz is not None:
            self.hp -= HAZARD_DPS * dt
            self.scare = 2.0
            self.dir = -1 if hz > self.x else 1
        self.scare = max(0.0, self.scare - dt)

        self._fall(dt)

        # решаем, идти ли
        if self.scare > 0:
            want_move = True
        elif self.goal is not None:
            d = self.goal - self.x
            want_move = abs(d) >= 1.0
            if want_move:
                self.dir = 1 if d > 0 else -1
        else:
            self.idle -= dt
            if self.idle <= 0:
                self.idle = random.uniform(1.5, 4.0)
                self.dir = random.choice((-1, 1))
                self.pause = random.random() < 0.3
            want_move = not self.pause

        if want_move:
            speed = RUN if self.scare > 0 else WALK
            self._walk(speed * dt)

        # не даём уйти за край
        self.x = min(max(self.x, self.w / 2 + 1), self.world.w - self.w / 2 - 1)

    def _fall(self, dt):
        # если застряли внутри песка — выталкиваем вверх
        if self._solid_at(self.x, self.y - 0.5):
            self.y -= 1.0
            self.vy = 0.0
            return
        self.vy = min(self.vy + GRAVITY * dt, 22.0)
        steps = max(1, int(abs(self.vy * dt) * 4) + 1)
        sub = self.vy * dt / steps
        for _ in range(steps):
            ny = self.y + sub
            if sub > 0 and self._solid_at(self.x, ny + 0.5):
                self.y = float(math.floor(ny + 0.5))   # приземлились
                self.vy = 0.0
                return
            self.y = ny

    def _on_ground(self):
        return self._solid_at(self.x, self.y + 0.5)

    def _walk(self, dist):
        d = self.dir
        nx = self.x + d * dist
        front_x = nx + d * (self.w / 2)
        if self._solid_at(front_x, self.y - 0.5):
            # препятствие у ног
            if self._solid_at(front_x, self.y - 2.5):
                # высокая стена — разворачиваемся
                self.dir = -d
                self.pause = False
                return
            if self._on_ground():
                self.vy = -JUMP
            return
        self.x = nx

    def blast(self, cx, cy, r):
        dx = self.x - cx
        dy = (self.y - self.h / 2) - cy
        dist = math.hypot(dx, dy)
        reach = r + 6
        if dist > reach:
            return
        k = 1.0 - dist / reach
        self.hp = max(0.0, self.hp - 90.0 * k)
        self.vy = -JUMP * 1.4 * k
        if dist > 0.01:
            self.x += dx / dist * 4.0 * k
        self.scare = 3.0

    # ----- отрисовка -----
    def draw(self, surf, cs, ox, oy, font):
        pw = max(4, int(self.w * cs))
        ph = max(4, int(self.h * cs))
        dead = self.hp <= 0
        key = (pw, ph, self.dir < 0, dead)
        if key not in self._cache:
            img = pygame.transform.smoothscale(self.img, (pw, ph))
            if self.dir < 0:
                img = pygame.transform.flip(img, True, False)
            if dead:
                img = pygame.transform.rotate(img, 90)
            self._cache[key] = img
        img = self._cache[key]
        rect = img.get_rect(midbottom=(ox + self.x * cs, oy + self.y * cs))
        surf.blit(img, rect)

        if not dead:
            bar_w = rect.width
            bar = pygame.Rect(rect.left, rect.top - 8, bar_w, 5)
            pygame.draw.rect(surf, (80, 20, 20), bar)
            fill = bar.copy()
            fill.width = int(bar_w * self.hp / 100.0)
            pygame.draw.rect(surf, (90, 220, 90), fill)
        label = font.render(self.name, True, (240, 240, 240))
        surf.blit(label, label.get_rect(midbottom=(rect.centerx, rect.top - 10)))
