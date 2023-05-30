from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Tag name",
        unique=True,
    )
    color = models.CharField(
        max_length=7,
        verbose_name="HEX-code",
        unique=True,
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
    )

    class Meta:
        verbose_name = "Tag"
        ordering = ("pk",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name="ingredient name",
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name="measurement unit",
        unique=True,
        max_length=200,
    )

    class Meta:
        verbose_name = "ingredient"
        ordering = ("pk",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="author",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="name",
    )
    tags = models.ManyToManyField(Tag, verbose_name="Tags")
    image = models.ImageField(
        verbose_name="image",
        upload_to="recipes/",
    )
    text = models.TextField(
        verbose_name="description",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Cooking time, min",
        validators=(validators.MinValueValidator(1),)
    )
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name="ingredients"
    )

    class Meta:
        verbose_name = "recipe"
        ordering = ('-id',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients_in_recipe",
        verbose_name="recipe",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="used_in_recipes",
        verbose_name="ingredient",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="amount",
        validators=(validators.MinValueValidator(1),)
    )

    class Meta:
        verbose_name = "IngredientInRecipe"

    def __str__(self):
        return f"{self.recipe}-({self.ingredient} - {self.amount})"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="favorites list author",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="recipe from list",
    )

    class Meta:
        verbose_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite_recipes"
            )
        ]

    def __str__(self):
        return f"{self.user} added to favorites {self.recipe}"
