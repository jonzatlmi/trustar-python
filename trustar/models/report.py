# python 2 backwards compatibility
from __future__ import print_function
from builtins import object, super
from future import standard_library
from six import string_types

# package imports
from ..utils import normalize_timestamp
from .base import ModelBase
from .enum import *


class Report(ModelBase):
    """
    Models a |Report_resource|.

    :ivar id: the report guid
    :ivar title: the report title
    :ivar body: the report body
    :ivar time_began: the time that the incident began; either an integer (milliseconds since epoch) or an isoformat
        datetime string
    :ivar external_id: An external tracking id.  For instance, if the report is a copy of a corresponding report in some
        external system, this should contain its id in that system.
    :ivar external_url: A URL to the report in an external system (if one exists).
    :ivar is_enclave: A boolean representing whether the distribution type of the report is ENCLAVE or COMMUNITY.
    :ivar enclave_ids: A list of IDs of enclaves that the report belongs to
    """

    ID_TYPE_INTERNAL = IdType.INTERNAL
    ID_TYPE_EXTERNAL = IdType.EXTERNAL

    DISTRIBUTION_TYPE_ENCLAVE = DistributionType.ENCLAVE
    DISTRIBUTION_TYPE_COMMUNITY = DistributionType.COMMUNITY

    def __init__(self,
                 id=None,
                 title=None,
                 body=None,
                 time_began=None,
                 external_id=None,
                 external_url=None,
                 is_enclave=True,
                 enclave_ids=None,
                 created=None,
                 updated=None):
        """
        Constructs a Report object.

        :param id: the report guid
        :param title: the report title
        :param body: the report body
        :param time_began: the time that the incident began; either an integer (milliseconds since epoch) or an
            isoformat datetime string
        :param external_id: An external tracking id.  For instance, if the report is a copy of a corresponding report in
            some external system, this should contain its id in that system.
        :param external_url: A URL to the report in an external system (if one exists).
        :param is_enclave: A boolean representing whether the distribution type of the report is ENCLAVE or COMMUNITY.
        :param enclave_ids: The list of enclave_ids the report is associated with.  If ``is_enclave`` is ``True``, this
            cannot be ``None`` or empty.
        """

        # default to distribution type ENCLAVE
        if is_enclave is None:
            is_enclave = True

        self.id = id
        self.title = title
        self.body = body
        self.external_id = external_id
        self.external_url = external_url
        self.is_enclave = is_enclave
        self.enclave_ids = enclave_ids
        self.created = created
        self.updated = updated

        self.set_time_began(time_began)

        if isinstance(self.enclave_ids, string_types):
            self.enclave_ids = [self.enclave_ids]

    def set_time_began(self, time_began):
        self.time_began = normalize_timestamp(time_began)

    def _get_distribution_type(self):
        """
        :return: A string indicating whether the report belongs to an enclave or not.
        """

        if self.is_enclave:
            return DistributionType.ENCLAVE
        else:
            return DistributionType.COMMUNITY

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the object.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the report.
        """

        if remove_nones:
            report_dict = super(Report, self).to_dict(remove_nones=True)
        else:
            report_dict = {
                'title': self.title,
                'reportBody': self.body,
                'timeBegan': self.time_began,
                'externalUrl': self.external_url,
                'distributionType': self._get_distribution_type(),
                'externalTrackingId': self.external_id,
                'enclaveIds': self.enclave_ids,
                'created': self.created,
                'updated': self.updated,
            }

        # id field might not be present
        if self.id is not None:
            report_dict['id'] = self.id
        else:
            report_dict['id'] = None

        return report_dict

    @classmethod
    def from_dict(cls, report):
        """
        Create a report object from a dictionary.  This method is intended for internal use, to construct a
        :class:`Report` object from the body of a response json.  It expects the keys of the dictionary to match those
        of the json that would be found in a response to an API call such as ``GET /report/{id}``.

        :param report: The dictionary.
        :return: The report object.
        """

        # determine distribution type
        distribution_type = report.get('distributionType')
        if distribution_type is not None:
            is_enclave = distribution_type.upper() != DistributionType.COMMUNITY
        else:
            is_enclave = None

        return Report(id=report.get('id'),
                      title=report.get('title'),
                      body=report.get('reportBody'),
                      time_began=report.get('timeBegan'),
                      external_id=report.get('externalTrackingId'),
                      external_url=report.get('externalUrl'),
                      is_enclave=is_enclave,
                      enclave_ids=report.get('enclaveIds'),
                      created=report.get('created'),
                      updated=report.get('updated'))
