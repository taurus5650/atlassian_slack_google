from json import JSONDecodeError

from flask import Blueprint, request

from integration_tool import AtlassianJira, SlackBot
from utility import logger, response_spec
from utility.constant import ResponseResult

demo_qjts_route = Blueprint('demo_qjts_route', __name__)
atlassian_jira = AtlassianJira()
slack_bot = SlackBot()


def _extract_jira_data(jql: str):
    return atlassian_jira.query_by_jql(jql=jql)


def _format_slack_ticket_message(ticket_result: dict) -> str:
    if not ticket_result:
        return "No tickets found."

    ticket_entries = []
    for ticket in ticket_result:
        assignee = f"<@{ticket.get('Assignee', '')}>" if ticket.get('Assignee') else ""
        issue_validator = f"<@{ticket.get('IssueValidator', '')}>" if ticket.get('IssueValidator') else ""

        ticket_entry = (
            f"▶   *{ticket.get('Summary', '')}*\n"
            f"    ○   {ticket.get('URL', '')}\n"
            f"    ○   Assignee: {assignee}\n"
            f"    ○   IssueValidator: {issue_validator}\n\n"
            f"    ○   Status: `{ticket.get('Status', '')}`\n"
            f"    ○   StoryPoint: {ticket.get('StoryPoint', '')}"
        )
        ticket_entries.append(ticket_entry)

    return "\n\n".join(ticket_entries)


@demo_qjts_route.route('/query_jira_to_slack', methods=['POST'])
def index():
    try:
        request_data = request.get_json(silent=True) or {}
    except Exception as e:
        logger.error(f"Failed to parse request JSON: {e}")
        return response_spec(
            result=ResponseResult.JSON_DECODE_ERROR.code,
            message=ResponseResult.JSON_DECODE_ERROR.message,
            result_obj=f"Error parsing request JSON: {e}"
        )

    jql = request_data.get('jql')
    slack_channel = request_data.get('slack_channel')

    if not jql:
        return response_spec(
            result=ResponseResult.INVALID_PARAMETER.code,
            message="Missing JQL parameter",
            result_obj="JQL parameter is required"
        )

    try:
        ticket_result = _extract_jira_data(jql=jql)

        if slack_channel:
            try:
                ticket_slack_msg = _format_slack_ticket_message(ticket_result=ticket_result)
                slack_bot.chat_post_message(
                    channels=slack_channel,
                    message=ticket_slack_msg,
                    message_builder_method="customize"
                )
                logger.info(f"Sent to Slack Channel: {slack_channel}")
            except Exception as slack_error:
                logger.error(f"Failed to send message to Slack: {slack_error}")

        return response_spec(
            result=ResponseResult.SUCCESS.code,
            message=ResponseResult.SUCCESS.message,
            result_obj=ticket_result
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
