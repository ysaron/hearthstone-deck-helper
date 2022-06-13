from deck_helper.celery import app
from django.conf import settings

from decks.models import Deck, Render
from core.services.images import DeckRender


@app.task
def generate_deck_render(deck_id: str, name: str, language: str) -> dict:
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
