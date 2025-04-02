from typing import Any, Dict, List

from atlassian import Jira

from configuration.account import AtlassianConnectionConfig
from utility import logger, log_func
from datetime import datetime, timedelta


class AtlassianJira:
    @staticmethod
    def _connection(username: str, password: str,
                    atlassian_domain: str = AtlassianConnectionConfig.ATLASSIAN_DOMAIN):
        return Jira(
            url=atlassian_domain,
            username=username,
            password=password,
            cloud=True
        )

    @log_func
    def query_by_jql(self, jql: Any, username: str = None, password: str = None) -> List[Dict[str, Any]]:
        """ Get ticket from JQL search result with all related fields. """
        jira_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        jql_result = jira_server.jql(jql)
        logger.info(f"JQL: {jql}")
        # logger.debug(f"JQL Result: {jql_result}")

        try:
            ticket_list = []
            for resp_id, ticket in enumerate(jql_result.get('issues', []), 1):
                ticket_dict = self._query_by_jql_resp(
                    resp_id=resp_id,
                    ticket=ticket
                )
                ticket_list.append(ticket_dict)

            return ticket_list
        except Exception as e:
            logger.error(f"Failed {str(e)}")
            raise

    @staticmethod
    def _query_by_jql_resp(ticket: Dict[str, Any], resp_id: int) -> Dict[str, Any]:
        """ Extract and format data from a single Jira ticket. """
        fields = ticket.get('fields', {})
        ticket_key = ticket.get('key', 'UNKNOWN')

        ticket_dict = {
            'RespId': resp_id,
            'Key': ticket_key,
            'URL': f"{AtlassianConnectionConfig.ATLASSIAN_DOMAIN}browse/{ticket_key}",
            'Summary': fields.get('summary'),
            'Status': fields.get('status', {}).get('name'),
            'Priority': fields.get('priority', {}).get('name'),
            'StoryPoint': fields.get('customfield_10039'),
            'Sprint': fields.get('customfield_10020'),
            'Assignee': None,
            'AssigneeEmail': None,
            'IssueValidator': None,
            'IssueValidatorEmail': None,
        }

        assignee = fields.get('assignee', {})
        if assignee:
            email = assignee.get('emailAddress', '')
            ticket_dict.update({
                'AssigneeEmail': email,
                'Assignee': email.split("@")[0] if email else ""
            })

        validator = fields.get('customfield_10088', {})
        if validator:
            email = validator.get('emailAddress', '')
            ticket_dict.update({
                'IssueValidatorEmail': email,
                'IssueValidator': email.split("@")[0] if email else ""
            })

        return ticket_dict

    def issue_create(
            self, summary: str, project: str = "JKO", ticket_type: str = "Task", labels: list = ['ags_jkos_rd'],
            priority: str = "P1", assignee: str = None, issue_validator: str = None, story_point: float = None,
            description: str = None, parent_ticket: str = None, sprint: str = None, username: str = None,
            password: str = None) -> Dict[str, Any]:
        """ Create Jira ticket """
        jira_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        fields = {
            'project': {'key': project},
            'issuetype': {'name': ticket_type},
            'summary': summary,
            'priority': {'name': priority},
            'labels': labels or [],
            'description': description or "",
        }

        if assignee:
            fields['assignee'] = {'accountId': assignee}  # ToDo: 只能用 AccountId, Email 無效

        if issue_validator:
            fields['customfield_10088'] = {'accountId': issue_validator}  # ToDo: 只能用 AccountId, Email 無效

        if parent_ticket:
            fields['parent'] = {'key': parent_ticket}

        if story_point:
            fields['customfield_10039'] = story_point

        if sprint:
            fields['customfield_10020'] = sprint

        logger.info(f"Fields: {fields}")

        try:
            create_response = jira_server.issue_create(fields=fields)
            logger.info(f"CreateTicket: {create_response}")
            return create_response
        except Exception as e:
            logger.error(f"Failed to create ticket: {str(e)}")
            raise

    @staticmethod
    def _get_current_sprint(sprints: Any):
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)

        for sprint in sprints['values']:
            if sprint['name'].startswith('SDET'):
                if 'startDate' in sprint:
                    sprint_start = datetime.strptime(sprint['startDate'], '%Y-%m-%dT%H:%M:%S.%fZ')

                    if week_start <= sprint_start <= week_end:
                        return sprint

        return None

    def get_new_sprint(self, board_id: int = 76, limit: int = 50, username: str = None, password: str = None):
        """ Get new sprint value. """
        jira_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        try:
            total_sprints = jira_server.get_all_sprints_from_board(
                board_id=board_id,
                start=0,
                limit=limit
            )['total']

            start = total_sprints - limit

            new_sprints = jira_server.get_all_sprints_from_board(
                board_id=board_id,
                start=start,
                limit=limit
            )

            new_sprint = self._get_current_sprint(sprints=new_sprints)
            # logger.info(f"New sprint: {new_sprint}")
            return new_sprint

        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            raise
