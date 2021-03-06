import csv
import logging
import sys
import pdb
import traceback
import tempfile
from datetime import datetime

from nectar_reporting.nova import client as nova_client
from nectar_reporting.keystone import client as keystone_client
from nectar_reporting.ceilometer import client as ceilometer_client
from nectar_reporting import config
from nectar_reporting.common import with_retries
from nectar_reporting import mail

LOG = logging.getLogger(__name__)


def parse_date(date_string):
    if date_string.endswith('Z'):
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")


def seconds_to_days(seconds):
    return seconds/60/60/24


def list_servers(limit=None, **kwargs):
    client = nova_client()
    servers = []
    marker = None
    opts = {"all_tenants": True}
    if limit:
        opts['limit'] = limit
    opts.update(kwargs)

    while True:
        if marker:
            opts["marker"] = marker

        try:
            result = client.servers.list(search_opts=opts)
        except Exception as exception:
            LOG.exception(exception)
            sys.exit(1)

        if not result:
            break

        servers.extend(result)

        # Quit if we have got enough servers.
        if limit and len(servers) >= int(limit):
            break

        marker = servers[-1].id
    return servers


def filter_flavors(flavors, names):
    for flavor in flavors:
        if flavor.name in names:
            yield flavor


def list_flavors():
    n_client = nova_client()
    return n_client.flavors.list()


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


def filtered_servers(parser, target_flavors, limit=None):
    flavors = list_flavors()
    if not list(filter_flavors(flavors, target_flavors)):
        parser.error("Can't find any flavors matching, %s in %s"
                     % (target_flavors, [f.name for f in flavors]))
    servers = []
    for flavor in filter_flavors(flavors, target_flavors):
        servers.extend(list_servers(limit=limit, flavor=flavor.id))
    if limit:
        return servers[:limit]
    else:
        return servers


def report(servers, file=None):
    if not file:
        file = tempfile.TemporaryFile()
    csv_file = csv.writer(file)
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
    file.seek(0)
    return file


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
        '--email', action='store_true', default=False,
        help="Email the report on completion.")
    parser.add_argument(
        '--limit',  default=None, type=int,
        help="The number of servers to report on.")
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
        servers = filtered_servers(parser, args.flavor, limit=args.limit)
        file = report(servers)
        if args.email:
            mail.send("Idle Servers Report",
                      "Attached is the idle servers report.",
                      filename="idle_servers",
                      csv_file=file)
        else:
            print file.read()
    except:
        if args.pdb:
            type, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
        else:
            raise
