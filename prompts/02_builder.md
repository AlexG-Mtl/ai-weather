Implement the approved plan in specs/01_weather_plan.md.

Keep the implementation minimal.
Reuse the existing Snowflake ai_dwh_svc connection where practical.
Use uv for Python dependencies.

Run the relevant Python tests and dbt validation.

Do not push or merge.

Report only:
- files changed
- test summary
- unresolved issues

--

Fix all Reviewer blockers in the weather implementation.

Use the existing working ai_dwh_svc Snowflake CLI connection/key-pair setup
instead of requiring separate password-style credentials.

Also fix any directly related dbt configuration issue needed for the same
authentication path.

Add tests that cover Snowflake connection selection.

Run:
- Python tests
- dbt parse
- live dbt compile/run/test if possible

Do not push or merge.

Report only:
- files changed
- test summary
- unresolved blockers