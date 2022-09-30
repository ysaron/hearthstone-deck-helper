import pytest
import json
from rest_framework import status


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
        response = api_client.get('/api/v1/cards/', data=params)
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /cards/ недоступен'
        assert len(response.data) == 4, 'возвращено неверное кол-во карт'
        assert all(card['card_class'][0] == 'Rogue' for card in response.data), 'возвращен неверный список карт'
        assert any(card['dbf_id'] == 45531 for card in response.data), 'в списке не обнаружена искомая карта'

    @pytest.mark.django_db
    def test_card_retrieve_api(self, api_client):
        response = api_client.get('/api/v1/cards/45975/')
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
        response = api_client.get('/api/v1/decks/', data=params)
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /decks/ недоступен'
        data = json.loads(response.content)
        assert len(data) == 1, 'в ответе должна быть ровно 1 тестовая колода'
        assert data[0]['string'] == deckstring, 'код колоды в ответе не совпал с кодом тестовой колоды'

    @pytest.mark.django_db
    def test_deck_retrieve_api(self, api_client, deck, deckstring):
        response = api_client.get(f'/api/v1/decks/{deck.pk}/')
        assert response.status_code == status.HTTP_200_OK, 'эндпойнт /decks/<id>/ недоступен'
        data = json.loads(response.content)
        assert data['string'] == deckstring, 'код колоды в ответе не совпал с кодом тестовой колоды'

    @pytest.mark.django_db
    def test_deck_decode_api(self, api_client, deckstring):
        response = api_client.post('/api/v1/decks/', data={'string': 'some invalid deckstring'})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, \
            'ошибка не возвращается при передаче некорректного кода колоды'

        response = api_client.post('/api/v1/decks/', data={'string': deckstring})
        assert response.status_code == status.HTTP_201_CREATED, 'эндпойнт создания колоды недоступен'
        data = json.loads(response.content)
        assert data['string'] == deckstring, 'код колоды в ответе не совпал с кодом тестовой колоды'
        assert data['deck_class'] == 'Rogue', 'ошибка в расшифровке кода колоды'
