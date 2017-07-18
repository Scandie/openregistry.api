# -*- coding: utf-8 -*-
"""Main entry point
"""
if 'test' not in __import__('sys').argv[0]: # pragma: no cover
    import gevent.monkey
    gevent.monkey.patch_all()
import os
from logging import getLogger
from pkg_resources import iter_entry_points
from libnacl.sign import Signer, Verifier
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON, JSONP
from pyramid.settings import asbool

from openregistry.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openregistry.api.database import set_api_security
from openregistry.api.utils import forbidden, request_params
from openregistry.api.constants import ROUTE_PREFIX

LOGGER = getLogger("{}.init".format(__name__))


def main(global_config, **settings):
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(settings['auth.file'], __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=ROUTE_PREFIX,
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_request_method(check_accreditation)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))

    # search for plugins
    plugins = settings.get('plugins') and settings['plugins'].split(',')
    for entry_point in iter_entry_points('openregistry.api.plugins'):
        if not plugins or entry_point.name in plugins:
            plugin = entry_point.load()
            plugin(config)

    # CouchDB connection
    aserver, server, db = set_api_security(settings)
    config.registry.couchdb_server = server
    if aserver:
        config.registry.admin_couchdb_server = aserver
    config.registry.db = db

    # Document Service key
    config.registry.docservice_url = settings.get('docservice_url')
    config.registry.docservice_username = settings.get('docservice_username')
    config.registry.docservice_password = settings.get('docservice_password')
    config.registry.docservice_upload_url = settings.get('docservice_upload_url')
    config.registry.docservice_key = dockey = Signer(settings.get('dockey', '').decode('hex'))
    config.registry.keyring = keyring = {}
    dockeys = settings.get('dockeys') if 'dockeys' in settings else dockey.hex_vk()
    for key in dockeys.split('\0'):
        keyring[key[:8]] = Verifier(key)

    # migrate data
    if not os.environ.get('MIGRATION_SKIP'):
        for entry_point in iter_entry_points('openregistry.api.migrations'):
            plugin = entry_point.load()
            plugin(config.registry)

    config.registry.server_id = settings.get('id', '')

    # search subscribers
    subscribers_keys = [k for k in settings if k.startswith('subscribers.')]
    for k in subscribers_keys:
        subscribers = settings[k].split(',')
        for subscriber in subscribers:
            for entry_point in iter_entry_points('openregistry.{}'.format(k), subscriber):
                if entry_point:
                    plugin = entry_point.load()
                    plugin(config)

    config.registry.health_threshold = float(settings.get('health_threshold', 512))
    config.registry.health_threshold_func = settings.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(settings.get('update_after', True))
    return config.make_wsgi_app()
