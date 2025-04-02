import json
import textwrap
import time
from datetime import datetime
from typing import Any, Tuple, Union

from flask import g, jsonify


def response_spec(result: str, message: str, result_obj: Union[dict, str]) -> Tuple[Any, int]:
    """
    Generate a standardized API response.

    Args:
        result: Result code
        message: Result message
        result_obj: Result data object
        spec_type: Response type specification

    Returns:
        Tuple of (jsonified response, status code)
    """
    response_data = {
        'Result': result,
        'Message': message,
        'ResultObject': result_obj
    }

    return jsonify(response_data), 200


def log_response_spec(request: Any, request_body: Any, response: Any, response_body: Any
                      ) -> str:
    """
    Generate a standardized log message for request/response cycle.

    Args:
        request: Flask request object
        request_body: Request body content
        response: Flask response object
        response_body: Response body content

    Returns:
        Formatted log message string
    """
    current_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    start_time = getattr(g, 'request_start_time', None)
    elapsed_time = round(time.time() - start_time) if start_time else 0
    correlation_id = getattr(g, 'correlation_id', 'N/A')
    status = response.status if response else 'NA'
    try:
        headers_json = json.dumps(dict(request.headers), indent=4, ensure_ascii=False)
    except Exception:
        headers_json = "Could not serialize headers"

    log_message = textwrap.dedent(f"""
                ***
--------------------------------
🐞 debug prints
--------------------------------

 * datetime: {current_time}
 * request: [{request.method}] {request.url}
 * correlation-id: {correlation_id}
 * headers: {headers_json}
 * body: {request_body}
 * elapsed: {elapsed_time}s
 * status: {status}
 * response: {response_body if response else 'No response'}
--------------------------------
""").strip()

    return log_message
