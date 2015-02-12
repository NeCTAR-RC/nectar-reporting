import logging

from novaclient.v1_1 import client as nova_client

from nectar_reporting.config import CONFIG

logger = logging.getLogger(__name__)


def client():
    username = CONFIG.get('openstack', 'user')
    password = CONFIG.get('openstack', 'passwd')
    tenant_name = CONFIG.get('openstack', 'name')
    url = CONFIG.get('openstack', 'url')
    assert username, 'No username in configuration file.'
    assert password, 'No password in configuration file.'
    assert tenant_name, 'No Tenant Name in configuration file.'
    assert url, 'No URL in configuration file.'
    conn = nova_client.Client(username=username, api_key=password,
                              project_id=tenant_name, auth_url=url)
    return conn
