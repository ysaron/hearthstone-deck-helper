import pytest

from core.tasks import generate_deck_render


@pytest.mark.django_db
def test_generate_deck_render(deck):
    assert generate_deck_render.run(deck.pk, 'some name', 'en')
    deck.renders.first().render.delete(save=True)  # удаление тестового рендера вручную
