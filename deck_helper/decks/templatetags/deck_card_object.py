from django import template
from django.conf import settings

from cards.models import Card
from decks.models import Deck

register = template.Library()


@register.inclusion_tag('decks/tags/deck_card_td.html', name='deck_card_inclusion_content')
def card_in_deck(deck: Deck, card: Card, tooltip_cls: str = ''):
    """
    Используется для генерации контента тега ``<td>`` названия карты в HTML-таблице-колоде.

    В большинстве случаев - просто ссылка с названием карты.
    Если карта расширяет колоду доп. картами - ссылки на доп. карты помещаются в тот же ``<td>``.
    """
    context = {
        'card': card,
        'additional_cards': [],
        'tooltip_cls': tooltip_cls,
        'truncate': 22,
    }
    if card.dbf_id not in settings.KNOWN_EXPANDER_ID_LIST:
        return context

    if not deck.additional_cards.exists():
        return context

    cards_added_by_current_card = deck.additional_cards.filter(source=card.dbf_id)
    context['additional_cards'] = cards_added_by_current_card
    context['truncate'] = 22 - 2 * cards_added_by_current_card.count()
    return context
