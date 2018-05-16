# Running and writing tests for **pyvas** in a virtual environment

## Preliminaries

1. Ensure that you can communicate with your instance of OpenVAS using 
the omp command line utility. 

2. Ensure that you have the **omp** command line utility installed, and
that you can connect to OpenVAS

If you haven't already done so, you can create a file 
called `~/omp.config` containing the parameters you need to connect
to OpenVAS:
 
```
host=127.0.0.1
port=9390
username=admin
password=admin
```

To test the connection, use *omp* with the *--ping* option.  If it is 
successful it will look like this:

```
anna@some-host:~$ omp --ping
OMP ping was successful.
```

If it looks like the following, you will need to check your settings, 
or whether your connection is being blocked by a firewall on the 
OpenVAS host.

```
anna@some-host:~$ omp --ping
OMP ping failed: Failed to establish connection.
```

Once you have determined the correct settings, please make a note of 
them as you will need them later.

3. Set up a virtual environment by installing `virtualenv` with your 
distribution's package manager (e.g. `apt-get` or `yum`), or using `pip3`

4. Create a `virtualenvironment` or `venv` (directory in the base of 
your pyvas directory), then create a virtual environment with the 
command:

```
mkdir /path/to/pyvas/virtualenvironment
virtualenv -p $(which python3) /path/to/pyvas/virtualenvironment
```

Be sure to add this directory to `.gitignore` in your pyvas directory,
for example:

```
# Virtual Environment
virtualenvironment/
```

5. Add the variables for connecting to OpenVAS to your virtual 
environment based on the values you determined in step 2 above:

```
cat <<EOF >> /path/to/pyvas/virtualenvironment/bin/activate
export OPENVAS_HOST=127.0.0.1 
export OPENVAS_USER=admin
export OPENVAS_PASSWORD=admin
export OPENVASMD_PORT=9390
EOF
```

6. Activate your virtual environment:

```
cd /path/to/pyvas
source virtualenvironment/bin/activate

```

7. Ensure that the following python packages are installed within your
virtual environment with pip3
  * pytest-cov
  * pytest-mock
  * lxml
  * pluggy
  * six
  * tox

## Running tests

```
cd /path/to/pyvas
python -m pytest -v
```

## Writing new tests


## Further information

* Pytest documentation - (https://docs.pytest.org/en/latest/)
* Virtualenv Tutorial - (http://www.pythonforbeginners.com/basics/how-to-use-python-virtualenv)
* OpenVAS Project OMP Documentation - (http://docs.greenbone.net/API/OMP/omp-7.0.html)


## Authors

* **Anna Langley** - *Initial work on this document* - [jal58](https://github.com/jal58)

## Acknowledgments

* Martin Picard (original developer of pyvas) - (https://github.com/mpicard)
