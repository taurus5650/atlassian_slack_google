import os


class AtlassianConnectionConfig:
    USER_NAME = "ATLASSIAN_MAIL"
    ATLASSIAN_API_TOKEN = os.getenv('ATLASSIAN_API_TOKEN')
    ATLASSIAN_DOMAIN = "https://atlassian.net/"


class SlackBotConfig:
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
    SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')


class GoogleConnectionConfig:
    SERVICE_ACC = {
        "type": "service_account"
    }

class DatabaseConfig:
    driver = "mysql"
    host = "HOST"
    port = "3306"
    user = "USER"
    password = "PWD"
    database = "TABLE"

