import json
from typing import Dict, Any, List


class MessageBuilderMethod:

    @staticmethod
    def customize(message: str) -> Dict[str, str]:
        """ Slack message design by anyone. """
        return {'text': message}

    @staticmethod
    def raw(message: Dict[str, Any]) -> Dict[str, Any]:
        """ Slack message in dict. """
        return message

    @staticmethod
    def api_req_resp_block(message: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """ Slack message display 2 blocks : 1. API request, 2. API response"""
        blocks = [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '*You have a new request:*'
                }
            }
        ]

        for key, value in message.items():
            if value is not None:
                formatted_value = json.dumps(value, indent=4, ensure_ascii=False)
                blocks.append(
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"*{key}:*\n```{formatted_value}```"
                        }
                    }
                )

        return {'blocks': blocks}

    @staticmethod
    def single_button_block(message: Dict[str, str]) -> Dict[str, Any]:
        """ Slack message display one button. (E.g. The btn can create ticket.). """
        return {
            'text': message['title_mrkdwn_text'],
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': message['title_mrkdwn_text']
                    }
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': message['button_mrkdwn_text']
                    },
                    'accessory': {
                        'type': 'button',
                        'style': message.get('button_style', 'primary'),
                        'text': {
                            'type': 'plain_text',
                            'text': message['button_text'],
                            'emoji': True
                        },
                        'value': message['button_value'],
                        'action_id': message['button_action_id'],
                    }
                }
            ]
        }