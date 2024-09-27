# CI/CD

The project uses GitHub Actions for CI/CD. The pipeline configuration, including a pull request template, is located in the `.github` directory.

Two pipelines are defined in the `.github/workflows` directory:

- `ci.yml`: The CI pipeline runs on every pull request.
- `semantic-pr.yml`: The semantic PR pipeline runs on every pull request and checks for semantic versioning compliance.
- `semantic-release.yml`: The semantic release pipeline runs on every push to the `main` branch and, based upon pull request tags, automatically bumps the version of the package.

### Pipeline 1: CI

This `CI` pipeline is triggered upon a pull request to any branch. It runs continuous integration tasks across multiple operating systems, setting up the environment, installing dependencies, running formatting checks with `ruff` and `mypy`, executing unit tests with coverage reporting, and finally building and validating the package to ensure consistency between source and built files.

### Pipeline 2: Lint Pull Request Title

This pipeline is triggered when a pull request is opened, edited, or synchronized. It ensures that the pull request title follows Conventional Commits guidelines using the `amannn/action-semantic-pull-request` action.

### Pipeline 3: Semantic Release

This pipeline is triggered when a pull request is closed and merged into the main branch. It checks out the code, sets up the environment, and uses `python-semantic-release` to handle versioning and releasing the package. To trigger the automated versioning process, please ensure your commit messages follow semantic versioning conventions. Use prefixes like `fix:`, `feat:`, or `*!:` (or using `BREAKING CHANGES` in the commit message) in your commits to indicate the type of change:

| Commit Type                               | Description                                     | Example                     |
|-------------------------------------------|-------------------------------------------------|-----------------------------|
| `fix:`                                    | for bug fixes: triggers a **patch** version update | 1.0.0 -> 1.0.1              |
| `feat:`                                   | for new features: triggers a **minor** version update | 1.0.0 -> 1.1.0              |
| `*!:` (or using `BREAKING CHANGES` in the commit message) | for breaking changes: triggers a **major** version update | 1.0.0 -> 2.0.0              |

This ensures automated semantic versioning and release management, maintaining consistency and clarity in version updates.

## Dependabot

We use GitHub's Dependabot to automatically check for updates to GitHub Actions and Python dependencies. It performs daily checks and groups dependencies as follows:

- **GitHub Actions**: All dependencies within GitHub Actions are monitored and updated daily.
- **Python Dependencies**:
  - **Development Dependencies**: Development-specific dependencies are updated daily.
  - **Production Dependencies**: Production-specific dependencies are also checked daily.

This ensures dependencies are regularly maintained while adhering to the fixed environment constraints.

By default, we are excluding `pandas` and `numpy`, since they are fixed at Databricks Runtime 14.3 LTS.
