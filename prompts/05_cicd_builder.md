Implement the approved CI/CD plan in specs/02_weather_cicd_plan.md.

Keep the implementation small and follow the existing project conventions.

Requirements:
- add PR CI with pytest and dbt parse
- add CD on merge to main
- use GitHub Actions
- use the existing Snowflake key-pair/named-connection approach
- execute a real ingestion in CD
- verify RAW and staging contain rows for the payload loaded by that run
- keep secrets out of logs
- do not modify Snowflake prerequisites outside the repository

Run all local validations you can.

Do not push or merge.

Report only:
- files changed
- validation summary
- unresolved issues