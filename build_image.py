from collections import defaultdict
from pycarol import Carol, Apps, Tasks, ApiKeyAuth
import argparse, json, os
import logging
import time

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

git_token = args.gittoken
tenant = args.tenant
app_name = args.appname
organization = args.org
api_key = args.apikey
connector_id = args.connectorid
manifest_path = args.manifestpath

login = Carol(domain=tenant,
app_name=app_name,
organization=organization,
auth=ApiKeyAuth(api_key),
connector_id=connector_id)

manifest_path = manifest_path + 'manifest.json'
manifest_path = manifest_path[1:len(manifest_path)]

with open(manifest_path) as f:
    manifest = json.load(f)

logger.debug(f'Manifest: {manifest}')

app = Apps(login)

r = app.edit_manifest(app_name=app_name, manifest=manifest)

tasks = app.build_docker_git(git_token=git_token)

carol_task = Tasks(login)

indices = {task['mdmId']:0 for task in tasks}

while all([carol_task.get_task(task['mdmId']).task_status in ['READY', 'RUNNING'] for task in tasks]):

    to_remove = []

    for task in tasks[:]:
        task_id = task['mdmId']
        logs = carol_task.get_logs(task_id)

        if len(logs) > indices[task_id]:
            for i in range(indices[task_id], len(logs)):
                logger.info(logs[i]['mdmLogMessage'])   
                indices[task_id] += 1

        task_status = carol_task.get_task(task_id).task_status

        if task_status == 'COMPLETED':
            logger.info(f'Task {task_id} completed.')
            to_remove.append(task)
        elif task_status not in ['READY', 'RUNNING']:
            logger.error(f'Something went wrong while building your docker image. Task id: {task_id}')
            to_remove.append(task)

    tasks = [task for task in tasks if task not in to_remove]
    time.sleep(1)