import pytest

from django.core.management import call_command

pytest_plugins = [
    'tests.fixtures.fixture_data',
    'tests.fixtures.fixture_user',
]


# заполнение тестовой БД
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'common_fixture.json')
        call_command('loaddata', 'card_fixture.json')
