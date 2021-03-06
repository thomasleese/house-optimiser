from argparse import ArgumentParser
import logging

import yaml

from .cache import Cache
from .evaluator import Evaluator
from .maps import Maps
from .objectives import Objective
from .outputs import output_html, output_plot
from .search import Query, Zoopla
from .secrets import Secrets


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('--input', '-i', help='input yaml file with search specifications')
    parser.add_argument('--secrets', '-s', help='yaml file containing passcodes and keys')
    parser.add_argument('--output', '-o', help='output file path')
    args = parser.parse_args()

    return load_yaml(args.input), load_yaml(args.secrets), args.output


def load_yaml(file_path):
    with open(file_path) as file:
        return yaml.load(file)


def main():
    input_config, secrets_config, output = parse_arguments()

    secrets = Secrets.from_config(secrets_config)
    cache = Cache()
    maps = Maps(secrets['google'], cache)
    zoopla = Zoopla(secrets['zoopla'], cache)

    query = Query.from_config(input_config['search'])

    objectives = [
        Objective.from_dict(config, maps) for config in input_config['objectives']
    ]

    listings = zoopla.search(query)

    logger.info(f'Found {len(listings)} listings.')

    evaluated_listings = Evaluator(listings, objectives)

    valid_evaluated_listings = [
        e for e in evaluated_listings if e.is_valid and e.satisfies_constaints
    ]

    logger.info(f'{len(listings)} listings satisfy the constraints.')

    output_html(secrets, valid_evaluated_listings, objectives, output)
