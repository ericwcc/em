from abc import ABC, abstractmethod
from em.entity.entities import (
    MockEntity
)
from em.entity.specs import (
    MockEntityFieldSpec,
)
from em.entity.seeders import (
    FieldSeeder,
)
from typing import Any, Dict, List
from dataclasses import dataclass
from em.utils.import_utils import load_function
from em.entity.specs import MockEntitySpec
from datetime import datetime, timedelta
import random
from decimal import Decimal, ROUND_HALF_UP
import math

from loguru import logger

@dataclass
class MockContext:
    index: int
    updating: Dict[str, Any]

class FieldMocker(ABC):
    def __init__(self, spec: MockEntityFieldSpec, seeder: type[FieldSeeder] = None):
        self.spec = spec
        self.seeder = seeder
    
    def load_seeds(self) -> List[Any]:
        self.seeds = self.spec.seeds
        if self.seeder:
            self.seeds = self.seeds + self.seeder.get_seeds()

    def get_name(self):
        return self.spec.name
    
    @abstractmethod
    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        pass

    def __repr__(self) -> str:
        return self.spec.name
    
class EntityMocker:
    def __init__(self, spec: MockEntitySpec, entity: type[MockEntity], field_mockers: List[type[FieldMocker]]):
        self.spec = spec
        self.entity = entity
        self.field_mockers  = field_mockers
    
    def load_entity_records(self):
        self.entity.load_records()

    def mock(self):
        logger.debug(f'Mock {self.spec.name} entity')
        records = []
        for i in range(self.spec.records):
            updating = {}
            for field_mocker in self.field_mockers:
                field_mocker.load_seeds()
                mock_data = field_mocker.mock(MockContext(index=i, updating=updating), self.entity)
                updating[field_mocker.get_name()] = mock_data
            records.append(updating.copy())
        self.entity.insertall(records)

class CustomFieldMocker(FieldMocker):
    def __init__(self, spec: MockEntityFieldSpec, seeder: FieldSeeder = None):
        super().__init__(spec, seeder)
        self.custom_function = load_function(self.spec.function)

    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        return self.custom_function(context, entity)

class RandomIntFieldMocker(FieldMocker):
    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        number = random.randint(self.spec.min, self.spec.max)
        rounding_base = self.spec.precision if self.spec.precision else 1
        return math.ceil(number / rounding_base) * rounding_base

class RandomDecimalFieldMocker(FieldMocker):
    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        number = (self.spec.max - self.spec.min) * random.random() + self.spec.min
        decimal_places = self.spec.precision if self.spec.precision else 3
        return Decimal(number).quantize(Decimal(10) ** (-1 * decimal_places), ROUND_HALF_UP)

class RandomFieldMocker(FieldMocker):
    def mock(self, context: MockContext, entity: MockEntity) -> Any:
        if not self.seeds:
            raise Exception(f'Seeds must be provided, field={self.spec.name}')
        return random.choice(self.seeds)

class ConstantFieldMocker(FieldMocker):
    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        if self.spec.nullable and random.random() < 0.4:
            return None
        if not self.seeds:
            raise Exception(f'Seeds must be provided, field={self.spec.name}')
        return self.seeds[context.index % len(self.seeds)]

class TimestampFieldMocker(FieldMocker):
    def __init__(self, spec: MockEntityFieldSpec, seeder: FieldSeeder = None):
        super().__init__(spec, seeder)
        now = datetime.now()
        self.min_dt = datetime.strptime(self.spec.min, self.spec.format) if self.spec.min else now - timedelta(hours=24)
        self.max_dt = datetime.strptime(self.spec.max, self.spec.format) if self.spec.max else now
        self.interval_td = self.parse_interval_dt(self.spec.interval)

    def parse_interval_dt(self, value: str) -> int:
        count = int(value[:-1])
        unit = value[-1]
        allowed_units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours'}
        return timedelta(**{allowed_units[unit]: count}) if unit in allowed_units else None
    
class RandomTimestampFieldMocker(TimestampFieldMocker):
    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        timeslots = (self.max_dt - self.min_dt) // self.interval_td
        return self.min_dt + self.interval_td * random.randint(0, timeslots)

class CurrentTimestampFieldMocker(TimestampFieldMocker):
    def mock(self, context: MockContext, entity: type[MockEntity]) -> Any:
        return datetime.now()
        