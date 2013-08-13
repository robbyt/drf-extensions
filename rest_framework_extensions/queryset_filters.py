# -*- coding: utf-8 -*-
import django_filters


class MethodFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        args = value.split(',')
        try:
            return getattr(qs, self.name)(*args)
        except TypeError:
            return qs


class BooleanFilter(django_filters.BooleanFilter):
    def __init__(self, true_method_name, false_method_name, *args, **kwargs):
        self.true_method_name = true_method_name
        self.false_method_name = false_method_name
        super(BooleanFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value is not None:
            if value:
                return getattr(qs, self.true_method_name)()
            else:
                return getattr(qs, self.false_method_name)()
        return qs