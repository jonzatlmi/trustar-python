# python 2 backwards compatibility
from __future__ import print_function
from builtins import object, str
from typing import Type
from future import standard_library
from six import string_types

# external imports
import json
from datetime import datetime
import functools
from requests.exceptions import BaseHTTPError

# package imports
from .log import get_logger
from .models import NumberedPage, Report, RedactedReport, DistributionType, IdType
from .utils import get_time_based_page_generator, DAY

# python 2 backwards compatibility
standard_library.install_aliases()

logger = get_logger(__name__)


class ReportClient(object):

    def get_report_details(self, report_id, id_type=None):
        """
        Retrieves a report by its ID.  Internal and external IDs are both allowed.

        :param str report_id: The ID of the incident report.
        :param str id_type: Indicates whether ID is internal or external.

        :return: The retrieved |Report| object.

        Example:

        >>> report = ts.get_report_details("1a09f14b-ef8c-443f-b082-9643071c522a")
        >>> print(report)
        {
          "id": "1a09f14b-ef8c-443f-b082-9643071c522a",
          "created": 1515571633505,
          "updated": 1515620420062,
          "reportBody": "Employee reported suspect email.  We had multiple reports of suspicious email overnight ...",
          "title": "Phishing Incident",
          "enclaveIds": [
            "ac6a0d17-7350-4410-bc57-9699521db992"
          ],
          "distributionType": "ENCLAVE",
          "timeBegan": 1479941278000
        }

        """

        params = {'idType': id_type}
        resp = self._client.get("reports/%s" % report_id, params=params)
        return Report.from_dict(resp.json())

    def get_reports_page(self, is_enclave=None, enclave_ids=None, tag=None, excluded_tags=None,
                         from_time=None, to_time=None):
        """
        Retrieves a page of reports, filtering by time window, distribution type, enclave association, and tag.
        The results are sorted by updated time.
        This method does not take ``page_number`` and ``page_size`` parameters.  Instead, each successive page must be
        found by adjusting the ``from_time`` and ``to_time`` parameters.

        Note:  This endpoint will only return reports from a time window of maximum size of 2 weeks. If you give a
        time window larger than 2 weeks, it will pull reports starting at 2 weeks before the "to" date, through the
        "to" date.

        :param boolean is_enclave: restrict reports to specific distribution type (optional - by default all accessible
            reports are returned).
        :param list(str) enclave_ids: list of enclave ids used to restrict reports to specific enclaves (optional - by
            default reports from all of user's enclaves are returned)
        :param list(str) tag: Name (or list of names) of tag(s) to filter reports by.  Only reports containing
            ALL of these tags will be returned.
        :param list(str) excluded_tags: Reports containing ANY of these tags will be excluded from the results.
        :param int from_time: start of time window in milliseconds since epoch (optional)
        :param int to_time: end of time window in milliseconds since epoch (optional)

        :return: A |NumberedPage| of |Report| objects.

        """

        distribution_type = None

        # explicitly compare to True and False to distinguish from None (which is treated as False in a conditional)
        if is_enclave:
            distribution_type = DistributionType.ENCLAVE
        elif not is_enclave:
            distribution_type = DistributionType.COMMUNITY

        if enclave_ids is None:
            enclave_ids = self.enclave_ids

        params = {
            'from': from_time,
            'to': to_time,
            'distributionType': distribution_type,
            'enclaveIds': enclave_ids,
            'tags': tag,
            'excludedTags': excluded_tags
        }
        resp = self._client.get("reports", params=params)
        result = NumberedPage.from_dict(resp.json(), content_type=Report)

        # create a NumberedPage object from the dict
        return result

    def submit_report(self, report):
        """
        Submit a report.

        * If ``report.is_enclave`` is ``True``, then the report will be submitted to the enclaves
          identified by ``report.enclaves``; if that field is ``None``, then the enclave IDs registered with this
          |TruStar| object will be used.
        * If ``report.time_began`` is ``None``, then the current time will be used.

        :param report: The |Report| object that was submitted, with the ``id`` field updated based
            on values from the response.

        Example:

        >>> report = Report(title="Suspicious Activity",
        >>>                 body="We have been receiving suspicious requests from 169.178.68.63.",
        >>>                 enclave_ids=["602d4795-31cd-44f9-a85d-f33cb869145a"])
        >>> report = ts.submit_report(report)
        >>> print(report.id)
        ac6a0d17-7350-4410-bc57-9699521db992
        >>> print(report.title)
        Suspicious Activity
        """

        # make distribution type default to "enclave"
        if report.is_enclave is None:
            report.is_enclave = True

        if report.enclave_ids is None:
            # use configured enclave_ids by default if distribution type is ENCLAVE
            if report.is_enclave:
                report.enclave_ids = self.enclave_ids
            # if distribution type is COMMUNITY, API still expects non-null list of enclaves
            else:
                report.enclave_ids = []

        if report.is_enclave and len(report.enclave_ids) == 0:
            raise Exception("Cannot submit a report of distribution type 'ENCLAVE' with an empty set of enclaves.")

        # default time began is current time
        if report.time_began is None:
            report.set_time_began(datetime.now())

        data = json.dumps(report.to_dict())
        resp = self._client.post("reports", data=data, timeout=60)

        # get report id from response body
        report_id = resp.content

        if isinstance(report_id, bytes):
            report_id = report_id.decode('utf-8')

        report.id = report_id

        return report

    def update_report(self, report):
        """
        Updates the report identified by the ``report.id`` field; if this field does not exist, then
        ``report.external_id`` will be used if it exists.  Any other fields on ``report`` that are not ``None``
        will overwrite values on the report in TruSTAR's system.   Any fields that are  ``None`` will simply be ignored;
        their values will be unchanged.

        :param report: A |Report| object with the updated values.
        :return: The |Report| object.

        Example:

        >>> report = ts.get_report_details(report_id)
        >>> print(report.title)
        Old Title
        >>> report.title = "Changed title"
        >>> updated_report = ts.update_report(report)
        >>> print(updated_report.title)
        Changed Title
        """

        # default to interal ID type if ID field is present
        if report.id is not None:
            id_type = IdType.INTERNAL
            report_id = report.id
        # if no ID field is present, but external ID field is, default to external ID type
        elif report.external_id is not None:
            id_type = IdType.EXTERNAL
            report_id = report.external_id
        # if no ID fields exist, raise exception
        else:
            raise Exception("Cannot update report without either an ID or an external ID.")

        # not allowed to update value of 'reportId', so remove it
        report_dict = {k: v for k, v in report.to_dict().items() if k != 'reportId'}

        params = {'idType': id_type}

        data = json.dumps(report.to_dict())
        self._client.put("reports/%s" % report_id, data=data, params=params)

        return report

    def delete_report(self, report_id, id_type=None):
        """
        Deletes the report with the given ID.

        :param report_id: the ID of the report to delete
        :param id_type: indicates whether the ID is internal or an external ID provided by the user
        :return: the response object

        Example:

        >>> response = ts.delete_report("4d1fcaee-5009-4620-b239-2b22c3992b80")
        """

        params = {'idType': id_type}
        self._client.delete("reports/%s" % report_id, params=params)

    def copy_report(self, src_report_id, dest_enclave_id, from_provided_submission=False, report=None, tags=None):
        """
        Copy a report to another enclave.  All properties of the report, including tags, will be copied.
        A reference to the original report will still be stored on the child, allowing the system to track the
        relationship between the original report and copies made from it.

        If the ``from_provided_submission`` parameter is ``True``, then edits can be applied to the copied report.  This
        is useful in cases where the body or title must be redacted first, or the list of tags needs to be altered for
        the copy.  In this case, a |Report| object and a list of tag names must be provided, which will fill out the
        copied report.  A reference to the original report will still be stored on the copy.
        **NOTE:** Partial edits are not allowed.  ALL fields must be filled out on this object, and the
        fields from the original report will completely ignored.

        :param str src_report_id: the ID of the report to copy
        :param str dest_enclave_id: the ID of the enclave to copy the report to
        :param boolean from_provided_submission: whether to apply edits from a supplied report object and list of tags
        :param Report report: (required if ``from_provided_submission`` is ``True``) a report object containing an edited version to use as the copy.
            This allows information to be redacted, or other arbitrary edits to be made to the copied version.
            **NOTE:** Partial edits are not allowed.  ALL fields must be filled out on this object, and the fields from
            the original report will completely ignored.
        :param list(str) tags: (required if ``from_provided_submission`` is ``True``) a list of tags to use if ``from_provided_submission`` is ``True``.
            **NOTE:** if ``from_provided_submission`` is True, the tags from the source report will be completely
            ignored, and this list of tags will be used instead.  MUST be provided if ``from_provided_submission`` is ``True``.
        :return: the ID of the newly-created copy
        """

        params = {
            'destEnclaveId': dest_enclave_id,
            'copyFromProvidedSubmission': from_provided_submission
        }

        # determine if edits are being made to the copy
        if from_provided_submission:
            # ensure an edited version of the report has been provided
            if not report:
                raise Exception("Cannot copy from provided submission without providing a report object")
            # ensure an edited list of tags has been provided
            if not tags:
                raise Exception("Cannot copy from provided submission without providing a list of tags")

            # form the JSON dictionary of the report
            body = report.to_dict()
            # add the list of tags to the JSON
            # NOTE: this field on the report object cannot be used in other endpoints on this API version
            body['tags'] = tags
        else:
            body = None

        response = self._client.post('reports/copy/{id}'.format(id=src_report_id), params=params, data=json.dumps(body))
        return response.json().get('id')

    def move_report(self, report_id, dest_enclave_id):
        """
        Move a report from one enclave to another.

        **NOTE:** All tags will be moved, as well.

        :param report_id: the ID of the report to move
        :param dest_enclave_id: the ID of the enclave to move the report to
        :return: the ID of the report
        """

        params = {
            'destEnclaveId': dest_enclave_id
        }

        response = self._client.post('reports/move/{id}'.format(id=report_id), params=params)
        return response.json().get('id')

    def get_correlated_report_ids(self, indicators):
        """
        DEPRECATED!
        Retrieves a list of the IDs of all TruSTAR reports that contain the searched indicators.

        :param indicators: A list of indicator values to retrieve correlated reports for.
        :return: The list of IDs of reports that correlated.

        Example:

        >>> report_ids = ts.get_correlated_report_ids(["wannacry", "www.evil.com"])
        >>> print(report_ids)
        ["e3bc6921-e2c8-42eb-829e-eea8da2d3f36", "4d04804f-ff82-4a0b-8586-c42aef2f6f73"]
        """

        params = {'indicators': indicators}
        resp = self._client.get("reports/correlate", params=params)
        return resp.json()

    def get_correlated_reports_page(self, indicators, enclave_ids=None, is_enclave=True,
                                    page_size=None, page_number=None):
        """
        Retrieves a page of all TruSTAR reports that contain the searched indicators.

        :param indicators: A list of indicator values to retrieve correlated reports for.
        :param enclave_ids: The enclaves to search in.
        :param is_enclave: Whether to search enclave reports or community reports.
        :param int page_number: the page number to get.
        :param int page_size: the size of the page to be returned.
        :return: The list of IDs of reports that correlated.

        Example:

        >>> reports = ts.get_correlated_reports_page(["wannacry", "www.evil.com"]).items
        >>> print([report.id for report in reports])
        ["e3bc6921-e2c8-42eb-829e-eea8da2d3f36", "4d04804f-ff82-4a0b-8586-c42aef2f6f73"]
        """

        if is_enclave:
            distribution_type = DistributionType.ENCLAVE
        else:
            distribution_type = DistributionType.COMMUNITY

        params = {
            'indicators': indicators,
            'enclaveIds': enclave_ids,
            'distributionType': distribution_type,
            'pageNumber': page_number,
            'pageSize': page_size
        }
        resp = self._client.get("reports/correlated", params=params)

        return NumberedPage.from_dict(resp.json(), content_type=Report)

    def search_reports_page(self, search_term=None,
                            enclave_ids=None,
                            from_time=None,
                            to_time=None,
                            tags=None,
                            excluded_tags=None,
                            page_size=None,
                            page_number=None):
        """
        Search for reports containing a search term.

        :param str search_term: The term to search for.  If empty, no search term will be applied.  Otherwise, must
            be at least 3 characters.
        :param list(str) enclave_ids: list of enclave ids used to restrict reports to specific enclaves (optional - by
            default reports from all of user's enclaves are returned)
        :param int from_time: start of time window in milliseconds since epoch (optional)
        :param int to_time: end of time window in milliseconds since epoch (optional)
        :param list(str) tags: Name (or list of names) of tag(s) to filter reports by.  Only reports containing
            ALL of these tags will be returned. (optional)
        :param list(str) excluded_tags: Reports containing ANY of these tags will be excluded from the results.
        :param int page_number: the page number to get. (optional)
        :param int page_size: the size of the page to be returned.
        :return: a |NumberedPage| of |Report| objects.  *NOTE*:  The bodies of these reports will be ``None``.
        """

        body = {
            'searchTerm': search_term
        }

        params = {
            'enclaveIds': enclave_ids,
            'from': from_time,
            'to': to_time,
            'tags': tags,
            'excludedTags': excluded_tags,
            'pageSize': page_size,
            'pageNumber': page_number
        }

        resp = self._client.post("reports/search", params=params, data=json.dumps(body))
        page = NumberedPage.from_dict(resp.json(), content_type=Report)

        return page

    def _get_reports_page_generator(self, is_enclave=None, enclave_ids=None, tag=None, excluded_tags=None,
                                    from_time=None, to_time=None):
        """
        Creates a generator from the |get_reports_page| method that returns each successive page.

        :param boolean is_enclave: restrict reports to specific distribution type (optional - by default all accessible
            reports are returned).
        :param list(str) enclave_ids: list of enclave ids used to restrict reports to specific
            enclaves (optional - by default reports from all enclaves are returned)
        :param str tag: name of tag to filter reports by.  if a tag with this name exists in more than one enclave
            indicated in ``enclave_ids``, the request will fail.  handle this by making separate requests for each
            enclave ID if necessary.
        :param int from_time: start of time window in milliseconds since epoch
        :param int to_time: end of time window in milliseconds since epoch (optional, defaults to current time)
        :return: The generator.
        """

        def get_next_to_time(result, to_time):
            """
            For each page, get the timestamp of the earliest report in the result set.  The next query will use this
            timestamp as the end of its interval.  This endpoint limits queries to 1 day.  If the result set is
            empty, subtract 1 day from the to_time for the next interval.

            :param result: the result set of the previous call
            :param to_time: the to_time of the previous call
            :return: the next to_time
            """

            if len(result.items) > 0:
                return result.items[-1].updated - 1
            else:
                return to_time - DAY

        get_page = functools.partial(self.get_reports_page, is_enclave, enclave_ids, tag, excluded_tags)
        return get_time_based_page_generator(
            get_page=get_page,
            get_next_to_time=get_next_to_time,
            from_time=from_time,
            to_time=to_time
        )

    def get_reports(self, is_enclave=None, enclave_ids=None, tag=None, excluded_tags=None, from_time=None, to_time=None):
        """
        Uses the |get_reports_page| method to create a generator that returns each successive report as a trustar
        report object.

        :param boolean is_enclave: restrict reports to specific distribution type (optional - by default all accessible
            reports are returned).
        :param list(str) enclave_ids: list of enclave ids used to restrict reports to specific
            enclaves (optional - by default reports from all enclaves are returned)
        :param list(str) tag: a list of tags; only reports containing ALL of these tags will be returned. 
            If a tag with this name exists in more than one enclave in the list passed as the ``enclave_ids``
            argument, the request will fail.  Handle this by making separate requests for each
            enclave ID if necessary.
        :param list(str) excluded_tags: a list of tags; reports containing ANY of these tags will not be returned. 
        :param int from_time: start of time window in milliseconds since epoch (optional)
        :param int to_time: end of time window in milliseconds since epoch (optional)
        :return: A generator of Report objects.

        Note:  If a report contains all of the tags in the list passed as argument to the 'tag' parameter and also 
        contains any (1 or more) of the tags in the list passed as argument to the 'excluded_tags' parameter, that 
        report will not be returned by this function.  
        
        Example:

        >>> page = ts.get_reports(is_enclave=True, tag="malicious", from_time=1425695711000, to_time=1514185311000)
        >>> for report in reports: print(report.id)
        '661583cb-a6a7-4cbd-8a90-01578fa4da89'
        'da131660-2708-4c8a-926e-f91fb5dbbc62'
        '2e3400d6-fa37-4a8c-bc2f-155aaa02ae5a'
        '38064828-d3db-4fff-8ab8-e0e3b304ff44'
        'dbf26104-cee5-4ca4-bdbf-a01d0178c007'

        """

        return NumberedPage.get_generator(page_generator=self._get_reports_page_generator(is_enclave, enclave_ids, tag,
                                                                                  excluded_tags, from_time, to_time))

    def _get_correlated_reports_page_generator(self, indicators, enclave_ids=None, is_enclave=True,
                                               start_page=0, page_size=None):
        """
        Creates a generator from the |get_correlated_reports_page| method that returns each
        successive page.

        :param indicators: A list of indicator values to retrieve correlated reports for.
        :param enclave_ids:
        :param is_enclave:
        :return: The generator.
        """

        get_page = functools.partial(self.get_correlated_reports_page, indicators, enclave_ids, is_enclave)
        return NumberedPage.get_page_generator(get_page, start_page, page_size)

    def get_correlated_reports(self, indicators, enclave_ids=None, is_enclave=True):
        """
        Uses the |get_correlated_reports_page| method to create a generator that returns each successive report.

        :param indicators: A list of indicator values to retrieve correlated reports for.
        :param enclave_ids: The enclaves to search in.
        :param is_enclave: Whether to search enclave reports or community reports.
        :return: The generator.
        """

        return NumberedPage.get_generator(page_generator=self._get_correlated_reports_page_generator(indicators,
                                                                                             enclave_ids,
                                                                                             is_enclave))

    def _search_reports_page_generator(self, search_term=None,
                                       enclave_ids=None,
                                       from_time=None,
                                       to_time=None,
                                       tags=None,
                                       excluded_tags=None,
                                       start_page=0,
                                       page_size=None):
        """
        Creates a generator from the |search_reports_page| method that returns each successive page.

        :param str search_term: The term to search for.  If empty, no search term will be applied.  Otherwise, must
            be at least 3 characters.
        :param list(str) enclave_ids: list of enclave ids used to restrict reports to specific enclaves (optional - by
            default reports from all of user's enclaves are returned)
        :param int from_time: start of time window in milliseconds since epoch (optional)
        :param int to_time: end of time window in milliseconds since epoch (optional)
        :param list(str) tags: Name (or list of names) of tag(s) to filter reports by.  Only reports containing
            ALL of these tags will be returned. (optional)
        :param list(str) excluded_tags: Reports containing ANY of these tags will be excluded from the results.
        :param int start_page: The page to start on.
        :param page_size: The size of each page.
        :return: The generator.
        """

        get_page = functools.partial(self.search_reports_page, search_term, enclave_ids, from_time, to_time, tags,
                                     excluded_tags)
        return NumberedPage.get_page_generator(get_page, start_page, page_size)

    def search_reports(self, search_term=None,
                       enclave_ids=None,
                       from_time=None,
                       to_time=None,
                       tags=None,
                       excluded_tags=None):
        """
        Uses the |search_reports_page| method to create a generator that returns each successive report.

        :param str search_term: The term to search for.  If empty, no search term will be applied.  Otherwise, must
            be at least 3 characters.
        :param list(str) enclave_ids: list of enclave ids used to restrict reports to specific enclaves (optional - by
            default reports from all of user's enclaves are returned)
        :param int from_time: start of time window in milliseconds since epoch (optional)
        :param int to_time: end of time window in milliseconds since epoch (optional)
        :param list(str) tags: Name (or list of names) of tag(s) to filter reports by.  Only reports containing
            ALL of these tags will be returned. (optional)
        :param list(str) excluded_tags: Reports containing ANY of these tags will be excluded from the results.
        :return: The generator of Report objects.  Note that the body attributes of these reports will be ``None``.
        """

        return NumberedPage.get_generator(page_generator=self._search_reports_page_generator(search_term, enclave_ids,
                                                                                     from_time, to_time, tags,
                                                                                     excluded_tags))

    def redact_report(self, title=None, report_body=None):
        """
        Redacts a report's title and body.

        :param str title: The title of the report to apply redaction to.
        :param str report_body: The body of the report to apply redaction to.
        :return: a |RedactedReport| object.
        """

        body = {
            'title': title,
            'reportBody': report_body
        }

        resp = self._client.post("redaction/report", data=json.dumps(body))

        return RedactedReport.from_dict(resp.json())
    
    def get_report_deeplink(self, report):
        """
        Retrieves the Station's report deeplink.

        :param report: A |Report| or a str object.
        :return: A report URL object.

        Example:

        >>> report = "fcda196b-eb30-4b59-83b8-a25ab6d70d17"
        >>> deeplink = ts.get_report_deeplink(report)
        >>> isinstance(report, str) or isinstance(report, Report)
        True
        >>> isinstance(deeplink, str)
        True
        >>> print(deeplink)
        """

        # default to interal ID if report ID field is present
        # else treat report as an ID string
        try:
            report_id = report.id
        except AttributeError:
            report_id = report
        deeplink = "{}/constellation/reports/{}".format(self._client.station, report_id)

        return deeplink

    def get_report_status(self, report):
        """
        Finds the processing status of a report.

        :param report: A |Report| or a str object.
        :return: A dict.

        Example result:
        
        {
            "id": "3f8824de-7858-4e07-b6d5-f02d020ee675",
            "status": "SUBMISSION_PROCESSING",
            "errorMessage": ""
        }

        The possible status values for a report are:
        * SUBMISSION_PROCESSING,
        * SUBMISSION_SUCCESS,
        * SUBMISSION_FAILURE,
        * UNKNOWN
        
        A report can have an UNKNOWN processing status if the report
        has not begun processing or if it is an older report
        that has not been recently updated.

        >>> report = "fcda196b-eb30-4b59-83b8-a25ab6d70d17"
        >>> result = ts.get_report_status(report)
        >>> result['status']
        "SUBMISSION_SUCCESS"
        """
        if isinstance(report, Report):
            lookup = report.id
        elif isinstance(report, string_types):
            lookup = report
        else:
            raise TypeError("report must be of type trustar.models.Report or str")

        response = self._client.get("reports/{id}/status".format(id=lookup))
        response.raise_for_status()
        result = response.json()
        return result
