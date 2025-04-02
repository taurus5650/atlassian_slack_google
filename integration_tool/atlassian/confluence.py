import json

from atlassian import Confluence

from configuration.account import AtlassianConnectionConfig
from utility import logger


class AtlassianConfluence:
    @staticmethod
    def _connection(username: str, password: str,
                    atlassian_domain: str = AtlassianConnectionConfig.ATLASSIAN_DOMAIN):
        return Confluence(
            url=atlassian_domain,
            username=username,
            password=password,
            cloud=True
        )

    def create_page(
            self, space: str, title: str, body: str, parent_id: int, create_type: str, representation: str, editor: str,
            full_width: bool, username: str = None, password: str = None):
        """ Create page from scratch """
        confluence_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        create_page = confluence_server.create_page(
            space=space,
            title=title,
            body=body,
            parent_id=parent_id,  # None
            type=create_type,  # 'page'
            representation=representation,  # 'storage'
            editor=editor,  # 'v2'
            full_width=full_width  # False
        )
        logger.info(f"Create page: {create_page}")
        return create_page

    def get_page_space(self, page_id: str, username: str = None, password: str = None):
        """ Get the space by page_id (Ex. SDET, 街口支付) """
        confluence_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        try:
            get_page_space = confluence_server.get_page_space(
                page_id=page_id
            )
            logger.info(f"Page space {get_page_space}")

            confluence_url = f"{AtlassianConnectionConfig.ATLASSIAN_DOMAIN}wiki/spaces/{get_page_space}/pages/{page_id}"
            logger.info(f"Confluence Url: {confluence_url}")

            return confluence_url, get_page_space
        except Exception as e:
            logger.error(f"Failed {str(e)}")
            raise

    def get_page_by_title(
            self, space: str, title: str, start: str = None, limit: str = None,
            username: str = None, password: str = None):
        """ Returns the list of labels on a piece of Content. """
        confluence_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        try:
            get_page_by_title = confluence_server.get_page_by_title(
                space=space,
                title=title,
                start=start,  # None
                limit=limit  # None
            )
            logger.info(f"PageTitle: {get_page_by_title}")
            return get_page_by_title
        except Exception as e:
            logger.error(f"Failed {str(e)}")
            raise

    def get_tables_from_page(self, page_id: str, username: str = None, password: str = None):
        """ Read table from Confluence page. """
        confluence_server = self._connection(
            username=username or AtlassianConnectionConfig.USER_NAME,
            password=password or AtlassianConnectionConfig.ATLASSIAN_API_TOKEN
        )

        try:
            tables = confluence_server.get_tables_from_page(
                page_id=page_id
            )
            # logger.info(f"TableResult: {tables}")
            return json.loads(tables)
        except Exception as e:
            logger.error(f"Exception: {e}")
            raise
