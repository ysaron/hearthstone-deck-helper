import pytest

from core.services.deck_codes import parse_deckstring
from core.services.images import DeckRender
from core.exceptions import DecodeError
from decks.models import Deck, Render
from cards.models import Card, Mechanic


def calc_deck_cards(deck: Deck) -> int:
    cards = deck.included_cards
    return sum([n * cards.filter(number=n).count() for n in (1, 2)])


@pytest.mark.django_db
def test_parse_deckstring(deck_code):
    with pytest.raises(DecodeError):
        parse_deckstring('some invalid string')

    result = parse_deckstring(deckstring=deck_code)
    assert isinstance(result, tuple), f'parse_deckstring вернула {type(result)} вместо tuple'
    assert len(result) == 3, 'данные о колоде должны быть кортежем из 3 элементов'
    cards, heroes, format_ = result
    assert isinstance(cards, list), 'cards должно быть списком'
    for card in cards:
        assert isinstance(card, tuple), 'данные о карте должны быть кортежем'
        assert len(card) == 2, 'кортеж карты должен содержать 2 элемента: dbf_id и кол-во вхождений в колоду'
        assert all(isinstance(i, int) for i in card), 'элементы кортежа карты должны иметь тип int'
        assert card[1] in [1, 2], 'кол-во вхождений карты в колоду должно быть равно 1 или 2'


@pytest.mark.django_db
def test_deck_from_deckstring(db, deckstring, deck_code):
    with pytest.raises(Card.DoesNotExist):
        Deck.from_deckstring(deck_code)
    deck = Deck.from_deckstring(deckstring)
    assert Deck.nameless.count() == 1
    assert Deck.nameless.filter(
        deck_class__name='Rogue',
        deck_format__name='Wild',
    ).exists(), 'колода была сохранена, но не имеет ожидаемых параметров'
    assert calc_deck_cards(deck) == 30, 'в колоде должно быть ровно 30 карт'


class TestDeckStatistics:

    @pytest.mark.django_db
    def test_set_statistics(self, db, deck):
        set_stat = deck.sets_statistics
        assert set_stat, 'sets_statistics вернул пустой список'
        assert isinstance(set_stat, list), 'sets_statistics должно быть списком'
        for stat in set_stat:
            assert isinstance(stat, dict), 'каждый элемент списка sets_statistics должен быть словарем'
            assert 'name' in stat, 'каждый словарь в sets_statistics должен иметь ключ "name"'
            assert 'data' in stat, 'каждый словарь в sets_statistics должен иметь ключ "data"'
            assert 'num_cards' in stat, 'каждый словарь в sets_statistics должен иметь ключ "num_cards"'
            assert isinstance(stat['num_cards'], int), 'кол-во карт "num_cards" должно быть целым числом'

    @pytest.mark.django_db
    def test_rarity_statistics(self, db, deck):
        rar_stat = deck.rarity_statistics
        assert rar_stat, 'rarity_statistics вернул пустой список'
        assert isinstance(rar_stat, list), 'rarity_statistics должно быть списком'
        for stat in rar_stat:
            assert isinstance(stat, dict), 'каждый элемент списка rarity_statistics должен быть словарем'
            assert 'name' in stat, 'каждый словарь в rarity_statistics должен иметь ключ "name"'
            assert 'data' in stat, 'каждый словарь в rarity_statistics должен иметь ключ "data"'
            assert 'num_cards' in stat, 'каждый словарь в rarity_statistics должен иметь ключ "num_cards"'
            assert isinstance(stat['num_cards'], int), 'кол-во карт "num_cards" должно быть целым числом'

        assert rar_stat[0]['data'] == 'C', 'неверно определена самая популярная редкость колоды'
        assert rar_stat[0]['num_cards'] == 11, 'неверно посчитано кол-во обычных карт колоды'

    @pytest.mark.django_db
    def test_type_statistics(self, db, deck):
        type_stat = deck.types_statistics
        assert type_stat, 'types_statistics вернул пустой список'
        assert isinstance(type_stat, list), 'types_statistics должно быть списком'
        for stat in type_stat:
            assert isinstance(stat, dict), 'каждый элемент списка types_statistics должен быть словарем'
            assert 'name' in stat, 'каждый словарь в types_statistics должен иметь ключ "name"'
            assert 'data' in stat, 'каждый словарь в types_statistics должен иметь ключ "data"'
            assert 'num_cards' in stat, 'каждый словарь в types_statistics должен иметь ключ "num_cards"'
            assert isinstance(stat['num_cards'], int), 'кол-во карт "num_cards" должно быть целым числом'

        assert type_stat[0]['data'] == 'S', 'неверно определен самый популярный тип карт колоды'
        assert type_stat[0]['num_cards'] == 18, 'неверно посчитано кол-во заклинаний колоды'

    @pytest.mark.django_db
    def test_mechanic_statistics(self, db, deck):
        mech_stat = deck.mechanics_statistics
        assert mech_stat, 'mechanics_statistics вернул пустой список'
        assert isinstance(mech_stat, list), 'mechanics_statistics должно быть списком'
        for stat in mech_stat:
            assert isinstance(stat, dict), 'каждый элемент списка mechanics_statistics должен быть словарем'
            assert 'mech' in stat, 'каждый словарь в mechanics_statistics должен иметь ключ "mech"'
            assert 'num_cards' in stat, 'каждый словарь в mechanics_statistics должен иметь ключ "num_cards"'
            assert isinstance(stat['mech'], Mechanic), '"mech" должно быть экземпляром Mechanic'
            assert isinstance(stat['num_cards'], int), 'кол-во карт "num_cards" должно быть целым числом'

        assert mech_stat[0]['num_cards'] == 9, 'неверно посчитано кол-во карт с самой популярной механикой колоды'


@pytest.mark.django_db
def test_deck_craft_cost(db, deck):
    cost = deck.craft_cost
    assert isinstance(cost, dict), 'данные о стоимости крафта колоды должны быть словарем'
    assert 'basic' in cost, 'словарь deck.craft_cost должен иметь ключ "basic"'
    assert 'gold' in cost, 'словарь deck.craft_cost должен иметь ключ "gold"'
    assert isinstance(cost['basic'], int), 'обычная стоимость крафта должна быть целым числом'
    assert isinstance(cost['gold'], int), 'стоимость крафта в золоте должна быть целым числом'
    assert cost['basic'] == 5340, 'неверно посчитана обычная стоимость крафта колоды'
    assert cost['gold'] == 30800, 'неверно посчитана стоимость крафта колоды в золоте'


@pytest.mark.django_db
def test_deck_rendering(db, deck):
    dr = DeckRender(name='Qwerty', deck=deck, language='en')
    dr.create()
    render = Render(name=dr.name, deck=deck, language=Render.Languages('en'))
    render.render.save(**dr.for_imagefield)
    render.save()

    assert dr.exists, 'рендер не был сохранен в файловой системе'
    assert deck.renders.count() == 1

    dr.erase()       # удаление тестового рендера вручную
