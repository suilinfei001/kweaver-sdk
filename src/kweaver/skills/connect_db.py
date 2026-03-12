"""Skill: connect_db — connect a database and discover tables."""

from __future__ import annotations

from typing import Any

from kweaver.skills._base import BaseSkill


class ConnectDbSkill(BaseSkill):
    def _execute(self, **kwargs: Any) -> dict[str, Any]:
        db_type: str = kwargs["db_type"]
        host: str = kwargs["host"]
        port: int = kwargs["port"]
        database: str = kwargs["database"]
        account: str = kwargs["account"]
        password: str = kwargs["password"]
        schema: str | None = kwargs.get("schema")

        # 1. Test connectivity
        self.client.datasources.test(
            type=db_type, host=host, port=port,
            database=database, account=account, password=password, schema=schema,
        )

        # 2. Register datasource
        name = kwargs.get("name") or database
        ds = self.client.datasources.create(
            name=name, type=db_type, host=host, port=port,
            database=database, account=account, password=password, schema=schema,
        )

        # 3. Discover tables
        tables = self.client.datasources.list_tables(ds.id)

        return {
            "datasource_id": ds.id,
            "tables": [
                {
                    "name": t.name,
                    "columns": [
                        {"name": c.name, "type": c.type, "comment": c.comment}
                        for c in t.columns
                    ],
                }
                for t in tables
            ],
        }
