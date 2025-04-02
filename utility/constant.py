from aenum import MultiValueEnum, unique


@unique
class ResponseResult(MultiValueEnum):
    _init_ = 'code message'
    SUCCESS = "AGS_000", "SUCCESS"
    REQUIRED_KEY_MISSING = "AGS_001", "REQUIRED_KEY_MISSING"

    UNEXPECTED_ERROR = "AGS_900", "UNEXPECTED_ERROR"
    HTTP_ERROR = "AGS_901", "HTTP_ERROR"
    JSON_DECODE_ERROR = "AGS_902", "JSON_DOCODE_ERROR"
    ATLASSIAN_API_ERROR = "AGS_903", "ATLASSIAN_ERROR"
    SLACK_API_ERROR = "AGS_904", "SLACK_ERROR"
