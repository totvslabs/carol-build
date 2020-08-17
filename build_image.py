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

    if tasks is None:
        tasks = create_build_jobs(login, manifest, app_name, git_token)
        tasks = [task['mdmId'] for task in tasks]

    carol_task = Tasks(login)

    fail = False  # for exit code purpose
    while any([carol_task.get_task(task).task_status in ['READY', 'RUNNING'] for task in tasks]):
        time.sleep(3)

    for task_id in tasks:
        logs = carol_task.get_logs(task_id)
        for log in logs:
            logger.info(log['mdmLogMessage'])
        task_status = carol_task.get_task(task_id).task_status

        if task_status == 'COMPLETED':
            logger.info(f'Task {task_id} completed.')
        elif task_status in ['FAILED']:
            logger.error(f'Something went wrong while building your docker image. Task id: {task_id}')
            mdmId = Apps(login).get_by_name(app_name)['mdmId']
            logger.error(f'Check logs in https://{organization}.carol.ai/{tenant}/carol-ui/carol-app-dev/{mdmId}/logs?s=labels.%22k8s-pod%2Fkind%22%3D%22build%22&p=1&ps=25')
            fail = True

    return int(fail)


if __name__ == '__main__':
    fail = run(args)
    sys.exit(int(fail))
