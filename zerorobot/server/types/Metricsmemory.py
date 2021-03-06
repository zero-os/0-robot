# DO NOT EDIT THIS FILE. This file will be overwritten when re-running go-raml.

"""
Auto-generated class for Metricsmemory
"""

from . import client_support


class Metricsmemory(object):
    """
    auto-generated. don't touch.
    """

    @staticmethod
    def create(**kwargs):
        """
        :type active: float
        :type cached: float
        :type free: float
        :type swap_free: float
        :type swap_total: float
        :type total: float
        :rtype: Metricsmemory
        """

        return Metricsmemory(**kwargs)

    def __init__(self, json=None, **kwargs):
        if json is None and not kwargs:
            raise ValueError('No data or kwargs present')

        class_name = 'Metricsmemory'
        data = json or kwargs

        # set attributes
        data_types = [float]
        self.active = client_support.set_property('active', data, data_types, False, [], False, True, class_name)
        data_types = [float]
        self.cached = client_support.set_property('cached', data, data_types, False, [], False, True, class_name)
        data_types = [float]
        self.free = client_support.set_property('free', data, data_types, False, [], False, True, class_name)
        data_types = [float]
        self.swap_free = client_support.set_property('swap_free', data, data_types, False, [], False, True, class_name)
        data_types = [float]
        self.swap_total = client_support.set_property(
            'swap_total', data, data_types, False, [], False, True, class_name)
        data_types = [float]
        self.total = client_support.set_property('total', data, data_types, False, [], False, True, class_name)

    def __str__(self):
        return self.as_json(indent=4)

    def as_json(self, indent=0):
        return client_support.to_json(self, indent=indent)

    def as_dict(self):
        return client_support.to_dict(self)
