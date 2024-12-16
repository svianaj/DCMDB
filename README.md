# The DE_330 case meta database

[![case_availability.yaml](https://github.com/destination-earth-digital-twins/dcmdb/actions/workflows/case_availability.yaml/badge.svg)](https://github.com/destination-earth-digital-twins/dcmdb/actions/workflows/case_availability.yaml)

## Introduction

`dcmbd` is an attempt to bring some order in the output from the case studies performed within DE_330. The initial cases will be done with different setup using different name conventions and the idea is to handle these differences in an organized manner. The meta database consists of metadata for individual cases along with data availibility information. The aim is to allow an easy access to data without having to worry to much about the location. 

## The metadata

### The user provided metadata

For each case we suggest to create a directory under `cases`. Pick a name that is descriptive and unique enough. In a file called meta.yaml we introduce

``` yaml
mcp43h2_prod: 

  file_templates : ['fc%Y%m%d%H+%LLLgrib_sfxs','fc%Y%m%d%H+%LLLh%LMmgrib2_fp','PFDEODE+%LLLL:%LM:00']

  atos:
     path_template : 'ec:/snh/harmonie/mcp43h2_prod/%Y/%m/%d/%H/mbr000/'

  domain : 
     name : 'METCOOP25D'
     resolution : 2500
     levels : 65
```

where 
 * the top level is the experiment name or similar
 * `file_templates` describes the files of interest. Note that date/time information is parameterized using standard linux/python notation. Note that we are mainly interested in the GRIB files here, so list those.
 * `atos` here tells us where the data is located. For the future we could consider lumi and other hosts as well
 * `path_template` the search path for the data, note that ECFS notation is supported.
 * `domain` gives some information about the domain used. Could contain geometry information as well.

The available wild cards are used above are 
 * %Y,%m,%d,%H,%M,%S for year, month, day, hour, minute, second respectively
 * %LLL, %LLLL for forecast legth in hours (3,4) length
 * %LM for forecast length in minutes in combination with hours
 * %* any character
 
In each `meta.yaml` file we may specify an arbitrary number of experiments/runs. Please repeat the above mentioned for each run. The data section, `data.json`, should be generated, not manually edited. Instructions for how the generation is done is found further down.

### The generated metadata

We generate two types of metadata files for each run.
 * data.json where all information about periods and forecast lengths are found for each file type.
 * {run}_{file_template}.json which contains a table of content for each GRIB filetype to allow a quick search without having to open a file.
 
## The python support tools

A module and a command line tool has been created to support inspection of the case content and recounstruction of file paths. The yaml files of course could be accessed from other languages such as R or julia as well.

### Command line tool

#### Installation
```
pip install git+https://github.com/destination-earth-digital-twins/dcmdb@develop
```

#### Usage

Running `dcmdb chase` will show some options. Assuming we're running on atos list cases and their content is done by 
```
dcmdb chase -list 
```
where more options can be added. Add a few `-v` or `-s` to see more/less information.

##### Generate the data availability information

For a newly added case the data part has to be benerated running
```
dcmdb chase -scan -case MYCASE [ -exp MYEXP ]
```
This will generate the file `cases/MYCASE/data.json` containing all dates and leadtimes (in seconds) for the given files. Default is to scan all experiments within a case, give MYEXP to just updated a single run. Note that scanning ECFS may take some minutes. Check the result by

```
dcmdb chase -list -case MYCASE [ -exp MYEXP ] -v -v 
```
Run without [ -exp MYEXP ] if you have stored multiple exp's in meta.yaml:

```
dcmdb chase -scan -case MYCASE -v -v
```
To generate the table of content for each file_template run, in the same way as for the scanning:
```
dcmdb chase -toc [-case MYCASE -v -v]
```

Don't forget to commit the new json files to the repo after you've created or updated them. Make sure to only commit to the develop branch.

### The python module

The file `cases.py` contains some methods to access information and reconstruct file names.

## Caveats

This is still work in progess and the usefulness still to be proven. At the moment leadtimes in subhourly format is not yet handled.

