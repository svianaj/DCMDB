import os

import fsspec
import tqdm
from upath import UPath


def find_files(path, prefix="", level=0, recursive=True):
    # Scan given path and subdirs and return files matching the pattern
    result = []
    try:
        protocol = UPath(path).protocol
        fs = fsspec.filesystem(protocol)
        it = fs.ls(path, detail=False, recursive=recursive)
    except OSError:
        it = []
    iterator = tqdm.tqdm(it, disable=len(it) <= 10, desc=path, position=level)
    for entry in iterator:
        entry = UPath(entry)
        if not entry.name.startswith(".") and entry.is_file():
            result.append(os.path.relpath(entry, path))
        elif not entry.name.startswith(".") and entry.is_dir() and not recursive:
            subresult = find_files(
                os.path.join(path, entry.name), prefix, level + 1, False
            )
            subresult = [entry.name + "/" + e for e in subresult]
            result.extend(subresult)
    return result


def merge_dict_items(d: dict):
    """
    Merge

    Inputs
    ------
    d: dict
        A dictionary whose first level values are dicts that shall be merged.

    Returns
    -------
    dict
        A dictionary with the first level keys dropped and their referenced dicts merged.

    Example
    -------
    >>> d = {
    ...     "a": {"b": {"c": 1}},
    ...     "x": {"b": {"c": 2}},
    ...     "y": {"d": {"c": 3}},
    ... }
    >>> merge_dict_items(d)
    {'b': {'c': 2}, 'd': {'c': 3}}
    """
    merged_dict = {}
    for key in d:
        for sub_dict in d[key]:
            if sub_dict in merged_dict:
                merged_dict[sub_dict].update(d[key][sub_dict])
            else:
                merged_dict[sub_dict] = d[key][sub_dict]
    return merged_dict
