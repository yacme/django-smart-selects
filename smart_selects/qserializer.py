from __future__ import unicode_literals

from time import mktime
from datetime import datetime, date

from django.db.models import Q
from django.core.serializers.base import SerializationError

import json

__all__ = ('QSerializer',)

dt2ts = lambda obj: mktime(obj.timetuple()) if isinstance(obj, date) else obj


class QSerializer(object):
    """
    A Q object serializer base class. Pass base64=True when initalizing
    to base64 encode/decode the returned/passed string.

    By default the class provides loads/dumps methods that wrap around
    json serialization, but they may be easily overwritten to serialize
    into other formats (i.e xml, yaml, etc...)
    """

    def _prepare_value(self, qtuple):
        if qtuple[0].endswith("__range") and len(qtuple[1]) == 2:
            qtuple[1] = (datetime.fromtimestamp(qtuple[1][0]),
                         datetime.fromtimestamp(qtuple[1][1]))
        return qtuple

    def _serialize(self, q):
        """
        Serialize a Q object.
        """
        children = []
        for child in q.children:
            if isinstance(child, Q):
                children.append(self._serialize(child))
            else:
                children.append(child)
        serialized = q.__dict__
        serialized['children'] = children
        return serialized

    def _deserialize(self, d):
        """
        Serialize a Q object.
        """
        children = []
        for child in d.pop('children'):
            if isinstance(child, dict):
                children.append(self._deserialize(child))
            else:
                children.append(self._prepare_value(child))
        query = Q()
        query.children = tuple(children)
        query.connector = d['connector']
        query.negated = d['negated']
        return query

    def dumps(self, obj):
        if not isinstance(obj, Q):
            raise SerializationError
        string = json.dumps(self._serialize(obj), default=dt2ts)
        return string

    def loads(self, string):
        d = json.loads(string)
        if d is None:
            return None
        return self._deserialize(d)
