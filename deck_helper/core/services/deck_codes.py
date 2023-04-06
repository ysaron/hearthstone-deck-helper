import base64
from io import BytesIO
from typing import IO, NamedTuple
from dataclasses import dataclass, field

from django.utils.translation import gettext_lazy as _

from core.exceptions import DecodeError

DECKSTRING_VERSION = 1

CardList = list[int]
CardIncludeList = list[tuple[int, int]]


class ParsedCard(NamedTuple):
    dbf_id: int
    number: int


class ParsedAdditionalCard(NamedTuple):
    dbf_id: int
    source_dbf_id: int
    number: int = 1


@dataclass
class ParsedCardList:
    native: list[ParsedCard] = field(default_factory=list)
    additional: list[ParsedAdditionalCard] = field(default_factory=list)


@dataclass
class ParsedDeckstring:
    cards: ParsedCardList | None = None
    heroes: list[int] = field(default_factory=list)
    format_: int = 0


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
        try:
            c = stream.read(1)      # считываем по 1 байту в строку (1 символ)
            if c == "":
                raise EOFError("Unexpected EOF")
            i = ord(c)

            result |= (i & 0x7f) << shift   # 0x7f = 0b01111111
            shift += 7
            if not (i & 0x80):              # если 0 < i < 128
                break
        except Exception:
            raise DecodeError(_('Invalid deck code'))

    return result


def parse_deckstring(deckstring) -> ParsedDeckstring:
    """
    Расшифровка кода колоды

    :param deckstring: строка ASCII или байты
    :return: список кортежей[dbf_id, count]; список[dbf_id]; значение енума формата
    """
    try:
        decoded = base64.b64decode(deckstring)      # декстринг в байты
    except Exception:
        raise DecodeError('Invalid deck code')
    data = BytesIO(decoded)                     # байты в поток байтов в оперативной памяти

    # первый байт: должен быть \0
    if data.read(1) != b"\0":
        raise DecodeError('Invalid deck code')

    # второй байт: версия шифрования кодов колод
    version = _read_varint(data)
    if version != DECKSTRING_VERSION:
        raise DecodeError('Unsupported deckstring version')

    parsed = ParsedDeckstring()

    # третий байт: формат (режим игры)
    parsed.format_ = _read_varint(data)

    # 4-й байт: число героев, упомянутых в декстринге
    num_heroes = _read_varint(data)
    for i in range(num_heroes):
        parsed.heroes.append(_read_varint(data))

    parsed_cards = ParsedCardList()
    # кол-во карт в одном экземпляре
    num_cards_x1 = _read_varint(data)
    for i in range(num_cards_x1):
        card = ParsedCard(dbf_id=_read_varint(data), number=1)
        parsed_cards.native.append(card)

    num_cards_x2 = _read_varint(data)
    for i in range(num_cards_x2):
        card = ParsedCard(dbf_id=_read_varint(data), number=2)
        parsed_cards.native.append(card)

    num_cards_xn = _read_varint(data)
    for i in range(num_cards_xn):
        card = ParsedCard(dbf_id=_read_varint(data), number=_read_varint(data))
        parsed_cards.native.append(card)

    try:
        # Есть ли доп. скрытые карты?
        # Если нет - будет брошено DecodeError
        _read_varint(data)

        # Кол-во доп. карт
        num_cards_additional = _read_varint(data)
        for _ in range(num_cards_additional):
            card = ParsedAdditionalCard(dbf_id=_read_varint(data), source_dbf_id=_read_varint(data))
            parsed_cards.additional.append(card)
    except DecodeError:
        # В колоде нет дополнительных карт
        pass

    parsed.cards = parsed_cards

    return parsed
