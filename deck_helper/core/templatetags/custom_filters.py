from django import template
from django.utils.translation import to_locale, get_language, gettext_lazy as _

from collections import namedtuple

from cards.models import Card

register = template.Library()
Parameter = namedtuple('Parameter', ['name', 'icon', 'value'])


@register.filter
def get_item(dictionary, key):
    """ Используется в связке с другими фильтрами, возвращающими словарь """
    return dictionary.get(key)


@register.filter(name='cclass')
def get_cardclass_css(card):
    """ Возвращает классы CSS соответствующего Hearthstone-класса """

    match card.card_class.count():
        case 0:
            return 'neutral'
        case 1:
            return ''.join(card.card_class.all()[0].service_name.lower().split())
        case _:
            lst = [''.join(cls.service_name.lower().split()) for cls in card.card_class.all()]
            return f'multiclass {"-".join(lst)}'


@register.filter(name='dclass')
def get_deckclass_css(deck):
    """ Возвращает класс CSS для колоды соответствующего Hearthstone-класса """
    return ''.join(deck.deck_class.service_name.lower().split())


@register.filter(name='rar')
def get_rarity_style(card) -> str:
    """ Возвращает класс CSS для соответствующей редкости карты """

    match card.rarity:
        case Card.Rarities.LEGENDARY:
            return 'legendary'
        case Card.Rarities.EPIC:
            return 'epic'
        case Card.Rarities.RARE:
            return 'rare'
        case _:
            return 'common'


@register.filter(name='dformat')
def get_format_style(deck) -> str:
    """ Возвращает соответствующий класс стиля формата колоды """

    match deck.deck_format.numerical_designation:
        case 1:
            return 'wild'
        case 2:
            return 'standard'
        case 3:
            return 'classic'
        case _:
            return 'unknown'


@register.inclusion_tag('cards/tags/stat_cell.html', takes_context=True, name='format_stats')
def format_stats(context, card):
    """ Формирует строку <tr> таблицы card-detail с числовыми параметрами карты """

    svg_path = 'core/svg/'
    cost = Parameter(_('Cost'), f'{svg_path}cost.svg', card.cost)

    # карты любого типа имеют, помимо стоимости, максимум 2 параметра, различающихся от типа к типу
    first_param, second_param = Parameter(None, None, None), Parameter(None, None, None)

    match card.card_type:
        case Card.CardTypes.MINION:
            first_param = Parameter(_('Attack'), f'{svg_path}attack.svg', card.attack)
            second_param = Parameter(_('Health'), f'{svg_path}health.svg', card.health)
        case Card.CardTypes.WEAPON:
            first_param = Parameter(_('Attack'), f'{svg_path}attack.svg', card.attack)
            second_param = Parameter(_('Durability'), f'{svg_path}durability.svg', card.durability)
        case Card.CardTypes.HERO:
            second_param = Parameter(_('Armor'), f'{svg_path}armor.svg', card.armor)
        case Card.CardTypes.LOCATION:
            second_param = Parameter(_('Health'), f'{svg_path}health.svg', card.health)

    context.update({'params': [p for p in (cost, first_param, second_param) if p.name]})

    return context


@register.filter(name='setcls')
def set_class_to_form_field(field, css_class: str):
    return field.as_widget(attrs={'class': css_class})


@register.filter(name='mktitle')
def get_page_title(title: str):
    """ Возвращает заголовок, отображаемый на вкладках """
    return f'{title} | HS Deck Helper'


@register.filter(name='locale')
def get_locale_name(language_code):
    match language_code:
        case 'en':
            return 'enUS'
        case 'ru':
            return 'ruRU'
        case _:
            return 'enUS'


@register.filter(name='shortclassname')
def get_short_class_name(deck):
    """ Заменяет слишком длинное название класса Hearthstone на синоним для улучшения отображения """
    if deck.deck_class.service_name == 'Demon Hunter':
        return _('DH')
    return deck.deck_class


@register.filter(name='locrender')
def get_localized_render(card: Card):
    lang = to_locale(get_language())

    remote_url = 'https://art.hearthstonejson.com/v1/render/latest/{loc}/256x/{id}.png'

    match lang:
        case 'en':
            return card.image_en.url if card.image_en else remote_url.format(loc='enUS', id=card.card_id)
        case 'ru':
            return card.image_ru.url if card.image_ru else remote_url.format(loc='ruRU', id=card.card_id)
        case _:
            return remote_url.format(loc='enUS', id=card.card_id)
