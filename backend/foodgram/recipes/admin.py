from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientInRecipeFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_num = 1

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if not any(
            form.cleaned_data.get('DELETE') is False for form in self.forms
        ):
            raise ValidationError(
                'Recipe must contain ingredient'
            )


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    formset = IngredientInRecipeFormSet


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('name',)
    list_filter = (
        'name',
        'color',
        'slug',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInRecipeInline]
    list_display = ('name', 'author', 'count_add_favorites')
    list_filter = ('author', 'name', 'tags',)
    search_fields = ('username', 'email', 'first_name', 'last_name',)
    ordering = ('name',)

    def count_add_favorites(self, obj):
        return obj.favorites.count()

    count_add_favorites.short_description = 'Added to favorites'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('ingredient',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
    search_fields = ('recipe', 'ingredient',)
    list_filter = ('recipe', 'ingredient',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
