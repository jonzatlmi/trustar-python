# python 2 backwards compatibility
from __future__ import print_function
from builtins import super

# package imports
from .base import ModelBase


class RedactedReport(ModelBase):
    """
    Models the response of the `POST /redaction/report` endpoint.

    :ivar title: the report title
    :ivar body: the report body
    """

    def __init__(self,
                 title=None,
                 body=None):
        """
        Constructs a RedactedReport object.

        :param title: the report title
        :param body: the report body
        """

        self.title = title
        self.body = body

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the object.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the redacted report.
        """

        if remove_nones:
            redacted_report_dict = super(RedactedReport, self).to_dict(remove_nones=True)
        else:
            redacted_report_dict = {
                'title': self.title,
                'reportBody': self.body
            }

        return redacted_report_dict

    @classmethod
    def from_dict(cls, redacted_report):
        """
        Create a RedactedReport object from a dictionary.  This method is intended for internal use, to construct a
        :class:`RedactedReport` object from the body of a response json.  It expects the keys of the dictionary to match those
        of the json that would be found in a response to an API call such as ``POST redaction/report``.

        :param redacted_report: The dictionary.
        :return: The RedactionReport object.
        """

        return RedactedReport(title=redacted_report.get('title'),
                              body=redacted_report.get('reportBody'))
