# -*- coding: utf-8 -*-

# Django 1.5 has moved this constant up one level.
from django.core.exceptions import ValidationError

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError:
    from django.db.models.sql.constants import LOOKUP_SEP

from rest_framework.filters import BaseFilterBackend


# Enable all basic ORM filters but do not allow filtering across relationships.
ALL = 1
# Enable all ORM filters, including across relationships
ALL_WITH_RELATIONS = 2


class DictFilterBackend(BaseFilterBackend):
    """
    Tastypie-like filter backend
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        filters = request.QUERY_PARAMS.copy()
        serializer_class = view.get_serializer_class()
        filters_dict = getattr(view, 'filters_dict', None)

        if not filters_dict:
            return queryset.all()

        applicable_filters = self.build_filters(
            filters=filters,
            queryset=queryset,
            serializer_class=serializer_class,
            filters_dict=filters_dict
        )

        try:
            return queryset.filter(**applicable_filters)
        except (ValueError, ValidationError):  # todo: test ValueError handling
            return queryset.all()

    def build_filters(self, filters, queryset, serializer_class, filters_dict):
        """
        Given a dictionary of filters, create the necessary ORM-level filters.

        Keys should be resource fields, **NOT** model fields.

        Valid values are either a list of Django filter types (i.e.
        ``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
        ``ALL_WITH_RELATIONS`` constant.
        """
        # At the declarative level:
        #     filtering = {
        #         'resource_field_name': ['exact', 'startswith', 'endswith', 'contains'],
        #         'resource_field_name_2': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        #         'resource_field_name_3': ALL,
        #         'resource_field_name_4': ALL_WITH_RELATIONS,
        #         ...
        #     }
        qs_filters = {}
        query_terms = self.get_query_terms(queryset)

        for filter_expr, value in filters.items():
            # example: author__id__in=1,2,3
            filter_bits = filter_expr.split(LOOKUP_SEP)  # => ['author', 'id', 'in']
            field_name = filter_bits.pop(0)  # => 'author'
            filter_type = 'exact'

            if not field_name in serializer_class.Meta.fields:
                # It's not a field we know about. Move along citizen.
                continue

            if filter_bits and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()  # => 'in'

            lookup_bits = self.check_filtering(
                field_name=field_name,
                filter_type=filter_type,
                filter_bits=filter_bits,
                filters_dict=filters_dict,
                serializer_class=serializer_class
            )
            if not lookup_bits:
                continue
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return qs_filters

    def get_query_terms(self, queryset):
        if hasattr(queryset.query.query_terms, 'keys'):
            # Django 1.4 & below compatibility.
            return queryset.query.query_terms.keys()
        else:
            # Django 1.5+.
            return queryset.query.query_terms

    def check_filtering(self, field_name, filter_type, filter_bits, filters_dict, serializer_class):
        if not field_name in filters_dict:
            return None

        # Check to see if it's an allowed lookup type.
        if not filters_dict[field_name] in (ALL, ALL_WITH_RELATIONS):
            # Must be an explicit whitelist.
            if not filter_type in filters_dict[field_name]:
                return None

        # todo: check if it is relation model field
        # todo: if field is relational serializer, then recursively drill through and use serializer fieldname
        # (not model)

        if field_name in serializer_class.base_fields:
            model_field_name = serializer_class.base_fields[field_name].source or field_name
        else:
            model_field_name = field_name

        # Check to see if it's a relational lookup and if that's allowed.
        if filter_bits:
            if not filters_dict[field_name] == ALL_WITH_RELATIONS:
                return None
            return [model_field_name] + filter_bits
        else:
            return [model_field_name]

    def filter_value_to_python(self, value, field_name, filters, filter_expr, filter_type):
        """
        Turn the string ``value`` into a python object.
        """
        # Simple values
        if value in ['true', 'True', True]:
            value = True
        elif value in ['false', 'False', False]:
            value = False
        elif value in ('nil', 'none', 'None', None):
            value = None

        # Split on ',' if not empty string and either an in or range filter.
        if filter_type in ('in', 'range') and len(value):
            if hasattr(filters, 'getlist'):
                value = []
                for part in filters.getlist(filter_expr):
                    value.extend(part.split(','))
            else:
                value = value.split(',')

        return value