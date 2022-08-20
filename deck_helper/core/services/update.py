from django.db import transaction
import json
import re
from tqdm import tqdm

from django.utils.text import slugify
from django.conf import settings

from core.services.deck_utils import parse_deckstring
from core.services.api_workers import HsRapidApiWorker
from core.services.images import CardRender, Thumbnail
from core.exceptions import UpdateError
from core.models import HearthstoneState
from cards.models import Card, CardClass, Tribe, CardSet, Mechanic
from decks.models import Deck, Format, Inclusion

C_TYPES = {
    'minion': Card.CardTypes.MINION,
    'spell': Card.CardTypes.SPELL,
    'weapon': Card.CardTypes.WEAPON,
    'hero': Card.CardTypes.HERO,
    'hero power': Card.CardTypes.HEROPOWER,
    'location': Card.CardTypes.LOCATION,
}
RARITIES = {
    'free': Card.Rarities.NO_RARITY,
    'common': Card.Rarities.COMMON,
    'rare': Card.Rarities.RARE,
    'epic': Card.Rarities.EPIC,
    'legendary': Card.Rarities.LEGENDARY,
}
SPELL_SCHOOLS = {
    'holy': Card.SpellSchools.HOLY,
    'shadow': Card.SpellSchools.SHADOW,
    'nature': Card.SpellSchools.NATURE,
    'fel': Card.SpellSchools.FEL,
    'fire': Card.SpellSchools.FIRE,
    'frost': Card.SpellSchools.FROST,
    'arcane': Card.SpellSchools.ARCANE,
}
HIDDEN_MECHANICS = ['AIMustPlay', 'AffectedBySpellPower', 'ImmuneToSpellpower', 'InvisibleDeathrattle',
                    'OneTurnEffect']
ADDITIONAL_MECHANICS = ['Lackey', 'Dormant', 'Choose One', 'Start of Game', 'Immune']


class Updater:

    def __init__(self, writer, progress_bars: bool = True, rewrite: bool = False, reload_images: bool = False):
        self.__bar = progress_bars
        self.__rewrite = rewrite
        self.__reload_images = reload_images
        self.__writer = writer
        self.__en_cards = []
        self.__ru_cards = []
        self.__card_classes = []
        self.__tribes = []
        self.__card_sets = []
        self.__mechanics = []
        self.__hidden_mechanics = HIDDEN_MECHANICS
        self.__additional_mechanics = ADDITIONAL_MECHANICS

        self.__standard_sets = []
        self.__wild_sets = []
        self.__classic_sets = []

        self.report = {
            'FAIL_DOWNLOAD_RENDER_EN': [],
            'FAIL_DOWNLOAD_RENDER_RU': [],
            'FAIL_DOWNLOAD_THUMBNAIL': [],
        }

        self.__get_data()

    @staticmethod
    def __prepare_update():
        state = HearthstoneState.load()
        state.success = False
        state.save()

    def __get_data(self):
        """ Формирует данные карт для записи в БД """
        try:
            worker = HsRapidApiWorker()
        except ConnectionError as ce:
            raise UpdateError(ce)

        self.__writer(f'Using "{worker}"')
        self.__writer('Getting data...')
        worker.get_raw_json()
        self.__writer('Cleaning data...')
        worker.clear_data()

        self.__en_cards = worker.clean_data['en_cards']
        self.__ru_cards = worker.clean_data['ru_cards']
        self.__card_classes = worker.clean_data['classes']
        self.__tribes = worker.clean_data['tribes']
        self.__card_sets = worker.clean_data['sets']
        self.__mechanics = worker.clean_data['mechanics']
        self.__mechanics.extend(self.__additional_mechanics)

        self.__standard_sets = worker.clean_data['standard_sets']
        self.__wild_sets = worker.clean_data['wild_sets']
        self.__classic_sets = worker.clean_data['classic_sets']

        self.__version = worker.clean_data['version']

    def __clear_database(self):
        """ Удаляет все карты Hearthstone из БД """
        if self.__rewrite:
            Card.objects.all().delete()

    def __update_version(self):
        """ Обновляет текущую версию игры """
        state = HearthstoneState(version=self.__version)
        state.success = True
        state.save()

    def __write_classes(self):
        """ Записывает в БД отсутствующие классы """
        with open(settings.MODEL_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            for cls in tqdm(self.__card_classes, desc='Classes', ncols=100):
                if CardClass.objects.filter(service_name=cls).exists():
                    continue
                class_translation = translations['classes'].get(cls)
                name_en = translations['classes'][cls]['enUS'] if class_translation else cls
                card_class = CardClass(name=name_en, service_name=cls)
                card_class.name_ru = translations['classes'][cls]['ruRU'] if class_translation else cls
                card_class.save()

    @staticmethod
    def __update_classes():
        """ Обновляет данные классов на основе записанных карт """
        for cls in tqdm(CardClass.objects.all(), desc='Updating class data...', ncols=100):
            if Card.objects.filter(collectible=True, card_class=cls).exists():
                cls.collectible = True
                cls.save()

    def __write_tribes(self):
        """ Записывает в БД отсутствующие расы """
        with open(settings.MODEL_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            for t in tqdm(self.__tribes, desc='Tribes', ncols=100):
                if Tribe.objects.filter(service_name=t).exists():
                    continue
                tribe_translation = translations['tribes'].get(t)
                name_en = translations['tribes'][t]['enUS'] if tribe_translation else t
                tribe = Tribe(name=name_en, service_name=t)
                tribe.name_ru = translations['tribes'][t]['ruRU'] if tribe_translation else t
                tribe.save()

    @staticmethod
    def __write_formats():
        """ Записывает в БД отсутствующие форматы игры """
        with open(settings.MODEL_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            for fmt in tqdm(translations['formats'], desc='Formats', ncols=100):
                if Format.objects.filter(numerical_designation=fmt['num']).exists():
                    continue
                format_ = Format(numerical_designation=fmt['num'], name=fmt['name_en'])
                format_.name_ru = fmt['name_ru']
                format_.save()

    def __write_sets(self):
        """ Записывает в БД отсутствующие наборы карт """
        with open(settings.MODEL_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            formats = Format.objects.all()
            unknown_fmt = formats.get(numerical_designation=0)
            wild_fmt = formats.get(numerical_designation=1)
            standard_fmt = formats.get(numerical_designation=2)
            classic_fmt = formats.get(numerical_designation=3)

            for s in tqdm(self.__card_sets, desc='Addons', ncols=100):
                if CardSet.objects.filter(service_name=s).exists():
                    continue
                set_translation = translations['sets'].get(s)
                name_en = translations['sets'][s]['enUS'] if set_translation else s
                card_set = CardSet(name=name_en, service_name=s)
                card_set.name_ru = translations['sets'][s]['ruRU'] if set_translation else s

                if s in self.__standard_sets:
                    card_set.set_format = standard_fmt
                elif s in self.__classic_sets:
                    card_set.set_format = classic_fmt
                elif s in self.__wild_sets:
                    card_set.set_format = wild_fmt
                else:
                    card_set.set_format = unknown_fmt

                card_set.save()

            if not CardSet.objects.filter(service_name='unknown').exists():
                unknown_set = CardSet(name='unknown', service_name='unknown')
                unknown_set.name_ru = 'неизвестно'
                unknown_set.set_format = unknown_fmt
                unknown_set.save()

    def __write_mechanics(self):
        """ Записывает в БД отсутствующие механики карт """
        with open(settings.MODEL_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            for t in tqdm(self.__mechanics, desc='Mechanics', ncols=100):
                if Mechanic.objects.filter(service_name=t).exists():
                    continue
                mech_translation = translations['mechanics'].get(t)
                name_en = translations['mechanics'][t]['enUS'] if mech_translation else t
                mechanic = Mechanic(name=name_en, service_name=t)
                mechanic.name_ru = translations['mechanics'][t]['ruRU'] if mech_translation else t
                if t in self.__hidden_mechanics:
                    mechanic.hidden = True
                mechanic.save()

    @staticmethod
    def __align_card_type(type_name: str) -> str:
        """ Возвращает соответствующий тип карты, как он определен в модели """
        return C_TYPES.get(type_name.lower(), Card.CardTypes.UNKNOWN)

    @staticmethod
    def __align_rarity(rarity_name: str) -> str:
        """ Возвращает соответствующую редкость, как она определена в модели """
        return RARITIES.get(rarity_name.lower(), Card.Rarities.UNKNOWN)

    @staticmethod
    def __align_spellschool(spellschool: str):
        """ Возвращает соответствующий тип заклинания, как он определен в модели """
        return SPELL_SCHOOLS.get(spellschool.lower(), Card.SpellSchools.UNKNOWN)

    @staticmethod
    def __write_set_to_card(r_card: Card, j_card: dict):
        """ Связывает карту с набором (FK) """
        try:
            base_set = CardSet.objects.get(service_name=j_card.get('cardSet'))
        except CardSet.DoesNotExist:
            base_set = CardSet.objects.get(service_name='unknown')
        r_card.card_set = base_set

    def __write_mechanics_to_card(self, r_card: Card, j_card: dict):
        """ Связывает карту с механиками (m2m) """

        for m in self.__additional_mechanics:
            if m in r_card.text:
                r_card.mechanic.add(Mechanic.objects.get(service_name=m))

        if 'mechanics' not in j_card:
            return

        mechanics = [m['name'] for m in j_card['mechanics']]
        for m in mechanics:
            r_card.mechanic.add(Mechanic.objects.get(service_name=m))

    @staticmethod
    def __write_classes_to_card(r_card: Card, j_card: dict):
        """ Связывает карту с классами (m2m) """
        if 'classes' in j_card:
            for cls in j_card['classes']:
                r_card.card_class.add(CardClass.objects.get(service_name=cls))
        elif 'playerClass' in j_card:
            r_card.card_class.add(CardClass.objects.get(service_name=j_card['playerClass']))

    @staticmethod
    def __write_tribe_to_card(r_card: Card, j_card: dict):
        """ Связывает карту с расами (m2m) """
        if 'race' in j_card:
            r_card.tribe.add(Tribe.objects.get(service_name=j_card['race']))

    def __write_cards(self):
        """ Обновляет карты в БД """
        card_sequence = tqdm(self.__en_cards, desc='Cards', ncols=100) if self.__bar else self.__en_cards
        for index, j_card in enumerate(card_sequence, start=1):
            image_en = CardRender(name=j_card['cardId'], language='en')
            image_ru = CardRender(name=j_card['cardId'], language='ru')
            thumbnail = Thumbnail(name=j_card['cardId'])

            if all([
                not self.__rewrite,
                (r_card_queryset := Card.objects.filter(card_id=j_card['cardId'])).exists(),
                unchanged := self.__is_equivalent(r_card_queryset.first(), j_card),
                not (j_card.get('collectible', False) and not image_en.exists),
                not (j_card.get('collectible', False) and not image_ru.exists),
                not (j_card.get('collectible', False) and not thumbnail.exists),
            ]):
                # Карта обновляется, если соблюдено хотя бы 1 из условий:
                # - установлен флаг `--rewrite` (данные о картах полностью переписываются)
                # - карты нет в БД (выпущена новая карта)
                # - карта есть в БД, но не совпадает с данными API по ключевым параметрам (карта понерфлена)
                # - карта коллекционная, но не имеет сохраненного рендера или миниатюры
                continue
            r_card, card_created = Card.objects.get_or_create(
                card_id=j_card['cardId'],
                dbf_id=int(j_card['dbfId']),
            )
            r_card.name = j_card['name']
            r_card.service_name = r_card.name
            r_card.card_type = self.__align_card_type(j_card.get('type', ''))
            r_card.cost = int(j_card.get('cost', 0))
            r_card.attack = int(j_card.get('attack', 0))
            r_card.health = int(j_card.get('health', 0))
            r_card.durability = int(j_card.get('durability', 0))
            r_card.armor = int(j_card.get('armor', 0))
            r_card.text = _clear_unreadable(j_card.get('text', ''))
            r_card.flavor = _clear_unreadable(j_card.get('flavor', ''))
            r_card.rarity = self.__align_rarity(j_card.get('rarity', ''))
            r_card.spell_school = self.__align_spellschool(j_card.get('spellSchool', ''))
            r_card.slug = f'{slugify(r_card.name)}-{str(r_card.dbf_id)}'

            if card_created:
                r_card.artist = j_card.get('artist', '')
                r_card.collectible = j_card.get('collectible', False)
                r_card.battlegrounds = r_card.card_set == 'Battlegrounds'
                r_card.mercenaries = r_card.card_set == 'Mercenaries'

                # если карта только создана, а ее рендеры/миниатюра уже есть в файловой системе,
                # (например, после --rewrite) - прикручиваем их
                image_en_path = f'cards/en/{r_card.card_id}.png'
                image_ru_path = f'cards/ru/{r_card.card_id}.png'
                thumbnail_path = f'cards/thumbnails/{r_card.card_id}.png'
                if (settings.MEDIA_ROOT / image_en_path).is_file():
                    r_card.image_en = image_en_path
                if (settings.MEDIA_ROOT / image_ru_path).is_file():
                    r_card.image_ru = image_ru_path
                if (settings.MEDIA_ROOT / thumbnail_path).is_file():
                    r_card.thumbnail = thumbnail_path

                self.__write_set_to_card(r_card, j_card)

            # --- Перевод карты на русский -----------------------------------------
            j_card_ru = self.__extract_ru_card('cardId', r_card.card_id)
            # KeyError исключено - j_card_ru гарантированно имеет искомые ключи
            r_card.name_ru = j_card_ru['name']
            r_card.text_ru = _clear_unreadable(j_card_ru['text'])
            r_card.flavor_ru = _clear_unreadable(j_card_ru['flavor'])

            # --- Загрузка изображений ----------------------------------------------
            if self.__reload_images:
                image_en.erase()
                image_ru.erase()
                thumbnail.erase()

            if r_card.collectible and not image_en.exists:
                try:
                    image_en.download()
                    r_card.image_en.save(**image_en.for_imagefield)
                except ConnectionError:
                    self.report['FAIL_DOWNLOAD_RENDER_EN'].append(f'{r_card.name} ({r_card.card_id}.{r_card.dbf_id})')
            if r_card.collectible and not image_ru.exists:
                try:
                    image_ru.download()
                    r_card.image_ru.save(**image_ru.for_imagefield)
                except ConnectionError:
                    self.report['FAIL_DOWNLOAD_RENDER_RU'].append(f'{r_card.name} ({r_card.card_id}.{r_card.dbf_id})')
            if r_card.collectible and not thumbnail.exists:
                try:
                    thumbnail.download()
                    r_card.thumbnail.save(**thumbnail.for_imagefield)
                    thumbnail.fade()
                except ConnectionError:
                    self.report['FAIL_DOWNLOAD_THUMBNAIL'].append(f'{r_card.name} ({r_card.card_id}.{r_card.dbf_id})')
            if all([
                r_card.collectible,
                not card_created,
                not unchanged,
            ]):
                # если коллекционная карта уже была в БД и теперь изменяется - перезакачиваем рендеры
                try:
                    image_en.download()
                    image_ru.download()
                    image_en.erase()
                    image_ru.erase()
                    r_card.image_en.save(**image_en.for_imagefield)
                    r_card.image_ru.save(**image_ru.for_imagefield)
                except ConnectionError:
                    self.report['FAIL_DOWNLOAD_RENDER_EN'].append(f'{r_card.name} ({r_card.card_id}.{r_card.dbf_id})')
                    self.report['FAIL_DOWNLOAD_RENDER_RU'].append(f'{r_card.name} ({r_card.card_id}.{r_card.dbf_id})')

            r_card.save()

            # --- Заполнение ManyToMany-полей ---------------------------------
            self.__write_mechanics_to_card(r_card, j_card)
            self.__write_classes_to_card(r_card, j_card)
            self.__write_tribe_to_card(r_card, j_card)

    def __is_equivalent(self, r_card: Card, j_card: dict) -> bool:
        """ Проверяет, была ли карта понерфлена """

        if not r_card:
            return False

        equivalent = all([r_card.name == j_card['name'],
                          r_card.text == _clear_unreadable(j_card.get('text', '')),
                          r_card.spell_school == self.__align_spellschool(j_card.get('spellSchool', '')),
                          r_card.cost == int(j_card.get('cost', 0)),
                          r_card.attack == int(j_card.get('attack', 0)),
                          r_card.health == int(j_card.get('health', 0)),
                          r_card.durability == int(j_card.get('durability', 0)),
                          r_card.armor == int(j_card.get('armor', 0))])

        return equivalent

    def __extract_ru_card(self, key: str, value) -> dict:
        """ Извлекает карту-словарь из списка ``ru_cards`` """
        for index, d in enumerate(self.__ru_cards):
            if d[key] == value:
                return self.__ru_cards.pop(index)
        return {}

    def __rebuild_decks(self):
        """ Пересборка существующих колод после обновления данных о картах """
        if not self.__rewrite:
            return

        for deck in tqdm(Deck.objects.all(), desc='Rebuilding decks', ncols=100):
            cards, heroes, format_ = parse_deckstring(deck.string)
            deck.deck_class = Card.objects.get(dbf_id=heroes[0]).card_class.all().first()
            deck.deck_format = Format.objects.get(numerical_designation=format_)
            deck.save()
            for dbf_id, number in cards:
                card = Card.includibles.get(dbf_id=dbf_id)
                ci = Inclusion(deck=deck, card=card, number=number)
                ci.save()
                deck.cards.add(card)

    def update(self):
        """ Выполняет обновление БД """

        self.__prepare_update()

        with transaction.atomic():
            if self.__rewrite:
                self.__clear_database()
            self.__write_classes()
            self.__write_tribes()
            self.__write_formats()
            self.__write_sets()
            self.__write_mechanics()
            self.__write_cards()
            self.__update_classes()
            self.__rebuild_decks()
            self.__update_version()


def _clear_unreadable(text: str) -> str:
    """ Избавляет текст от нечитаемых символов и прочего мусора """

    if text is None:
        return ''

    new_text = re.sub(r'\\n', ' ', text)
    new_text = re.sub(r'-\[x]__', '', new_text)
    new_text = re.sub(r'\[x]', '', new_text)
    new_text = re.sub(r'\$', '', new_text)
    new_text = re.sub(r'_', ' ', new_text)
    new_text = re.sub(r'@', '0', new_text)
    return new_text
