from pydantic import BaseModel, Field
from typing import Optional, List, Union
from enum import Enum

class RandomDecimalPrecisionType(int, Enum):
    TWO = 2
    THREE = 3

class RandomIntPrecisionType(int, Enum):
    HUNDRED = 100
    TEN = 10

class TimePrecisionType(str, Enum):
    HOUR = 'hour'
    MINUTE = 'minute'
    SECOND = 'second'

class FileFieldSeederSpec(BaseModel):
    path: str

class EntityFieldSeederSpec(BaseModel):
    name: str
    field: str

class MockEntityFieldType(str, Enum):
    custom = 'custom'
    constant = 'constant'
    current_datetime = 'current_datetime'
    random_datetime = 'random_datetime',
    random_int = 'random_int'
    random_decimal = 'random_decimal',
    random = 'random'

class MockEntityFieldSpec(BaseModel):
    name: str
    type: MockEntityFieldType
    nullable: bool = False
    min: Union[float, str] = None
    max: Union[float, str] = None
    # random/constant field
    seeds: List[Union[float, str]] = []
    seedsFromEntity: EntityFieldSeederSpec = None
    seedsFromFile: FileFieldSeederSpec = None
    # custom field
    function: str = None
    dependencies: List[str] = []
    # timestamp field
    format: str = '%Y-%m-%dT%H:%M:%S%z'
    interval: str = Field(default='1s', patten=r'[0-9]+[s|m|h]')
    # random int/decimal field
    precision: Union[RandomIntPrecisionType, RandomDecimalPrecisionType, TimePrecisionType] = None

class MockEntitySpec(BaseModel):
    name: str
    implementation: str = None
    fields: List[MockEntityFieldSpec]
    records: int = 1
    schema: str = None