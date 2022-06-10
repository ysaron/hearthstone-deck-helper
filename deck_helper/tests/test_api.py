import pytest
import json
from rest_framework import status
from django.urls import reverse_lazy


class TestAPICards:

    @pytest.mark.django_db
    def test_card_list_api(self, api_client):
        params = {
            'cost_min': 1, 'cost_max': 4,
            'attack_min': 3, 'attack_max': 3,
            'health_min': 2, 'health_max': 3,
            'ctype': 'M',
            'classes': 'Rogue,Mage,Druid,Hunter',
        }
        response = api_client.get(reverse_lazy('api:card_list'), data=params)
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /cards/ недоступен'
        assert len(response.data) == 4, 'возвращено неверное кол-во карт'
        assert all(card['card_class'][0] == 'Rogue' for card in response.data), 'возвращен неверный список карт'
        assert any(card['dbf_id'] == 45531 for card in response.data), 'в списке не обнаружена искомая карта'

    @pytest.mark.django_db
    def test_card_retrieve_api(self, api_client):
        response = api_client.get(reverse_lazy(
            'api:card_retrieve',
            kwargs={'dbf_id': 45975},
        ))
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /cards/<dbf_id>/ недоступен'
        data = json.loads(response.content)
        assert data['card_id'] == 'ICC_910', 'возвращена неверная карта'


class TestAPIDecks:

    @pytest.mark.django_db
    def test_deck_list_api(self, api_client, deck, deckstring):
        params = {
            'dformat': 'Wild',
            'dclass': 'Rogue',
            'cards': '69623,49972,45535,45975',
        }
        response = api_client.get(reverse_lazy('api:deck_list'), data=params)
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /decks/ недоступен'
        data = json.loads(response.content)
        assert len(data) == 1, 'в ответе должна быть ровно 1 тестовая колода'
        assert data[0]['string'] == deckstring, 'код колоды в ответе не совпал с кодом тестовой колоды'

    @pytest.mark.django_db
    def test_deck_retrieve_api(self, api_client, deck, deckstring):
        response = api_client.get(reverse_lazy(
            'api:deck_retrieve',
            kwargs={'pk': deck.pk},
        ))
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /decks/<id>/ недоступен'
        data = json.loads(response.content)
        assert data['string'] == deckstring, 'код колоды в ответе не совпал с кодом тестовой колоды'

    @pytest.mark.django_db
    def test_deck_decode_api(self, api_client, deckstring):
        response = api_client.post(
            reverse_lazy('api:deck_decode'),
            data={'d': 'some invalid deckstring'},
        )
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /decode_deck/ недоступен'
        data = json.loads(response.content)
        assert 'error' in data, 'ошибка не возвращается при передаче некорректного кода колоды'

        response = api_client.post(
            reverse_lazy('api:deck_decode'),
            data={'d': deckstring},
        )
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /decode_deck/ недоступен'
        data = json.loads(response.content)
        assert data['string'] == deckstring, 'код колоды в ответе не совпал с кодом тестовой колоды'
        assert data['deck_class'] == 'Rogue', 'ошибка в расшифровке кода колоды'
