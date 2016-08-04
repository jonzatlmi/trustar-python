import ConfigParser
import json
import requests
import requests.auth
import sys


class TruStar:
    """
    Main class you to instantiate the TruStar API
    """

    def __init__(self, config_file="trustar.conf", config_role="trustar"):

        config_parser = ConfigParser.RawConfigParser()
        config_parser.read(config_file)

        try:
            self.auth = config_parser.get(config_role, 'auth_endpoint')
            self.base = config_parser.get(config_role, 'api_endpoint')
            self.apikey = config_parser.get(config_role, 'user_api_key')
            self.apisecret = config_parser.get(config_role, 'user_api_secret')
            self.enclaveId = config_parser.get(config_role, 'enclave_id')
        except:
            print "Problem reading config file"
            sys.exit(1)

    def get_token(self):
        """
        Retrieves the OAUTH token generated by your API key and API secret.
        this function has to be called before any API calls can be made
        """
        client_auth = requests.auth.HTTPBasicAuth(self.apikey, self.apisecret)
        post_data = {"grant_type": "client_credentials"}
        resp = requests.post(self.auth, auth=client_auth, data=post_data)
        token_json = resp.json()
        return token_json["access_token"]

    def get_latest_reports(self, access_token):
        """
        Retrieves the latest 10 reports submitted to the TruSTAR community
        """

        headers = {"Authorization": "Bearer " + access_token}
        resp = requests.get(self.base + "/reports/latest", headers=headers)
        return json.loads(resp.content)

    def get_correlated_reports(self, access_token, indicator):
        """
        Retrieves all TruSTAR reports that contain the searched indicator. You can specify multiple indicators
        separated by commas
        """

        headers = {"Authorization": "Bearer " + access_token}
        payload = {'q': indicator}
        resp = requests.get(self.base + "/reports/correlate", payload, headers=headers)
        return json.loads(resp.content)

    def query_indicator(self, access_token, indicator, limit):
        """
        Finds all reports that contain the indicators and returns correlated indicators from those reports.
        you can specify the limit of indicators returned.
        """

        headers = {"Authorization": "Bearer " + access_token}
        payload = {'q': indicator, 'limit': limit}
        resp = requests.get(self.base + "/indicators", payload, headers=headers)
        return json.loads(resp.content)

    def submit_report(self, access_token, report_body_txt, report_name, enclave=False):
        """
        Wraps supplied text as a JSON-formatted TruSTAR Incident Report and submits it to TruSTAR Station
        By default, this submits to the TruSTAR community. To submit to your enclave, pass in your enclave_id
        """

        distribution_type = 'ENCLAVE' if enclave else 'COMMUNITY'
        headers = {'Authorization': 'Bearer ' + access_token, 'content-Type': 'application/json'}

        payload = {'incidentReport': {
            'title': report_name,
            'reportBody': report_body_txt,
            'distributionType': distribution_type},
            'enclaveId': self.enclaveId}

        print "Submitting report %s to TruSTAR Station..." % report_name
        resp = requests.post(self.base + "/reports/submit", json.dumps(payload), headers=headers, timeout=60)
        return resp.json()

    def process_file(self, file):
        print "Extracting text from file %s" % file
        try:
            txt = open(file, 'r')
            return txt.read()
        except:
            print "Failed to extract text from file %s " % file
