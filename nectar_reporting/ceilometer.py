import ceilometerclient.client

from nectar_reporting.config import CONFIG


def client():
    username = CONFIG.get('openstack', 'user')
    password = CONFIG.get('openstack', 'passwd')
    tenant_name = CONFIG.get('openstack', 'name')
    url = CONFIG.get('openstack', 'url')
    client = ceilometerclient.client.get_client(
        2,
        username=username,
        password=password,
        tenant_name=tenant_name,
        auth_url=url)
    return client
