import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load data from json file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        json_file = options['json_file']
        with open(json_file, 'r') as f:
            data = json.load(f)

        for item in data:
            my_model = Ingredient(**item)
            my_model.save()

        self.stdout.write(self.style.SUCCESS('successfully'))
