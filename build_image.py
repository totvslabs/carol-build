from pycarol import Carol, Apps, Tasks, ApiKeyAuth
import argparse, json, os
import numpy as np
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

for build in manifest['docker']:
    docker_name = build['dockerName']
    docker_tag = build['dockerTag']
    instance_type = build['instanceType']
    app_name = build['appName']

    app = Apps(login)
    r = app.edit_manifest(app_name=app_name, manifest=manifest)

tasks = app.build_docker_git(git_token=git_token)

for task in tasks:
    task_id = task['mdmId']

    logger.debug(f'Task id: {task_id}')

    task = Tasks(login, task_id)
    logs = task.get_logs(task_id)
    index = 0

    for idx, log in enumerate(logs):
        index = idx
        logger.info(log['mdmLogMessage'])

    while task.task_status == 'READY' or task.task_status == 'RUNNING':
        task.get_task(task_id)
        logs = task.get_logs(task_id)
        if len(logs) > index:
            for i in np.arange(index, len(logs)):
                logger.info(logs[i]['mdmLogMessage'])   
                index += 1
        time.sleep(1)

    if task.task_status != 'COMPLETED':
        logger.error(f'Something went wrong while building your docker image: {docker_name}:{docker_tag}. Task id: {task_id}')
    
