from keystoneclient.v2_0 import client as keystone_client

from nectar_reporting.config import CONFIG


def client():
    username = CONFIG.get('openstack', 'user')
    password = CONFIG.get('openstack', 'passwd')
    tenant_name = CONFIG.get('openstack', 'name')
    url = CONFIG.get('openstack', 'url')
    return keystone_client.Client(username=username,
                                  password=password,
                                  tenant_name=tenant_name,
                                  auth_url=url)
