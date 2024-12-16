"""
Functions for collecting information about all cases in the database.
"""

from pathlib import Path
from typing import Generator, List, Union

from dcmdb.src.cls.case import Case
from dcmdb.src.cls.cases import Cases
from dcmdb.src.cls.experiment import Exp


def collect_cases(
    selection: Union[dict, list] = [],
    path: Union[Path, str, None] = "../../cases",
    host: Union[str, None] = None,
) -> List[Case]:
    """
    Collects all cases from the database.

    Returns:
        List[Case]: List of all cases in the database.
    """
    myc = Cases(
        selection=selection,
        path=path,
        host=host,
    )

    return myc


class NoExperimentsGivenError(Exception):
    pass


def generate_experiments(cases: Cases) -> Generator[Exp, None, None]:
    """
    Extract experiments/runs from Cases.

    Args:
        cases (Cases): Cases object.

    Yields:
        Experiment: An experiment/run from the Cases object.
    """
    for name, case in cases.cases.items():
        if isinstance(case.runs, dict):
            for exp_name, experiment in case.runs.items():
                yield experiment
        elif isinstance(case.runs, Exp):
            yield case.runs
        else:
            raise NoExperimentsGivenError(
                f"No experiments given for case {name}, experiment {exp_name}. Please provide experiments."
            )


if __name__ == "__main__":
    cases = collect_cases()
    # do something with the cases
