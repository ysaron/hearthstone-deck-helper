import pytest
import json
from django.urls import reverse_lazy
from django.utils import translation
from django.http import JsonResponse
from rest_framework import status

from core.services.deck_codes import parse_deckstring
from core.exceptions import DecodeError
from decks.models import Deck


class TestDeckViews:

    @pytest.mark.django_db
    def test_create_deck_view(self, client):
        translation.activate('en')  # иначе reverse_lazy возвращает здесь некорректный префикс языка (/en-us/)
        response = client.get(reverse_lazy('decks:index'))
        assert response.status_code == status.HTTP_200_OK, 'Страница создания колоды недоступна'

    @pytest.mark.django_db
    def test_all_decks_view(self, client):
        response = client.get(reverse_lazy('decks:all_decks'))
        assert response.status_code == status.HTTP_200_OK, 'Список всех колод недоступен'

    @pytest.mark.django_db
    def test_user_decks_superuser_view(self, admin_client):
        response = admin_client.get(reverse_lazy('decks:user_decks'))
        assert response.status_code == status.HTTP_200_OK, 'Личное хранилище колод суперюзера недоступно'

    @pytest.mark.django_db
    def test_user_decks_unauthorized_view(self, client):
        response = client.get(reverse_lazy('decks:user_decks'))
        assert response.status_code == status.HTTP_302_FOUND, 'Личное хранилище колод доступно без авторизации'

    @pytest.mark.django_db
    def test_get_random_deckstring_ajax_view(self, client, deckstring, deck):
        response = client.get(reverse_lazy('decks:get_random_deckstring'))
        assert response.status_code == status.HTTP_302_FOUND, 'Должно быть доступно только для AJAX-запросов'
        response = client.get(
            path=reverse_lazy('decks:get_random_deckstring'),
            data={'deckstring': 'random'},
        )
        assert response.status_code == status.HTTP_302_FOUND, 'Должно быть доступно только для AJAX-запросов'
        response = client.get(
            path=reverse_lazy('decks:get_random_deckstring'),
            data={'deckstring': 'random'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response.status_code == status.HTTP_200_OK, 'не работает получение случайной колоды через AJAX'
        assert isinstance(response, JsonResponse), 'ответ должен иметь тип JsonResponse'
        data = json.loads(response.content)
        assert 'deckstring' in data, 'get_random_deckstring вернул ответ без "deckstring"'
        try:
            parse_deckstring(data['deckstring'])
        except DecodeError:
            pytest.fail('get_random_deckstring вернул некорректный код')

    @pytest.mark.django_db
    def test_get_deck_render_ajax_view(self, client, deck):
        response = client.get(reverse_lazy('decks:deck_render'))
        assert response.status_code == status.HTTP_302_FOUND, 'Должно быть доступно только для AJAX-запросов'
        response = client.get(
            path=reverse_lazy('decks:deck_render'),
            data={
                'render': True,
                'deck_id': deck.pk,
                'name': 'test deck',
                'language': 'en',
            },
        )
        assert response.status_code == status.HTTP_302_FOUND, 'Должно быть доступно только для AJAX-запросов'
        response = client.get(
            path=reverse_lazy('decks:deck_render'),
            data={
                'render': True,
                'deck_id': deck.pk,
                'name': 'test deck',
                'language': 'en',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response.status_code == status.HTTP_200_OK, 'не работает получение рендера колоды через AJAX'
        assert isinstance(response, JsonResponse), 'ответ должен иметь тип JsonResponse'
        data = json.loads(response.content)
        assert 'render' in data, 'get_deck_render вернул ответ без "render"'
        assert 'width' in data, 'get_deck_render вернул ответ без "width"'
        assert 'height' in data, 'get_deck_render вернул ответ без "height"'

        deck.renders.first().render.delete(save=True)  # удаление тестового рендера вручную

    @pytest.mark.django_db
    def test_deck_detail_view(self, client, deck):
        response = client.get(reverse_lazy('decks:deck_detail', kwargs={'deck_id': deck.pk}))
        assert response.status_code == status.HTTP_200_OK, 'просмотр тестовой колоды недоступен'

        response = client.post(reverse_lazy('decks:deck_detail', kwargs={'deck_id': deck.pk}))
        assert response.status_code == status.HTTP_302_FOUND, 'сохранение колоды доступно без авторизации'

    @pytest.mark.django_db
    def test_deck_detail_save_view(self, user_client, deck):
        user, client = user_client
        deck_name = 'Test Deck'
        response = client.post(
            reverse_lazy(
                'decks:deck_detail',
                kwargs={'deck_id': deck.pk},
            ),
            data={
                'string_to_save': deck.string,
                'deck_name': deck_name,
            }
        )
        assert response.status_code == status.HTTP_302_FOUND, 'неудачное сохранение тестовой колоды'
        assert '/decks/' in response.url, 'после сохранения колоды не произошел редирект на ее страницу'
        assert Deck.named.count() == 1
        assert Deck.named.filter(name=deck_name).exists(), 'сохраненная колода не найдена в БД'

    @pytest.mark.django_db
    def test_deck_detail_rename_view(self, user_client, deckstring):
        user, client = user_client
        old_deck_name = 'Test Deck'
        new_deck_name = 'New deck name'

        named_deck = Deck.from_deckstring(deckstring, named=True)
        named_deck.user = user
        named_deck.name = old_deck_name
        named_deck.save()

        response = client.post(
            reverse_lazy(
                'decks:deck_detail',
                kwargs={'deck_id': named_deck.pk},
            ),
            data={'deck_name': new_deck_name}
        )
        assert response.status_code == status.HTTP_200_OK, 'неудачное переименование колоды'
        assert not Deck.named.filter(name=old_deck_name).exists(), 'колода осталась с прежним названием'
        assert Deck.named.filter(name=new_deck_name).exists(), 'колода с новым названием в БД не обнаружена'


class TestCardViews:

    @pytest.mark.django_db
    def test_card_list_view(self, client):
        response = client.get(reverse_lazy('cards:card_list'))
        assert response.status_code == status.HTTP_200_OK, 'Список карт Hearthstone недоступен'

    @pytest.mark.django_db
    def test_card_detail_view(self, client):
        slug = 'preparation-69623'
        response = client.get(reverse_lazy('cards:card_detail', kwargs={'card_slug': slug}))
        assert response.status_code == status.HTTP_200_OK, f'Тестовая карта {slug} недоступна'


class TestCoreViews:

    def test_contact_view(self, client):
        response = client.get(reverse_lazy('contact'))
        assert response.status_code == status.HTTP_302_FOUND, 'Должно быть доступно только для AJAX-запросов'

        response = client.get(
            path=reverse_lazy('contact'),
            data={'email': True},
        )
        assert response.status_code == status.HTTP_302_FOUND, 'Должно быть доступно только для AJAX-запросов'

        response = client.get(
            path=reverse_lazy('contact'),
            data={'email': True},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response.status_code == status.HTTP_200_OK, 'не работает получение контактной почты через AJAX'
        assert isinstance(response, JsonResponse), 'ответ должен иметь тип JsonResponse'
        data = json.loads(response.content)
        assert 'email' in data, 'contact вернул ответ без "email"'

    @pytest.mark.django_db
    def test_statistics_view(self, client):
        response = client.get(reverse_lazy('statistics'))
        assert response.status_code == status.HTTP_200_OK, 'раздел Статистика недоступен'

    def test_api_greeting_view(self, client):
        response = client.get(reverse_lazy('api_greeting'))
        assert response.status_code == status.HTTP_200_OK, 'страница API Greeting недоступна'
