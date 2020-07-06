# Carol Build

Builds docker images on Carol based on the information from the manifest file stored in a GitHub repository.

## Usage

Create a workflow (eg: `.github/workflows/action.yml`. See [Creating a Workflow file](https://help.github.com/en/articles/configuring-a-workflow#creating-a-workflow-file)) with the content below to use this action on your repository.
See the `action.yml` file in this repository for arguments' description.

```
name: Build docker image on Carol

# Controls when the action will run. Triggers the workflow on tag creation but
# only for the master branch. For triggering it on push or pull request events
# replace tag by push. 
on:
  push:
    branches: [ master ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
        
    - name: Build
      uses: totvslabs/carol-build@master
      with:
        git-token: ${{ secrets.GITTOKEN }}
        carol-tenant: 'tenant'
        carol-organization: 'organization'
        carol-app-name: 'app'
        carol-connector-id: ${{ secrets.CAROLCONNECTORID }}
        carol-api-key: ${{ secrets.CAROLAPPOAUTH }}
        manifest-path: '.'
```
PS: It is recommended storing the GitHub token, the connector id and its api key in the repository's secrets. See [Creating and storing encrypted secrets](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets) for more details.