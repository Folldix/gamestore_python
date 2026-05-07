from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
import datetime

from .models import User, Genre, Game, Cart, Wishlist, Library


def make_game(title='Test Game', price='199.99', discount=0):
    genre, _ = Genre.objects.get_or_create(name='Action', slug='action')
    game = Game.objects.create(
        title=title,
        slug=title.lower().replace(' ', '-'),
        description='Test description',
        developer='Test Dev',
        publisher='Test Pub',
        release_date=datetime.date.today(),
        price=Decimal(price),
        discount_percent=discount,
    )
    game.genres.add(genre)
    return game


class AuthTests(APITestCase):
    def test_register(self):
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123',
            'password2': 'StrongPass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_register_password_mismatch(self):
        url = reverse('register')
        data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'StrongPass123',
            'password2': 'WrongPass456',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        User.objects.create_user(username='u', email='u@test.com', password='Pass1234!')
        url = reverse('login')
        response = self.client.post(url, {'email': 'u@test.com', 'password': 'Pass1234!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_wrong_password(self):
        User.objects.create_user(username='u2', email='u2@test.com', password='Pass1234!')
        url = reverse('login')
        response = self.client.post(url, {'email': 'u2@test.com', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GameTests(APITestCase):
    def setUp(self):
        self.game = make_game('Awesome Game', '599.00', discount=15)

    def test_game_list(self):
        response = self.client.get(reverse('game-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_game_detail(self):
        response = self.client.get(reverse('game-detail', kwargs={'slug': self.game.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Awesome Game')

    def test_discounted_price(self):
        response = self.client.get(reverse('game-detail', kwargs={'slug': self.game.slug}))
        expected = Decimal('599.00') * Decimal('0.85')
        self.assertAlmostEqual(float(response.data['discounted_price']), float(expected), places=2)

    def test_game_search(self):
        make_game('Another Title', '100.00')
        response = self.client.get(reverse('game-list') + '?search=Awesome')
        self.assertEqual(response.data['count'], 1)


class CartTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@test.com', password='Pass1234!')
        Cart.objects.create(user=self.user)
        Wishlist.objects.create(user=self.user)
        Library.objects.create(user=self.user)
        self.game = make_game('Cart Game', '299.00')
        # Get token
        response = self.client.post(reverse('login'), {'email': 'buyer@test.com', 'password': 'Pass1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_get_cart(self):
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_to_cart(self):
        response = self.client.post(reverse('cart'), {'game_id': self.game.pk})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['items']), 1)

    def test_remove_from_cart(self):
        self.client.post(reverse('cart'), {'game_id': self.game.pk})
        response = self.client.delete(reverse('cart'), {'game_id': self.game.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_checkout(self):
        self.client.post(reverse('cart'), {'game_id': self.game.pk})
        response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        # Cart should be empty after checkout
        cart_response = self.client.get(reverse('cart'))
        self.assertEqual(len(cart_response.data['items']), 0)


class WishlistTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='wisher', email='wisher@test.com', password='Pass1234!')
        Wishlist.objects.create(user=self.user)
        self.game = make_game('Wish Game', '399.00')
        response = self.client.post(reverse('login'), {'email': 'wisher@test.com', 'password': 'Pass1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_add_to_wishlist(self):
        response = self.client.post(reverse('wishlist'), {'game_id': self.game.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['games']), 1)

    def test_remove_from_wishlist(self):
        self.client.post(reverse('wishlist'), {'game_id': self.game.pk})
        response = self.client.delete(reverse('wishlist'), {'game_id': self.game.pk})
        self.assertEqual(len(response.data['games']), 0)
