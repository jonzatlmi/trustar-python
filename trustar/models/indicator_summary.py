# python 2 backwards compatibility
from __future__ import print_function
from builtins import object, super
from future import standard_library
from six import string_types

# package imports
from .base import ModelBase
from .intelligence_source import IntelligenceSource


class IndicatorSummary(ModelBase):
    """
    Models an |IndicatorSummary_resource|.  This represents a normalized summary of common properties extracted from the
    body of a report, from an intelligence source, that gives details about a specific indicator.

    The score field will only be populated if the source contained information that can be interpreted as a type of score.
    The attributes field is a list of |IndicatorAttribute| objects for fields that are specific to this source.

    :ivar str value: The indicator's value.
    :ivar IndicatorType indicator_type: The indicator's type.
    :ivar str report_id: The ID of the report for this summary.
    :ivar str enclave_id: The ID of the report's enclave.
    :ivar IntelligenceSource source: An object containing information about the source that the report came from.
    :ivar IndicatorScore score: The score of the report, according to the source.
    :ivar int created: The created or first seen timestamp of the indicator, according to the source.
    :ivar int updated: The updated or last seen timestamp of the indicator, according to the source.
    :ivar str description: The description of the indicator, according to the source.
    :ivar list(Attribute) attributes: A list of attributes about the indicator, according to the source.
    :ivar str severity_level: a normalized representation of the score from this source (if one exists).  This is
        an integer between 0 and 3, with 0 being the lowest score and 3 being the highest.
    """

    def __init__(self,
                 value=None,
                 indicator_type=None,
                 report_id=None,
                 enclave_id=None,
                 source=None,
                 score=None,
                 created=None,
                 updated=None,
                 description=None,
                 attributes=None,
                 severity_level=None):

        self.value = value
        self.indicator_type = indicator_type
        self.report_id = report_id
        self.enclave_id = enclave_id
        self.source = source
        self.score = score
        self.created = created
        self.updated = updated
        self.description = description
        self.attributes = attributes
        self.severity_level = severity_level

    @classmethod
    def from_dict(cls, indicator_summary):
        """
        Create an |IndicatorSummary| object from a dictionary.

        :param indicator_summary: The dictionary.
        :return: The |IndicatorSummary| object.
        """

        attributes = [IndicatorAttribute.from_dict(attribute) for attribute in indicator_summary.get('attributes', [])]

        source = indicator_summary.get('source')
        if source:
            source = IntelligenceSource.from_dict(indicator_summary.get('source'))
            
        score = indicator_summary.get('score')
        if score:
            score = IndicatorScore.from_dict(indicator_summary.get('score'))

        return IndicatorSummary(value=indicator_summary.get('value'),
                                indicator_type=indicator_summary.get('type'),
                                report_id=indicator_summary.get('reportId'),
                                enclave_id=indicator_summary.get('enclaveId'),
                                source=source,
                                score=score,
                                created=indicator_summary.get('created'),
                                updated=indicator_summary.get('updated'),
                                description=indicator_summary.get('description'),
                                attributes=attributes,
                                severity_level=indicator_summary.get('severityLevel'))

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the indicator summary.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the indicator summary.
        """

        if remove_nones:
            return super(IndicatorSummary, self).to_dict(remove_nones=True)

        source = None
        if self.source is not None:
            source = self.source.to_dict()

        score = None
        if self.score is not None:
            score = self.score.to_dict()

        attributes = None
        if self.attributes is not None:
            attributes = [attribute.to_dict(remove_nones=remove_nones) for attribute in self.attributes]

        return {
            'value': self.value,
            'type': self.indicator_type,
            'reportId': self.report_id,
            'enclaveId': self.enclave_id,
            'source': source,
            'score': score,
            'created': self.created,
            'updated': self.updated,
            'description': self.description,
            'attributes': attributes,
            'severityLevel': self.severity_level
        }


class IndicatorScore(ModelBase):
    """
    Models a |IndicatorScore_resource|.

    :ivar str name: The name of the score type, e.g. "Risk Score" or "Malicious Confidence"
    :ivar str value: The value of the score, as directly extracted from the source.
    """

    def __init__(self,
                 name=None,
                 value=None):

        self.name = name
        self.value = value

    @classmethod
    def from_dict(cls, indicator_score):
        """
        Create an |IndicatorScore| object from a dictionary.

        :param indicator_score: The dictionary.
        :return: The |IndicatorScore| object.
        """

        return IndicatorScore(name=indicator_score.get('name'),
                              value=indicator_score.get('value'))

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the indicator score.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the indicator score.
        """

        return {
            'name': self.name,
            'value': self.value
        }


class IndicatorAttribute(ModelBase):
    """
    Models a |IndicatorAttribute_resource|.  This is an attribute of an indicator, according to an intelligence source.

    :ivar str name: The name of the attribute, e.g. "Actors" or "Malware Families"
    :ivar any value: The value of the attribute, e.g. "North Korea" or "Emotet"
    :ivar str logical_type: Describes how to interpret the ``value`` field, e.g. could be "timestamp" if ``value`` is an integer
    :ivar str description: A description of how to interpret this attribute.  This corresponds to the attribute name,
        i.e. this will be the same for all attributes in a source with the same name.
    """

    def __init__(self,
                 name=None,
                 value=None,
                 logical_type=None,
                 description=None):

        self.name = name
        self.value = value
        self.logical_type = logical_type
        self.description = description

    @classmethod
    def from_dict(cls, indicator_attribute):
        """
        Create an |IndicatorAttribute| object from a dictionary.

        :param indicator_attribute: The dictionary.
        :return: The |IndicatorAttribute| object.
        """

        return IndicatorAttribute(name=indicator_attribute.get('name'),
                                  value=indicator_attribute.get('value'),
                                  logical_type=indicator_attribute.get('logicalType'),
                                  description=indicator_attribute.get('description'))

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the indicator attribute.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the indicator attribute.
        """

        return {
            'name': self.name,
            'value': self.value,
            'logicalType': self.logical_type,
            'description': self.description
        }
