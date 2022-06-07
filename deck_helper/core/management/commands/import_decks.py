from django.core.management.base import BaseCommand

from core.services.deck_utils import import_decks


class Command(BaseCommand):
    help = 'Loads deck data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('tempfile', nargs='?', default=None, help='Use temporary dump file for tests')
        parser.add_argument('-f', '--file', nargs='?', default=None, help='Deck data file')

    def handle(self, *args, **options):
        temp = options['tempfile']
        file = options['file']

        import_decks(self.stdout.write, path=temp, file=file)
