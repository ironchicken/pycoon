from pycoon.helpers import pycoon_sax_handler
import lxml.etree

def test_etree_transform(tree):
    e = lxml.etree.Element("foo")
    e.text = "bar"
    tree.append(e)

    return tree

class test_sax_handler(pycoon_sax_handler):
    def startDocument(self):
        self.result_tree = lxml.etree.Element("result")
        
    def startElement(self, name, attribs):
        self.result_tree.append(lxml.etree.Element(name))

        
