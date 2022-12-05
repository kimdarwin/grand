#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import sys, zipfile, xml.dom.minidom
#import StringIO
#from io import StringIO
#import io as StringIO

class OpenDocumentTextFile :
    def __init__ (self, filepath):
        zip = zipfile.ZipFile(filepath)
        self.content = xml.dom.minidom.parseString(zip.read("content.xml"))
    def tolist (self):
        buffer = []
        for val in ["text:p", "text:h", "text:list"]:
            for paragraph in self.content.getElementsByTagName(val) :
                buffer.append(self.textToString(paragraph))
        return buffer
    def toString (self):
        """ Converts the document to a string. """
        buffer = u""
        for val in ["text:p", "text:h", "text:list"]:
            for paragraph in self.content.getElementsByTagName(val) :
                buffer += self.textToString(paragraph) + "\n"
        return buffer

    def textToString(self, element):
        buffer = u""
        for node in element.childNodes :
            if node.nodeType == xml.dom.Node.TEXT_NODE :
                buffer += node.nodeValue
            elif node.nodeType == xml.dom.Node.ELEMENT_NODE :
                buffer += self.textToString(node)
        return buffer

if __name__ == "__main__" :
    #s =StringIO.StringIO(file(sys.argv[1]).read())
    infile = './doc/agc2022_n05c00.odt'
    '''
    #infile = './doc/content.xml'
    inf = open(infile,'r');
    lines = inf.readlines();
    inf.close();
    
    cont = ""
    for line in lines:
        cont = cont+"\n"+line;
    s =cont
    '''
    #s =StringIO.StringIO(file(sys.argv[1]).read())
    #odt = OpenDocumentTextFile(s)
    
    odt = OpenDocumentTextFile(infile)
    #print odt.toString().encode('ascii','replace')
    #print (odt.toString().encode('ascii','replace'))
    #print (odt.toString())
    print (odt.tolist())

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
