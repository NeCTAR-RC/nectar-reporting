import logging

from novaclient.v1_1 import client as nova_client

from nectar_reporting.config import CONFIG

if __name__ == '__main__':
    LOG_NAME = __file__
else:
    LOG_NAME = __name__

logger = logging.getLogger(LOG_NAME)


def client():
    username = CONFIG.get('openstack', 'user')
    password = CONFIG.get('openstack', 'passwd')
    tenant_name = CONFIG.get('openstack', 'name')
    url = CONFIG.get('openstack', 'url')
    conn = nova_client.Client(username=username, api_key=password,
                              project_id=tenant_name, auth_url=url)
    return conn
