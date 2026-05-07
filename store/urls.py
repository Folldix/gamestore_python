from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('auth/users/', views.UsersListView.as_view(), name='users-list'),
    path('auth/users/<int:user_id>/role/', views.UserRoleUpdateView.as_view(), name='user-role-update'),
    path('auth/users/<int:user_id>/', views.UserUpdateView.as_view(), name='user-update'),
    path('auth/users/ban/', views.BanUserView.as_view(), name='user-ban'),
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    # Games
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('games/', views.GameListView.as_view(), name='game-list'),
    path('games/<slug:slug>/', views.GameDetailView.as_view(), name='game-detail'),
    path('games/<slug:slug>/reviews/', views.ReviewCreateView.as_view(), name='review-create'),
    path('games/<int:pk>/', views.GameDetailByIdView.as_view(), name='game-detail-by-id'),
    path('games/admin/create/', views.GameAdminCreateView.as_view(), name='game-admin-create'),
    path('games/admin/<int:pk>/', views.GameAdminUpdateView.as_view(), name='game-admin-update'),
    path('games/admin/<int:pk>/delete/', views.GameAdminDeleteView.as_view(), name='game-admin-delete'),

    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('cart/items/', views.CartItemsCreateView.as_view(), name='cart-item-create'),
    path('cart/items/<int:item_id>/', views.CartItemsDeleteView.as_view(), name='cart-item-delete'),
    path('cart/clear/', views.CartClearView.as_view(), name='cart-clear'),

    # Wishlist
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:game_id>/', views.WishlistDeleteByGameIdView.as_view(), name='wishlist-delete-by-game-id'),

    # Library
    path('library/', views.LibraryView.as_view(), name='library'),
    path('library/<int:game_id>/', views.LibraryGameUpdateView.as_view(), name='library-game-update'),
    path('library/games/<int:game_id>/install/', views.LibraryInstallToggleView.as_view(), name='library-install'),
    path('library/games/<int:game_id>/play/', views.LibraryPlayView.as_view(), name='library-play'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/my-orders/', views.OrderListView.as_view(), name='order-list-my'),
    path('orders/checkout/', views.OrderCheckoutView.as_view(), name='order-checkout'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),

    # Reviews
    path('reviews/game/<int:game_id>/', views.ReviewListByGameIdView.as_view(), name='reviews-by-game'),
    path('reviews/', views.ReviewCreateByGameIdView.as_view(), name='reviews-create'),
    path('reviews/<int:review_id>/', views.ReviewUpdateDeleteView.as_view(), name='reviews-update-delete'),
    path('reviews/<int:review_id>/helpful/', views.ReviewHelpfulToggleView.as_view(), name='review-helpful'),
    path('reviews/<int:review_id>/moderate/', views.ReviewModerateView.as_view(), name='review-moderate'),

    # Discounts / Promotions
    path('discounts/', views.PromotionListCreateView.as_view(), name='promotion-list-create'),
    path('discounts/<int:pk>/', views.PromotionUpdateDeleteView.as_view(), name='promotion-update-delete'),
]
