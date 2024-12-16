"""Wrapper around eccodes python API to mimic eccodes CLI tools"""

import eccodes
import fsspec


def grib_ls(filepath, parameters, output_format="json"):
    results = []
    with fsspec.open(filepath, "rb").open() as f:
        while True:
            gid = eccodes.codes_grib_new_from_file(f)
            if gid is None:
                break
            message = {}
            for param in parameters:
                try:
                    value = eccodes.codes_get(gid, param)
                    message[param] = value
                except eccodes.CodesInternalError:
                    print(f"Parameter '{param}' not found in the GRIB file.")
            results.append(message)
            eccodes.codes_release(gid)
    if output_format == "json":
        return {"messages": results}

    return results
