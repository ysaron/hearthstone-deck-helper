import base64
from io import BytesIO
from typing import IO

from django.utils.translation import gettext_lazy as _

from core.exceptions import DecodeError

DECKSTRING_VERSION = 1

CardList = list[int]
CardIncludeList = list[tuple[int, int]]


def get_clean_deckstring(deckstring: str) -> str:
    """ Выделяет код колоды из формата, в котором колода копируется из Hearthstone """

    deckstring = deckstring.strip()

    if not deckstring.startswith('###'):
        return deckstring

    return deckstring.split('#')[-3].strip()


def _read_varint(stream: IO) -> int:
    shift = 0
    result = 0
    while True:
        c = stream.read(1)      # считываем по 1 байту в строку (1 символ)
        if c == "":
            raise EOFError("Unexpected EOF")
        i = ord(c)

        result |= (i & 0x7f) << shift   # 0x7f = 0b01111111
        shift += 7
        if not (i & 0x80):              # если 0 < i < 128
            break

    return result


def parse_deckstring(deckstring) -> tuple[CardIncludeList, CardList, int]:
    """
    Расшифровка кода колоды
    :param deckstring: строка ASCII или байты
    :return: список кортежей[dbf_id, count]; список[dbf_id]; значение енума формата
    """
    try:
        decoded = base64.b64decode(deckstring)      # декстринг в байты
    except Exception:
        raise DecodeError(_('Invalid deck code'))
    data = BytesIO(decoded)                     # байты в поток байтов в оперативной памяти

    # первый байт: должен быть \0
    if data.read(1) != b"\0":
        raise DecodeError(_('Invalid deck code'))

    # второй байт: версия шифрования кодов колод
    version = _read_varint(data)
    if version != DECKSTRING_VERSION:
        raise DecodeError(_('Unsupported deckstring version'))

    # третий байт: формат (режим игры)
    format_ = _read_varint(data)

    heroes: CardList = []
    # 4-й байт: число героев, упомянутых в декстринге
    num_heroes = _read_varint(data)
    for i in range(num_heroes):
        heroes.append(_read_varint(data))

    cards: CardIncludeList = []
    # кол-во карт в одном экземпляре
    num_cards_x1 = _read_varint(data)
    for i in range(num_cards_x1):
        card_id = _read_varint(data)
        cards.append((card_id, 1))

    num_cards_x2 = _read_varint(data)
    for i in range(num_cards_x2):
        card_id = _read_varint(data)
        cards.append((card_id, 2))

    num_cards_xn = _read_varint(data)
    for i in range(num_cards_xn):
        card_id = _read_varint(data)
        count = _read_varint(data)
        cards.append((card_id, count))

    # TODO: добавить поддержку нового типа колод с 40 картами
    if sum(c[1] for c in cards) != 30:
        raise DecodeError(_('Unsupported deckstring version'))

    return cards, heroes, format_
