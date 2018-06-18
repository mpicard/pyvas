# How to get OpenVAS to communicate with both OMP and its web interface

It can be challenging to set up OpenVAS correctly on Ubuntu (and
possibly other Linux distributions.

Edit these configuration files with the following values (substituting
your own IP address as appropriate.

## /etc/default/openvas-gsa

Set the listening and manager address to this host, e.g.
```
LISTEN_ADDRESS="203.0.113.56"
PORT_NUMBER=4000
MANAGER_ADDRESS="203.0.113.56"
```

## /etc/default/openvas-manager

```
LISTEN_ADDRESS="0.0.0.0"
PORT_NUMBER=9390
```

## GSA local directory

If it doesn't already exist, create the directory 
`/usr/share/openvas/gsa/locale` by running the command:
```
sudo mkdir -p /usr/share/openvas/gsa/locale
```


## Testing the OMP connection

Ensure that you have the **omp** command line utility installed, and
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

## Testing the GSA connection

Point your web browser to (for example) `https://203.0.113.56:4000/`

If you have problems, look to the file `/var/log/openvas/gsad.log` for 
guidance, into what has gone wrong.

## Further information

* OpenVAS Documentation - (http://docs.greenbone.net)

## Authors

* **Anna Langley** - *Initial work on this document* - (https://github.com/jal58)

## Acknowledgments

* Martin Picard (original developer of pyvas) - (https://github.com/mpicard)
* RFC 5737: IPv4 Address Blocks Reserved for Documentation - (https://tools.ietf.org/html/rfc5737)
