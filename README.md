# Django REST Framework extensions

DRF-extensions is a collection of custom extensions for [Django REST Framework](https://github.com/tomchristie/django-rest-framework)

[![Build Status](https://travis-ci.org/chibisov/drf-extensions.png?branch=master)](https://travis-ci.org/chibisov/drf-extensions)

# Installation:

    pip install drf-extensions

### Extended @action, @link decorators and router

    class DistributionViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = DistributionNews.objects.all()
        serializer_class = DistributionSerializer

        # curl -X POST /v1/distributions/1/unsubscribe/
        @action(permission_classes=[permissions.IsAuthenticated])
        def unsubscribe(self, request, *args, **kwargs):
            pass

        # curl -X POST /v1/distributions/unsubscribe/
        @action(endpoint='unsubscribe',
                is_for_list=True,
                permission_classes=[permissions.IsAuthenticated])
        def unsubscribe_from_all(self, request, *args, **kwargs):
            pass

        # curl /v1/distributions/1/unsubscribe-by-code/?code=xxxx
        @link(endpoint='unsubscribe-by-code')
        def unsubscribe_by_code(self, request, *args, **kwargs):
            pass

        # curl /v1/distributions/unsubscribe-by-code/?code=xxxx
        @link(endpoint='unsubscribe-by-code', is_for_list=True)
        def unsubscribe_by_code_from_all(self, request, *args, **kwargs):
            pass

        # curl -X POST /v1/distributions/1/subscribe/
        @action(permission_classes=[permissions.IsAuthenticated])
        def subscribe(self, request, *args, **kwargs):
            pass

        # curl -X POST /v1/distributions/subscribe/
        @action(endpoint='subscribe',
                is_for_list=True,
                permission_classes=[permissions.IsAuthenticated])
        def subscribe_to_all(self, request, *args, **kwargs):
            pass


    from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
    router = DefaultRouter()
    router.register(r'distributions', DistributionViewSet, base_name='distribution')
    urlpatterns = router.urls

### Detail serializer

DetailSerializerMixin lets add custom serializer for detail view:

    class SurveySerializer(serializers.ModelSerializer):
        class Meta:
            model = Survey
            fields = (
                'id',
                'name',
            )


    class SurveySerializerDetail(serializers.ModelSerializer):
        class Meta:
            model = Survey
            fields = (
                'id',
                'name',
                'form',
            )


    from rest_framework_extensions.mixins import DetailSerializerMixin

    class SurveyViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
        serializer_class = SurveySerializer
        serializer_detail_class = SurveySerializerDetail
        queryset = Survey.objects.all()


Custom queryset for detail view:

    class SurveyViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
        serializer_class = SurveySerializer
        serializer_detail_class = SurveySerializerDetail
        queryset = Survey.objects.all()
        queryset_detail = queryset.select_related('form')

### Tastypie-like filter backend

    from rest_framework_extensions.filters import ALL, ALL_WITH_RELATIONS, DictFilterBackend

    class ActionViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = ActionSerializer
        queryset = Action.objects.all()
        filter_backend = DictFilterBackend
        filters_dict = {
            'id': ['exact', 'in', 'range'],
            'registration_status': ALL,
            'slug': ALL,
            'category': ALL_WITH_RELATIONS,
        }

Ofcourse you can use it in backend settings:

    # settings.py

    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework_extensions.filters.DictFilterBackend',
            'rest_framework.filters.OrderingFilter',
        )
    }

### Django-filter QuerySet method filtering

Allows filtering by QuerySet methods. Definition example:

    from rest_framework_extensions import queryset_filters

    class User(models.Model):
        activities = models.CharField(max_length=100)
        name = models.CharField(max_length=100)
        surname = models.CharField(max_length=100)


    class UserFilter(django_filters.FilterSet):
        is_student = queryset_filters.BooleanFilter(
            true_method_name='filter_by_students',
            false_method_name='exclude_students',
        )
        with_name_and_surname = queryset_filters.MethodFilter('filter_by_with_name_and_surname')

        class Meta:
            model = User
            fields = [
                'is_student',
                'with_name_and_surname',
            ]


    class UserViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.all()
        filter_class = UserFilter

And now you can filter by QuerySet methods:

    $ curl /v1/users/?is_student=True
    # => User.objects.all().filter_by_students()

    $ curl /v1/users/?is_student=False
    # => User.objects.all().exclude_students()

    $ curl /v1/users/?with_name_and_surname=gennady,chibisov
    # => User.objects.all().filter_by_with_name_and_surname('gennady','chibisov')



How to run tests locally:

    $ python setup.py test