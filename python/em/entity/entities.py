from abc import ABC, abstractmethod
from typing import List, Any, Dict, Tuple, Iterable

from em.entity.specs import (
    MockEntitySpec
)

import psycopg
from psycopg import Connection, sql
from psycopg.abc import Query, Params
from psycopg.rows import DictRow, dict_row
from prettytable import PrettyTable
from environs import Env
import shutil

from loguru import logger

class SeedEntity(ABC):
    def __init__(self, name: str) -> None:
        self.name = name
    
    @abstractmethod
    def get_seeds(self, field: str) -> List[Any]:
        raise NotImplementedError()
    

class PostgresSeedEntity(SeedEntity):
    def __init__(self, name: str, schema: str) -> None:
        super().__init__(name)
        self.schema = schema
        self.connector = PostgresConnector()

    def get_seeds(self, field: str) -> List[Any]:
        query = sql.SQL('SELECT DISTINCT {column} FROM {table}').format(
            column=sql.Identifier(field),
            table=sql.Identifier(self.schema, self.name)
        )
        with self.connector.create_session() as session:
            rows = session.fetchall(query)
        return [ row[field] for row in rows ]
    
class MockEntity(ABC):
    def __init__(self, spec: MockEntitySpec) -> None:
        self.spec = spec
    
    @abstractmethod
    def load_records(self) -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def insertall(self) -> None:
        raise NotImplementedError()
    
class PostgresSession:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn
    
    def insertmany(self, query: Query, params_seq: Iterable[Params]):
        logger.debug(f'Execute {query.as_string(self.conn)}, values={params_seq}')
        with self.conn.cursor() as cur:
            cur.executemany(query, params_seq)

    def fetchall(self, query: Query) -> DictRow:
        logger.debug(f'Execute {query.as_string(self.conn)}')
        with self.conn.execute(query) as cur:
            return cur.fetchall()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.commit()
            self.conn.close()

env = Env()
env.read_env()

class PostgresConnector:
    def __init__(self) -> None:
        self.host = env.str('POSTGRES_HOST', default='localhost')
        self.port = env.int('POSTGRES_PORT', default=5432)
        self.database = env.str('POSTGRES_DATABASE', default='postgres')
        self.user = env.str('POSTGRES_USER', default='postgres')
        self.password = env.str('POSTGRES_PASSWORD', default=None)

    def create_session(self) -> PostgresSession:
        uri = f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
        conn = psycopg.connect(uri, row_factory=dict_row)
        return PostgresSession(conn)

class PostgresMockEntity(MockEntity):
    def __init__(self, spec: MockEntitySpec) -> None:
        super().__init__(spec)
        self.connector = PostgresConnector()

    def load_records(self) -> None:
        pass

    def get_schema(self) -> str:
        return self.spec.schema if self.spec.schema else 'public'

    def insertall(self, records: List[Dict[str, Any]]) -> None:
        all_values = []
        for record in records:
            columns, values = zip(*record.items())
            all_values.append(values)
        
        self.print_table(columns, all_values)

        query = sql.SQL('INSERT INTO {table} ({columns}) VALUES ({placeholders})').format(
            table=sql.Identifier(self.get_schema(), self.spec.name),
            columns=sql.SQL(',').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(',').join(sql.Placeholder() * len(columns))
        )
        with self.connector.create_session() as session:
            session.insertmany(query, all_values)

    def print_table(self, columns: List[str], rows: List[Tuple[Any]]):
        screen_width = shutil.get_terminal_size().columns

        cells = [ columns ] + [ list(map(str, row)) for row in rows ]
        max_column_widths = [ max(len(cell) + 10 for cell in column_cells) for column_cells in zip(*cells)] 

        current_width = 0
        current_indices = []
        subtables = []

        for i, max_column_width in enumerate(max_column_widths):
            if current_width + max_column_width < screen_width:
                current_width += max_column_width
                current_indices.append(i)
            else:
                subtables.append(current_indices)
                current_width = max_column_width
                current_indices = [i]

        if current_indices:
            subtables.append(current_indices)

        for indices in subtables:
            subcolumns = [ columns[i] for i in indices ]
            subvalues = [ tuple(row[i] for i in indices) for row in rows ]

            table = PrettyTable()
            table.title = self.spec.name
            table.field_names = subcolumns
            table.align = 'r'
            table.add_rows(subvalues)
            print(table)
            print()
