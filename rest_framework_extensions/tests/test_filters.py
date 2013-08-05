# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from mock import patch

from rest_framework import serializers, routers
from rest_framework import viewsets

from rest_framework_extensions.tests.models import Comment, CommentRating, User
from rest_framework_extensions.test import APIRequestFactory  # todo: use from rest_framework when released
from rest_framework_extensions import filters


class CommentRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentRating
        fields = (
            'id',
            'rating',
            'comment',
            'created',
        )


class CommentRatingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentRatingSerializer
    queryset = CommentRating.objects.all()
    filters_dict = {
        'id': ['exact', 'startswith', 'endswith', 'contains'],
        'rating': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        'created': ['year', 'month', 'day'],
        'is_moderated': ['exact'],
        'comment': filters.ALL,
        'user': filters.ALL_WITH_RELATIONS
    }


router = routers.DefaultRouter()
router.register(r'comment-ratings', CommentRatingViewSet, base_name='comment-rating')
urlpatterns = router.urls

@patch(
    'rest_framework.settings.api_settings',
    'DEFAULT_FILTER_BACKENDS', ('rest_framework_extensions.filters.DictFilterBackend',)
)
class TestDictFilterBackend(TestCase):
    urls = 'rest_framework_extensions.tests.test_filters'

    def setUp(self):
        self.created = datetime.datetime(2012, 12, 1)
        self.user = User.objects.create(name='Gena')
        self.comment = Comment.objects.create(
            email='example@ya.ru',
            content='Hello world',
            created=self.created
        )
        self.comment_rating = CommentRating.objects.create(
            user=self.user,
            comment=self.comment,
            rating='1',
            created=self.created,
        )

    def test_me(self):
        resp = self.client.get('/comment-ratings/')
        expected = [
            {
                'id': 1,
                'rating': u'1',
                'comment': 1,
                'created': self.created
            }
        ]
        self.assertEquals(resp.data, expected)

    def test_me2(self):
        resp = self.client.get('/comment-ratings/?rating__gte=2')
        print resp.data
        print api_settings.DEFAULT_FILTER_BACKENDS