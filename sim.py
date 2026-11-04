"""Клеточная песочница: каждая клетка — кусочек песка, воды, огня и т.д.

Все вещества — выдуманные игровые материалы, без реальных рецептов.
"""
import random

EMPTY, SAND, WATER, STONE, ACID, FIRE, POWDER, OIL, METAL = range(9)

NAMES = {
    EMPTY: "Ластик", SAND: "Песок", WATER: "Вода", STONE: "Камень",
    ACID: "Кислота", FIRE: "Огонь", POWDER: "Порох", OIL: "Нефть", METAL: "Металл",
}

COLORS = {
    EMPTY: (18, 20, 28),
    SAND: (222, 196, 120),
    WATER: (50, 120, 230),
    STONE: (120, 122, 130),
    ACID: (130, 245, 70),
    FIRE: (255, 130, 40),
    POWDER: (70, 70, 74),
    OIL: (100, 66, 30),
    METAL: (176, 182, 196),
}

POWDERS = (SAND, POWDER)          # сыпучие: падают, образуют кучи
LIQUIDS = (WATER, ACID, OIL)      # жидкости: растекаются
PASSABLE = (EMPTY, WATER, ACID, OIL)  # куда сыпучие могут провалиться
NEIGH4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
MAX_BLASTS_PER_STEP = 10          # ограничитель цепной реакции, чтобы не тормозило


class World:
    def __init__(self, cols, rows):
        self.w = cols
        self.h = rows
        self.g = [[EMPTY] * cols for _ in range(rows)]
        self.animals = []
        self.shake = 0.0
        self._blasts = 0

    # ----- доступ к клеткам -----
    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def get(self, x, y):
        # за пределами поля считаем камнем — это удобная «стена»
        return self.g[y][x] if self.inside(x, y) else STONE

    def set(self, x, y, t):
        if self.inside(x, y):
            self.g[y][x] = t

    def count(self, t):
        return sum(row.count(t) for row in self.g)

    # ----- заполнение -----
    def clear(self):
        """Полная очистка: и вещества, и животные."""
        self.clear_grid()
        self.animals = []

    def clear_grid(self):
        self.g = [[EMPTY] * self.w for _ in range(self.h)]

    def fill(self, x0, y0, x1, y1, t):
        """Заполнить прямоугольник (x1, y1 не включаются)."""
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.g[y][x] = t

    def frame(self, x0, y0, x1, y1, t):
        """Только рамка прямоугольника."""
        for x in range(x0, x1):
            self.set(x, y0, t)
            self.set(x, y1 - 1, t)
        for y in range(y0, y1):
            self.set(x0, y, t)
            self.set(x1 - 1, y, t)

    def paint(self, cx, cy, r, t):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if not self.inside(x, y):
                    continue
                if (x - cx) ** 2 + (y - cy) ** 2 > r * r + r:
                    continue
                if t in POWDERS and random.random() < 0.35:
                    continue  # чтобы сыпучее ложилось «пылью», а не сплошняком
                self.g[y][x] = t

    # ----- шаг симуляции -----
    def step(self):
        self._blasts = 0
        g, w = self.g, self.w
        for y in range(self.h - 1, -1, -1):
            left_to_right = random.random() < 0.5
            xs = range(w) if left_to_right else range(w - 1, -1, -1)
            for x in xs:
                t = g[y][x]
                if t == EMPTY or t == STONE or t == METAL:
                    continue
                if t == FIRE:
                    self._fire(x, y)
                elif t == ACID:
                    if not self._acid(x, y):
                        self._liquid(x, y)
                elif t in POWDERS:
                    self._powder(x, y)
                elif t in LIQUIDS:
                    self._liquid(x, y)
        if self.shake > 0:
            self.shake = max(0.0, self.shake - 0.6)

    def _pass(self, x, y):
        return self.inside(x, y) and self.g[y][x] in PASSABLE

    def _swap(self, x1, y1, x2, y2):
        g = self.g
        g[y1][x1], g[y2][x2] = g[y2][x2], g[y1][x1]

    def _powder(self, x, y):
        if self._pass(x, y + 1):
            self._swap(x, y, x, y + 1)
            return
        d = 1 if random.random() < 0.5 else -1
        if self._pass(x + d, y + 1):
            self._swap(x, y, x + d, y + 1)
        elif self._pass(x - d, y + 1):
            self._swap(x, y, x - d, y + 1)

    def _liquid(self, x, y):
        if self._pass(x, y + 1):
            self._swap(x, y, x, y + 1)
            return
        d = 1 if random.random() < 0.5 else -1
        for dx, dy in ((d, 1), (-d, 1), (d, 0), (-d, 0)):
            if self._pass(x + dx, y + dy):
                self._swap(x, y, x + dx, y + dy)
                return

    def _acid(self, x, y):
        """Кислота съедает песок и камень. Возвращает True, если сама исчезла."""
        g = self.g
        if random.random() < 0.004:
            g[y][x] = EMPTY
            return True
        for dx, dy in NEIGH4:
            nx, ny = x + dx, y + dy
            if self.inside(nx, ny) and g[ny][nx] in (SAND, STONE) and random.random() < 0.06:
                g[ny][nx] = EMPTY
                if random.random() < 0.35:
                    g[y][x] = EMPTY
                    return True
                return False
        return False

    def _fire(self, x, y):
        g = self.g
        if random.random() < 0.2:
            g[y][x] = EMPTY          # огонь гаснет сам
            return
        for dx, dy in NEIGH4:
            nx, ny = x + dx, y + dy
            if not self.inside(nx, ny):
                continue
            n = g[ny][nx]
            if n == WATER:
                g[y][x] = EMPTY      # вода тушит
                return
            if n == OIL and random.random() < 0.15:
                g[ny][nx] = FIRE
            elif n == POWDER and random.random() < 0.6:
                self.explode(nx, ny)
                return

    def explode(self, cx, cy, r=6):
        if self._blasts >= MAX_BLASTS_PER_STEP:
            self.set(cx, cy, FIRE)
            return
        self._blasts += 1
        self.shake = min(12.0, self.shake + 6.0)
        r2 = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if not self.inside(x, y):
                    continue
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if d2 > r2:
                    continue
                t = self.g[y][x]
                if t in (STONE, METAL) and d2 > 6:
                    continue     # по краю взрыва стены выдерживают
                self.g[y][x] = FIRE if random.random() < 0.55 else EMPTY
        for a in self.animals:
            a.blast(cx, cy, r)
