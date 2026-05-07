from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    user_type = models.CharField(max_length=20, default='CUSTOMER')
    account_status = models.CharField(max_length=20, default='ACTIVE')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    customer_level = models.CharField(max_length=20, default='NONE')
    loyalty_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'

    def __str__(self):
        return self.email


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанри'

    def __str__(self):
        return self.name


class Game(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    developer = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    release_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    cover_image = models.ImageField(upload_to='games/covers/', null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name='games', blank=True)

    # System requirements
    min_os = models.CharField(max_length=255, blank=True)
    min_cpu = models.CharField(max_length=255, blank=True)
    min_ram = models.CharField(max_length=100, blank=True)
    min_gpu = models.CharField(max_length=255, blank=True)
    min_storage = models.CharField(max_length=100, blank=True)
    rec_os = models.CharField(max_length=255, blank=True)
    rec_cpu = models.CharField(max_length=255, blank=True)
    rec_ram = models.CharField(max_length=100, blank=True)
    rec_gpu = models.CharField(max_length=255, blank=True)
    rec_storage = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Гра'
        verbose_name_plural = 'Ігри'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def discounted_price(self):
        if self.discount_percent > 0:
            return self.price * (1 - self.discount_percent / 100)
        return self.price

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0


class GameScreenshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='games/screenshots/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.game.title} — screenshot {self.order}"


class Review(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'user')
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'

    def __str__(self):
        return f"{self.user.email} → {self.game.title} ({self.rating}★)"

class ReviewHelpfulVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_helpful_votes')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.email} liked review #{self.review_id}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Кошик'
        verbose_name_plural = 'Кошики'

    def __str__(self):
        return f"Кошик: {self.user.email}"

    @property
    def total(self):
        return sum(item.game.discounted_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'game')

    def __str__(self):
        return f"{self.cart.user.email} — {self.game.title}"


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    games = models.ManyToManyField(Game, related_name='wishlisted_by', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Список бажань'
        verbose_name_plural = 'Списки бажань'

    def __str__(self):
        return f"Wishlist: {self.user.email}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує'),
        ('paid', 'Оплачено'),
        ('cancelled', 'Скасовано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    games = models.ManyToManyField(Game, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.user.email}"


class Promotion(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    discount_percent = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    games = models.ManyToManyField(Game, related_name='promotions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Library(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='library')
    games = models.ManyToManyField(Game, through='LibraryGame', related_name='owned_by')

    class Meta:
        verbose_name = 'Бібліотека'
        verbose_name_plural = 'Бібліотеки'

    def __str__(self):
        return f"Library: {self.user.email}"


class LibraryGame(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    play_time_minutes = models.PositiveIntegerField(default=0)
    is_installed = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)
    last_played = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('library', 'game')

    def __str__(self):
        return f"{self.library.user.email} — {self.game.title}"
