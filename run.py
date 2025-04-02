import json
import os
import secrets
import socket
import subprocess
from http import HTTPStatus

from flask import Flask, g, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

import blueprint
from configuration.base import Config, DevelopmentConfig, FlaskSecretKey
from utility import logger, log_func, set_correlation_id, response_spec, log_response_spec
from utility.constant import ResponseResult

app = Flask(__name__, template_folder="./template")
blueprint.register_blueprints(app)


@app.before_request
def _set_request_correlation_id():
    correlation_id = request.headers.get('X-Correlation-ID') or set_correlation_id()
    g.correlation_id = correlation_id
    logger.uuid_var.set(correlation_id)


@app.after_request
def _add_correlation_id_to_response(response):
    if hasattr(g, 'correlation_id'):
        response.headers['X-Correlation-ID'] = g.correlation_id
    return response


@log_func
def _log_response_info(response: Response):
    if request.is_json:
        request_body = json.dumps(request.get_json(), indent=4, ensure_ascii=False)
    elif request.data:
        request_body = request.data.decode('utf-8')
    else:
        request_body = "None"

    try:
        if response.is_json:
            response_body = json.dumps(response.get_json(), indent=4, ensure_ascii=False)
        else:
            response_body = response.get_data(as_text=True)
    except (TypeError, json.JSONDecodeError):
        response_body = response.get_data(as_text=True)

    logger.info(log_response_spec(
        request=request,
        request_body=request_body,
        response=response,
        response_body=response_body
    ))

    return response


def _configure_app():
    env = os.environ.get('FLASK_ENV', 'development')
    env_mapping = {
        'production': Config,
        'development': DevelopmentConfig,
    }
    app.config.from_object(env_mapping.get(env, DevelopmentConfig))
    app.secret_key = secrets.token_hex(16)
    app.json.sort_keys = False # Resp would not sort by alphabet.


def _setup_middleware():
    app.wsgi_app = DispatcherMiddleware(
        Response(response='Not Found', status=HTTPStatus.NOT_FOUND.value),
        {'/api': app.wsgi_app}
    )
    app.after_request(_log_response_info)


def _get_git_commit_id():
    try:
        # Add timeout to prevent hanging
        commit_id = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.STDOUT,
            timeout=3  # 3 seconds timeout
        ).strip().decode('utf-8')
        return commit_id
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        error_msg = getattr(e, 'output', str(e))
        if hasattr(error_msg, 'decode'):
            error_msg = error_msg.decode('utf-8')
        logger.error(f"Failed to get Git commit ID: {error_msg}")
        return "unknown"


@app.route('/')
def index():
    resp_msg = {
        'title': 'SDET Atlassian-Google-Slack Integration Hub',
        'message': 'Welcome & Happy Testing :)',
        'git_commit_id': _get_git_commit_id(),
    }

    return response_spec(
        result=ResponseResult.SUCCESS.code,
        message=ResponseResult.SUCCESS.message,
        result_obj=resp_msg
    )


_configure_app()
_setup_middleware()

if __name__ == '__main__':
    host = "0.0.0.0"
    port = app.config['PORT']
    app_path = "/api"
    debug_mode = app.config['DEBUG']

    try:
        container_ip = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        container_ip = "127.0.0.1"

    print(f" * AGS URL: http://{container_ip}:{port}{app_path}")

    app.run(
        host=host,
        port=port,
        debug=debug_mode
    )
