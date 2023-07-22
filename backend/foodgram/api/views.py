from rest_framework.decorators import action

import users.models
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
from django_filters import rest_framework as filters
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPageNumberPagination
from .permissions import AdminPermission, IsAuthorOrReadOnly
from .serializers import (DjoserUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeDetailShortSerializer,
                          RecipeSerializer, SubscribeSerializer, TagSerializer)
from .services import get_shoping_cart_file

User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPageNumberPagination
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, AdminPermission
    )
    serializer_class = DjoserUserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset.annotate(recipes_count=Count('recipes'))
        return queryset


class SubscribtionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeCreateSerializer
    queryset = Recipe.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly, AdminPermission)
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return Recipe.objects.annotate(
            is_favorite=Exists(
                Recipe.objects.filter(
                    author=self.request.user, id=OuterRef('id'))),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef('id')))
        ).select_related('author').all()

    @staticmethod
    def _create_or_delete_item(request, recipe, model, serializer):
        try:
            item = model.objects.get(user=request.user, recipe=recipe)
            if request.method == 'DELETE':
                item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except model.DoesNotExist:
            if request.method == 'POST':
                item = model.objects.create(user=request.user, recipe=recipe)
                serializer = serializer(item)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[
            permissions.IsAuthenticatedOrReadOnly,
            AdminPermission
        ],
    )
    def favorite(self, request):
        recipe = self.get_object()
        serializer = RecipeDetailShortSerializer
        return self._create_or_delete_item(
            request, recipe, Favorite, serializer
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[
            permissions.IsAuthenticatedOrReadOnly,
            AdminPermission
        ],
    )
    def shopping_cart(self, request):
        recipe = self.get_object()
        serializer = RecipeDetailShortSerializer
        return self._create_or_delete_item(
            request, recipe, ShoppingCart, serializer
        )

    @staticmethod
    def download_shopping_cart(request):
        shopping_cart = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_carts__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        return get_shoping_cart_file(shopping_cart)


class ShoppingListViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeDetailShortSerializer

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)


class SubscriptionListView(generics.ListAPIView):
    search_fields = ['author__username']
    permission_classes = [permissions.IsAuthenticated, AdminPermission]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_fields = ['author__username']
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return users.models.Subscribe.objects.filter(
            user=self.request.user
        ).select_related('author')


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeDetailShortSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
