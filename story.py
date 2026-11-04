"""Сюжетный режим: главы, диалоги и задания.

Задания проверяются прямо по состоянию симуляции — например,
«сколько камня построено» или «все ли питомцы в домике».
"""
import pygame

from sim import EMPTY, WATER, STONE, ACID, FIRE, POWDER, OIL, METAL


def wrap(text, font, width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if font.size(test)[0] <= width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------- карта сюжета ----------

def house_rect(world):
    """Внутренность домика для питомцев: x0, y0, x1, y1 (x1, y1 не входят)."""
    return 4, world.h - 15, 20, world.h - 1


def in_house(world, animal):
    x0, y0, x1, y1 = house_rect(world)
    return x0 <= animal.x < x1 and y0 < animal.y <= y1 and animal.hp > 0


def build_map(world):
    """Фон сюжета: домик слева и завод справа. Питомцы добавляются отдельно."""
    w, h = world.w, world.h
    world.clear()
    # домик (стены из металла, дверь справа внизу)
    world.frame(3, h - 16, 21, h, METAL)
    world.fill(20, h - 13, 21, h - 1, EMPTY)
    # завод (справа): корпус и склад с порохом
    world.frame(w - 44, h - 34, w - 5, h, METAL)
    world.fill(w - 38, h - 10, w - 12, h - 2, POWDER)


def setup_spark(world):
    """Искра: нефтяная дорожка от огня к бочкам с порохом."""
    w, h = world.w, world.h
    world.fill(w - 43, h - 9, w - 38, h - 8, METAL)     # полка
    world.fill(w - 41, h - 10, w - 38, h - 9, OIL)      # нефть на полке
    world.set(w - 42, h - 10, FIRE)                     # огонёк


def setup_pets_to_house(world):
    for a in world.animals:
        a.goal = 12.0
        a.scare = 0.0


def setup_acid(world):
    cx = world.w // 2
    world.fill(cx - 6, 6, cx + 6, 9, ACID)


# ---------- главы ----------

CHAPTERS = [
    {
        "title": "Глава 1. Дым с завода",
        "lines": [
            ("Бублик", "Мур... опять завод дымит. Вон какой чёрный дым."),
            ("Мурка", "И на складе у них бочки с порохом. Это опасно."),
            ("Бублик", "Надо отгородить нас каменной стеной!"),
        ],
        "task": "Построй каменную стену: выбери «Камень» и рисуй по полю.",
        "done": lambda world: world.count(STONE) >= 90,
    },
    {
        "title": "Глава 2. Искра",
        "lines": [
            ("Мурка", "Ой! Искра упала на нефть! Огонь ползёт к порохом!"),
            ("Бублик", "Лей воду, быстрее, пока не рвануло!"),
        ],
        "setup": setup_spark,
        "task": "Потуши огонь водой (выбери «Вода»), пока он не добрался до пороха.",
        "done": lambda world: world.count(FIRE) == 0 and world.count(WATER) >= 40,
    },
    {
        "title": "Глава 3. Укрытие",
        "lines": [
            ("Бублик", "Мы напуганы! Побежали в домик за дверью!"),
            ("Мурка", "Только быстрее, нас всё ещё пугает дым!"),
        ],
        "setup": setup_pets_to_house,
        "task": "Загони обоих питомцев в металлический домик слева.",
        "done": lambda world: len(world.animals) >= 2
        and all(in_house(world, a) for a in world.animals),
    },
    {
        "title": "Глава 4. Кислота",
        "lines": [
            ("Мурка", "Из цистерны на заводе льётся кислота! Она ест всё подряд!"),
            ("Бублик", "Она съедает песок и камень. Надо дать ей вытечь и выветриться."),
        ],
        "setup": setup_acid,
        "task": "Дождись, пока кислота исчезнет. Можно построить стены, чтобы её остановить.",
        "done": lambda world: world.count(ACID) == 0,
    },
    {
        "title": "Эпилог",
        "lines": [
            ("Бублик", "Ура! Мы спасли город и не поджарились!"),
            ("Мурка", "Теперь можно и в песочнице поиграться. Жми «Меню»!"),
        ],
        "task": None,
        "done": None,
    },
]


class Story:
    def __init__(self, world, on_start):
        """on_start(world) добавляет питомцев после постройки карты."""
        self.world = world
        self.on_start = on_start
        self.chapter = 0
        self.line = 0
        self.phase = "dialog"   # dialog | task | finished
        build_map(world)
        on_start(world)

    @property
    def dialog_active(self):
        return self.phase == "dialog"

    @property
    def finished(self):
        return self.phase == "finished"

    def click(self):
        if self.phase != "dialog":
            return
        ch = CHAPTERS[self.chapter]
        self.line += 1
        if self.line >= len(ch["lines"]):
            if ch.get("setup"):
                ch["setup"](self.world)
            if ch["task"] is None:
                self._next_chapter()
            else:
                self.phase = "task"

    def update(self, world):
        if self.phase != "task":
            return
        ch = CHAPTERS[self.chapter]
        if ch["done"](world):
            self._next_chapter()

    def _next_chapter(self):
        self.chapter += 1
        self.line = 0
        self.phase = "finished" if self.chapter >= len(CHAPTERS) else "dialog"

    def draw(self, surf, font, small, width):
        """Окно сюжета сверху поля."""
        box = pygame.Rect(12, 10, width - 24, 118)
        shade = pygame.Surface(box.size, pygame.SRCALPHA)
        shade.fill((10, 12, 20, 215))
        surf.blit(shade, box.topleft)
        pygame.draw.rect(surf, (90, 95, 115), box, 2, border_radius=10)

        if self.phase == "finished":
            txt = font.render("Сюжет пройден! Песочница открыта — жми «Меню».", True, (240, 210, 120))
            surf.blit(txt, txt.get_rect(center=box.center))
            return

        ch = CHAPTERS[self.chapter]
        title = small.render(ch["title"], True, (150, 160, 190))
        surf.blit(title, (box.x + 14, box.y + 8))

        if self.phase == "dialog":
            speaker, text = ch["lines"][self.line]
            color = (240, 200, 120) if speaker == "Бублик" else (170, 220, 255)
            name = font.render(speaker + ":", True, color)
            surf.blit(name, (box.x + 14, box.y + 30))
            y = box.y + 30 + name.get_height() + 4
            for line in wrap(text, font, box.width - 28)[:3]:
                surf.blit(font.render(line, True, (235, 235, 235)), (box.x + 14, y))
                y += font.get_linesize()
            hint = small.render("Нажми на поле, чтобы продолжить", True, (120, 130, 150))
            surf.blit(hint, (box.right - hint.get_width() - 14, box.bottom - hint.get_height() - 6))
        else:
            task = ch["task"]
            y = box.y + 34
            for line in wrap("Задание: " + task, font, box.width - 28)[:3]:
                surf.blit(font.render(line, True, (250, 230, 130)), (box.x + 14, y))
                y += font.get_linesize()
