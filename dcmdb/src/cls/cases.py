#!/usr/bin/env python3

import os
import re
import subprocess
import sys

import yaml

from ..ecfs import ecfs_copy
from ..helpers import find_files
from .case import Case


class Cases:
    def __init__(self, names=None, path=None, printlev=None, host=None, selection=None):

        self.path = path if path is not None else "cases"
        self.printlev = printlev if printlev is not None else 1
        self.host = host if host is not None else self.get_hostname()
        self.selection = selection if selection is not None else {}

        if isinstance(self.selection, dict):
            self.exp_given = False
            for k, v in self.selection.items():
                self.exp_given = len(v) > 0 or self.exp_given
        if isinstance(self.selection, str):
            self.selection = [self.selection]
        if isinstance(self.selection, list):
            self.exp_given = False
            self.selection = {k: [] for k in self.selection}

        if names is None:
            if self.selection is not None:
                self.names = list(self.selection.keys())
            else:
                self.names = []
        elif isinstance(names, str):
            self.names = [names]
        else:
            self.names = names

        self.cases, self.names, self.meta = self.load_cases()

        self.domains = {}
        for k, v in self.meta.items():
            self.domains[k] = {}
            for x, y in v.items():
                self.domains[k][x] = y["domain"]

        if len(self.names) == 0:
            print("No cases found")
            print(
                "Available cases:",
                [
                    x.split("/")[0]
                    for x in find_files(self.path, "meta.yaml", recursive=False)
                ],
            )
            sys.exit()

    def get_hostname(self):

        import socket

        host = socket.gethostname()
        if re.search(r"^a(a|b|c|d)", host):
            return "atos"

        return None

    def scan(self):
        if isinstance(self.cases, dict):
            for case in self.cases:
                self.cases[case].scan()
        else:
            self.cases.scan()

    def load_cases(self):
        def intersection(lst1, lst2):
            lst3 = [value for value in lst1 if value in lst2]
            lst4 = [value for value in lst1 if value not in lst3]
            return lst3, lst4

        meta_file = "meta.yaml"
        case_list = [
            x.split("/")[0] for x in find_files(self.path, meta_file, recursive=False)
        ]
        if self.names is not None:
            if len(self.names) > 0:
                case_list, missing = intersection(self.names, case_list)
                if len(missing) > 0:
                    print("\nCould not find cases:", missing, "\n")

        if len(case_list) == 0:
            return {}, [], {}

        res = {}
        mm = {}
        for x in case_list:
            p = "{}/{}/{}".format(self.path, x, meta_file)
            meta = yaml.safe_load(open(p))
            if x in self.selection:
                y = self.selection[x]
                if isinstance(y, str):
                    y = [y]
                if len(y) > 0:
                    exp_list, missing = intersection(y, meta.keys())
                    if len(missing) > 0:
                        print("\nCould not find exp:", missing, "\n")
                    meta = {k: v for k, v in meta.items() if k in exp_list}

            mm[x] = meta
            res[x] = Case(self.host, self.path, self.printlev, meta, x)
            res[x].exp_given = self.exp_given

        if self.printlev > 0:
            print("Loaded:", case_list)

        return res, case_list, mm

    def show(self):

        for case, body in self.cases.items():
            print("\nCase:", case)
            print("   ", body)

    def print(self, printlev=None):

        if printlev is not None:
            self.printlev = printlev

        if self.printlev < 0:
            print("Cases:", self.names)
            return

        if isinstance(self.cases, dict):
            for name, case in self.cases.items():
                print("\nCase:", name)
                case.print(self.printlev)
        else:
            self.cases.print(self.printlev)

    def toc(self, printlev=None):

        if printlev is not None:
            self.printlev = printlev

        if isinstance(self.cases, dict):
            for name, case in self.cases.items():
                print("\nCase:", name)
                case.toc(self.printlev)
        else:
            self.cases.toc(self.printlev)

    def reconstruct(self, dtg=None, leadtime=None, file_template=None):

        res = []
        if isinstance(self.cases, dict):
            for name, case in self.cases.items():
                res.extend(case.reconstruct(dtg, leadtime, file_template))
        else:
            res.extend(self.cases.reconstruct(dtg, leadtime, file_template))

        return res

    def get(self, files=[], outpath="."):
        clean = True
        for f in files:
            if re.match("^ec", f):
                ecfs_copy(f, outpath, self.printlev)
            else:
                try:
                    os.symlink(f, os.path.join(outpath, os.path.basename(f)))
                except FileExistsError:
                    clean = False

        return clean

    def clean(self, files=[], outpath="."):

        for fname in files:
            f = os.path.join(outpath, os.path.basename(fname))
            os.remove(f)
            print("  remove:", f)

    def check_remote(self, files=[], remote=None):

        bare_files = [os.path.basename(x) for x in files]
        listcmd = ["ssh", remote["host"], "ls", "-1", remote["outpath"]]
        cmd = subprocess.Popen(listcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_out, cmd_err = cmd.communicate()
        if cmd_out is not None:
            for line in cmd_out.splitlines():
                fname = line.decode("utf-8")
                try:
                    i = bare_files.index(fname)
                    bare_files.pop(i)
                except ValueError:
                    pass

        return bare_files

    def transfer(self, files=[], outpath=".", remote=None):

        os.makedirs(outpath, exist_ok=True)
        missing_files = self.check_remote(files, remote)

        if len(missing_files) > 0:
            nfiles = len(missing_files)
            print(f"  Transfer {nfiles} files this date")
            clean = self.get(files, outpath)
            cmd = 'ssh {} "mkdir -p {}"'.format(remote["host"], remote["outpath"])
            print(cmd)
            os.system(cmd)
            rhost = remote["host"]
            rpath = remote["outpath"]
            cmd = f"rsync -vaux --copy-unsafe-links {outpath}/ {rhost}:{rpath}/"
            print(cmd)
            os.system(cmd)
            if clean:
                self.clean(files, outpath)
        else:
            nfiles = len(files)
            print(f"  all {nfiles} files already in place for this date")
            if self.printlev > 0:
                print(files)
