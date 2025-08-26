"""
database_client.py
------------------
Módulo responsável por abstrair a comunicação com o banco PostgreSQL.
- Cria pool de conexões com asyncpg.
- Implementa operações básicas: insert, update, delete.
"""

import os
import logging
import asyncpg
from typing import Any, Dict, Optional
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class DatabaseClient:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")
        self.database = os.getenv("DB_NAME", "labdb")
        self.pool: Optional[Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            min_size=1,
            max_size=10
        )
        logger.info("✅ Conectado ao PostgreSQL")

    async def insert(self, table: str, data: Dict[str, Any]) -> bool:
        keys = ", ".join(data.keys())
        values = ", ".join(f"${i+1}" for i in range(len(data)))
        query = f"INSERT INTO {table} ({keys}) VALUES ({values})"
        async with self.pool.acquire() as conn:
            await conn.execute(query, *data.values())
        return True

    async def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> bool:
        set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])
        where_clause = " AND ".join([f"{k} = ${i+1+len(data)}" for i, k in enumerate(where.keys())])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        async with self.pool.acquire() as conn:
            await conn.execute(query, *list(data.values()), *list(where.values()))
        return True

    async def delete(self, table: str, where: Dict[str, Any]) -> bool:
        where_clause = " AND ".join([f"{k} = ${i+1}" for i, k in enumerate(where.keys())])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        async with self.pool.acquire() as conn:
            await conn.execute(query, *list(where.values()))
        return True

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("🛑 Pool de conexões fechado")
