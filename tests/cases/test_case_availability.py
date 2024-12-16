"""
Test the availability of archived cases.
"""

import argparse

import fsspec
import tqdm
from upath import UPath

from dcmdb.src.collection import collect_cases, generate_experiments


def file_exists(path: str) -> bool:
    p = UPath(path)
    protocol = p.protocol
    fs = fsspec.filesystem(protocol)
    return fs.exists(path)


def check(path: str, selection: str = None) -> None:
    cases = collect_cases(path=path, selection=selection)
    experiments = generate_experiments(cases)
    files_to_test = 1

    experiments_w_fileissues = []
    for exp in tqdm.tqdm(experiments):
        for fname in exp.file_templates:
            if fname in exp.data:
                content = exp.data[fname]  # Leadtimes
                dates = [d for d in sorted(content)]
                files_to_scan = exp.reconstruct(dates[-1], file_template=fname)
                for file_to_scan in files_to_scan[:files_to_test]:
                    exists = file_exists(file_to_scan)
                    if not exists:
                        experiments_w_fileissues.append([exp.name, file_to_scan])
                        break
    if len(experiments_w_fileissues) > 0:
        error_messages = [
            f"Files of {exp} like {fname} not found/accessible. Check path and access rights (also of parent folders).\n"
            for exp, fname in experiments_w_fileissues
        ]
        raise FileNotFoundError("\n----\n".join(set(error_messages)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test the availability of archived cases."
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="Path to the cases directory. Use subdirecotires for specific cases.",
        default="cases/",
    )
    parser.add_argument(
        "-s", "--selection", type=str, help="List of cases to test.", default=None
    )
    args = parser.parse_args()

    check(args.path, args.selection)
