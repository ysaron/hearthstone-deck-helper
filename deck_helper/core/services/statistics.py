from collections import namedtuple

from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

from cards.models import Card, Mechanic
from decks.models import Deck, Format

StatSection = namedtuple('StatSection', ['header', 'cells'])
StatCell = namedtuple('StatCell', ['header', 'items_'])
StatItem = namedtuple('StatItem', ['label', 'value', 'link', 'css'])


def _get_card_num_stat() -> StatCell:
    num_cards_all = Card.objects.count()
    num_collectibles = Card.objects.search_collectible(True).count()

    return StatCell(
        header=_('Amount'),
        items_=(
            StatItem(
                label=_('Total'),
                value=num_cards_all,
                link=f"{reverse_lazy('cards:card_list')}?collectible=unknown",
                css='dim'
            ),
            StatItem(
                label=_('Collectible'),
                value=num_collectibles,
                link=f"{reverse_lazy('cards:card_list')}?collectible=true",
                css=''
            ),
        )
    )


def _get_card_rar_stat() -> StatCell:
    collectibles = Card.objects.search_collectible(True)
    num_leg = collectibles.search_by_rarity(Card.Rarities.LEGENDARY).count()
    num_epic = collectibles.search_by_rarity(Card.Rarities.EPIC).count()
    num_rare = collectibles.search_by_rarity(Card.Rarities.RARE).count()
    num_common = collectibles.search_by_rarity(Card.Rarities.COMMON).count()

    return StatCell(
        header=_('Rarities'),
        items_=(
            StatItem(
                label=_('Legendary'),
                value=num_leg,
                link=f"{reverse_lazy('cards:card_list')}?collectible=true&rarity=L",
                css=''
            ),
            StatItem(
                label=_('Epic'),
                value=num_epic,
                link=f"{reverse_lazy('cards:card_list')}?collectible=true&rarity=E",
                css=''
            ),
            StatItem(
                label=_('Rare'),
                value=num_rare,
                link=f"{reverse_lazy('cards:card_list')}?collectible=true&rarity=R",
                css=''
            ),
            StatItem(
                label=_('Common'),
                value=num_common,
                link=f"{reverse_lazy('cards:card_list')}?collectible=true&rarity=C",
                css=''
            ),
        )
    )


def _get_most_popular_mechanics_stat(top: int) -> StatCell:
    mechanics = Mechanic.objects.annotate(num_cards=Count('card', filter=Q(card__collectible=True)))
    most_popular = mechanics.order_by('-num_cards')[:top]
    items = []
    for mech in most_popular:
        item = StatItem(
            label=mech.name,
            value=mech.num_cards,
            link=f"{reverse_lazy('cards:card_list')}?collectible=true&mechanic={mech.pk}",
            css=''
        )
        items.append(item)
    return StatCell(
        header=_('Most popular mechanics'),
        items_=tuple(items)
    )


def _get_most_popular_cards_stat(top: int) -> StatCell:
    """ Самые популярные карты в колодах БД сайта """
    cards = Card.includibles.annotate(num_decks=Count('deck', filter=Q(deck__name='', deck__user=None)))
    most_popular = cards.order_by('-num_decks')[:top]
    items = []
    for card in most_popular:
        item = StatItem(
            label=card.name,
            value=card.num_decks,
            link=card.get_absolute_url(),
            css=''
        )
        items.append(item)
    return StatCell(
        header=_('Most popular cards'),
        items_=tuple(items)
    )


def _get_deck_num_stat() -> StatCell:
    decks = Deck.nameless.annotate(num_unique_cards=Count('cards'))
    num_all = decks.count()
    num_highlander = decks.filter(num_unique_cards=30).count()
    return StatCell(
        header=_('Amount'),
        items_=(
            StatItem(
                label=_('Total'),
                value=num_all,
                link=reverse_lazy('decks:all_decks'),
                css=''
            ),
            StatItem(
                label=_('Highlander'),
                value=num_highlander,
                link='#',
                css=''
            ),
        )
    )


def _get_deck_format_stat() -> StatCell:
    decks = Deck.nameless.all()
    standard = Format.objects.get(numerical_designation=2)
    wild = Format.objects.get(numerical_designation=1)
    classic = Format.objects.get(numerical_designation=3)
    num_standard = decks.filter(deck_format=standard).count()
    num_wild = decks.filter(deck_format=wild).count()
    num_classic = decks.filter(deck_format=classic).count()
    return StatCell(
        header=_('Formats'),
        items_=(
            StatItem(
                label=_('Standard'),
                value=num_standard,
                link=f"{reverse_lazy('decks:all_decks')}?deck_format={standard.pk}",
                css=''
            ),
            StatItem(
                label=_('Wild'),
                value=num_wild,
                link=f"{reverse_lazy('decks:all_decks')}?deck_format={wild.pk}",
                css=''
            ),
            StatItem(
                label=_('Classic'),
                value=num_classic,
                link=f"{reverse_lazy('decks:all_decks')}?deck_format={classic.pk}",
                css=''
            ),
        )
    )


def _get_cards_statistics() -> StatSection:
    return StatSection(
        header=_('Cards'),
        cells=(
            _get_card_num_stat(),
            _get_card_rar_stat(),
            _get_most_popular_mechanics_stat(top=5),
        )
    )


def _get_decks_statistics() -> StatSection:
    return StatSection(
        header=_('Decks'),
        cells=(
            _get_deck_num_stat(),
            _get_deck_format_stat(),
            _get_most_popular_cards_stat(top=5),
        )
    )


def get_statistics_context() -> dict:
    context = {
        'cards': _get_cards_statistics(),
        'decks': _get_decks_statistics(),
    }
    return context
