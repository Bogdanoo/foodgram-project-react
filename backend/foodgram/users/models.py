from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class AccessLevels(models.TextChoices):
        ADMIN = "admin"
        AUTHORIZED = "authorized user"
        GUEST = "guest"

    access_levels = models.CharField(
        verbose_name="user's role",
        max_length=50,
        choices=AccessLevels.choices,
        default=AccessLevels.GUEST,
    )
    username = models.CharField(
        verbose_name="login",
        max_length=150,
        unique=True,
        error_messages={
            "unique": "Such a user already exists.",
        },
    )
    email = models.EmailField(
        verbose_name="email",
        max_length=254,
        unique=True,
        error_messages={
            "unique": "This email already exists.",
        },
    )
    first_name = models.CharField(
        verbose_name="name",
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name="second name",
        max_length=150,
        blank=True,
    )
    followers = models.ManyToManyField(
        "self",
        related_name="following",
        blank=True,
    )
    REQUIRED_FIELDS = ["username", "password", "first_name", "last_name"]
    USERNAME_FIELD = "email"

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=["email", "username"], name="unique_auth"
            ),
        ]
        verbose_name = "user"

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        related_name="following",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        CustomUser,
        related_name="follower",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "subscribe"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscribe"
            )
        ]

    def __str__(self):
        return self.user.username
