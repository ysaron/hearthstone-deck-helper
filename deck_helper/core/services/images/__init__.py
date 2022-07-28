import requests
import time
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from collections import namedtuple
from qrcode import QRCode, constants

from django.conf import settings
from django.core.files import File
from django.db.models import Q

from decks.models import Deck
from cards.models import Card
from .config import SUPPORTED_LANGUAGES, IMAGE_CLASS_MAP, BASE_FONT

Point = namedtuple('Point', ['x', 'y'])
Size = namedtuple('Size', ['x', 'y'])
Window = namedtuple('Window', ['size', 'top_left'])     # определяет размеры и положение инфо-окна на рендере

COMPONENTS = Path(__file__).resolve().parent / 'components'


class Picture:
    """
    Класс для работы с изображениями в проекте.

    Объединяет в одну сущность изображение, адрес в файловой системе, удаленный адрес,
    возможность скачивания, удаления и сохранения в Django ``ImageField``
    """

    def __init__(self, language: str = 'en'):
        self.language = language
        self.__check_language()
        self.name = ''
        self.path = Path()                                  # адрес в файловой системе
        self.url = 'https://art.hearthstonejson.com/v1'     # URL для скачивания
        self.data = BytesIO()                               # изображение

    def __check_language(self):
        languages_list = SUPPORTED_LANGUAGES.keys()
        if self.language not in languages_list:
            raise ValueError(f'Unsupported language: {self.language}. Allowed: {", ".join(languages_list)}')

    def download(self):
        """ Скачивает файл по URL в файлоподобный объект ``self.data`` """
        try:
            r = requests.get(self.url, stream=True)
        except Exception as e:
            raise ConnectionError(f'Cannot download [{self.url}]\nError: {e}')

        for chunk in r.iter_content(1024):
            self.data.write(chunk)

        time.sleep(0.3)

    @property
    def exists(self):
        """ Проверяет наличие изображения в файловой системе """
        return self.path.is_file()

    def erase(self):
        """ Удаляет изображение из файловой системы """
        self.path.unlink(missing_ok=True)

    @property
    def for_imagefield(self):
        """
        Возвращает словарь с именованными аргументами для ``ImageField`` (для распаковки **).

        Пример:

        ``model.image.save(**picture.for_imagefield)``
        """
        return {'name': self.path.name, 'content': File(self.data)}

    def __str__(self):
        return f'{self.path} [{self.language}]'


class CardRender(Picture):
    """ Локализованное изображение карты Hearthstone """

    def __init__(self, name: str, language: str = 'en'):
        super().__init__(language=language)
        self.name = name
        self.path: Path = settings.MEDIA_ROOT / 'cards' / self.language / f'{self.name}.png'
        self.url = f'{self.url}/render/latest/{SUPPORTED_LANGUAGES[self.language]["loc"]}/256x/{self.name}.png'


class Thumbnail(Picture):
    """ Миниатюра для отображения карты в колоде """

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.path: Path = settings.MEDIA_ROOT / 'cards' / 'thumbnails' / f'{self.name}.png'
        self.url = f'{self.url}/tiles/{self.name}.png'

    def fade(self, from_perc: int = 20, to_perc: int = 50):
        """
        Добавляет изображению затухание справа налево

        :param from_perc: % от ширины изображения (отсчет слева направо), определяющий место начала затухания
        :param to_perc: % от ширины изображения (отсчет слева направо), определяющий место конца затухания
        """
        if not all(0 <= x <= 100 for x in (from_perc, to_perc)):
            raise ValueError('from_perc and to_perc must be in range 0-100')

        with Image.open(self.path) as orig:
            orig.putalpha(255)          # добавление альфа-канала без прозрачности
            width, height = orig.size
            pixels = orig.load()        # получение r/w доступа к изображению на уровне пикселей

            from_, to_ = from_perc / 100, to_perc / 100

            for x in range(int(width * from_), int(width * to_)):
                alpha = int((x - width * from_) * 255 / width / (to_ - from_))
                for y in range(height):
                    pixels[x, y] = pixels[x, y][:3] + (alpha,)
            for x in range(0, int(width * from_)):
                for y in range(height):
                    pixels[x, y] = pixels[x, y][:3] + (0,)

            orig.save(self.path)


class DeckRender(Picture):
    """ Детализированное изображение колоды """

    def __init__(self, name: str, deck: Deck, language: str):
        super().__init__(language=language)
        self.name = name
        self.deck = deck
        self.path = self.__generate_path()
        self.width = 2380
        self.height = 1644
        self.coord: list[tuple[int, int]] = []

        self.footer = Window(Size(0, 0), Point(0, 0))
        self.manacurve = Window(Size(0, 0), Point(0, 0))
        self.stats = Window(Size(0, 0), Point(0, 0))
        self.craft = Window(Size(0, 0), Point(0, 0))
        self.qr = Window(Size(0, 0), Point(0, 0))

        self.__pre_format_render()
        self.__render = Image.new('RGBA', size=self.size, color='#333')
        self.__draw = ImageDraw.Draw(self.__render)

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height

    def __generate_path(self) -> Path:
        filename = f'{self.deck.pk}{int(time.time()):x}.png'
        return settings.MEDIA_ROOT / 'decks' / filename

    def download(self):
        raise NotImplementedError()

    def create(self):
        """ Создает рендер """

        self.__draw_cards()
        self.__draw_header()
        self.__draw_footer()
        self.__render.save(self.data, 'PNG')

    def __pre_format_render(self):
        """ Устанавливает разрешение и координаты плейсхолдеров в зависимости от кол-ва карт """
        cards = self.deck.included_cards
        amount = cards.count()
        vertical_num = 3 if amount <= 30 else (amount + 9) // 10
        self.height += 362 * (vertical_num - 3)
        horizontal_num = (amount + vertical_num - 1) // vertical_num    # деление с округлением вверх
        if horizontal_num < 6:
            horizontal_num = 6
        self.width = 238 * horizontal_num + 10

        x, y = 0, 120
        for card in cards:
            if x >= self.width - 238:
                x = 0
                y += 360

            # исходные PNG карт-героев смещены --> корректировка
            coords = (x - 8, y - 18) if card.card_type == Card.CardTypes.HERO else (x, y)
            self.coord.append(coords)
            x += 238

    def __draw_cards(self):
        """ Добавляет на рендер колоды рендеры ее карт """
        image_field = SUPPORTED_LANGUAGES[self.language]['field']
        for card, c in zip(self.deck.included_cards, self.coord):
            with Image.open(getattr(card, image_field), 'r') as card_render:
                if card.number > 1:
                    cr2 = card_render.rotate(angle=-8, center=(350, 150), resample=Image.BICUBIC, expand=True)
                    cr2 = self.__adjust_brightness(cr2, factor=0.8)
                    self.__render.paste(cr2, c, mask=cr2)
                card_render = self.__adjust_brightness(card_render, factor=1.2)
                card_render = self.__contrast(card_render, 1.1)
                self.__render.paste(card_render, c, mask=card_render)

    def __draw_header(self):
        """ Добавляет на рендер шапку с заголовком """
        self.__draw_title_stripe()
        self.__draw_title_text()

    def __draw_title_stripe(self):
        """ Добавляет на рендер полосу-рамку для заголовка """
        with Image.open(COMPONENTS / 'title.png', 'r') as title:
            w, h = title.size
            self.__render.paste(title, ((self.width - w) // 2, 10))

    def __draw_title_text(self):
        """ Добавляет на рендер текст заголовка """
        path: Path = COMPONENTS / BASE_FONT
        font = ImageFont.truetype(str(path), 60, encoding='utf-8')
        title_text = self.name
        self.__draw.text(
            (self.width // 2, 55),
            title_text,
            anchor='mm',
            fill='#ffffff',
            font=font,
            stroke_width=2,
            stroke_fill='#000000',
        )

    def __draw_footer(self):
        """ Добавляет на рендер нижний колонтитул """
        stripe_png = IMAGE_CLASS_MAP[self.deck.deck_class.service_name]['stripe']
        with Image.open(COMPONENTS / stripe_png, 'r') as stripe:
            footer_width, footer_height = stripe.size
            footer_size = Size(x=footer_width, y=footer_height)
            footer_topleft = Point(
                x=(self.width - footer_size.x) // 2,
                y=self.height - footer_size.y - 14
            )
            self.footer = Window(size=footer_size, top_left=footer_topleft)
            self.__render.paste(stripe, self.footer.top_left)

        self.__calc_footer_params_v1() if self.width > 2000 else self.__calc_footer_params_v2()
        self.__draw_craft_cost()
        self.__draw_mana_curve()
        self.__draw_statistics()
        self.__draw_qr()

    def __calc_footer_params_v1(self):
        """ Рассчитывает размеры и положение инфо-окон нижнего колонтитула (рендер *шире* 2000px) """
        max_window_height = 330
        max_window_width = 550
        qr_size = Size(x=max_window_height, y=max_window_height)    # квадрат со стороной == макс. высоте
        manacurve_size = Size(x=max_window_width, y=max_window_height)
        stats_size = Size(x=max_window_width + 10, y=max_window_height)
        craft_size = Size(x=max_window_height, y=100)
        gap = int((self.width - qr_size.x - manacurve_size.x - stats_size.x - craft_size.x) / 5)
        manacurve_topleft = Point(
            x=gap,
            y=self.footer.top_left.y + (self.footer.size.y - manacurve_size.y) // 2 + 5
        )
        craft_topleft = Point(
            x=2 * gap + manacurve_size.x,
            y=self.footer.top_left.y + (self.footer.size.y - craft_size.y) // 2 + 5
        )
        qr_topleft = Point(
            x=3 * gap + manacurve_size.x + craft_size.x,
            y=self.footer.top_left.y + (self.footer.size.y - qr_size.y) // 2 + 5
        )
        stats_topleft = Point(
            x=4 * gap + manacurve_size.x + craft_size.x + qr_size.x,
            y=self.footer.top_left.y + (self.footer.size.y - stats_size.y) // 2 + 5
        )
        self.manacurve = Window(size=manacurve_size, top_left=manacurve_topleft)
        self.craft = Window(size=craft_size, top_left=craft_topleft)
        self.qr = Window(size=qr_size, top_left=qr_topleft)
        self.stats = Window(size=stats_size, top_left=stats_topleft)

    def __calc_footer_params_v2(self):
        """ Рассчитывает размеры и положение инфо-окон нижнего колонтитула (рендер *уже* 2000px) """
        max_window_height = 330
        max_window_width = 550
        craft_width = 230
        qr_size = Size(x=craft_width, y=craft_width)
        craft_height = max_window_height - qr_size.y - 10
        craft_size = Size(x=craft_width, y=craft_height)
        manacurve_size = Size(x=max_window_width, y=max_window_height)
        stats_size = Size(x=max_window_width + 10, y=max_window_height)
        gap = int((self.width - manacurve_size.x - qr_size.x - stats_size.x) / 4)
        manacurve_topleft = Point(
            x=gap,
            y=self.footer.top_left.y + (self.footer.size.y - manacurve_size.y) // 2 + 5
        )
        craft_topleft = Point(
            x=2 * gap + manacurve_size.x,
            y=manacurve_topleft.y
        )
        qr_topleft = Point(
            x=craft_topleft.x,
            y=craft_topleft.y + craft_size.y + 10
        )
        stats_topleft = Point(
            x=3 * gap + manacurve_size.x + qr_size.x,
            y=manacurve_topleft.y
        )
        self.manacurve = Window(size=manacurve_size, top_left=manacurve_topleft)
        self.craft = Window(size=craft_size, top_left=craft_topleft)
        self.qr = Window(size=qr_size, top_left=qr_topleft)
        self.stats = Window(size=stats_size, top_left=stats_topleft)

    def __draw_mana_curve(self):
        """ Добавляет на рендер столбчатую диаграмму, отражающую распределение карт колоды по стоимости """
        cards = self.deck.included_cards
        cost_distribution = self.__calc_cost_distribution(cards)
        mfc_value = max(cost_distribution)
        col_max_height = self.manacurve.size.y - 50
        col_width = int(self.manacurve.size.x / 100 * 8)
        gap = int(col_width / 8)

        x0, y0 = self.manacurve.top_left.x, self.manacurve.top_left.y
        x1, y1 = self.manacurve.top_left.x + self.manacurve.size.x, self.manacurve.top_left.y + self.manacurve.size.y
        one_card_height = col_max_height / 10 if mfc_value <= 10 else col_max_height / mfc_value

        path: Path = COMPONENTS / BASE_FONT
        font_1 = ImageFont.truetype(str(path), 44, encoding='utf-8')
        font_2 = ImageFont.truetype(str(path), 26, encoding='utf-8')

        self.__draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline='#ffffff', fill='#333', width=2)

        x0 += gap // 2      # корректировка положения столбцов по горизонтали
        for cost, value in enumerate(cost_distribution):
            rect_area = [
                x0 + (col_width + gap) * cost + gap,
                y1 - (self.manacurve.size.y - col_max_height) - one_card_height * value + gap,
                x0 + (col_width + gap) * cost + gap + col_width,
                y1 - (self.manacurve.size.y - col_max_height) + gap,
            ]
            if not value:
                # улучшение отображения столбца, соотв. 0 карт
                rect_area[1] -= 3

            if (rect_area[3] - rect_area[1]) < font_2.size + 5:
                value = 0

            cost_text_area = [
                x0 + col_width / 2 + (col_width + gap) * cost + gap,
                (y1 + rect_area[3] + gap - 10) / 2
            ]
            value_text_area = [
                cost_text_area[0],
                rect_area[1] - 10 + (one_card_height + gap) / 2,
            ]
            if value_text_area[1] < (max_y := rect_area[1] + 3 * gap):
                value_text_area[1] = max_y
            cost_digit = str(cost) if cost < 10 else '+'

            self.__draw.rectangle(rect_area, outline='#000000', fill='#ffffff', width=1)
            self.__draw.text(
                cost_text_area,
                text=cost_digit,
                anchor='mm',
                font=font_1,
                stroke_fill='#000000',
                stroke_width=1,
            )
            if value:
                self.__draw.text(value_text_area, text=str(value), anchor='mm', font=font_2, fill='#333')

    def __draw_craft_cost(self):
        """ Добавляет на нижний колонтитул информацию о стоимости колоды """

        x0, y0 = self.craft.top_left.x, self.craft.top_left.y
        x1, y1 = self.craft.top_left.x + self.craft.size.x, self.craft.top_left.y + self.craft.size.y
        self.__draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline='#ffffff', fill='#333', width=2)

        with Image.open(COMPONENTS / 'craft.png', 'r') as craft_cost_icon:
            w, h = craft_cost_icon.size
            w, h = int(w * self.craft.size.y * 0.85 / h), int(self.craft.size.y * 0.85)
            craft_cost_icon = craft_cost_icon.resize((w, h))
            self.__render.paste(craft_cost_icon, (int(x0) + 10, int(y0) + 7), mask=craft_cost_icon)

        path: Path = COMPONENTS / BASE_FONT
        font_size = 60 if self.width > 2000 else 48
        font = ImageFont.truetype(str(path), font_size, encoding='utf-8')

        self.__draw.text(
            (int(x1 + x0 + w + 10) // 2, int(y0 + y1) // 2 - 2),
            text=str(self.deck.craft_cost.get('basic')),
            anchor='mm',
            fill='#ffffff',
            font=font,
            stroke_width=1,
            stroke_fill='#ffffff',
        )

    def __draw_qr(self):
        """ Добавляет на рендер QR-код с кодом колоды """
        x0, y0 = self.qr.top_left.x, self.qr.top_left.y
        x1, y1 = self.qr.top_left.x + self.qr.size.x, self.qr.top_left.y + self.qr.size.y
        self.__draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline='#ffffff', fill='#333', width=2)

        qr = QRCode(
            version=None,
            error_correction=constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(self.deck.string)
        qr.make(fit=True)
        img = qr.make_image(
            fill_color='#333333',
            back_color='#ffffff',
        )
        resize_factor = 0.92
        offset_factor = (1 - resize_factor) / 2
        img = img.resize((
            int(self.qr.size.x * resize_factor),
            int(self.qr.size.y * resize_factor)
        ))
        self.__render.paste(
            img,
            (
                self.qr.top_left.x + int(self.qr.size.x * offset_factor) + 1,
                self.qr.top_left.y + int(self.qr.size.y * offset_factor) + 1
            ),
        )

    def __draw_statistics(self):
        """ Добавляет на рендер информацию о колоде """
        self.__draw_statistics_fmt()
        self.__draw_statistics_types()
        self.__draw_statistics_rarities()

    def __draw_statistics_fmt(self):
        """ Добавляет на рендер информацию о формате колоды """
        fmt_area_size = Size(
            x=self.stats.size.x,
            y=self.stats.size.y - (self.stats.size.x + 10) // 2 + 10
        )
        fmt_top_left = self.stats.top_left
        fmt = Window(size=fmt_area_size, top_left=fmt_top_left)
        x0, y0 = fmt.top_left.x, fmt.top_left.y
        x1, y1 = fmt.top_left.x + fmt.size.x, fmt.top_left.y + fmt.size.y
        self.__draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline='#ffffff', fill='#333', width=2)

        path: Path = COMPONENTS / BASE_FONT
        font = ImageFont.truetype(str(path), 54, encoding='utf-8')

        fmt_text = getattr(self.deck.deck_format, f'name_{self.language}').capitalize()
        fmt_text = ' '.join(fmt_text)

        self.__draw.text(
            ((x0 + x1) // 2, (y0 + y1) // 2 - 1),
            text=fmt_text,
            anchor='mm',
            fill='#ffffff',
            font=font,
            stroke_width=1,
            stroke_fill='#ffffff',
        )

    def __draw_statistics_types(self):
        """ Добавляет на рендер информацию о типах карт колоды """
        types_area_size = Size(
            x=(self.stats.size.x + 10) // 2,
            y=(self.stats.size.x - 10) // 2 - 10
        )
        types_top_left = Point(
            x=self.stats.top_left.x,
            y=self.stats.top_left.y + self.stats.size.y - types_area_size.y
        )
        types = Window(size=types_area_size, top_left=types_top_left)
        x0, y0 = types.top_left.x, types.top_left.y
        x1, y1 = types.top_left.x + types.size.x, types.top_left.y + types.size.y
        self.__draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline='#ffffff', fill='#333', width=2)

        vertical = [(x0 + x1) // 2, y0 + 10, (x0 + x1) // 2, y1 - 10]
        self.__draw.line(vertical, fill='#ffffff')
        horizontal = [x0 + 10, (y0 + y1) // 2, x1 - 10, (y0 + y1) // 2]
        self.__draw.line(horizontal, fill='#ffffff')

        path: Path = COMPONENTS / BASE_FONT
        font = ImageFont.truetype(str(path), 54, encoding='utf-8')

        card_types = (
            Card.CardTypes.MINION,
            Card.CardTypes.HERO,
            Card.CardTypes.SPELL,
            Card.CardTypes.WEAPON,
        )
        icon_coordinates = (
            Point(x=x0 + int(types.size.x / 20), y=y0 + int(types.size.y / 8)),
            Point(x=x0 + int(types.size.x * 11 / 20), y=y0 + int(types.size.y * 5 / 8)),
            Point(x=x0 + int(types.size.x / 20), y=y0 + int(types.size.y * 5 / 8)),
            Point(x=x0 + int(types.size.x * 11 / 20), y=y0 + int(types.size.y / 8)),
        )
        for data, icon_top_left in zip(card_types, icon_coordinates):
            stat = next((x for x in self.deck.types_statistics if x['data'] == data), {'num_cards': '-'})
            with Image.open(COMPONENTS / f'{data}.png', 'r') as type_icon:
                w, h = int(types.size.x / 5), int(types.size.y / 4)
                type_icon = type_icon.resize((w, h))
                self.__render.paste(type_icon, icon_top_left, mask=type_icon)

            self.__draw.text(
                (icon_top_left.x + int(w * 1.6), icon_top_left.y + h // 2 - 1),
                text=str(stat['num_cards']),
                anchor='mm',
                fill='#ffffff',
                font=font,
                stroke_width=1,
                stroke_fill='#ffffff',
            )

    def __draw_statistics_rarities(self):
        """ Добавляет на рендер информацию о редкостях карт колоды """
        rar_area_size = Size(
            x=(self.stats.size.x - 10) // 2 - 10,
            y=(self.stats.size.x - 10) // 2 - 10
        )
        rar_top_left = Point(
            x=self.stats.top_left.x + self.stats.size.x - rar_area_size.x,
            y=self.stats.top_left.y + self.stats.size.y - rar_area_size.y
        )
        rarities = Window(size=rar_area_size, top_left=rar_top_left)
        x0, y0 = rarities.top_left.x, rarities.top_left.y
        x1, y1 = rarities.top_left.x + rarities.size.x, rarities.top_left.y + rarities.size.y
        self.__draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline='#ffffff', fill='#333', width=2)

        vertical = [(x0 + x1) // 2, y0 + 10, (x0 + x1) // 2, y1 - 10]
        self.__draw.line(vertical, fill='#ffffff')
        horizontal = [x0 + 10, (y0 + y1) // 2, x1 - 10, (y0 + y1) // 2]
        self.__draw.line(horizontal, fill='#ffffff')

        path: Path = COMPONENTS / BASE_FONT
        font = ImageFont.truetype(str(path), 60, encoding='utf-8')

        rarities = {
            Card.Rarities.COMMON: '#ffffff',
            Card.Rarities.RARE: '#3366ff',
            Card.Rarities.EPIC: '#db4dff',
            Card.Rarities.LEGENDARY: '#ffa31a',
        }
        text_coordinates = (
            Point(x=x0 + int(rar_area_size.x / 4 * 3), y=y0 + int(rar_area_size.y / 4 * 3 - 1)),
            Point(x=x0 + int(rar_area_size.x / 4 * 3), y=y0 + int(rar_area_size.y / 4 - 1)),
            Point(x=x0 + int(rar_area_size.x / 4), y=y0 + int(rar_area_size.y / 4 * 3 - 1)),
            Point(x=x0 + int(rar_area_size.x / 4), y=y0 + int(rar_area_size.y / 4 - 1)),
        )
        for data, text_coord in zip(rarities.keys(), text_coordinates):
            stat = next((x for x in self.deck.rarity_statistics if x['data'] == data), {'num_cards': '-'})
            self.__draw.text(
                text_coord,
                text=str(stat['num_cards']),
                anchor='mm',
                fill=rarities.get(data, '#ffffff'),
                font=font,
                stroke_width=2,
                stroke_fill='#ffffff',
            )

    @staticmethod
    def __adjust_brightness(image: Image, factor: float) -> Image:
        """
        :param image: изображение
        :param factor: 1 - без эффекта, меньше - затемнение, больше - осветление
        """
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    @staticmethod
    def __contrast(image: Image, factor: float = 1):
        """
        Возвращает копию изображения с измененным контрастом

        :param image: изображение
        :param factor: 1 - без эффекта, меньше - уменьшить контраст, больше - увеличить
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @staticmethod
    def __calc_cost_distribution(cards) -> tuple[int, ...]:
        """
        Возвращает кортеж с распределением карт по стоимости.

        Индексы - стоимости карт, значения - количества карт данной стоимости
        """
        cost_distribution = []
        for cost in range(11):
            kwargs_1 = Q(cost=cost, number=1) if cost < 10 else Q(cost__gte=cost, number=1)
            kwargs_2 = Q(cost=cost, number=2) if cost < 10 else Q(cost__gte=cost, number=2)
            num_cards = cards.filter(kwargs_1).count() + cards.filter(kwargs_2).count() * 2
            cost_distribution.append(num_cards)

        return tuple(cost_distribution)
