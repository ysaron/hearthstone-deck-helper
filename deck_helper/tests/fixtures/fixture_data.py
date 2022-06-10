import pytest

from decks.models import Deck


@pytest.fixture
def deckstring():
    """ Код колоды (класс: Rogue, формат: Wild), содержащей предварительно загруженные карты """
    return 'AAEBAd75AwTQ4wLD4QOd8AOh9AMN9bsC2+MC3+MCl+cCtIYD5dED390D590D/u4DvYAEkZ8E9p8E958EAA=='


@pytest.fixture
def deck_code():
    """ Код колоды (класс: Mage, формат: Wild) с картами, не загруженными предварительно """
    return 'AAEBAf0EHsAB9w36DsMWhRfYuwLZuwLBwQLfxALD6gK+7ALO7wK9mQP8owOSpAO/pAOMt' \
           'gPDtgPgzAPl0QOL1QPo4QOS5AOd7gOm7wOn9wPQ+QOgigTHsgSbyQQAAA=='


@pytest.fixture
def deck(db, deckstring):
    """ Экземпляр колоды, созданной из deckstring """
    return Deck.from_deckstring(deckstring)
