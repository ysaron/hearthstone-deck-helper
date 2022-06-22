from deck_helper.celery import app
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.management import call_command

from datetime import datetime, timedelta

from decks.models import Deck, Render
from core.services.images import DeckRender
from core.services.api_workers import HsRapidApiWorker

logger = get_task_logger(__name__)


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


@app.task
def check_for_hs_api_updates():
    logger.info('Checking for updates...')
    try:
        api = HsRapidApiWorker()
    except ConnectionError:
        logger.warning('RapidAPI is unreachable!')
        return

    response = api.check_for_updates()
    logger.info(f'DB version {response.current_version} | {response.api_version} API version')
    if response.is_equal:
        logger.info('Updating the database is not necessary.')
        return False

    # API с данными обновилось. Перед обновлением БД ждем обновления API с изображениями
    tomorrow = datetime.now() + timedelta(hours=23)
    logger.info(f'Versions vary. The database update is scheduled for {tomorrow:%d.%m.%Y %H:%M}')
    run_update_db.apply_async(eta=tomorrow)
    return True


@app.task
def run_update_db():
    """ Вызывает команду обновления БД, если версии БД и Hearthstone API различаются """
    try:
        api = HsRapidApiWorker()
    except ConnectionError:
        logger.warning('RapidAPI is unreachable!')
        return

    response = api.check_for_updates()
    if response.is_equal:
        logger.info('Updating the database is not necessary.')
        return False

    call_command('update_db', '--disableprogressbars')
    return True
