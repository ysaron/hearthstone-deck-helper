import logging

logger = logging.getLogger('deck_helper.custom')


class LoggingMiddleware:

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        response = self._get_response(request)
        return response

    def process_exception(self, request, exception):
        """ Вызывается при любом неотловленном исключении во views """
        msg = f'{exception}\nRequest: {request}\nRequest.META: {request.META}'
        logger.exception(msg=msg)
        return None
