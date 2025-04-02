import json

import pygsheets

from configuration.account import GoogleConnectionConfig
from utility import log_class


@log_class
class GoogleSheet:
    def __init__(self, service_account_json=None):
        if service_account_json is None:
            service_account_json = GoogleConnectionConfig.SDET_JKOPAY_GMAIL_SERVICE_ACC

        self.connection = self._establish_connection(service_account_json)

    def _establish_connection(self, service_account_json: dict):
        service_account_json = json.dumps(service_account_json)
        return pygsheets.authorize(service_account_json=service_account_json)

    def open_by_url(self, google_sheet_url: str):
        sheet = self.connection.open_by_url(google_sheet_url)
        worksheets = sheet.worksheets()
        return worksheets
