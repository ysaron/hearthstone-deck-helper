import requests
import jmespath
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from django.conf import settings

from core.models import HearthstoneState

UpdateInfo = namedtuple('UpdateInfo', ['current_version', 'api_version', 'is_equal'])


class HsApiWorker(metaclass=ABCMeta):

    def __init__(self):
        self._raw_json = {}
        self.clean_data = {
            'en_cards': [],
            'ru_cards': [],
            'classes': [],
            'tribes': [],
            'sets': [],
            'mechanics': [],
            'standard_sets': [],
            'wild_sets': [],
            'classic_sets': ["Vanilla"],
            'version': "",
        }
        self.check_api()

    @abstractmethod
    def check_api(self):
        pass

    @abstractmethod
    def check_for_updates(self):
        pass

    @abstractmethod
    def get_raw_json(self):
        """ Получает ответ API и сохраняет в self.__raw_json """
        pass

    @abstractmethod
    def clear_data(self):
        """ Приводит self.data в вид, пригодный для обновления БД """
        pass

    @abstractmethod
    def __str__(self):
        pass


class HsRapidApiWorker(HsApiWorker):

    def __init__(self):
        self.__base_url = settings.RAPIDAPI_BASEURL
        self.__headers = {'x-rapidapi-key': settings.X_RAPIDARI_KEY, 'x-rapidapi-host': settings.RAPIDAPI_HOST}
        super().__init__()

    def check_api(self):
        url = self.__base_url + 'info'
        r = requests.get(url=url, headers=self.__headers)
        if r.status_code != 200:
            raise ConnectionError('RapidAPI is not available')

    def check_for_updates(self) -> UpdateInfo:
        url = self.__base_url + 'info'
        r = requests.get(url=url, headers=self.__headers, stream=True)
        api_version: str = jmespath.search('patch', data=r.json())
        current_version: HearthstoneState = HearthstoneState.load()
        return UpdateInfo(
            current_version=current_version.version,
            api_version=api_version,
            is_equal=current_version == api_version,
        )

    def get_raw_json(self):
        url = f'{self.__base_url}cards'
        r = requests.get(url=url, headers=self.__headers, params={'locale': 'enUS'}, stream=True)
        self._raw_json['en_cards'] = r.json()

        url = f'{self.__base_url}cards'
        r = requests.get(url=url, headers=self.__headers, params={'locale': 'ruRU'}, stream=True)
        self._raw_json['ru_cards'] = r.json()

        url = f'{self.__base_url}info'
        r = requests.get(url=url, headers=self.__headers, stream=True)
        self._raw_json['info'] = r.json()

    def clear_data(self):
        self.clean_data['en_cards'] = jmespath.search(
            expression="*[?type!='Enchantment'][]",
            data=self._raw_json['en_cards'],
        )

        filter_ru_cards = "*[?type!='Enchantment'][].{cardId: cardId, name: name, text: text, flavor: flavor}"
        self.clean_data['ru_cards'] = jmespath.search(
            expression=filter_ru_cards,
            data=self._raw_json['ru_cards'],
        )

        self.clean_data['classes'] = jmespath.search(
            expression='classes',
            data=self._raw_json['info'],
        )

        self.clean_data['tribes'] = jmespath.search(
            expression='races',
            data=self._raw_json['info'],
        )

        self.clean_data['sets'] = list(set(jmespath.search(
            expression="*[?type!='Enchantment'][].cardSet",
            data=self._raw_json['en_cards'],
        )))

        self.clean_data['mechanics'] = list(set(jmespath.search(
            expression="*[?type!='Enchantment'][].mechanics[].name",
            data=self._raw_json['en_cards'],
        )))

        self.clean_data['standard_sets'] = jmespath.search(
            expression='standard',
            data=self._raw_json['info'],
        )

        self.clean_data['wild_sets'] = jmespath.search(
            expression='wild',
            data=self._raw_json['info'],
        )

        self.clean_data['version'] = jmespath.search(
            expression='patch',
            data=self._raw_json['info'],
        )

        self._raw_json = None

    def __str__(self):
        return 'RapidAPI/omgvamp: Hearthstone'
