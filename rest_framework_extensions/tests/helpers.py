# -*- coding: utf-8 -*-


class TestFiltersHelperMixin(object):
    test_filters_path = None

    def filter_should_find(self, filter_args, msg=None):
        return self._filter_should_find(filter_args, is_should_find=True, msg=msg)

    def filter_should_not_find(self, filter_args, msg=None):
        return self._filter_should_find(filter_args, is_should_find=False, msg=msg)

    def _filter_should_find(self, filter_args, is_should_find, msg=None):
        self.assertEqual(self.is_found_by_filter(filter_args), is_should_find, msg=msg)

    def is_found_by_filter(self, filter_args):
        assert self.test_filters_path is not None, 'set "test_filters_path" for %s' % self.__class__.__name__
        return bool(len(self.client.get(self.test_filters_path + '?' + filter_args).data))