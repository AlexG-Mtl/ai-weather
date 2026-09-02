from pathlib import Path

from ai_weather import dbt_cli
from ai_weather import snowflake as snowflake_loader


def test_connect_uses_default_named_connection(monkeypatch):
    calls = []
    monkeypatch.delenv("SNOWFLAKE_CONNECTION_NAME", raising=False)
    monkeypatch.setattr(
        snowflake_loader.snowflake.connector,
        "connect",
        lambda **kwargs: calls.append(kwargs) or object(),
    )

    snowflake_loader.connect()

    assert calls == [
        {
            "connection_name": "ai_dwh_svc",
            "database": "AI_DWH",
            "schema": "WEATHER_RAW",
        }
    ]


def test_connect_uses_selected_named_connection_and_ignores_password_env(monkeypatch):
    calls = []
    monkeypatch.setenv("SNOWFLAKE_CONNECTION_NAME", "alternate")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "must-not-be-used")
    monkeypatch.setattr(
        snowflake_loader.snowflake.connector,
        "connect",
        lambda **kwargs: calls.append(kwargs) or object(),
    )

    snowflake_loader.connect()

    assert calls[0]["connection_name"] == "alternate"
    assert "password" not in calls[0]


def test_dbt_connection_uses_selected_cli_config(tmp_path: Path, monkeypatch):
    config = tmp_path / "config.toml"
    config.write_text(
        """
[connections.ai_dwh_svc]
account = "account"
user = "user"
warehouse = "warehouse"
role = "role"
private_key_file = "/keys/service.p8"

[connections.alternate]
account = "other-account"
user = "other-user"
warehouse = "other-warehouse"
role = "other-role"
private_key_file = "/keys/other.p8"
"""
    )
    monkeypatch.setenv("SNOWFLAKE_CONNECTION_NAME", "alternate")

    selected = dbt_cli.snowflake_connection(config_path=config)

    assert selected == {
        "account": "other-account",
        "user": "other-user",
        "warehouse": "other-warehouse",
        "role": "other-role",
        "private_key_file": "/keys/other.p8",
    }
