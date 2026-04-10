# Scan Surfaces

Detailed guide to each scan surface with specific patterns, common vulnerabilities, and how to check for them.

## Code Patterns

### SQL Injection

Look for string concatenation or interpolation in SQL queries.

Patterns to flag:

- Python: `cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")`, `"SELECT ... " + variable`
- JavaScript/TypeScript: `` `SELECT * FROM users WHERE id = ${userId}` ``, `"SELECT ... " + variable`
- Go: `db.Query("SELECT * FROM users WHERE id = " + id)`
- Java: `stmt.executeQuery("SELECT * FROM users WHERE id = " + userId)`

Safe alternatives: parameterized queries, prepared statements, ORM query builders.

### Cross-Site Scripting (XSS)

Look for unescaped user input rendered in HTML responses.

Patterns to flag:

- JavaScript: `element.innerHTML = userInput`, `document.write(userInput)`
- Python (Flask/Django): `Markup(user_input)`, `|safe` filter on untrusted data
- Template engines: `{{{ unescaped }}}` in Handlebars, `<%- unescaped %>` in EJS

Safe alternatives: context-aware escaping, CSP headers, sanitization libraries.

### Command Injection

Look for user input passed to shell commands.

Patterns to flag:

- Python: `os.system(f"ping {host}")`, `subprocess.call(cmd, shell=True)` with user input
- JavaScript: `child_process.exec("ping " + host)`, `eval(userInput)`
- Go: `exec.Command("sh", "-c", userControlled)`
- Java: `Runtime.getRuntime().exec("ping " + host)`

Safe alternatives: parameterized APIs, allowlists for command arguments, avoid `shell=True`.

### Path Traversal

Look for user input used in file paths without validation.

Patterns to flag:

- `open(base_dir + user_input)` without path canonicalization
- `fs.readFile(req.params.filename)` without checking for `../`
- Any file operation where the path includes unsanitized user input

Safe alternatives: canonicalize paths, validate against allowed directories, use allowlists.

### Authentication And Authorization Issues

Look for:

- endpoints missing authentication middleware
- authorization checks that only verify authentication (not role/permission)
- JWT tokens without expiration, without signature verification, or with `none` algorithm
- session tokens with insufficient entropy
- password storage using MD5, SHA1, or unsalted hashes
- missing CSRF protection on state-changing endpoints

### Insecure Cryptography

Look for:

- weak algorithms: MD5, SHA1 for security purposes, DES, RC4
- hardcoded encryption keys or initialization vectors
- `Math.random()` or `random.random()` for security-sensitive values (use `crypto.randomBytes` or `secrets` module)
- custom crypto implementations instead of established libraries
- ECB mode for block ciphers

### Unsafe Deserialization

Look for:

- Python: `pickle.loads(untrusted)`, `yaml.load(data)` without `Loader=SafeLoader`
- Java: `ObjectInputStream.readObject()` with untrusted data
- JavaScript: `JSON.parse()` followed by `eval()` or prototype pollution
- Any deserialization of untrusted data without schema validation

### Race Conditions

Look for:

- time-of-check-to-time-of-use (TOCTOU) patterns in file operations
- concurrent balance/inventory updates without locking
- check-then-act patterns in multi-threaded code without synchronization
- database read-modify-write without transactions or optimistic locking

### Server-Side Request Forgery (SSRF)

Look for:

- user-controlled URLs passed to HTTP client calls
- URL validation that only checks the initial URL (not redirects)
- internal service endpoints accessible via user-provided URLs
- missing allowlists for external service calls

## Dependencies

### Known Vulnerabilities (CVEs)

How to check:

- Read `package.json`/`package-lock.json` and cross-reference known CVE databases
- Read `requirements.txt`/`Pipfile.lock` for Python packages
- Read `go.mod`/`go.sum` for Go modules
- Read `pom.xml`/`build.gradle` for Java dependencies
- Look for `.audit` or security scan output files already in the repo
- Check if the project uses Dependabot, Snyk, or similar tools

### Outdated Packages

Look for:

- lock files with significantly old versions when newer versions have security patches
- dependencies pinned to specific versions that are multiple major versions behind
- packages with known end-of-life status

### Unmaintained Dependencies

Look for:

- dependencies with no releases in 2+ years
- archived or deprecated packages still in use
- packages with known maintainer abandonment

### License Compliance

Look for:

- copyleft licenses (GPL, AGPL) in proprietary codebases
- incompatible license combinations
- missing license files for vendored code

### Typosquatting

Look for:

- package names that differ by one character from popular packages
- packages with suspiciously low download counts or recent creation dates
- internal package names that could conflict with public registry packages

## Secrets And Credentials

### What To Search For

Common patterns:

- `password`, `passwd`, `pwd` in variable names or config values
- `api_key`, `apikey`, `api-key`, `apiKey` assignments
- `secret`, `token`, `auth` followed by `=` or `:`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `PRIVATE_KEY`, `BEGIN RSA PRIVATE KEY`
- connection strings: `postgresql://user:pass@`, `mongodb://user:pass@`
- Base64-encoded strings that decode to credential patterns

### Where To Search

- all source files (not just config files)
- `.env`, `.env.local`, `.env.production` files
- `docker-compose.yml` and Dockerfiles
- CI/CD configuration files
- test fixtures and seed data
- documentation and comments
- git history (check for secrets added then removed)

### .gitignore Check

Verify `.gitignore` excludes:

- `.env*` files
- `*.pem`, `*.key`, `*.p12` files
- `credentials.json`, `service-account.json`
- IDE-specific files that may contain tokens
- build artifacts that might embed secrets

## Configuration

### Insecure Defaults

Look for:

- `DEBUG = True` or `debug: true` in production configs
- default passwords or admin credentials in config files
- sample configs that become production configs without hardening

### CORS And CSP

Look for:

- `Access-Control-Allow-Origin: *` on sensitive endpoints
- missing or overly permissive Content-Security-Policy headers
- `Access-Control-Allow-Credentials: true` combined with wildcard origins

### Rate Limiting

Look for:

- public API endpoints without rate limiting middleware
- authentication endpoints (login, password reset) without brute-force protection
- missing rate limiting on resource-intensive operations

### TLS Settings

Look for:

- TLS verification disabled: `verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify: true`
- support for deprecated TLS versions (TLS 1.0, 1.1)
- weak cipher suites in server configuration

## Infrastructure As Code

### Common Misconfigurations

#### Terraform

- `acl = "public-read"` on S3 buckets
- security groups with `cidr_blocks = ["0.0.0.0/0"]` on sensitive ports
- IAM policies with `"Action": "*"` or `"Resource": "*"`
- missing `encrypt = true` on storage resources
- missing `logging` blocks on load balancers and buckets

#### Kubernetes

- containers running as root: `runAsUser: 0` or missing `securityContext`
- `privileged: true` in container security context
- missing resource limits (CPU, memory)
- secrets stored as plain text in manifests instead of using Secret resources
- missing network policies allowing unrestricted pod-to-pod communication

#### CloudFormation / Pulumi

- S3 buckets without `BucketEncryption`
- security groups with unrestricted ingress
- RDS instances with `PubliclyAccessible: true`
- missing CloudTrail or logging configuration

### IAM Best Practices

Check for:

- least-privilege violations (wildcard actions or resources)
- cross-account access without explicit trust policies
- service roles with admin-level permissions
- missing conditions or constraints on sensitive actions

## Access Control

### File Permissions

- executable bit on files that should not be executable
- world-readable permissions on sensitive config files
- `.git/config` with embedded credentials

### Branch Protection

- missing branch protection on `main`/`master`/`production` branches
- no required reviewers for merges
- force push allowed on protected branches
- no required status checks before merging

### Repository Permissions

- overly broad collaborator access (write when read would suffice)
- personal access tokens with excessive scope in CI configs
- GitHub App installations with more permissions than needed
- missing audit logging for administrative actions

### MFA And Authentication

- no MFA requirement documented for repo access
- service account tokens without expiration
- shared credentials instead of individual accounts
