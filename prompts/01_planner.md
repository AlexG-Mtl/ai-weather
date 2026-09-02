Plan a small data-engineering feature.

Goal:
Fetch hourly weather data for Montreal from Open-Meteo, load the raw data
into Snowflake, and create one dbt staging model.

Keep the project intentionally small and suitable for demonstrating:
Plan → Build → Review.

Review the repository and propose:
- design
- acceptance criteria
- decisions I need to make

Do not implement anything.
Keep the plan under 2 pages.

Decisions approved:

- Use historical weather data.
- Store the untouched JSON response in VARIANT.
- Require explicit start_date and end_date.
- Use the existing Snowflake AI_DWH environment and ai_dwh_svc authentication.
- Create a separate raw schema for this weather project.
- Use uv.

Keep the implementation intentionally small.

Save the finalized plan as:
specs/01_weather_plan.md

Do not implement anything.

