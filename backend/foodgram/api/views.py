import users.models
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django_filters import rest_framework as filters
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer,
                          RecipeCreateSerializer, RecipeDetailShortSerializer,
                          RecipeSerializer, SubscribeSerializer, TagSerializer,
                          SubscriptionSerializer)
from .services import get_shoping_cart_file

User = get_user_model()


class SubscribtionViewSet(
    UserViewSet,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer = SubscribeSerializer

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id):
        author = users.models.User.objects.get(id=id)
        if request.method == 'POST':
            item = users.models.Subscribe.objects.create(
                user=request.user,
                author=author
            )
            return Response(
                self.serializer(item).data,
                status=status.HTTP_200_OK
            )
        if request.method == 'DELETE':
            item = users.models.Subscribe.objects.get(
                user=request.user,
                author=author
            )
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=["GET"]
    )
    def subscriptions(self, request):
        queryset = users.models.Subscribe.objects.filter(
            user=request.user
        ).select_related(
            'author'
        )
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeCreateSerializer
    queryset = Recipe.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (
        IsAuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly
    )
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
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
        methods=['POST', 'DELETE'],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def favorite(self, request, pk=None):
        recipe = Recipe.objects.get(id=pk)
        serializer = RecipeDetailShortSerializer
        return self._create_or_delete_item(
            request, recipe, Favorite, serializer
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def shopping_cart(self, request, pk=None):
        recipe = Recipe.objects.get(id=pk)
        serializer = RecipeDetailShortSerializer
        return self._create_or_delete_item(
            request, recipe, ShoppingCart, serializer
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def download_shopping_cart(self, request):
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
    permission_classes = [permissions.IsAuthenticated]
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
