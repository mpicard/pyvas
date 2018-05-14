# Running and writing tests for pyvas

## Preliminaries

* Ensure that you can communicate with your instance of OpenVAS using the omp
command line utility.
* Ensure that the following python packages are installed with pip3
  - pytest
  - pytest-cov
  - pytest-mock

## Environment

The following shell environment variables need to be set in order that
your script will communicate with your instance of OpenVAS:
* `OPENVAS_HOST`
* `OPENVAS_USER`
* `OPENVAS_PASSWORD`
* `OPENVASMD_PORT` N.B. Defined in `client.py` to default to 9390, if not set

## Running tests
```
cd pyvas
python3 -m pytest
```

## Writing new tests

## Authors

* **Anna Langley** - *Initial work on this document* - [jal58](https://github.com/jal58)

## Acknowledgments

* OpenVAS Project OMP Documentation - (http://docs.greenbone.net/API/OMP/omp-7.0.html)
* Martin Picard - [mpicard](https://github.com/mpicard)
