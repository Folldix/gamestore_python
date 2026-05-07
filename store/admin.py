from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Genre, Game, GameScreenshot, Review, Cart, CartItem, Wishlist, Order, Library, LibraryGame


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_staff', 'date_joined')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Додатково', {'fields': ('avatar',)}),
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug')


class GameScreenshotInline(admin.TabularInline):
    model = GameScreenshot
    extra = 1


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'developer', 'price', 'discount_percent', 'is_active')
    list_filter = ('genres', 'is_active', 'release_date')
    search_fields = ('title', 'developer', 'publisher')
    filter_horizontal = ('genres',)
    inlines = [GameScreenshotInline]
    fieldsets = (
        ('Основне', {'fields': ('title', 'slug', 'description', 'developer', 'publisher', 'release_date', 'cover_image', 'genres', 'is_active')}),
        ('Ціна', {'fields': ('price', 'discount_percent')}),
        ('Мінімальні вимоги', {'fields': ('min_os', 'min_cpu', 'min_ram', 'min_gpu', 'min_storage')}),
        ('Рекомендовані вимоги', {'fields': ('rec_os', 'rec_cpu', 'rec_ram', 'rec_gpu', 'rec_storage')}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('game', 'user', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status',)
    filter_horizontal = ('games',)


admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(Library)
admin.site.register(LibraryGame)
