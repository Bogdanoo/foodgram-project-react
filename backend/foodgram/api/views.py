from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser.views import UserViewSet
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from .permissions import IsAuthorOrReadOnly
from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Subscribe, CustomUser
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPageNumberPagination
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeDetailShortSerializer,
                          RecipeSerializer, SubscriptionSerializer,
                          SubscribeSerializer, TagSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = CustomUserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(recipes_count=Count('recipes'))
        return queryset

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=["POST", "DELETE"],
    )
    def subscribe(self, request):
        user = request.user
        author = get_object_or_404(CustomUser, id=id)

        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "You can't subscribe to yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription, created = Subscribe.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {"errors": "You are already subscribed to this user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SubscribeSerializer(
                subscription, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            if user == author:
                return Response(
                    {"errors": "You can't unsubscribe from yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscribe.objects.filter(user=user, author=author).delete()
            return Response(
                "Subscription deleted", status=status.HTTP_204_NO_CONTENT
            )

        else:
            return Response(
                {"errors": "You are not subscribed to this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False, permission_classes=[permissions.IsAuthenticated], methods=["GET"]
    )
    def subscriptions(self, request):
        queryset = Subscribe.objects.filter(user=request.user).select_related(
            'author'
        )
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeCreateSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPageNumberPagination
    queryset = Recipe.objects.all()

    def _create_or_delete_item(self, request, recipe, model, serializer):
        try:
            item = model.objects.get(user=request.user, recipe=recipe)
            if request.method == "DELETE":
                item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except model.DoesNotExist:
            if request.method == "POST":
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

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def favorite(self, request):
        recipe = self.get_object()
        serializer = RecipeDetailShortSerializer
        return self._create_or_delete_item(
            request, recipe, Favorite, serializer
        )


class SubscriptionListView(generics.ListAPIView):
    search_fields = ["author__username"]
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_fields = ["author__username"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = Subscribe.objects.filter(
            user=self.request.user
        ).select_related("author")
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
