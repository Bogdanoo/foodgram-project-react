import users.models
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import generics, permissions, status, viewsets
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
        queryset = queryset.annotate(recipes_count=Count('recipes'))
        return queryset


class SubscriptionViewSet(viewsets.ModelViewSet):

    @staticmethod
    def subscribe(request):
        user = request.user
        author = get_object_or_404(users.models.User, id=id)

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'You cant subscribe to yourself'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription, created = users.models.Subscribe.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'errors': 'You are already subscribed to this user.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SubscribeSerializer(
                subscription, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if user == author:
                return Response(
                    {'errors': 'You cant unsubscribe from yourself'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            users.models.Subscribe.objects.filter(
                user=user, author=author
            ).delete()
            return Response(
                'Subscription deleted', status=status.HTTP_204_NO_CONTENT
            )

        else:
            return Response(
                {'errors': 'You are not subscribed to this user'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeCreateSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly, AdminPermission)
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        sub_qs = Recipe.objects.filter(
            recipe=OuterRef('id'),
            is_favorited=True,
        )
        return Recipe.objects.annotate(
            is_favorited=Exists(sub_qs),
            is_in_shopping_cart=Exists(sub_qs)
        )

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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def favorite(self, request):
        recipe = self.get_object()
        serializer = RecipeDetailShortSerializer
        return self._create_or_delete_item(
            request, recipe, Favorite, serializer
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
        queryset = users.models.Subscribe.objects.filter(
            user=self.request.user
        ).select_related('author')
        return queryset


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
