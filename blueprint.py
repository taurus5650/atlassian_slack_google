import importlib
import json

from utility import logger, log_func

_ROUTES_CONFIG = None


@log_func
def _load_routes_json():
    global _ROUTES_CONFIG

    if _ROUTES_CONFIG is not None:
        return _ROUTES_CONFIG

    try:
        with open('routes.json', 'r') as f:
            _ROUTES_CONFIG = json.load(f)
        return _ROUTES_CONFIG
    except FileNotFoundError:
        logger.error("routes.json file not found")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e}")
        return None
    except Exception as e:
        logger.error(f"Exception: {e}")
        return None


_module_cache = {}

def _import_module(module_path):
    """ Import module and cache it to avoid repeated imports. """
    if module_path in _module_cache:
        return _module_cache[module_path]

    try:
        module = importlib.import_module(module_path)
        _module_cache[module_path] = module
        # logger.info(f"Module {module_path} successfully imported.")
        return module
    except ImportError as e:
        logger.error(f"ImportError: {module_path} import error: {e}")
        return None


@log_func
def register_blueprints(app):
    config = _load_routes_json()

    if not config:
        logger.error("Failed to load configuration. Exiting blueprint registration.")
        return

    registered_blueprints = set()

    for feature in config:
        feature_path = feature.get('feature_path')
        url_prefix = feature.get('url_prefix')
        routes_data = feature.get('routes', [])

        if not feature_path or not url_prefix:
            logger.error(f"Feature path or url_prefix not defined for feature: {feature}")
            continue

        # logger.info(f"Registering blueprints for feature: {feature_path} with URL prefix: {url_prefix}")

        for route in routes_data:
            module_name = route.get('module')  # e.g. 'slack_mention.py'
            blueprint_name = route.get('name')  # e.g. 'abc_route'

            if not module_name or not blueprint_name:
                logger.error(f"Invalid route configuration: {route}")
                continue

            # Build full module path and create uniqueness key for blueprint
            module_path = f"{feature_path}.{module_name}".replace('/', '.')
            blueprint_key = f"{module_path}:{blueprint_name}"

            if blueprint_key in registered_blueprints:
                logger.info(f"Blueprint {blueprint_key} already registered, skipping.")
                continue

            # Import module
            module = _import_module(module_path)
            if not module:
                continue

            # Get blueprint
            blueprint = getattr(module, blueprint_name, None)
            if blueprint is None:
                logger.error(f"Blueprint {blueprint_name} not found in {module_path}.")
                continue

            # Register blueprint
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            registered_blueprints.add(blueprint_key)
            # logger.info(f"Blueprint {blueprint_name} registered with prefix {url_prefix}.")