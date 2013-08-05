# -*- coding: utf-8 -*-
from django.db import models


class DRFExtensionsModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """
    class Meta:
        app_label = 'tests'
        abstract = True


class Comment(DRFExtensionsModel):
    email = models.EmailField()
    content = models.CharField(max_length=200)
    created = models.DateTimeField()


class Group(DRFExtensionsModel):
    name = models.CharField(max_length=100)


class User(DRFExtensionsModel):
    name = models.CharField(max_length=100)
    groups = models.ManyToManyField(Group)


class CommentRating(DRFExtensionsModel):
    RATING_CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    )
    rating = models.CharField(choices=RATING_CHOICES, max_length=5)
    comment = models.ForeignKey(Comment)
    created = models.DateTimeField()
    is_moderated = models.BooleanField(default=False)
    user = models.ForeignKey(User)