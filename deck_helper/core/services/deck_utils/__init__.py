from django.db.models import Q, Count
from django.conf import settings
from rest_framework import serializers

from pathlib import Path
import json

from decks.models import Deck, Format, Inclusion, Render
from cards.models import Card
from core.services.images import DeckRender
from core.services.deck_codes import parse_deckstring

DATA_FOLDER = Path(__file__).resolve().parent / 'data'


def get_render(deck_id: str, name: str, language: str) -> dict:
    """ Получает рендер колоды, возвращает словарь с его данными """
    deck = Deck.objects.get(pk=deck_id)
    dr = DeckRender(name=name, deck=deck, language=language)
    dr.create()
    render = Render()
    render.deck = deck
    render.render.save(**dr.for_imagefield)
    render.name = dr.name
    render.language = Render.Languages(language)
    render.save()

    if Render.objects.count() > settings.DECK_RENDER_MAX_NUMBER:
        r = Render.objects.first()  # автоудаление самого старого рендера
        r.render.delete(save=True)  # в т.ч. из файловой системы
        r.delete()

    return {
        'render': render.render.url,
        'width': dr.width,
        'height': dr.height,
    }


def find_similar_decks(target_deck: Deck):
    """ Возвращает колоды того же формата и класса с большим числом совпадений карт (>= 20) """

    if not target_deck:
        return

    return Deck.nameless.filter(
        deck_format=target_deck.deck_format,
        deck_class=target_deck.deck_class,
    ).exclude(
        string=target_deck.string
    ).annotate(
        num_matches=2 * Count(
            'cards',
            filter=Q(inclusions__number=2) & Q(cards__in=target_deck.cards.filter(inclusions__number=2))
        ) + Count(
            'cards',
            filter=Q(inclusions__number=2) & Q(cards__in=target_deck.cards.filter(inclusions__number=1))
        ) + Count(
            'cards',
            filter=Q(inclusions__number=1) & Q(cards__in=target_deck.cards.all())
        ),
    ).filter(
        num_matches__gt=19
    ).order_by('-num_matches')


class DumpDeckListSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField()

    class Meta:
        model = Deck
        fields = ('id', 'string', 'created', 'name', 'user')

    def create(self, validated_data) -> None:
        string, created = validated_data['string'], validated_data['created']
        if Deck.objects.filter(string=string, created=created).exists():
            return
        deck = Deck()
        deck.string = string
        deck.created = created

        parsed_deck = parse_deckstring(deck.string)
        deck.deck_class = Card.objects.get(dbf_id=parsed_deck.heroes[0]).card_class.all().first()
        deck.deck_format = Format.objects.get(numerical_designation=parsed_deck.format_)
        deck.save()

        for dbf_id, number in parsed_deck.cards.native:
            card = Card.includibles.get(dbf_id=dbf_id)
            ci = Inclusion(deck=deck, card=card, number=number)
            ci.save()

        for dbf_id, source_dbf_id, number in parsed_deck.cards.additional:
            card = Card.includibles.get(dbf_id=dbf_id)
            source_card = Card.includibles.get(dbf_id=source_dbf_id)
            ci = Inclusion(deck=deck, card=card, number=number, source_card=source_card, is_native=False)
            ci.save()


def import_decks(writer, path: Path, file: str):
    """ Импортирует колоды в БД из JSON файла """
    if not path:
        path = DATA_FOLDER
    if not file:
        file = 'initial_decks.json'

    path = path / file
    if not path.is_file():
        writer(f'(!) Error: Cannot find {file}')
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data.reverse()
        serializer = DumpDeckListSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
        else:
            writer(f'Invalid JSON dump\n{serializer.errors}')
