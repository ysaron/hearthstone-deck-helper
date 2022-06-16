from django.core.management.base import BaseCommand
import time

from core.services.update import Updater
from core.exceptions import UpdateError


class Command(BaseCommand):
    help = 'Update the card database'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--rewrite', action='store_true', help='Rewrite all cards')
        parser.add_argument('-i', '--images', action='store_true', help='Reload all card renders')
        parser.add_argument(
            '-d', '--disableprogressbars',
            action='store_true',
            help='Disable progress bars when recording cards. Do not use this manually.',
        )

    def handle(self, *args, **options):
        start = time.perf_counter()
        self.stdout.write('Starting database update...')
        try:
            upd = Updater(
                self.stdout.write,
                progress_bars=not options['disableprogressbars'],
                rewrite=options['rewrite'],
                reload_images=options['images'],
            )
            upd.update()
        except UpdateError as ue:
            self.stdout.write(f'Error during update: {ue}')
            return
        end = time.perf_counter()
        self.stdout.write(f'Database update took {end - start:.2f}s')

        self.stdout.write('Report:')
        for key, value in upd.report.items():
            self.stdout.write(f'{key}: {value}')
