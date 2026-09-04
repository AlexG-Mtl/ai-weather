# Weather CI/CD Plan

## Scope and workflow design

Add two small GitHub Actions workflows:

- **CI** runs on every pull request targeting `main`. It installs Python 3.12 and the locked `uv` environment, then runs the two required checks: `uv run pytest` and `uv run ai-weather-dbt parse --project-dir dbt --profiles-dir dbt`. It has no Snowflake credentials, makes no Snowflake connection, and cannot modify Snowflake data.
- **CD** runs automatically on a push to `main` (the post-merge commit), only after CI is required and successful through the `main` branch protection/ruleset. It uses GitHub's `production` environment, one concurrency group with `cancel-in-progress: false`, and the existing `ai_dwh_svc` key-pair connection. This serializes deployments and prevents one deployment from cancelling another during a load.

Both workflows use least-privilege default permissions (`contents: read`), pinned action major versions, `uv sync --frozen`, and shell failure handling. Job timeouts prevent stalled runs. CD should not run on pull requests or accept arbitrary dates.

CI's dbt parse will satisfy the existing wrapper without real credentials by creating a temporary, syntactically valid `~/.snowflake/config.toml` entry named `ai_dwh_svc` and a temporary unencrypted PEM key, with placeholder account/user/warehouse/role values. `dbt parse` is compile-time validation and must not connect to Snowflake. No production secret is exposed to CI.

## CD configuration and secrets

Store these GitHub environment secrets on `production`:

| Secret | Use |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | Existing service user |
| `SNOWFLAKE_WAREHOUSE` | Existing warehouse |
| `SNOWFLAKE_ROLE` | Existing least-privilege service role |
| `SNOWFLAKE_PRIVATE_KEY` | Complete PEM-encoded private key |

The CD job writes the key to a temporary file with mode `0600`, creates the Snowflake CLI named connection `ai_dwh_svc` in the runner's temporary home/config directory, and sets `SNOWFLAKE_CONNECTION_NAME=ai_dwh_svc`. Configure the connection for JWT/key-pair authentication and point `private_key_file` at that temporary key. Mask sensitive values, never print the config or key, and remove temporary credential files in an `always()` cleanup step. The current repository expects an unencrypted key because its dbt wrapper does not pass a private-key password.

The Snowflake database, warehouse, service user/role, public-key registration, and required grants are prerequisites managed outside this repository. In particular, the role must be able to use the warehouse/database, create/use the weather schemas and objects, merge into the raw table, and build/test the staging view. CD only provisions repository-owned objects declared in `sql/create_raw_objects.sql`.

## Exact validation sequence

### CI

1. Check out the pull-request commit.
2. Set up Python 3.12 and `uv`, then run `uv sync --frozen`.
3. Run `uv run pytest`.
4. Create the temporary non-production Snowflake CLI config/key described above.
5. Run `uv run ai-weather-dbt parse --project-dir dbt --profiles-dir dbt`.

### CD

1. Check out the exact commit pushed to `main`; set up Python 3.12 and `uv`; run `uv sync --frozen`.
2. Install the Snowflake CLI at a pinned version, create the temporary `ai_dwh_svc` connection, and verify authentication with a read-only `select current_account(), current_user(), current_role(), current_warehouse()`.
3. Provision repository-owned raw objects with `snow sql -c ai_dwh_svc -f sql/create_raw_objects.sql`.
4. Execute one real fixed-date ingestion: `uv run ai-weather 2024-01-01 2024-01-01`. Capture its emitted content hash for validation without logging credentials or payload data.
5. Query `AI_DWH.WEATHER_RAW.OPEN_METEO_RESPONSES` for that content hash and require at least one row whose `start_date` and `end_date` are both `2024-01-01` and whose `payload:hourly:time` is a non-empty array. Make the command exit non-zero when the predicate is false.
6. Run `uv run ai-weather-dbt run --project-dir dbt --profiles-dir dbt --select stg_open_meteo__hourly`.
7. Run `uv run ai-weather-dbt test --project-dir dbt --profiles-dir dbt --select stg_open_meteo__hourly`.
8. Query `AI_DWH.WEATHER_STAGING.STG_OPEN_METEO__HOURLY` for the captured `source_content_hash`; require at least one row, non-null `weather_hour_utc`, and dates confined to `2024-01-01`. Make the command exit non-zero when the predicate is false.
9. Always remove temporary key and connection files.

All steps are fail-fast. A failed command, false data assertion, API error, authentication error, dbt failure, or cleanup-independent timeout fails the workflow and blocks the deployment result. The raw load is safely repeatable because ingestion merges on the canonical payload hash; object creation is also idempotent. There is no automatic rollback because the pipeline writes durable raw history and deploys a view. Recovery is to correct the cause and rerun the failed CD workflow or merge a fix.

## Repository and platform changes

- Add `.github/workflows/ci.yml` and `.github/workflows/cd.yml` only when implementation is approved.
- Do not add credentials, account-specific configuration, infrastructure provisioning, schedules, or additional environments.
- Configure a `main` branch ruleset outside this repository to require the CI job before merge and prevent direct bypasses as appropriate.
- Configure the `production` GitHub environment and its secrets outside this repository. No manual approval gate is required because deployment is automatic after merge.

## Acceptance criteria

- Every pull request to `main` runs both `uv run pytest` and the project's existing dbt parse command, and CI has no real Snowflake credentials or data-writing step.
- Merging is blocked unless the required CI check succeeds.
- Every merge to `main` automatically starts exactly one serialized CD run for that commit.
- CD authenticates through the existing Snowflake key-pair pattern, provisions only the repository-owned raw objects, ingests Montreal weather for `2024-01-01`, and proves matching non-empty raw and staging data.
- CD runs dbt model execution and dbt tests as separate required steps; any failed command or validation makes the deployment fail visibly.
- Secrets never appear in source, artifacts, or logs, and temporary credential material is cleaned up.
- Re-running CD is idempotent for both object creation and an unchanged Open-Meteo response.

## Finalized decisions

- Validation date: `2024-01-01` (start and end).
- CD trigger: automatic push to `main` after merge.
- Snowflake infrastructure, identity, key registration, and grants: external prerequisites.
- Merge policy: successful CI is required.
- Required CI checks: `uv run pytest` and dbt parse through the repository's existing `ai-weather-dbt` command/configuration.
