from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
    )
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name="unique_order"
            )
        ]
