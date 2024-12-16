import glob
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import fsspec
import gribscan
from upath import UPath

from ..eccodes_helpers import grib_ls
from ..ecfs import ecfs_list
from ..helpers import find_files, merge_dict_items
from ..referencing import combine_joined_reference_parquet, export_dict_to_parq
from ..timehandling import hub, leadtime2hm, simulation_datetime

ECCODES_DEFINITIONS_PATH = gribscan.eccodes.codes_definition_path()
ECCODES_DEODE_DEF_PATH = Path(__file__).parent.parent / "eccodes" / "definitions"
ECCODES_DEFINITIONS_PATH = f"{ECCODES_DEODE_DEF_PATH}:{ECCODES_DEFINITIONS_PATH}"
gribscan.eccodes.codes_set_definitions_path(ECCODES_DEFINITIONS_PATH)


class Exp:
    def __init__(self, path, case, name, host, printlev, val, data):

        self.path = path
        self.case = case
        self.name = name
        self.host = host
        self.printlev = printlev
        self.file_templates = val["file_templates"]
        self.path_template = val[host]["path_template"]
        self.domain = val["domain"]
        self.data = data

    def check_template(self, x):

        known_keys = {
            "%Y": 4,  # Year
            "%m": 2,  # Month
            "%d": 2,  # Day
            "%H": 2,  # Hour
            "%M": 2,  # Minute
            "*": 0,  # Wildcard
            "%LM": 2,  # Leadtime in minutes
            "%LLLL": 4,  # Leadtime in hours
            "%LLL": 3,  # Leadtime in hours
            "%LL": 2,  # Leadtime in hours
        }

        mapped_keys = {}
        replace_keys = {}
        y = x
        for k, v in known_keys.items():
            kk = k
            if "%" in k:
                s = f"(\\d{{{v}}})"
            if "*" in k:
                s = "(.*)"
                kk = r"\*"
            if "+" in k:
                s = r"\+"

            mm = [m.start() for m in re.finditer(kk, x)]
            y = y.replace(k, s)
            if len(mm) > 0:
                mapped_keys[k] = mm[0]
                replace_keys[k] = s
                if k in ["%LLLL", "%LLL", "%LL"]:
                    break

        mk = dict(sorted(mapped_keys.items(), key=lambda item: item[1]))

        y = y.replace("+", r"\+")

        return y, mk, replace_keys

    def reconstruct(self, dtg=None, leadtime=None, file_template=None):
        """
        Reconstruct filenames based on file_template

        Inputs
        ------
        dtg : list
            Dates to apply to file_template
        leadtime : list
            List of lead times to apply to file_template
        file_template : str
            File format string

        Returns
        -------
        list of filenames
        """

        def matching(files, src):
            res = []
            for f in files:
                for x in src:
                    if f == x:
                        res.append(f)
                    else:
                        m = re.fullmatch(f, x)
                        if m is not None:
                            res.append(m.group(0))

            return res

        if file_template is None:
            files = self.file_templates
        else:
            files = [file_template]

        result = []
        for file in matching(files, self.data.keys()):
            if dtg is None or dtg == []:
                dtgs = list(self.data[file].keys())
            else:
                if isinstance(dtg, str):
                    dtgs = [dtg]
                else:
                    dtgs = dtg

            for ddd in dtgs:
                if ddd in self.data[file]:
                    if leadtime is None or leadtime == []:
                        leadtimes = self.data[file][ddd]
                    else:
                        if isinstance(leadtime, list):
                            leadtimes = [x for x in leadtime]
                        else:
                            leadtimes = [leadtime]

                    result.extend(
                        [
                            hub(f"{self.path_template}/{file}", ddd, l)
                            for l in leadtimes
                            if l in self.data[file][ddd]
                        ]
                    )

        return result

    def print(self, printlev=None):
        if printlev is not None:
            self.printlev = printlev
        print("\n ", self.name)
        print("   File templates:", self.file_templates)
        print("   Path template :", self.path_template)
        print("   Domain:", self.domain)
        for fname in self.file_templates:
            if fname in self.data:
                content = self.data[fname]
                dates = [d for d in sorted(content)]
                print("   File:", fname)
                if self.printlev < 2:
                    print("    Dates:", dates[0], "-", dates[-1])
                    if content[dates[0]][0] is None:
                        print("    No leadtime information available")
                    else:
                        maxlist = []
                        minlist = []
                        for date, leadtimes in sorted(content.items()):
                            maxlist.append(max(leadtimes))
                            minlist.append(min(leadtimes))
                        lhs, lms = leadtime2hm(min(minlist))
                        lhe, lme = leadtime2hm(max(maxlist))
                        print(
                            "    Leadtimes:{:02d}h{:02d}m - {:02d}h{:02d}m".format(
                                lhs, lms, lhe, lme
                            )
                        )
                elif self.printlev < 3:
                    if content[dates[0]][0] is not None:
                        for date, leadtimes in sorted(content.items()):
                            lhs, lms = leadtime2hm(leadtimes[0])
                            lhe, lme = leadtime2hm(leadtimes[-1])
                            print(
                                "    {} : {:02d}h{:02d}m - {:02d}h{:02d}m".format(
                                    date, lhs, lms, lhe, lme
                                )
                            )
                    else:
                        for date in sorted(dates):
                            print("    ", date)
                elif self.printlev > 2:
                    if content[dates[0]][0] is not None:
                        for date, leadtimes in sorted(content.items()):
                            print("   ", date, ":")
                            x = leadtimes[0]
                            fh, lm = leadtime2hm(x)
                            txt = "       {:02d}h : {:02d}".format(fh, lm)
                            for x in leadtimes[1:]:
                                lh, lm = leadtime2hm(x)
                                if lh == fh:
                                    txt += ",{:02d}".format(lm)
                                else:
                                    print(txt + "m")
                                    txt = "       {:02d}h : {:02d}".format(lh, lm)
                                    fh = lh
                            print(txt + "m")

                if self.printlev > 1:

                    if content[dates[0]][0] is None:
                        example = self.reconstruct(dates[0], file_template=fname)
                    else:
                        example = self.reconstruct(
                            dates[0], content[dates[0]][-1], fname
                        )
                    print("    Example:", example)
                    if re.match("^ec", example[0]):
                        if self.printlev > 2:
                            print("Checking", example[0])
                        listing = ecfs_list(example[0], detail=True)

                        if listing is not None:
                            for line in listing:
                                if "msdeode" not in line:
                                    print(
                                        "ERROR:Wrong group for",
                                        self.case,
                                        ":",
                                        self.name,
                                        line,
                                    )

    def build_toc(
        self,
        file_template,
        files_to_scan,
        gribref=False,
        level_dimension="*",
        toc_filetype="json",
    ):

        isgrib, issfx, grib_version = self.check_file_type(file_template)
        reference_filefmt = (
            f"{self.path}/{self.case}/{self.name}_{file_template}_"
            + "{level_dimension}.refs.{toc_filetype}"
        )

        reference_files = glob.glob(
            reference_filefmt.format(
                level_dimension=level_dimension, toc_filetype=toc_filetype
            )
        )
        if len(reference_files) > 1:
            # Local references exist and can be loaded
            if self.printlev > 0:
                print(f"Found local references: {' ,'.join(reference_files)}")
        else:
            print("No local references found. Creating them now.")
            if isgrib:
                print(f"Create references for {file_template}")

                if isinstance(files_to_scan, str):
                    files_to_scan = [files_to_scan]

                file_references = {}
                for file_to_scan in files_to_scan:
                    if self.printlev > 0:
                        print(" scanning", file_to_scan)

                    # Test if file exists (UPath().exists() is not implemented)
                    p = UPath(file_to_scan)
                    protocol = p.protocol
                    fs = fsspec.filesystem(protocol)
                    file_exists = fs.exists(file_to_scan)
                    if not file_exists:
                        print(f"File {file_to_scan} does not exist.")
                        raise FileNotFoundError(
                            f"File {file_to_scan} does not exist. Abort indexing for {file_template}."
                        )

                    if gribref:
                        with tempfile.NamedTemporaryFile() as idxfile:
                            gribscan.write_index(
                                gribfile=file_to_scan,
                                idxfile=Path(idxfile.name),
                                force=True,
                            )
                            magician = gribscan.magician.HarmonieMagician()
                            refs = gribscan.grib_magic(
                                filenames=[idxfile.name],
                                magician=magician,
                                global_prefix="",
                            )
                            file_references[os.path.basename(file_to_scan)] = refs
                    else:
                        json_filename = (
                            f"{self.path}/{self.case}/{self.name}_{file_template}.json"
                        )
                        if issfx and grib_version == 1:
                            parameters = [
                                "indicatorOfParameter",
                                "level",
                                "typeOfLevel",
                                "timeRangeIndicator",
                            ]
                        elif grib_version == 1:
                            parameters = [
                                "indicatorOfParameter",
                                "level",
                                "typeOfLevel",
                                "timeRangeIndicator",
                                "shortName",
                            ]
                        elif grib_version == 2:
                            parameters = [
                                "discipline",
                                "parameterCategory",
                                "parameterNumber",
                                "level",
                                "typeOfLevel",
                                "stepType",
                                "shortName",
                            ]
                        if p.protocol == "ec" or p.protocol == "ectmp":
                            # Copy the file to a local directory as eccodes API cannot handle byte streams (e.g. accesses fileno operation)
                            fs = fsspec.filesystem(p.protocol)
                            lpath = UPath(os.path.join(fs.ec_cache, p.path.strip("/")))
                            if not os.path.exists(lpath):
                                # Trigger copy from ECFS to local cache
                                p.open().seek(0)
                            p = lpath
                        param_vals = grib_ls(p, parameters)
                        with open(json_filename, "w") as f:
                            json.dump(param_vals, f, indent=2)
                        break  # only scan the file of the first timestep

                    # TODO: Delete the local copy of the file after scanning if it is an ecfs file

                if gribref:
                    # Merge all references into a single file (per height dimension)
                    level_dims = set().union(
                        *[reference.keys() for reference in file_references.values()]
                    )

                    for level_dim in level_dims:
                        level_refs = [
                            reference[level_dim]
                            for reference in file_references.values()
                        ]
                        # TODO: Do we know the times at this point? Can we pass them to the combine function?
                        filename = reference_filefmt.format(
                            level_dimension=level_dim, toc_filetype=toc_filetype
                        )
                        combined_refs = combine_joined_reference_parquet(level_refs)
                        if toc_filetype == "json":
                            with open(filename, "w") as outfile:
                                json.dump(combined_refs, outfile)
                        elif toc_filetype == "parquet":
                            export_dict_to_parq(combined_refs, filename)
            else:
                raise NotImplementedError("Only grib files can be indexed.")
        os.environ["ECCODES_DEFINITION_PATH"] = f"{self.edp}"

    def check_file_type(self, infile):

        isgrib = True
        issfx = False
        grib_version = -1

        self.edp = ECCODES_DEFINITIONS_PATH

        if "ICMSH" in infile:
            isgrib = False
        elif "sfx" in infile:
            issfx = True
            grib_version = 1
        elif "grib2" in infile:
            grib_version = 2
            os.environ["ECCODES_DEFINITION_PATH"] = (
                f"{os.getcwd()}/eccodes/definitions:{self.edp}"
            )
            if self.printlev > 1:
                print(
                    f" Update ECCODES_DEFINITION_PATH:{os.environ['ECCODES_DEFINITION_PATH']}"
                )
        elif "grib" in infile:
            grib_version = 1
        elif "GRIBPF" in infile:
            grib_version = 2
        elif ".grb2" in infile:
            grib_version = 2
        else:
            print(f"Cannot recognize {infile}")
            sys.exit()

        return isgrib, issfx, grib_version

    def toc(self, printlev=None):
        """
        Create TOC of most recent output file for each file_template
        """
        if printlev is not None:
            self.printlev = printlev
        for fname in self.file_templates:
            if fname in self.data:
                content = self.data[fname]  # Leadtimes
                dates = [d for d in sorted(content)]
                files_to_scan = self.reconstruct(dates[-1], file_template=fname)

                try:
                    self.build_toc(fname, files_to_scan)
                except NotImplementedError as e:
                    print(f"TOC for {fname} failed: {e}")

    def scan(self):

        print(" scan:", self.name)

        def subsub(path, subdirs, replace_keys):
            def pdir(x, replace_keys):
                y = x
                for k, v in replace_keys.items():
                    if k in y:
                        y = y.replace(k, v)
                return y

            result = []
            content = ecfs_list(path)
            for cc in content:
                pp = pdir(subdirs[0], replace_keys)
                mm = [m.start() for m in re.finditer(pp, cc)]
                if len(mm) > 0:
                    if len(subdirs) > 1:
                        subresult = subsub(path + cc, subdirs[1:], replace_keys)
                    else:
                        subresult = [path + cc]
                    result.extend(subresult)

            return result

        print(
            "  Search for files named {} in {}".format(
                self.file_templates, self.path_template
            )
        )

        # TODO: this needs to go into the constructor
        if isinstance(self.path_template, str):
            self.path_template = [self.path_template]

        findings = {}
        signal = True

        for path_template in self.path_template:
            i = path_template.find("%")
            base_path = path_template[:i] if i > -1 else path_template
            part_path = path_template[i:] if i > -1 else ""

            # Fix for path_templates without date directives (e.g. %Y/%m/%d) (Issue #28)
            # Assuming dateformat is %Y/%m/%d
            res = re.search(r"\d{4}/\d{2}/\d{2}", base_path)
            if res is not None:
                ymd = res.group()
                date = simulation_datetime.strptime(ymd, "%Y/%m/%d")
            else:
                date = None

            content = find_files(base_path)

            for file_template in self.file_templates:
                tmp = {}
                partial_path_format = os.path.join(part_path, file_template)
                for partial_path in content:
                    try:
                        dt = simulation_datetime.strptime(
                            partial_path, partial_path_format
                        )
                        if date is not None:
                            dt = dt.replace(
                                year=date.year, month=date.month, day=date.day
                            )
                    except ValueError:
                        # TODO: content contains all files even those not matching file_template
                        continue
                    dtg = dt.strftime("%Y-%m-%d %H:%M:%S")
                    if dtg not in tmp:
                        tmp[dtg] = []
                    tmp[dtg].append(int(dt.leadtime.total_seconds()))

                for k in tmp:
                    tmp[k].sort()

                signal = signal and bool(tmp)
                findings[path_template] = findings.get(path_template, {})
                findings[path_template].update({file_template: tmp})

                merged_findings = merge_dict_items(findings)

        return merged_findings, signal
