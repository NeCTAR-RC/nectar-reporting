import csv
import logging
import sys
import pdb
import traceback
from datetime import datetime

from nectar_reporting.nova import client as nova_client
from nectar_reporting.keystone import client as keystone_client
from nectar_reporting.ceilometer import client as ceilometer_client
from nectar_reporting import config
from nectar_reporting.common import with_retries

log = logging.getLogger(__file__)


def parse_date(date_string):
    if date_string.endswith('Z'):
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")


def seconds_to_days(seconds):
    return seconds/60/60/24


def list_servers(flavor):
    n_client = nova_client()
    servers = n_client.servers.list(search_opts={'all_tenants': 1,
                                                 'flavor': flavor.id})
    return servers


def list_flavors(names):
    n_client = nova_client()
    for flavor in n_client.flavors.list():
        if flavor.name in names:
            yield flavor


def server_owner(server):
    k_client = keystone_client()
    tenant = k_client.tenants.get(server.tenant_id).to_dict()
    user = k_client.users.get(server.user_id).to_dict()
    return {'user_id': user['id'],
            'user_email': user.get('email', ''),
            'tenant_id': tenant['id'],
            'tenant_name': tenant.get('name', '')}


def server_metrics(server):
    c_client = ceilometer_client()
    query = [dict(field='resource_id', op='eq', value=server.id)]
    stats = c_client.statistics.list('cpu_util', query)
    return stats[0].to_dict() if len(stats) > 0 else {}


def report(parser, target_flavors):
    flavors = list(list_flavors(target_flavors))
    if not flavors:
        parser.error("Can't find any flavors matching, %s" % target_flavors)
    servers = list_servers(flavors[0])
    csv_file = csv.writer(sys.stdout)
    csv_file.writerow(['Server UUID',
                       'Tenant UUID',
                       'Email',
                       'Tenant Name',
                       'Cell',
                       'Server Age (Days)',
                       'Ceilometer Data (Days)',
                       'Utilisation Average',
                       'Utilisation Max',
                       'Utilisation Min'])
    for server_object in servers:
        server = server_object.to_dict()
        owner = server_owner(server_object)
        stats = with_retries(server_metrics, server_object)
        zone = server['OS-EXT-AZ:availability_zone']
        launch_date = server['created']
        age = (datetime.now() - parse_date(launch_date))
        age = seconds_to_days(age.total_seconds())
        duration = stats.get('duration', '')
        if duration:
            duration = seconds_to_days(duration)

        row = [server['id'],
               owner['tenant_id'],
               owner['user_email'],
               owner['tenant_name'],
               zone,
               age,
               duration]

        ceilometer_data_age = stats.get('duration_end', '')
        if ceilometer_data_age:
            ceilometer_data_age = (datetime.now()
                                   - parse_date(ceilometer_data_age))
            # Check that the data is fresh
            if ceilometer_data_age.days == 0:
                row.extend([stats.get('avg', ''),
                            stats.get('max', ''),
                            stats.get('min', '')])
        csv_file.writerow(row)
        sys.stdout.flush()


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help="Increase verbosity (specify multiple times for more)")
    parser.add_argument(
        '-f', '--flavor', action='append', default=[],
        help="The flavors to report on.")
    parser.add_argument(
        '--pdb', action='store_true', default=False,
        help="Unable PDB on error.")
    parser.add_argument(
        '--config', default=config.CONFIG_FILE, type=str,
        help='Config file path.')
    args = parser.parse_args()
    config.read(args.config)

    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(name)s %(levelname)s %(message)s')

    try:
        report(parser, args.flavor)
    except:
        if args.pdb:
            type, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
        else:
            raise
