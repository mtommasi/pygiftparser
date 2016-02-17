#! /usr/bin/python3
import sys
sys.path.append('../src')
import pygiftparser
import yattag

import glob


d = yattag.Doc() 
d.asis('<!DOCTYPE html>')
with d.tag('html'):
    with d.tag('head'):
        d.stag('link', rel="stylesheet", href="default.css", type="text/css")
        with d.tag('body'):
            for filename in glob.glob('*gift'):
                with d.tag('h1'):
                    d.text(filename)
                
                with open(filename,'r') as f:
                    questions = pygiftparser.parseFile(f)
                f.close()
        
                for q in questions:
                    q.toHTML(d,True)

out =  open("index.html", "w")
out.write (d.getvalue())
out.close()

    
