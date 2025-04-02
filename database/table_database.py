from configuration.account import DatabaseConfig
from utility import logger, log_class
from .database import Database


@log_class
class TeamDatabase(Database):

    def __init__(self):
        super().__init__(DatabaseConfig)

    def get_team_member_detail(
            self, member_id: int = None, team: str = None, name: str = None, slack_user_id: str = None,
            slack_group_id: str = None, atlassian_id: str = None, gmail: str = None, jkopay_mail: str = None,
            order_by: str = "id", desc: bool = True, fetchall: bool = False):
        condition = {
            'id': member_id,
            'team': team,
            'name': name,
            'slack_user_id': slack_user_id,
            'slack_group_id': slack_group_id,
            'atlassian_id': atlassian_id,
            'gmail': gmail,
            'jkopay_mail': jkopay_mail,
        }
        condition = self.remove_dict_empty_value(condition)
        sql = self.select(
            table="team_member_detail",
            fields="*",
            condition=condition,
            order_by=order_by,
            desc=desc
        )

        return self._connection.execute_select_sql(sql, condition, fetchall=fetchall)