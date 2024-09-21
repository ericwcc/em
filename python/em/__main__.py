import yaml
import os
import graphlib
from loguru import logger
from typing import List, Dict, Set
import argparse
import sys

from em.entity.seeders import (
    FieldSeeder,
    EntityFieldSeeder,
    FileFieldSeeder
)

from em.entity.entities import (
    MockEntity,
    PostgresMockEntity,
    PostgresSeedEntity
)

from em.entity.mockers import (
    FieldMocker,
    CurrentDateTimeFieldMocker,
    RandomDateTimeFieldMocker,
    CustomFieldMocker,
    RandomDecimalFieldMocker,
    RandomIntFieldMocker,
    ConstantFieldMocker,
    RandomFieldMocker
)

from em.entity.mockers import EntityMocker
from em.utils.import_utils import load_class

from em.entity.specs import (
    Spec,
    MockEntitySpec,
    MockEntityFieldSpec,
    SpecType,
    ScenarioSpec,
)

def main(**kwargs):
    if not kwargs['debug']:
        logger.remove(0)
        logger.add(sys.stderr, level='INFO')
    
    input_files = kwargs['input_file'] + [ os.path.join(root, file) for root, _, files in os.walk(kwargs['input_dir']) for file in files ]
    input_files = set(input_files)

    if len(input_files) == 0:
        raise Exception(f'input files must be specified with --input_dir or --input_file')

    scenario_specs: Dict[str, ScenarioSpec] = {}

    entity_specs: Dict[str, MockEntitySpec] = {}
    entity_deps: Dict[str, Set[str]] = {}

    # parse input files
    for input_file in input_files:
        # skip non yaml files
        if not input_file.lower().endswith(('yaml', 'yml')):
            continue
        # check if file
        if not os.path.isfile(input_file):
            logger.error(f'Input must be a file, path={input_file}')
            continue
        # load yaml
        with open(input_file) as f:
            input_data = yaml.safe_load(f)
        
        spec = Spec(**input_data)
        if spec.kind == SpecType.SCENARIO:
            scenario_spec = spec.spec
            scenario_specs[scenario_spec.name] = scenario_spec
        elif spec.kind == SpecType.ENTITY:
            # convert yaml to pydantic
            entity_spec = spec.spec
            entity_specs[entity_spec.name] = entity_spec
            # build entity_deps
            entity_deps[entity_spec.name] = { field_spec.seedsFromEntity.name for field_spec in entity_spec.fields if field_spec.seedsFromEntity }

    logger.info(f'Loaded {len(scenario_specs)} scenarios and {len(entity_specs)} entities, scenarios={list(scenario_specs.keys())}, entities={list(entity_specs.keys())}')
    
    entity_impls: Dict[str, type[MockEntity]] = {}

    # build entity mockers
    entity_top_sorter = graphlib.TopologicalSorter(entity_deps)
    sorted_entity_specs = [ entity_specs[entity_name] for entity_name in entity_top_sorter.static_order() if entity_name in entity_specs ]
    entity_mockers: List[EntityMocker] = []
    for entity_spec in sorted_entity_specs:
        # build entity implementation
        entity_impl_klass = load_class(entity_spec.implementation, MockEntity)
        entity_impl = entity_impl_klass(entity_spec)

        field_mocker_klasses: Dict[str, type[FieldMocker]] = {
            'custom': CustomFieldMocker,
            'constant': ConstantFieldMocker,
            'random': RandomFieldMocker,
            'random_int': RandomIntFieldMocker,
            'random_decimal': RandomDecimalFieldMocker,
            'current_datetime': CurrentDateTimeFieldMocker,
            'random_datetime': RandomDateTimeFieldMocker
        }

        field_specs: Dict[str, MockEntityFieldSpec] = { field_spec.name: field_spec for field_spec in entity_spec.fields }
        
        # build field deps
        field_deps = { field_spec.name: set(field_spec.dependencies) for field_spec in entity_spec.fields }
        field_top_sorter = graphlib.TopologicalSorter(field_deps)
        sorted_field_specs = [ field_specs[field_name] for field_name in field_top_sorter.static_order() if field_name in field_specs ]

        # build field mockers
        field_mockers = []
        for field_spec in sorted_field_specs:
            seeder: type[FieldSeeder] = None

            if field_spec.seedsFromEntity:
                # build seed entity impl
                seed_entity_name = field_spec.seedsFromEntity.name
                if seed_entity_name in entity_impls:
                    seed_entity_impl = entity_impls[seed_entity_name]
                elif issubclass(entity_impl_klass, PostgresMockEntity):
                    seed_entity_impl = PostgresSeedEntity(field_spec.seedsFromEntity.name, entity_spec.schema)
                    entity_impls[seed_entity_name] = seed_entity_impl
                # build entity seeder
                seeder = EntityFieldSeeder(field_spec.seedsFromEntity, seed_entity_impl)

            if field_spec.seedsFromFile:
                # build file seeder
                seeder = FileFieldSeeder(field_spec.seedsFromFile)

            field_mocker = field_mocker_klasses[field_spec.type](field_spec, seeder)
            field_mockers.append(field_mocker)

        entity_mocker = EntityMocker(entity_spec, entity_impl, field_mockers)
        entity_mockers.append(entity_mocker)

    # start mock
    scenario_name = kwargs['scenario']
    if len(scenario_specs) == 0:
        for entity_mocker in entity_mockers:
            entity_mocker.load_entity_records()
            entity_mocker.mock(1)
    elif scenario_name:
        scenario_spec = scenario_specs[scenario_name]
        scenario_entity_specs = { scenario_entity_spec.name: scenario_entity_spec for scenario_entity_spec in scenario_spec.entities }
        
        # check if all entities in the scenario are known
        unknown_entity_names = scenario_entity_specs.keys() - entity_specs.keys()
        if unknown_entity_names:
            raise Exception(f'Entity specs must be provided, names={list(unknown_entity_names)}')
        
        logger.info(f'Run scenario, name={scenario_name}')
        for entity_mocker in entity_mockers:
            scenario_entity_spec = scenario_entity_specs.get(entity_mocker.entity_spec.name)
            if scenario_entity_spec:
                entity_mocker.load_entity_records()
                entity_mocker.mock(scenario_entity_spec)
    else:
        raise Exception(f'A scenario must be specified with --scenario, scenarios={list(scenario_specs.keys())}')

parser = argparse.ArgumentParser(description='Mock database data')
parser.add_argument('--debug', action='store_true', help='Enable debug log')
parser.add_argument('--input_dir', type=str, default='input', required=False, help='Directory that contains input yaml files')
parser.add_argument('--input_file', type=str, action='append', default=[], help='Yaml file')
parser.add_argument('--scenario', type=str, default=None, required=False, help='Scenario')

args = parser.parse_args()
args_dict = vars(args)
logger.info(f'Loaded input arguements, arguements={args_dict}')
try:
    main(**args_dict)
except KeyboardInterrupt:
    logger.info('Execution interrupted by user')