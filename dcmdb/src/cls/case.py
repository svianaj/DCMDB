import json
import os

from .experiment import Exp


class Case:
    def __init__(self, host, path, printlev, props, case):

        self.host, self.path, self.printlev = host, path, printlev
        self.case = case
        self.printlev = printlev

        self.data = self.load()
        self.runs = {}
        if len(props) > 1:
            for exp, val in props.items():
                if host in val:
                    try:
                        if exp not in self.data[host]:
                            self.data[host][exp] = {}
                    except KeyError:
                        self.data[host] = {}
                        self.data[host][exp] = {}
                    self.runs[exp] = Exp(
                        path, case, exp, host, printlev, val, self.data[host][exp]
                    )
        else:
            for exp, val in props.items():
                if host in val:
                    if exp not in self.data[host]:
                        self.data[host][exp] = {}
                    self.runs = Exp(
                        path, case, exp, host, printlev, val, self.data[host][exp]
                    )
        self.names = [x for x in props]

    def print(self, printlev=None):
        if printlev is not None:
            self.printlev = printlev

        if self.printlev == 0:
            print(" Runs:", self.names)
            return

        if isinstance(self.runs, dict):
            for run, exp in self.runs.items():
                exp.print(self.printlev)
        else:
            self.runs.print(self.printlev)

    def toc(self, printlev=None):
        if printlev is not None:
            self.printlev = printlev

        if isinstance(self.runs, dict):
            for run, exp in self.runs.items():
                exp.toc(self.printlev)
        else:
            self.runs.toc(self.printlev)

    def load(self):
        filename = f"{self.path}/{self.case}/data.json"
        if os.path.isfile(filename):
            with open(filename, "r") as infile:
                data = json.load(infile)
                infile.close()
        else:
            data = {}
            data[self.host] = {}
        return data

    def scan(self):
        if not self.exp_given:
            if self.data[self.host] != {}:
                self.data[self.host] = {}
                print(" rewrite data.json from scratch!")
        if isinstance(self.runs, dict):
            for name, exp in self.runs.items():
                result, signal = exp.scan()
                if signal:
                    self.data[self.host][name] = result
                else:
                    print("  no data found for", name)
        else:
            result, signal = self.runs.scan()
            if signal:
                self.data[self.host][self.names[0]] = result
            else:
                print("  no data found for", self.names)

        # Print a summary
        if self.printlev > 0:
            print(" Scan result:")
            self.print()

        self.dump()

    def dump(self):
        filename = f"{self.path}/{self.case}/data.json"
        with open(filename, "w") as outfile:
            print("  write to:", filename)
            json.dump(self.data, outfile, indent=1)
            outfile.close()

    def reconstruct(self, dtg=None, leadtime=None, file_template=None):
        res = []
        if isinstance(self.runs, dict):
            for run, exp in self.runs.items():
                res.extend(exp.reconstruct(dtg, leadtime, file_template))
        else:
            res.extend(self.runs.reconstruct(dtg, leadtime, file_template))
        return res
