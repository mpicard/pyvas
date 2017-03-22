try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
import xml.dom.minidom

def prettyPrint(element):
    txt = etree.tostring(element)
    print xml.dom.minidom.parseString(txt).toprettyxml()
