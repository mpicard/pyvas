# A note about how NVTs are assigned to configs in OpenVAS

OpenVAS configs record which NVTs they use in a slightly unexpected way,
which is not mentioned in the OMP documentation.

For NVT families where every NVT is active, just the family's name is
recorded in the config.  If fewer NVTs are active, all of them are 
listed.

## Implications for listing a config's NVTs using `list_config_nvts`

This behaviour provided the motivation to implement `list_config_nvts`
as it is.  Without any further options, it lists only the NVTs that do 
not belong to a complete family.  This can return a surprisingly small
list of results even for a big config such as "Full and very deep".

It's only when you call this function with the `families=True` option,
that an exhaustive list of the config's NVTs is returned.  This takes
a lot longer to run as pyvas has to look up every NVT and which family
it belongs to, in order to construct the list.

## Implications for disabling an NVT from a config

To disable a single NVT where a whole family is selected, it
is necessary to disable that entire family, and then add the list of 
NVTs which belong to that family which are still required.

## Further information

* OpenVAS Project OMP Documentation - (http://docs.greenbone.net/API/OMP/omp-7.0.html)

## Authors

* **Anna Langley** - *Initial work on this document* - (https://github.com/jal58)

## Acknowledgments

* Martin Picard (original developer of pyvas) - (https://github.com/mpicard)
