Plan CI/CD for the existing weather project using GitHub Actions.

Goal:
- CI on pull requests
- CD after merge to main
- use the existing Snowflake key-pair authentication
- validate the real Open-Meteo → Snowflake → dbt pipeline

Keep it intentionally small.

CI must not modify Snowflake data.

CD must:
1. provision required Snowflake objects
2. execute a real ingestion
3. verify RAW contains data
4. run dbt
5. run dbt tests
6. verify staging contains data

Review the existing repository before designing the workflow.

Define:
- workflow design
- GitHub secrets required
- exact validation sequence
- failure behavior
- acceptance criteria
- decisions I need to make

Do not implement anything.
Keep the plan under 2 pages.