# utils.py

Some very basic documentation and usage examples for utils.py

## dict_to_lxml(root, dct)
Convert a root and dictionary (all of strings) into an element tree 
(lxml.etree._Element).

Example:
```
>>> from pyvas import utils
>>> from lxml.etree import tostring
>>> xml = utils.dict_to_lxml('capitals', {'UK':'London','France':'Paris','Germany':'Berlin'})>>> type(xml)
<class 'lxml.etree._Element'>
>>> tostring(xml)
b'<capitals><UK>London</UK><Germany>Berlin</Germany><France>Paris</France></capitals>'

```

## lxml_to_dict(tree, strip_root=False)
Convert type lxml.etree._Element into a dictionary, optionally stripping
out the root element.

Example:
```
>>> from pyvas import utils
>>> from lxml.etree import tostring
>>> xml = utils.dict_to_lxml('capitals', {'UK':'London','France':'Paris','Germany':'Berlin'})>>> type(xml)
>>> utils.lxml_to_dict(xml)
{'capitals': {'UK': 'London', 'Germany': 'Berlin', 'France': 'Paris'}}
>>> utils.lxml_to_dict(xml, strip_root=True)
{'UK': 'London', 'Germany': 'Berlin', 'France': 'Paris'}
```

## Authors

* **Anna Langley** - *Initial work on this document* - (https://github.com/jal58)

## Acknowledgments

* Martin Picard (original developer of pyvas) - (https://github.com/mpicard)
