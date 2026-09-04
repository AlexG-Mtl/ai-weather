# AI Agent Workflow Retrospective — Weather Pipeline

## Experiment

Build a deliberately small data-engineering feature using:

**Plan → Build → Review → Remediate → Re-review → Approve**

Feature:

Open-Meteo → Python → Snowflake RAW → dbt staging

Final validation:

- Python tests: 9 passed
- dbt model: 1 passed
- dbt tests: 5 passed
- Final Reviewer verdict: APPROVE

## What worked

### Planner

The Planner produced a useful implementation specification from a relatively
short prompt.

It correctly defined:

- source and required weather fields
- raw JSON storage in Snowflake VARIANT
- raw/staging separation
- dbt model grain
- testing requirements
- project scope and explicit exclusions

The plan was detailed enough for another agent to implement without continuous
human instructions.

### Builder

The Builder created the complete vertical slice and successfully handled the
Reviewer remediation.

It was able to fix authentication/configuration problems after receiving
specific review findings rather than requiring the human to identify the code
changes.

### Reviewer

Independent review provided the most obvious value.

It found a real defect that the Builder's own tests had missed:

- the intended `ai_dwh_svc` connection path was unreachable
- dbt authentication did not match the existing key-pair configuration
- Snowflake connection-selection behavior lacked test coverage

After remediation, the Reviewer independently returned APPROVE.

## What did not work well

### Bootstrap/setup sequence was underspecified

The plan required:

`AI_DWH.WEATHER_RAW`

and included:

`sql/create_raw_objects.sql`

but did not explicitly require the Builder to execute the provisioning step
before live dbt validation.

This resulted in:

`dbt run → WEATHER_RAW does not exist`

The implementation was correct, but the environment was not fully prepared.

### Local tests were not enough

The first Builder result looked healthy:

- 6 Python tests passed
- dbt parse passed

but live Snowflake execution exposed authentication and provisioning problems.

For data-engineering work, successful parsing/unit tests should not be treated
as equivalent to end-to-end validation.

### Human intervention was still required

The human had to resolve an infrastructure permission:

`GRANT CREATE SCHEMA ON DATABASE AI_DWH TO ROLE AI_DWH_ROLE`

This was appropriate because an implementation agent should not automatically
grant itself additional Snowflake privileges.

## Workflow changes for future projects

Keep agent prompts short.

The specification should carry the detailed requirements rather than repeatedly
putting them into Builder and Reviewer prompts.

Every future plan should include an explicit end-to-end validation sequence:

1. Provision required objects.
2. Run ingestion.
3. Verify raw data.
4. Run transformations.
5. Run tests.
6. Verify representative output.

Environment prerequisites and required privileges should also be stated
explicitly.

Reviewer should remain a separate context from Builder.

After Reviewer identifies defects, remediation should normally return to the
same Builder context.

Limit the normal workflow to one remediation round unless the Reviewer finds a
genuine remaining implementation defect.

## Recommended standard workflow

**Planner**

Short human request → approved implementation plan.

**Builder**

Implement approved plan → unit/local validation → live integration validation.

**Reviewer**

Independent read-only review → BLOCKERS / WARNINGS / APPROVE.

**Remediation**

Same Builder fixes blockers.

**Final Reviewer**

Confirm fixes → APPROVE.

## Main lesson

The experiment supports using AI agents as separate engineering roles rather
than relying on one long agent conversation.

The biggest improvement needed is not longer prompts. It is a better
implementation specification that explicitly defines environment prerequisites
and the complete executable validation sequence.