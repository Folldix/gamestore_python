from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import (
    User, Genre, Game, GameScreenshot, Review, Cart, CartItem, Wishlist,
    Order, Library, LibraryGame, Promotion
)


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, data):
        password2 = data.get('password2') or data['password']
        if data['password'] != password2:
            raise serializers.ValidationError({'password': 'Паролі не співпадають.'})
        data['password2'] = password2
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        # Create default cart, wishlist, library
        Cart.objects.create(user=user)
        Wishlist.objects.create(user=user)
        Library.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Невірний email або пароль.')
        if not user.is_active:
            raise serializers.ValidationError('Акаунт заблоковано.')
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user_type', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'avatar', 'date_joined', 'role',
            'balance', 'account_status', 'customer_level', 'loyalty_points'
        )
        read_only_fields = ('id', 'date_joined')


# ── Genre ────────────────────────────────────────────────────────────────────

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


# ── Game ─────────────────────────────────────────────────────────────────────

class GameScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameScreenshot
        fields = ('id', 'image', 'order')


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            'id', 'user_email', 'username', 'rating', 'comment', 'created_at',
            'is_verified_purchase', 'helpful_count', 'is_hidden', 'is_liked'
        )
        read_only_fields = (
            'id', 'user_email', 'username', 'created_at', 'is_verified_purchase',
            'helpful_count', 'is_liked'
        )

    def get_user_email(self, obj):
        return obj.user.email

    def get_username(self, obj):
        return obj.user.username

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.helpful_votes.filter(user=request.user).exists()


class GameListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    discounted_price = serializers.ReadOnlyField()
    avg_rating = serializers.ReadOnlyField()

    class Meta:
        model = Game
        fields = (
            'id', 'title', 'slug', 'developer', 'publisher', 'price',
            'discount_percent', 'discounted_price', 'cover_image', 'external_cover_url',
            'genres', 'avg_rating', 'release_date', 'download_size', 'age_rating', 'video_trailer',
        )


class GameDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    screenshots = GameScreenshotSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    discounted_price = serializers.ReadOnlyField()
    avg_rating = serializers.ReadOnlyField()
    genre = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Game
        fields = (
            'id', 'title', 'slug', 'description', 'developer', 'publisher',
            'release_date', 'price', 'discount_percent', 'discounted_price',
            'cover_image', 'external_cover_url', 'genres', 'genre', 'screenshots', 'reviews', 'avg_rating',
            'min_os', 'min_cpu', 'min_ram', 'min_gpu', 'min_storage',
            'rec_os', 'rec_cpu', 'rec_ram', 'rec_gpu', 'rec_storage',
            'download_size', 'age_rating', 'video_trailer',
        )

    @staticmethod
    def _apply_genre_string(game: Game, genre_value: str) -> None:
        from django.utils.text import slugify

        s = (genre_value or '').strip()
        if not s:
            game.genres.clear()
            return
        slug = slugify(s) or 'genre'
        genre_obj, _ = Genre.objects.get_or_create(slug=slug, defaults={'name': s})
        game.genres.set([genre_obj])

    def create(self, validated_data):
        genre_val = validated_data.pop('genre', '')
        game = super().create(validated_data)
        self._apply_genre_string(game, genre_val)
        return game

    def update(self, instance, validated_data):
        genre_val = validated_data.pop('genre', serializers.empty)
        game = super().update(instance, validated_data)
        if genre_val is not serializers.empty:
            self._apply_genre_string(game, genre_val)
        return game


# ── Cart ─────────────────────────────────────────────────────────────────────

class CartItemSerializer(serializers.ModelSerializer):
    game = GameListSerializer(read_only=True)
    game_id = serializers.PrimaryKeyRelatedField(
        queryset=Game.objects.all(), source='game', write_only=True
    )

    class Meta:
        model = CartItem
        fields = ('id', 'game', 'game_id', 'added_at')


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total', 'updated_at')


# ── Wishlist ──────────────────────────────────────────────────────────────────

class WishlistSerializer(serializers.ModelSerializer):
    games = GameListSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'games', 'updated_at')


# ── Library ───────────────────────────────────────────────────────────────────

class LibraryGameSerializer(serializers.ModelSerializer):
    game = GameListSerializer(read_only=True)

    class Meta:
        model = LibraryGame
        fields = ('id', 'game', 'play_time_minutes', 'is_installed', 'added_at', 'last_played')


class LibrarySerializer(serializers.ModelSerializer):
    games_detail = serializers.SerializerMethodField()

    class Meta:
        model = Library
        fields = ('id', 'games_detail')

    def get_games_detail(self, obj):
        items = LibraryGame.objects.filter(library=obj).select_related('game')
        return LibraryGameSerializer(items, many=True).data


# ── Order ─────────────────────────────────────────────────────────────────────

class OrderSerializer(serializers.ModelSerializer):
    games = GameListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'games', 'total_price', 'status', 'created_at')
        read_only_fields = ('id', 'total_price', 'status', 'created_at')


class PromotionGameSerializer(serializers.ModelSerializer):
    game = GameListSerializer(read_only=True)

    class Meta:
        model = Promotion.games.through
        fields = ('game',)


class PromotionSerializer(serializers.ModelSerializer):
    game_ids = serializers.PrimaryKeyRelatedField(
        queryset=Game.objects.all(), many=True, write_only=True, required=False, source='games'
    )
    games = GameListSerializer(many=True, read_only=True)
    discountPercentage = serializers.IntegerField(source='discount_percent')
    startAt = serializers.DateTimeField(source='start_at')
    endAt = serializers.DateTimeField(source='end_at')
    isActive = serializers.BooleanField(source='is_active')

    class Meta:
        model = Promotion
        fields = (
            'id', 'title', 'description', 'discountPercentage',
            'startAt', 'endAt', 'isActive', 'games', 'game_ids'
        )

    def validate(self, attrs):
        start_at = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end_at = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError({'endAt': 'End date must be after start date'})
        return attrs

    @staticmethod
    def _sync_game_discounts(promotion: Promotion):
        """Ті самі відсотки, що в промо, записуємо в Game.discount_percent — так їх бачить вітрина."""
        ids = list(promotion.games.values_list('pk', flat=True))
        if not ids:
            return
        if promotion.is_active:
            Game.objects.filter(pk__in=ids).update(discount_percent=promotion.discount_percent)
        else:
            Game.objects.filter(pk__in=ids).update(discount_percent=0)

    def create(self, validated_data):
        games = validated_data.pop('games', None) or []
        promotion = Promotion.objects.create(**validated_data)
        promotion.games.set(games)
        self._sync_game_discounts(promotion)
        return promotion

    def update(self, instance, validated_data):
        games = validated_data.pop('games', serializers.empty)
        old_ids = set(instance.games.values_list('pk', flat=True))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if games is not serializers.empty:
            new_ids = {g.pk for g in games}
            removed = old_ids - new_ids
            if removed:
                Game.objects.filter(pk__in=removed).update(discount_percent=0)
            instance.games.set(games)
        self._sync_game_discounts(instance)
        return instance
