from em.entity.entities import (
    SeedEntity
)

from em.entity.specs import (
    EntityFieldSeederSpec,
    FileFieldSeederSpec
)

from typing import List, Any
from abc import ABC, abstractmethod

class FieldSeeder(ABC):
    @abstractmethod
    def get_seeds(self) -> List[Any]:
        raise NotImplementedError()

class EntityFieldSeeder(FieldSeeder):
    def __init__(self, spec: EntityFieldSeederSpec, entity: type[SeedEntity]) -> None:
        self.spec = spec
        self.entity = entity
        self.cached_seeds = []

    def get_seeds(self) -> List[Any]:
        if not self.cached_seeds:
            self.cached_seeds = self.entity.get_seeds(self.spec.field)
        return self.cached_seeds
    
class FileFieldSeeder(FieldSeeder):
    def __init__(self, spec: FileFieldSeederSpec) -> None:
        self.spec = spec
    
    def get_seeds(self) -> List[Any]:
        return []