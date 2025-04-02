from json import JSONDecodeError

from flask import Blueprint

from integration_tool import GoogleSheet
from utility import logger
from utility import response_spec
from utility.constant import ResponseResult

example_ggs_route = Blueprint('example_ggs_route', __name__)

google_sheet = GoogleSheet()

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/xxxxx/edit?usp=sharing"

@example_ggs_route.route('/get_google_sheet', methods=['GET'])
def index():
    try:
        worksheets = google_sheet.open_by_url(google_sheet_url=GOOGLE_SHEET_URL)

        for worksheet in worksheets:
            contents = worksheet.get_all_values()

            return response_spec(
                result=ResponseResult.SUCCESS.code,
                message=ResponseResult.SUCCESS.message,
                result_obj=contents
            )

    except JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e}")
        return response_spec(
            result=ResponseResult.JSON_DECODE_ERROR.code,
            message=ResponseResult.JSON_DECODE_ERROR.message,
            result_obj=f"Error: {e}"
        )
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return response_spec(
            result=ResponseResult.ATLASSIAN_API_ERROR.code,
            message=ResponseResult.ATLASSIAN_API_ERROR.message,
            result_obj=f"Error: {e}"
        )
