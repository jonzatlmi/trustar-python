# python 2 backwards compatibility
from __future__ import print_function
from builtins import object, super
from future import standard_library
from six import string_types

# package imports
from .base import ModelBase


class IntelligenceSource(ModelBase):
    """
    Models an |IntelligenceSource_resource|.

    :ivar str key: A string that uniquely identifies the source, e.g. virustotal
    :ivar str name: A human-readable name of the source, as a human-readable string, e.g. "VirusTotal"
    """

    def __init__(self,
                 key=None,
                 name=None):

        self.key = key
        self.name = name

    @classmethod
    def from_dict(cls, source):
        """
        Create an |IntelligenceSource| object from a dictionary.

        :param source: The dictionary.
        :return: The |IntelligenceSource| object.
        """

        return IntelligenceSource(key=source.get('key'),
                                  name=source.get('name'))

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the source.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the source.
        """

        return {
            'key': self.key,
            'name': self.name
        }
