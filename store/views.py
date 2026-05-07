from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from .models import (
    User, Genre, Game, Review, ReviewHelpfulVote,
    Cart, CartItem, Wishlist, Order, Library, LibraryGame, Promotion
)
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    GenreSerializer, GameListSerializer, GameDetailSerializer,
    ReviewSerializer, CartSerializer, CartItemSerializer,
    WishlistSerializer, OrderSerializer, LibrarySerializer, LibraryGameSerializer,
    PromotionSerializer
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': str(refresh.access_token),
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': str(refresh.access_token),
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class MeView(ProfileView):
    pass

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        current_password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')
        if not current_password or not new_password:
            return Response({'detail': 'currentPassword and newPassword are required.'}, status=400)
        if not request.user.check_password(current_password):
            return Response({'detail': 'Current password is incorrect.'}, status=400)
        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])
        return Response({'message': 'Password updated successfully'})

class UsersListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer

    def get_queryset(self):
        search = self.request.query_params.get('search')
        qs = User.objects.all().order_by('-date_joined')
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(username__icontains=search))
        return qs

class UserRoleUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        role = request.data.get('role')
        if role not in ['CUSTOMER', 'ADMIN']:
            return Response({'detail': 'Invalid role'}, status=400)
        user.user_type = role
        user.is_staff = role == 'ADMIN'
        user.save(update_fields=['user_type', 'is_staff'])
        return Response(UserSerializer(user).data)

class UserUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_url_kwarg = 'user_id'

class BanUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        email = request.data.get('email')
        user = get_object_or_404(User, email=email)
        user.account_status = 'BANNED'
        user.is_active = False
        user.save(update_fields=['account_status', 'is_active'])
        return Response(UserSerializer(user).data)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        response = {'message': 'If the email exists, password reset instructions have been sent.'}
        if user and request.headers.get('x-env') != 'production':
            token = PasswordResetTokenGenerator().make_token(user)
            response['resetToken'] = token
            response['uid'] = user.pk
        return Response(response)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        uid = request.data.get('uid')
        if not all([token, password, uid]):
            return Response({'detail': 'token, password and uid are required.'}, status=400)
        user = get_object_or_404(User, pk=uid)
        generator = PasswordResetTokenGenerator()
        if not generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired reset token'}, status=400)
        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'message': 'Password has been reset successfully'})

# ── Genres ────────────────────────────────────────────────────────────────────

class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


# ── Games ─────────────────────────────────────────────────────────────────────

class GameListView(generics.ListAPIView):
    serializer_class = GameListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'developer', 'publisher', 'genres__name']
    ordering_fields = ['price', 'release_date', 'title', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Game.objects.filter(is_active=True).prefetch_related('genres', 'reviews')
        genre = self.request.query_params.get('genre')
        if genre:
            qs = qs.filter(genres__slug=genre)
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        on_sale = self.request.query_params.get('on_sale')
        if on_sale == 'true':
            qs = qs.filter(discount_percent__gt=0)
        return qs


class GameDetailView(generics.RetrieveAPIView):
    queryset = Game.objects.filter(is_active=True).prefetch_related(
        'genres', 'screenshots', 'reviews__user'
    )
    serializer_class = GameDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

class GameDetailByIdView(generics.RetrieveAPIView):
    queryset = Game.objects.filter(is_active=True).prefetch_related('genres', 'screenshots', 'reviews__user')
    serializer_class = GameDetailSerializer
    permission_classes = [AllowAny]

class GameAdminCreateView(generics.CreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameDetailSerializer
    permission_classes = [IsAdminUser]

class GameAdminUpdateView(generics.UpdateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameDetailSerializer
    permission_classes = [IsAdminUser]

class GameAdminDeleteView(generics.DestroyAPIView):
    queryset = Game.objects.all()
    permission_classes = [IsAdminUser]


# ── Reviews ───────────────────────────────────────────────────────────────────

class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        game = get_object_or_404(Game, slug=self.kwargs['slug'])
        is_verified = LibraryGame.objects.filter(library__user=self.request.user, game=game).exists()
        serializer.save(user=self.request.user, game=game, is_verified_purchase=is_verified)

class ReviewListByGameIdView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Review.objects.filter(game_id=self.kwargs['game_id']).select_related('user').order_by('-created_at')

class ReviewCreateByGameIdView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        game = get_object_or_404(Game, pk=request.data.get('gameId'))
        if Review.objects.filter(user=request.user, game=game).exists():
            return Response({'detail': 'You already reviewed this game'}, status=400)
        is_verified = LibraryGame.objects.filter(library__user=request.user, game=game).exists()
        review = Review.objects.create(
            user=request.user,
            game=game,
            rating=serializer.validated_data['rating'],
            comment=serializer.validated_data['comment'],
            is_verified_purchase=is_verified,
        )
        return Response(ReviewSerializer(review, context={'request': request}).data, status=201)

class ReviewUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related('user', 'game')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'review_id'

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if not (request.user.is_staff or obj.user_id == request.user.id):
            raise PermissionDenied('Not your review')

class ReviewHelpfulToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        vote, created = ReviewHelpfulVote.objects.get_or_create(user=request.user, review=review)
        if created:
            review.helpful_count += 1
            is_liked = True
        else:
            vote.delete()
            review.helpful_count = max(0, review.helpful_count - 1)
            is_liked = False
        review.save(update_fields=['helpful_count'])
        data = ReviewSerializer(review, context={'request': request}).data
        data['isLiked'] = is_liked
        return Response(data)

class ReviewModerateView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        review.is_hidden = bool(request.data.get('is_hidden', not review.is_hidden))
        review.save(update_fields=['is_hidden'])
        return Response(ReviewSerializer(review, context={'request': request}).data)


# ── Cart ──────────────────────────────────────────────────────────────────────

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def get(self, request):
        cart = self.get_cart()
        return Response(CartSerializer(cart).data)

    def post(self, request):
        """Add game to cart"""
        game_id = request.data.get('game_id')
        game = get_object_or_404(Game, pk=game_id, is_active=True)
        cart = self.get_cart()

        # Check if already owned
        try:
            library = request.user.library
            if library.games.filter(pk=game_id).exists():
                return Response({'detail': 'Гра вже є у вашій бібліотеці.'}, status=400)
        except Library.DoesNotExist:
            pass

        item, created = CartItem.objects.get_or_create(cart=cart, game=game)
        if not created:
            return Response({'detail': 'Гра вже в кошику.'}, status=400)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """Remove game from cart"""
        game_id = request.data.get('game_id')
        cart = self.get_cart()
        CartItem.objects.filter(cart=cart, game_id=game_id).delete()
        return Response(CartSerializer(cart).data)

class CartItemsCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game_id = request.data.get('gameId')
        game = get_object_or_404(Game, pk=game_id, is_active=True)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if CartItem.objects.filter(cart=cart, game=game).exists():
            return Response({'detail': 'Game already in cart'}, status=400)
        if LibraryGame.objects.filter(library__user=request.user, game=game).exists():
            return Response({'detail': 'You already own this game'}, status=400)
        item = CartItem.objects.create(cart=cart, game=game)
        return Response(CartItemSerializer(item).data, status=201)

class CartItemsDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        item.delete()
        return Response(status=204)

class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        return Response(status=204)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.select_related('game').all()

        if not items.exists():
            return Response({'detail': 'Кошик порожній.'}, status=400)

        total = sum(item.game.discounted_price for item in items)
        games = [item.game for item in items]

        order = Order.objects.create(user=request.user, total_price=total)
        order.games.set(games)

        # Add to library
        library, _ = Library.objects.get_or_create(user=request.user)
        for game in games:
            LibraryGame.objects.get_or_create(library=library, game=game)

        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# ── Wishlist ──────────────────────────────────────────────────────────────────

class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get_wishlist(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    def get(self, request):
        return Response(WishlistSerializer(self.get_wishlist()).data)

    def post(self, request):
        game_id = request.data.get('game_id')
        game = get_object_or_404(Game, pk=game_id, is_active=True)
        wishlist = self.get_wishlist()
        wishlist.games.add(game)
        return Response(WishlistSerializer(wishlist).data)

    def delete(self, request):
        game_id = request.data.get('game_id')
        wishlist = self.get_wishlist()
        wishlist.games.remove(game_id)
        return Response(WishlistSerializer(wishlist).data)

class WishlistDeleteByGameIdView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, game_id):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        wishlist.games.remove(game_id)
        return Response(status=204)


# ── Library ───────────────────────────────────────────────────────────────────

class LibraryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        library, _ = Library.objects.get_or_create(user=request.user)
        return Response(LibrarySerializer(library).data)


class LibraryGameUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, game_id):
        library = get_object_or_404(Library, user=request.user)
        lib_game = get_object_or_404(LibraryGame, library=library, game_id=game_id)

        if 'is_installed' in request.data:
            lib_game.is_installed = request.data['is_installed']
        if 'play_time_minutes' in request.data:
            lib_game.play_time_minutes = request.data['play_time_minutes']
        lib_game.save()

        return Response(LibraryGameSerializer(lib_game).data)

class LibraryInstallToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, game_id):
        library = get_object_or_404(Library, user=request.user)
        lib_game = get_object_or_404(LibraryGame, library=library, game_id=game_id)
        lib_game.is_installed = not lib_game.is_installed
        lib_game.save(update_fields=['is_installed'])
        return Response(LibraryGameSerializer(lib_game).data)

class LibraryPlayView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, game_id):
        minutes = int(request.data.get('playTime', 0) or 0)
        library = get_object_or_404(Library, user=request.user)
        lib_game = get_object_or_404(LibraryGame, library=library, game_id=game_id)
        lib_game.play_time_minutes += max(0, minutes)
        lib_game.save(update_fields=['play_time_minutes'])
        return Response(LibraryGameSerializer(lib_game).data)


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('games')

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.prefetch_related('games')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

class OrderCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        items = request.data.get('items', [])
        game_ids = list({item.get('gameId') for item in items if item.get('gameId')})
        games = list(Game.objects.filter(pk__in=game_ids, is_active=True))
        if not games:
            return Response({'detail': 'One or more games not found'}, status=400)
        library, _ = Library.objects.get_or_create(user=request.user)
        owned = LibraryGame.objects.filter(library=library, game_id__in=game_ids).select_related('game')
        if owned.exists():
            titles = ', '.join([entry.game.title for entry in owned])
            return Response({'detail': f'You already own: {titles}'}, status=400)
        total = sum(game.discounted_price for game in games)
        order = Order.objects.create(user=request.user, total_price=total, status='paid')
        order.games.set(games)
        for game in games:
            LibraryGame.objects.get_or_create(library=library, game=game)
        Wishlist.objects.filter(user=request.user, games__in=games).update(updated_at=order.created_at)
        return Response(OrderSerializer(order).data, status=201)

# ── Discounts ─────────────────────────────────────────────────────────────────

class PromotionListCreateView(generics.ListCreateAPIView):
    serializer_class = PromotionSerializer

    def get_queryset(self):
        qs = Promotion.objects.prefetch_related('games')
        if self.request.query_params.get('activeOnly') == 'true':
            now = timezone.now()
            qs = qs.filter(is_active=True, start_at__lte=now, end_at__gte=now)
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

class PromotionUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Promotion.objects.prefetch_related('games')
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser]
