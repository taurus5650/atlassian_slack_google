from datetime import datetime, timedelta
from json import JSONDecodeError

from flask import Blueprint, request

from database.table_database import TeamDatabase
from integration_tool import AtlassianJira, SlackBot, SlackBoltApp
from utility import logger, log_func, response_spec
from utility.constant import ResponseResult

slack_btn_smsj_route = Blueprint('slack_btn_smsj_route', __name__)
atlassian_jira = AtlassianJira()
slack_bot = SlackBot()
slack_app = SlackBoltApp()
slack_app.start()
team_db = TeamDatabase()


def _current_date_time():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())  # Monday
    friday = monday + timedelta(days=4)  # Friday
    iso_year, iso_week, _ = today.isocalendar()
    current_week = f"W{iso_week:02}" if iso_week < 10 else f"W{iso_week}"

    return monday, friday, current_week


def _format_slack_message():
    return {
        'title_mrkdwn_text': '*【 Sprint Ticket 】*',
        'button_mrkdwn_text': '_StoryPoint default 0.5。_',
        'button_text': 'Create Jira Task',
        'button_value': 'NA',
        'button_action_id': 'sprint_ticket'
    }


@log_func
@slack_btn_smsj_route.route('/sprint_ticket', methods=['POST'])
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

    slack_channel = request_data.get('slack_channel', [])

    try:
        response = slack_bot.chat_post_message(
            channels=slack_channel,
            message=_format_slack_message(),
            message_builder_method='single_button_block'
        )

        return response_spec(
            result=ResponseResult.SUCCESS.code,
            message=ResponseResult.SUCCESS.message,
            result_obj=str(response)
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


def _create_jira(slack_user_id: str):
    monday, friday, current_week = _current_date_time()

    atlassian_id = team_db.get_team_member_detail(
        slack_user_id=slack_user_id
    )['atlassian_id']

    summary = f"{current_week} ({monday.strftime('%m-%d')} ~ {friday.strftime('%m-%d')})"
    description = ("""
    Meetings:
    - Weekly
    - Standup meeting
    - PRD review
   """)
    sprint_id = atlassian_jira.get_new_sprint()['id']
    if not sprint_id:
        return None

    if atlassian_id:
        atlassian_jira.issue_create(
            project='PROJECT',
            ticket_type='Task',
            summary=summary,
            priority='P0',
            assignee=atlassian_id if atlassian_id is not None else None,
            labels=['labelsss'],
            story_point=0.5,
            description=description,
            sprint=sprint_id,
            parent_ticket=''
        )


@slack_app.action('sprint_ticket')
def _handle_btn(ack, body, logger):
    try:
        ack()
        logger.info(f"ACK: {body}")

        user_id = (
            body.get('user', {}).get('id') or
            body.get('user_id')
        )
        logger.info(f"User click btn: {user_id}")

        if user_id:
            slack_bot.chat_post_message(
                channels=[user_id],
                message=f"<@{user_id}> Create Ticket - sprint_ticket",
                message_builder_method='customize'
            )

        _create_jira(slack_user_id=user_id)

    except Exception as e:
        logger.error(f"Exception {e}", exc_info=True)
