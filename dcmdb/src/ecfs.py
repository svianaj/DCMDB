"""
ECMWF file storage (ECFS) operation wrappers.
"""

import subprocess


def ecfs_copy(infile, outfile, printlev=0):

    args = ["ecp", infile, outfile]
    if printlev > 0:
        print(" " + " ".join(args))
    cmd = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_out, cmd_err = cmd.communicate()

    if cmd_err is not None and cmd_err != b"":
        res = cmd_err.decode("utf-8")
        print(res)
        return False
    else:
        return True


def ecfs_list(path, detail=False):
    if detail:
        cmd_parts = ["els", "-l", path]
    else:
        cmd_parts = ["els", path]
    cmd = subprocess.Popen(cmd_parts, stdout=subprocess.PIPE)
    cmd_out, cmd_err = cmd.communicate()

    if cmd_err is not None:
        if len(cmd_err) > 0:
            res = cmd_err.decode("utf-8")
            raise OSError(res)

    # Decode and filter output
    res = [line.decode("utf-8") for line in cmd_out.splitlines()]
    return res
