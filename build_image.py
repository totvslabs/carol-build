from pycarol import Carol, Apps, Tasks, ApiKeyAuth
from pycarol.compute import Compute
import argparse, json, os
import logging
import time, sys
from datetime import datetime

# Logger
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - [%(levelname)s]: %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)

parser = argparse.ArgumentParser()
parser.add_argument('--gittoken')
parser.add_argument('--tenant')
parser.add_argument('--org')
parser.add_argument('--appname')
parser.add_argument('--connectorid')
parser.add_argument('--apikey')
parser.add_argument('--manifestpath')

args = parser.parse_args()


def create_build_jobs(login, manifest, app_name, git_token):
    app = Apps(login)
    r = app.edit_manifest(app_name=app_name, manifest=manifest)
    tasks = app.build_docker_git(git_token=git_token)
    return tasks


def run(args, tasks=None):
    """
    Build function

    Args:

        args: `argparse like` object.
            The object has to have the following parameters:
                    1. args.gittoken: The GITHUB_TOKEN secret
                    2. args.tenant: Carol app's tenant
                    3. args.appname: Carol app's organization
                    4. args.org: Carol app's name
                    5. args.apikey: Carol app's connector id
                    6. args.connectorid: Carol app's API key
                    7. args.manifestpath: Manifest.json file path.

            Carol app name. It will overwrite the app name used in Carol() initialization.
        tasks: `list` default `carolApp`
            Possible values `carolApp` or `carolConnect`
        Returns:
    """

    git_token = args.gittoken
    tenant = args.tenant
    app_name = args.appname
    organization = args.org
    api_key = args.apikey
    connector_id = args.connectorid
    manifest_path = args.manifestpath

    login = Carol(
        domain=tenant,
        app_name=app_name,
        organization=organization,
        auth=ApiKeyAuth(api_key),
        connector_id=connector_id
    )

    manifest_path = os.path.join(manifest_path, 'manifest.json')

    with open(manifest_path) as f:
        manifest = json.load(f)

    logger.debug(f'Manifest: {manifest}')

    filters = ['''labels."k8s-pod/kind"="build"''', f'''labels."k8s-pod/appName":"{app_name}"''']

    if tasks is None:
        tasks = create_build_jobs(login, manifest, app_name, git_token)
        tasks = [task['mdmId'] for task in tasks]
        utc_now = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        filters.append(f'''timestamp>="{utc_now}"''')

    carol_task = Tasks(login)
    c = Compute(login)
    r = c.get_app_logs(filters=filters, page_size=100)

    fail = False  # for exit code purpose
    while (all([carol_task.get_task(task).task_status in ['READY', 'RUNNING'] for task in tasks]) and len(tasks) > 0) \
            or len(r['logEntries']) > 0:

        r = c.get_app_logs(filters=filters, page_size=100)

        if r['logEntries']:
            for entry in r['logEntries']:
                logger.debug(entry['payload']['data'])
            utc_now = datetime.utcfromtimestamp(entry['timestamp'] / 1000.0).isoformat(timespec='milliseconds') + 'Z'
            filters = ['''labels."k8s-pod/kind"="build"''', f'''labels."k8s-pod/appName":"{app_name}"''',
                       f'''timestamp>="{utc_now}"''']

        time.sleep(5)  # avoid rate limit from Carol.

    for task_id in tasks:
        logs = carol_task.get_logs(task_id)
        for log in logs:
            logger.info(log['mdmLogMessage'])
        task_status = carol_task.get_task(task_id).task_status

        if task_status == 'COMPLETED':
            logger.info(f'Task {task_id} completed.')
        elif task_status in ['FAILED']:
            logger.error(f'Something went wrong while building your docker image. Task id: {task_id}')
            fail = True

    sys.exit(int(fail))


if __name__ == '__main__':
    run(args)
