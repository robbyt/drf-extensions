# -*- coding: utf-8 -*-
from mock import Mock, patch

from django.db.models.query import QuerySet
from django.test import TestCase
from django.db import models

from rest_framework import serializers, routers
from rest_framework import viewsets
from rest_framework import filters as drf_filters
import django_filters

from rest_framework_extensions.tests.models import DRFExtensionsModel
from rest_framework_extensions.tests.helpers import TestFiltersHelperMixin
from rest_framework_extensions import queryset_filters


class ProfileQuerySet(QuerySet):
    def filter_by_students(self):
        return self.filter(activities='studying')

    def exclude_students(self):
        return self.exclude(activities='studying')

    def filter_by_with_name_and_surname(self, name, surname):
        return self.filter(name=name, surname=surname)


class ProfileManager(models.Manager):
    def get_query_set(self):
        return ProfileQuerySet(self.model, using=self._db)


class Profile(DRFExtensionsModel):
    activities = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)

    objects = ProfileManager()

    def is_student(self):
        return self.activities == 'studying'


class ProfileSerializer(serializers.ModelSerializer):
    is_student = serializers.BooleanField()

    class Meta:
        model = Profile
        fields = (
            'id',
            'name',
            'surname',
            'is_student',
        )


class ProfileFilter(django_filters.FilterSet):
    is_student = queryset_filters.BooleanFilter(
        true_method_name='filter_by_students',
        false_method_name='exclude_students',
    )
    with_name_and_surname = queryset_filters.MethodFilter('filter_by_with_name_and_surname')

    class Meta:
        model = Profile
        fields = [
            'is_student',
            'with_name_and_surname',
        ]


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filter_class = ProfileFilter


router = routers.DefaultRouter()
router.register(r'profiles', ProfileViewSet, base_name='profile')
urlpatterns = router.urls


class TestQuerySetFilters(TestFiltersHelperMixin, TestCase):
    urls = 'rest_framework_extensions.tests.test_queryset_filters'
    test_filters_path = '/profiles/'

    def setUp(self):
        self.profile = Profile.objects.create(
            id=1,
            name='gennady',
            surname='chibisov',
            activities='worker',
        )

    def test_boolean__true(self):
        self.profile.activities = 'studying'
        self.profile.save()

        self.filter_should_find('is_student=True')
        self.filter_should_not_find('is_student=False')

    def test_boolean__false(self):
        self.profile.activities = 'working'
        self.profile.save()

        self.filter_should_not_find('is_student=True')
        self.filter_should_find('is_student=False')

    def test_boolean__bad_value(self):
        self.filter_should_find('is_student=some bad value')

    def test_queryset_method(self):
        self.profile.name = 'gennady'
        self.profile.surname = 'chibisov'
        self.profile.save()
        self.filter_should_find('with_name_and_surname=gennady,chibisov')
        self.filter_should_not_find('with_name_and_surname=vladimir,chibisov')  # wrong name
        self.filter_should_not_find('with_name_and_surname=gennady,ivanov')  # wrong surname

    def test_queryset_method__wrong_number_of_params(self):
        self.filter_should_find('with_name_and_surname=gennady')
        self.filter_should_find('with_name_and_surname=')

    def test_queryset_method__should_not_perform_query_without_arguments(self):
        class MockException(Exception):
            pass

        with patch.object(ProfileQuerySet, 'filter_by_with_name_and_surname', Mock(side_effect=MockException)):
            try:
                self.filter_should_find('with_name_and_surname=')
            except MockException:
                self.fail('Should not perform queryset evaluation without arguments')

            try:
                self.filter_should_find('')
            except MockException:
                self.fail('Should not perform queryset evaluation without filter property')