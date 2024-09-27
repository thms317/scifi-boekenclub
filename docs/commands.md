# List of `make` Commands

## `install`

This command verifies the presence of necessary tools and installs them if they are not already installed. The tools include:

- `Homebrew`
- `Databricks CLI`
- `git`
- `Poetry`
- `pyenv`

The command also sets up the required Python version (specified in the `.python-version` file) using `pyenv` and, if needed, updates the shell configuration files (`.zprofile` and `.zshrc`) for `pyenv` compatibility.

<details>
  <summary>Usage</summary>

```bash
make install
```

```bash
Verifying if Homebrew is installed...
Installing required tools...
Databricks CLI is already installed. Skipping.
git is already installed. Skipping.
poetry is already installed. Skipping.
pyenv is already installed. Skipping.
Setting up Python version 3.10.12
Pyenv configuration already exists in .zshrc. Skipping.
Pyenv configuration already exists in .zprofile. Skipping.
Restarting the terminal...
All tools installed successfully.
```

</details>

## `setup`

This command sets up the project development environment by configuring `Poetry`, initializing `git` (if required), and installing `pre-commit` hooks.

<details>
  <summary>Usage</summary>

```bash
make setup
```

```bash
Setting up the project...
/Users/thomasbrouwer/.pyenv/shims/python
Python 3.10.12
Creating virtualenv scifi-boekenclub in /Users/thomasbrouwer/code/scifi-boekenclub/.venv
Using virtualenv: /Users/thomasbrouwer/code/scifi-boekenclub/.venv
Updating dependencies
Resolving dependencies... (1.6s)

Package operations: 93 installs, 1 update, 0 removals

  - Installing six (1.16.0)
  - Installing asttokens (2.4.1)
  - Installing executing (2.1.0)
  - Installing markupsafe (2.1.5)
  - Installing mergedeep (1.3.4)
  - Installing parso (0.8.4)
  - Installing platformdirs (4.3.6)
  - Installing ptyprocess (0.7.0)
  - Installing pure-eval (0.2.3)
  - Installing python-dateutil (2.9.0.post0)
  - Installing pyyaml (6.0.2)
  - Installing smmap (5.0.1)
  - Installing traitlets (5.14.3)
  - Installing wcwidth (0.2.13)
  - Installing certifi (2024.8.30)
  - Installing charset-normalizer (3.3.2)
  - Installing click (8.1.7)
  - Installing decorator (5.1.1)
  - Installing distlib (0.3.8)
  - Installing exceptiongroup (1.2.2)
  - Installing filelock (3.16.1)
  - Installing ghp-import (2.1.0)
  - Installing gitdb (4.0.11)
  - Installing idna (3.10)
  - Installing iniconfig (2.0.0)
  - Installing jedi (0.19.1)
  - Installing jinja2 (3.1.4)
  - Installing jupyter-core (5.7.2)
  - Installing markdown (3.7)
  - Installing matplotlib-inline (0.1.7)
  - Installing mkdocs-get-deps (0.2.0)
  - Installing packaging (24.1)
  - Installing pexpect (4.9.0)
  - Installing pathspec (0.12.1)
  - Installing pluggy (1.5.0)
  - Installing prompt-toolkit (3.0.48)
  - Installing pygments (2.18.0)
  - Installing pyyaml-env-tag (0.1)
  - Installing pyzmq (26.2.0)
  - Installing ruamel-yaml-clib (0.2.8)
  - Installing stack-data (0.6.3)
  - Installing tomli (2.0.1)
  - Installing tornado (6.4.1)
  - Installing urllib3 (2.2.3)
  - Installing watchdog (5.0.2)
  - Installing appnope (0.1.4)
  - Installing babel (2.16.0): Pending...
  - Installing cfgv (3.4.0)
  - Installing colorama (0.4.6)
  - Installing comm (0.2.2)
  - Installing coverage (7.6.1)
  - Installing debugpy (1.8.6): Installing...
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing cfgv (3.4.0)
  - Installing colorama (0.4.6)
  - Installing comm (0.2.2)
  - Installing coverage (7.6.1)
  - Installing debugpy (1.8.6): Installing...
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing babel (2.16.0): Installing...
  - Installing cfgv (3.4.0)
  - Installing colorama (0.4.6)
  - Installing comm (0.2.2)
  - Installing coverage (7.6.1)
  - Installing debugpy (1.8.6): Installing...
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing identify (2.6.1)
  - Installing ipython (8.18.1): Installing...
  - Installing jupyter-client (8.6.3)
  - Installing jupyter-client (8.6.3)
  - Installing ipython (8.18.1)
  - Installing jupyter-client (8.6.3)
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing identify (2.6.1)
  - Installing ipython (8.18.1)
  - Installing jupyter-client (8.6.3)
  - Installing debugpy (1.8.6)
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing identify (2.6.1)
  - Installing ipython (8.18.1)
  - Installing jupyter-client (8.6.3)
  - Installing cfgv (3.4.0)
  - Installing colorama (0.4.6)
  - Installing comm (0.2.2)
  - Installing coverage (7.6.1)
  - Installing debugpy (1.8.6)
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing identify (2.6.1)
  - Installing ipython (8.18.1)
  - Installing jupyter-client (8.6.3)
  - Installing babel (2.16.0)
  - Installing cfgv (3.4.0)
  - Installing colorama (0.4.6)
  - Installing comm (0.2.2)
  - Installing coverage (7.6.1)
  - Installing debugpy (1.8.6)
  - Installing docstring-parser-fork (0.0.9)
  - Installing gitpython (3.1.43)
  - Installing identify (2.6.1)
  - Installing ipython (8.18.1)
  - Installing jupyter-client (8.6.3)
  - Installing mako (1.3.5)
  - Installing mkdocs-material-extensions (1.3.1)
  - Installing mkdocs (1.6.1)
  - Installing mypy-extensions (1.0.0)
  - Installing nest-asyncio (1.6.0)
  - Installing nodeenv (1.9.1)
  - Installing numpy (1.23.5)
  - Installing paginate (0.5.7)
  - Installing pillow (10.4.0)
  - Installing psutil (6.0.0)
  - Installing py4j (0.10.9.7)
  - Installing pymdown-extensions (10.10.2)
  - Installing pytest (8.3.3)
  - Installing pytz (2024.2)
  - Installing regex (2024.9.11)
  - Installing requests (2.32.3)
  - Installing ruamel-yaml (0.18.6)
  - Updating setuptools (74.0.0 -> 75.1.0)
  - Installing types-pytz (2024.2.0.20240913)
  - Installing typing-extensions (4.12.2)
  - Installing virtualenv (20.26.5)
  - Installing defusedxml (0.7.1)
  - Installing genbadge (1.1.1)
  - Installing git-cliff (2.6.0)
  - Installing ipykernel (6.29.5)
  - Installing mkdocs-material (9.5.38)
  - Installing mypy (1.11.2)
  - Installing pandas (1.5.3)
  - Installing pandas-stubs (2.2.2.240807)
  - Installing pdoc3 (0.11.1)
  - Installing pre-commit (3.8.0)
  - Installing pre-commit-update (0.5.1.post1)
  - Installing pydoclint (0.5.8)
  - Installing pyspark (3.5.3)
  - Installing pytest-cov (5.0.0)
  - Installing pytest-mock (3.14.0)
  - Installing ruff (0.6.8)

Writing lock file

Installing the current project: scifi-boekenclub (0.1.0)
poetry types update;
Updating dependencies
Resolving dependencies... (1.5s)

No dependencies to install or update
Setting up pre-commit...
. .venv/bin/activate;
.venv/bin/pre-commit install --hook-type pre-commit --hook-type commit-msg;
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/commit-msg
```

</details>

## `clean`

This command cleans up the project development environment by removing the virtual environment, cache files, and resetting the terminal.

<details>
  <summary>Usage</summary>

```bash
make clean
```

```bash
Cleaning up...
rm -rf .venv poetry.lock
find . -type d \( -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" \) -exec rm -rf {} +
Cleanup completed. Resetting terminal...
```

</details>

## `test`

This command first updates Poetry dependencies and builds the package. Then, it runs a full test suite using `pytest`, generating a coverage report, for all the source code.

<details>
  <summary>Usage</summary>

```bash
make test
```

```bash
Running tests...
poetry run pytest tests --cov=src --cov-report term

====================== test session starts ======================

platform darwin -- Python 3.10.12, pytest-8.3.3, pluggy-1.5.0
rootdir: /Users/thomasbrouwer/code/scifi-boekenclub
configfile: pyproject.toml
plugins: cov-5.0.0, mock-3.14.0
collected 2 items

tests/default_test.py ..                                                                                                                                                                           [100%]

--------- coverage: platform darwin, python 3.10.12-final-0 ----------
Name                   Stmts   Miss  Cover
------------------------------------------
src/scifi/__init__.py       0      0   100%
src/scifi/main.py           3      0   100%
------------------------------------------
TOTAL                      3      0   100%


====================== 2 passed in 0.02s ======================
```

</details>

## `deploy_%`

This command deploys the bundle to a target Databricks Workspace environment. The supported environments are `dev` and `prd`.

<details>
  <summary>Usage</summary>

```bash
make deploy_dev
make deploy_prd
```

```bash
poetry build
Building scifi-boekenclub (0.1.0)
  - Building sdist
  - Built scifi-boekenclub-0.1.0.tar.gz
  - Building wheel
  - Built scifi-boekenclub-0.1.0-py3-none-any.whl
Building platform...
Uploading scifi-boekenclub-0.1.0-py3-none-any.whl...
Uploading bundle files to /Users/thomas.brouwer@revodata.nl/.bundle/scifi-boekenclub/dev/files...
Deploying resources...
Updating deployment state...
Deployment complete!
```

</details>

## `destroy_%`

This command destroys the deployed bundle in a target Databricks Workspace environment. The supported environments are `dev` and `prd`.

<details>
  <summary>Usage</summary>

```bash
make destroy_dev
make destroy_prd
```

```bash
Building platform...
The following resources will be deleted:
  delete job ingest_dataset_with_dlt
  delete job template_job
  delete pipeline dlt_ingest_dataset

All files and directories at the following location will be deleted: /Users/thomas.brouwer@revodata.nl/.bundle/scifi-boekenclub/dev

Would you like to proceed? [y/n]: y
Deleting files...
Destroy complete!
```

</details>

## `repo`

This command creates a repository in RevoData's GitHub and sets it up as a remote for the local Git repository. This command requires that the GitHub CLI (`gh`) is installed and authenticated.

<details>
  <summary>Usage</summary>

```bash
make repo
```

```bash
Creating repository in RevoData's GitHub...
Repository created at revodatanl/scifi-boekenclub...
Publishing project...
Repository published.
```

</details>

## `module`

This command provides a selection menu to deploy various custom RevoData modules. The available modules include:

- DLT
- Azure DevOps
- GitLab
- VSCode settings

<details>
  <summary>Usage</summary>

```bash
make module
```

```bash
Select the module to deploy:
1) DLT
2) Azure DevOps
3) GitLab
4) VSCode settings (update)
Enter the number of the module you want to deploy: 1

Your DLT ingestion pipeline, part of the 'ingest_dataset_using_dlt' workflow, has been added to the 'resources' directory.
```

</details>

## `tree`

This command generates a tree view of the project directory, excluding certain directories and files like `.venv`, `__pycache__`, and `.git`.

<details>
  <summary>Usage</summary>

```bash
make tree
```

```bash
.
├── .coverage
├── .github
│   ├── dependabot.yml
│   ├── pull_request_template.md
│   └── workflows
│       ├── ci.yml
│       ├── deploy-dab.yml
│       ├── semantic-pr.yml
│       └── semantic-release.yml
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── .vscode
│   ├── extensions.json
│   └── settings.json
├── Makefile
├── README.md
├── README_github.md
├── databricks.yml
├── dependabot.md
├── docs
│   ├── CHANGELOG.md
│   ├── api
│   │   ├── scifi
│   │   │   ├── index.html
│   │   │   └── main.html
│   │   └── tests
│   │       ├── default_test.html
│   │       └── index.html
│   ├── assets
│   │   ├── badge-coverage.svg
│   │   ├── badge-tests.svg
│   │   ├── make-clean.png
│   │   ├── make-deploy_dev.png
│   │   ├── make-destroy_dev.png
│   │   ├── make-install.png
│   │   ├── make-module-azure-devops.png
│   │   ├── make-module-dlt.png
│   │   ├── make-module-gitlab.png
│   │   ├── make-module-vscode.png
│   │   ├── make-module.png
│   │   ├── make-repo-github.png
│   │   ├── make-repo.png
│   │   ├── make-setup.png
│   │   ├── make-test.png
│   │   └── make-tree.png
│   ├── bundle_deployment.md
│   ├── cicd.md
│   ├── coding_standards.md
│   ├── commands.md
│   ├── getting_started.md
│   ├── index.md
│   ├── jobs
│   │   └── index.md
│   ├── modules.md
│   ├── notebooks
│   │   └── index.md
│   ├── release.md
│   └── tests
│       ├── coverage
│       │   ├── class_index.html
│       │   ├── coverage_html_cb_6fb7b396.js
│       │   ├── favicon_32_cb_58284776.png
│       │   ├── function_index.html
│       │   ├── index.html
│       │   ├── keybd_closed_cb_ce680311.png
│       │   ├── status.json
│       │   ├── style_cb_8e611ae1.css
│       │   ├── z_df71c8327dd0b782___init___py.html
│       │   └── z_df71c8327dd0b782_main_py.html
│       ├── coverage_report.md
│       ├── test_configuration.md
│       └── tests.md
├── mkdocs.yml
├── poetry.lock
├── poetry.toml
├── pyproject.toml
├── resources
│   ├── jobs
│   │   ├── ingest_dataset_using_dlt.yml
│   │   └── template_job.yml
│   └── notebooks
│       ├── dlt_ingest_dataset.py
│       └── hello_revodata.py
├── src
│   └──
│       ├── __init__.py
│       └── main.py
└── tests
    ├── __init__.py
    └── default_test.py

19 directories, 73 files
```

</details>

## `docs`

Our project used `MkDocs` to generate comprehensive HTML documentation from markdown files in the `docs` directory. In addition, we use `pdoc3` to auto-generate HTML documentation (from doctrings) of modules and tests. Embedded in the documentation is the coverage report generated by `pytest-cov`. Lastly, we use `mkdocs-material` to enhance the visual appearance of the documentation.

To generate documentation, run the following command:

<details>
  <summary>Usage</summary>

```bash
make docs
```

```bash
Generating HTML documentation...
docs/api/scifi/index.html
docs/api/scifi/main.html
docs/api/tests/index.html
docs/api/tests/default_test.html
Generating coverage report...
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: ./site
INFO    -  Documentation built in 0.24 seconds
INFO    -  Building documentation...
INFO    -  Cleaning site directory
INFO    -  Documentation built in 0.21 seconds
INFO    -  [14:20:30] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO    -  [14:20:30] Serving on http://127.0.0.1:8000/
```

</details>
