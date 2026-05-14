from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Genre, Game
from django.utils.text import slugify
from decimal import Decimal
import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding genres...')
        genres_data = [
            ('Action', 'action'), ('RPG', 'rpg'), ('Strategy', 'strategy'),
            ('Adventure', 'adventure'), ('Simulation', 'simulation'),
            ('Sports', 'sports'), ('Horror', 'horror'), ('Indie', 'indie'),
        ]
        genres = {}
        for name, slug in genres_data:
            g, _ = Genre.objects.get_or_create(slug=slug, defaults={'name': name})
            genres[slug] = g

        self.stdout.write('Seeding games...')
        games_data = [
            {
                'title': 'Cyber Odyssey 2077',
                'slug': 'cyber-odyssey-2077',
                'description': 'Відкритий світ у кіберпанк-всесвіті. Досліджуйте місто майбутнього.',
                'developer': 'NightDev Studios',
                'publisher': 'NightDev Publishing',
                'release_date': datetime.date(2023, 12, 10),
                'price': Decimal('899.99'),
                'discount_percent': 20,
                'genre_slugs': ['action', 'rpg'],
                'min_os': 'Windows 10 64-bit',
                'min_cpu': 'Intel Core i5-8600K',
                'min_ram': '12 GB RAM',
                'min_gpu': 'NVIDIA GTX 1060',
                'min_storage': '70 GB',
            },
            {
                'title': 'Kingdoms & Empires',
                'slug': 'kingdoms-and-empires',
                'description': 'Будуйте цивілізацію з нуля та завойовуйте світ у цій стратегії.',
                'developer': 'StratForge',
                'publisher': 'StratForge',
                'release_date': datetime.date(2022, 5, 15),
                'price': Decimal('499.99'),
                'discount_percent': 0,
                'genre_slugs': ['strategy'],
                'min_os': 'Windows 7 64-bit',
                'min_cpu': 'Intel Core i3-4340',
                'min_ram': '8 GB RAM',
                'min_gpu': 'NVIDIA GTX 970',
                'min_storage': '25 GB',
            },
            {
                'title': 'Shadow Realms',
                'slug': 'shadow-realms',
                'description': 'Темне фентезі-RPG з глибокою бойовою системою та багатим лором.',
                'developer': 'DarkArts Interactive',
                'publisher': 'Epic Games',
                'release_date': datetime.date(2024, 3, 1),
                'price': Decimal('1199.00'),
                'discount_percent': 10,
                'genre_slugs': ['rpg', 'action'],
                'min_os': 'Windows 10 64-bit',
                'min_cpu': 'Intel Core i7-8700K',
                'min_ram': '16 GB RAM',
                'min_gpu': 'NVIDIA RTX 2080',
                'min_storage': '90 GB',
            },
        ]

        for data in games_data:
            genre_slugs = data.pop('genre_slugs')
            game, created = Game.objects.get_or_create(
                slug=data['slug'], defaults=data
            )
            if created:
                game.genres.set([genres[s] for s in genre_slugs])
                self.stdout.write(f'  Created: {game.title}')

        # Create superuser if not exists
        if not User.objects.filter(email='admin@gamestore.ua').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@gamestore.ua',
                password='Admin1234!',
                user_type='ADMIN',
            )
            self.stdout.write(self.style.SUCCESS('Created admin: admin@gamestore.ua / Admin1234!'))

        self.stdout.write(self.style.SUCCESS('Seeding completed!'))
