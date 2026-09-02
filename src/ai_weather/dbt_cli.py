import os
import subprocess
import sys
import tomllib
from pathlib import Path


def snowflake_connection(
    connection_name: str | None = None, config_path: Path | None = None
) -> dict[str, str]:
    name = connection_name or os.getenv("SNOWFLAKE_CONNECTION_NAME", "ai_dwh_svc")
    path = config_path or Path.home() / ".snowflake" / "config.toml"
    try:
        config = tomllib.loads(path.read_text())
        connection = config["connections"][name]
    except (OSError, tomllib.TOMLDecodeError, KeyError) as exc:
        raise RuntimeError(
            f"Snowflake CLI connection {name!r} could not be read from {path}"
        ) from exc

    required = ("account", "user", "warehouse", "role", "private_key_file")
    missing = [key for key in required if not connection.get(key)]
    if missing:
        raise RuntimeError(
            f"Snowflake CLI connection {name!r} is missing: {', '.join(missing)}"
        )
    return {key: str(connection[key]) for key in required}


def dbt_environment(connection: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        AI_WEATHER_SNOWFLAKE_ACCOUNT=connection["account"],
        AI_WEATHER_SNOWFLAKE_USER=connection["user"],
        AI_WEATHER_SNOWFLAKE_WAREHOUSE=connection["warehouse"],
        AI_WEATHER_SNOWFLAKE_ROLE=connection["role"],
        AI_WEATHER_SNOWFLAKE_PRIVATE_KEY_PATH=connection["private_key_file"],
    )
    return env


def main() -> int:
    try:
        connection = snowflake_connection()
        dbt_executable = Path(sys.executable).with_name("dbt")
        result = subprocess.run(
            [str(dbt_executable), *sys.argv[1:]], env=dbt_environment(connection)
        )
    except (RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
