from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from rest_framework import serializers
from users.models import CustomUser, Subscribe

from .fields import Base64ImageField

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class UserRegistrationSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['user', 'author']
        read_only_fields = ['user', 'author']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'count cannot be negative.'
            )
        return value

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateIngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField()

    class Meta:
        fields = ('id', 'amount')
        model = IngredientInRecipe


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = CreateIngredientInRecipeSerializer(
        many=True,
        write_only=True,
    )
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_in_shopping_cart',
            'is_favorite',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('id', 'is_favorite', 'is_in_shopping_cart')


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = CreateIngredientInRecipeSerializer(
        many=True,
        write_only=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        read_only_fields = ('author',)

    def validate_cooking_time(self, data):
        cooking_time = data.get('cooking_time')
        if cooking_time is None or int(cooking_time) <= 0:
            raise serializers.ValidationError(
                'Cooking time cannot be negative or 0'
            )
        tags = data.get('tags')

        if not tags:
            raise serializers.ValidationError('no any tag')

        if not data:
            raise serializers.ValidationError(
                'Add an ingredient'
            )
        total_weight = 0
        ingredients = set()

        for ingredient_data in data:
            ingredient_id = ingredient_data['id']
            if ingredient_id in ingredients:
                raise serializers.ValidationError(
                    f'ingredient {ingredient_id} already exist'
                )
            weight = ingredient_data.get('amount')
            if int(weight) <= 0:
                raise serializers.ValidationError(
                    f'weight of ingredient {ingredient_id} must be greater than 0'
                )
            total_weight += int(weight)
            ingredients.add(ingredient_id)

        if total_weight <= 0:
            raise serializers.ValidationError(
                'total weight of ingredients must be greater than 0'
            )

        data['author'] = self.context['request'].user

        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients_data = self.context['request'].data.get('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        validated_data.pop('ingredients', [])
        for tag in tags:
            recipe.tags.add(tag)

        recipe.ingredients.set([])

        for ingredient_data in ingredients_data:
            amount = ingredient_data['amount']
            ingredient = Ingredient.objects.get(name=ingredient_data['name'])
            IngredientInRecipe.objects.create(
                recipe=recipe, ingredient=ingredient, amount=amount
            )

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients_data = self.context['request'].data.get('ingredients')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        instance.tags.set(tags)

        IngredientInRecipe.objects.filter(recipe=instance).delete()
        ingredient_in_recipe_list = []
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(name=ingredient_data['name'])
            amount = ingredient_data['amount']
            ingredient_in_recipe = IngredientInRecipe(
                recipe=instance, ingredient=ingredient, amount=amount
            )
            ingredient_in_recipe_list.append(ingredient_in_recipe)
        IngredientInRecipe.objects.bulk_create(ingredient_in_recipe_list)

        instance.save()
        return instance


class RecipeDetailShortSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeRecipeDetailShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    recipes = SubscribeRecipeDetailShortSerializer(
        many=True, source='author.recipes', read_only=True
    )
    recipes_count = serializers.SerializerMethodField(read_only=True)
    id = serializers.EmailField(source='author.id')
    first_name = serializers.EmailField(source='author.first_name')
    last_name = serializers.EmailField(source='author.last_name')
    username = serializers.EmailField(source='author.username')
    email = serializers.EmailField(source='author.email')
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    class Meta:
        model = Subscribe
        fields = ('id', 'author', 'recipes', 'recipes_count')
