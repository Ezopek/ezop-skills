# Platform Patterns

Platform-specific best practices and examples. Use these as references when auditing, creating, or improving pipelines.

## GitHub Actions

### Structure

- One workflow per concern (CI, deploy, release, scheduled checks).
- Use `on.push.paths` and `on.pull_request.paths` to skip irrelevant runs.
- Prefer reusable workflows (`workflow_call`) over copy-pasted jobs.
- Use `concurrency` to cancel redundant runs on the same branch.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Caching

- Use `actions/cache` or built-in caching in setup actions (`actions/setup-node`, `actions/setup-python`).
- Cache key should include lockfile hash.

```yaml
- uses: actions/cache@<sha>
  with:
    path: ~/.npm
    key: npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: npm-${{ runner.os }}-
```

### Secrets And Permissions

- Set `permissions` at the workflow level, override per job when needed.
- Default to minimal permissions.

```yaml
permissions:
  contents: read
  pull-requests: write
```

- Use `${{ secrets.NAME }}` for secrets, never inline values.
- Use environment-scoped secrets for deployment credentials.
- Prefer OIDC (`aws-actions/configure-aws-credentials` with `role-to-assume`) over long-lived access keys.

### Security

- Pin all actions to full SHA, not tags.

```yaml
# Good
- uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29  # v4.1.6

# Bad
- uses: actions/checkout@v4
```

- Avoid `pull_request_target` with `actions/checkout` of the PR ref (code injection risk).
- Use `if: github.event.pull_request.head.repo.full_name == github.repository` to restrict fork runs when needed.
- Set `CODEOWNERS` for `.github/workflows/` to require review on pipeline changes.

### Optimization

- Use `matrix` for multi-version testing.
- Use `needs` to parallelize independent jobs.
- Use `paths` and `paths-ignore` filters on triggers.
- Use `if: contains(github.event.head_commit.message, '[skip ci]')` sparingly and intentionally.

```yaml
strategy:
  matrix:
    node-version: [18, 20, 22]
    os: [ubuntu-latest, macos-latest]
  fail-fast: false
```

## GitLab CI

### Structure

- Define stages explicitly at the top of `.gitlab-ci.yml`.
- Use `include` for shared configuration and templates.
- Use `extends` and YAML anchors to reduce duplication.
- Use `rules` instead of deprecated `only/except`.

```yaml
stages:
  - lint
  - test
  - build
  - deploy

include:
  - template: Security/SAST.gitlab-ci.yml
  - local: .gitlab/ci/deploy.yml
```

### Caching

- Cache per-job with fallback keys.
- Use `policy: pull` for jobs that only read the cache.

```yaml
cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/
  policy: pull-push
```

### Secrets And Permissions

- Use CI/CD variables (Settings > CI/CD > Variables) for secrets.
- Mark sensitive variables as masked and protected.
- Use environment-scoped variables for deployment credentials.
- Use `id_tokens` for OIDC-based cloud authentication.

```yaml
deploy:
  id_tokens:
    AWS_TOKEN:
      aud: https://gitlab.com
  script:
    - aws sts assume-role-with-web-identity --role-arn $ROLE_ARN --web-identity-token $AWS_TOKEN
```

### Security

- Pin Docker images to digest, not tag.

```yaml
# Good
image: node@sha256:abc123...

# Bad
image: node:20
```

- Use `protected` branches and tags to restrict deployment jobs.
- Enable SAST, DAST, and dependency scanning templates.
- Use `rules` to control when sensitive jobs run.

### Optimization

- Use `parallel` for test splitting.
- Use `needs` for DAG-based execution (skip waiting for unrelated stages).
- Use `interruptible: true` for jobs that can be safely cancelled.
- Use `changes` in rules to skip jobs when relevant files did not change.

```yaml
test:
  rules:
    - changes:
        - src/**/*
        - tests/**/*
        - package.json
  parallel: 4
  needs: ["lint"]
  interruptible: true
```

## Jenkins

### Structure

- Prefer declarative pipeline syntax over scripted.
- Use `stages` and `parallel` blocks for clear structure.
- Use shared libraries for reusable logic.
- Keep `Jenkinsfile` in the repo root.

```groovy
pipeline {
    agent any
    stages {
        stage('Lint') {
            steps {
                sh 'npm run lint'
            }
        }
        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
        stage('Deploy') {
            when {
                branch 'main'
            }
            input {
                message 'Deploy to production?'
            }
            steps {
                sh './deploy.sh'
            }
        }
    }
}
```

### Caching

- Use `stash`/`unstash` for passing files between stages.
- Use workspace caching plugins or Docker layer caching for dependencies.
- Mount persistent volumes for dependency caches on agents.

### Secrets And Permissions

- Use Jenkins Credentials (credentials binding plugin) for secrets.
- Never use `sh "echo $SECRET"` (leaks to logs); use `withCredentials` block.

```groovy
withCredentials([string(credentialsId: 'api-key', variable: 'API_KEY')]) {
    sh 'deploy --key $API_KEY'
}
```

- Use folder-level or pipeline-level credential scoping.
- Restrict who can approve `input` steps.

### Security

- Pin plugin versions in the Jenkins configuration.
- Use `agent { docker { image 'node@sha256:abc123...' } }` with pinned images.
- Enable Pipeline: Groovy Sandbox for untrusted pipelines.
- Restrict script approval to administrators.
- Use RBAC (Role-Based Access Control) for job and folder permissions.

### Optimization

- Use `parallel` blocks for concurrent stages.
- Use `when` conditions to skip unnecessary stages.
- Use lightweight checkout for large repos (`checkout scm: [$class: 'GitSCM', extensions: [[$class: 'CloneOption', shallow: true]]]`).
- Cache Docker layers with `--cache-from`.

```groovy
stage('Tests') {
    parallel {
        stage('Unit') {
            steps { sh 'npm run test:unit' }
        }
        stage('Integration') {
            steps { sh 'npm run test:integration' }
        }
    }
}
```

## Azure DevOps

### Structure

- Use multi-stage YAML pipelines (`azure-pipelines.yml`) over classic UI pipelines.
- Separate stages for build, test, and deploy.
- Use templates for shared logic across pipelines.
- Use `trigger` and `pr` sections to control when pipelines run.

```yaml
trigger:
  branches:
    include: [main]
  paths:
    include: [src/*, tests/*]

stages:
  - stage: Build
    jobs:
      - job: BuildApp
        pool:
          vmImage: ubuntu-latest
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '20.x'
          - script: npm ci && npm run build
```

### Secrets And Permissions

- Use Variable Groups linked to Azure Key Vault for secrets.
- Use service connections with minimal scoped permissions.
- Mark sensitive variables as `isSecret: true`.
- Use environment approvals and checks for deployment stages.

### Security

- Pin task versions to major version (e.g., `NodeTool@0`); Azure DevOps tasks use `@major` versioning.
- Use `resources.repositories` for secure checkout of external repos.
- Enable branch policies (required reviewers, build validation) on protected branches.
- Use `environments` with approval gates for production deployments.

### Optimization

- Use pipeline caching with `Cache@2` task.
- Use `dependsOn` and `condition` for DAG-based execution.
- Use `strategy.parallel` for test splitting.

## Bitbucket Pipelines

### Structure

- Define pipelines in `bitbucket-pipelines.yml` at repo root.
- Use `default`, `branches`, `pull-requests`, and `tags` sections for trigger control.
- Use `definitions.caches` and `definitions.services` for reuse.
- Use `step` with `name` for clarity.

```yaml
pipelines:
  default:
    - step:
        name: Build and Test
        caches:
          - node
        script:
          - npm ci
          - npm test
  branches:
    main:
      - step:
          name: Deploy
          deployment: production
          script:
            - ./deploy.sh
```

### Secrets And Permissions

- Use Repository Variables or Workspace Variables (Settings > Pipelines > Variables).
- Mark sensitive variables as "Secured" (masked in logs, not editable after creation).
- Use Deployment environments with environment-level variables for deployment secrets.

### Security

- Pin Docker images to digest when using custom images.
- Use `deployment` keyword with environments that have required reviewers.
- Restrict pipeline modifications via branch permissions.
- Limit `BITBUCKET_*` variable exposure in scripts.

### Optimization

- Use built-in caches (`node`, `pip`, `maven`, `docker`) where available.
- Use `parallel` steps for concurrent execution.
- Use `condition` to skip steps based on file changes.
- Keep pipeline minutes in mind (Bitbucket has usage limits on cloud).

## CircleCI

### Structure

- Define configuration in `.circleci/config.yml`.
- Use `workflows` for job orchestration and parallel execution.
- Use `orbs` for reusable, versioned configuration packages.
- Use `executors` to define reusable execution environments.

```yaml
version: 2.1

orbs:
  node: circleci/node@5

workflows:
  build-test-deploy:
    jobs:
      - node/install-packages
      - test:
          requires: [node/install-packages]
      - deploy:
          requires: [test]
          filters:
            branches:
              only: main
```

### Secrets And Permissions

- Use Project Settings > Environment Variables for secrets.
- Use Contexts for shared secrets across projects (manage access via security groups).
- Restrict Context access to specific branches or security groups.
- Use OIDC for cloud authentication where supported.

### Security

- Pin orb versions to exact version (e.g., `circleci/node@5.2.0`), not floating.
- Use `restricted` contexts for production secrets.
- Enable branch-level filtering for sensitive jobs.
- Review third-party orbs before use — prefer certified orbs.

### Optimization

- Use workspace persistence (`persist_to_workspace`/`attach_workspace`) for sharing build artifacts between jobs.
- Use `parallelism` with test splitting (`circleci tests split`).
- Use Docker layer caching (DLC) for faster image builds.
- Use resource classes to right-size compute for each job.

## Generic (Makefile / Script-Based)

### Structure

- Use a `Makefile` or script directory (`scripts/`) as the CI/CD entry point.
- Define standard targets: `lint`, `test`, `build`, `deploy`.
- Keep CI platform config thin — delegate to Makefile targets for portability.
- Document available targets in the project README.

```makefile
.PHONY: lint test build deploy

lint:
	npm run lint

test:
	npm test

build:
	npm run build

deploy: build
	./scripts/deploy.sh
```

### Secrets And Permissions

- Never hardcode secrets in Makefiles or scripts.
- Expect secrets as environment variables injected by the CI platform.
- Document required environment variables in README or AGENTS.md.
- Use `.env.example` (without real values) for local development.

### Security

- Validate that scripts do not execute untrusted input (no `eval "$USER_INPUT"`).
- Use `set -euo pipefail` in bash scripts for fail-fast behavior.
- Pin tool versions in scripts (e.g., `TERRAFORM_VERSION=1.5.7`).
- Do not store deployment credentials in the repo.

### Optimization

- Use `make -j` for parallel target execution where targets are independent.
- Cache dependency directories between CI runs (platform-specific cache config).
- Use incremental builds where the build system supports them.
