# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 10:00:42 2021

@author: mlatyshev
"""

import xml.etree.ElementTree as ET

def get_graph():

    tree = ET.parse("map")
    nodes = {}
    edges = {}

    ways = ['primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'primary_link', 'secondary_link', 'tertiary_link', 'service', 'track']

    # root = tree.getroot()
    # 1011297209

    garage = {'lat': "52.6175510", 'lon': "39.5284553", 'ref': "875930696" }
    test = tree.find(f"node[@id='{garage['ref']}']")
    res = tree.findall("way")
    all_nodes = {}
    for child in tree.findall("node"):
        all_nodes[child.attrib['id']] = child.attrib
    for child in res:
        isWay = False
        for i in child:
            if i.tag == 'tag' and i.attrib['k'] == 'highway' and i.attrib['v'] in ways:
                isWay = True
                break
        if isWay == False:
            continue
        
        nds = []
        tags = {}
        for i in child:
            if i.tag == 'nd':
                # info_node = tree.find(f"node[@id='{i.attrib['ref']}']")
                # if i.attrib['ref'] not in nodes:
                #     nodes[i.attrib['ref']] = tree.find(f"node[@id='{i.attrib['ref']}']").attrib
                nds.append(i)
            if i.tag == 'tag':
                tags[i.attrib['k']] = i.attrib['v']
                
        for num, item in enumerate(nds):
            nodes[item.attrib['ref']] = all_nodes[item.attrib['ref']]
            if num + 1 < len(nds):
                edges.setdefault(item.attrib['ref'], {}).setdefault(nds[num + 1].attrib['ref'], tags)
                
        if 'oneway' in tags and tags['oneway'] == 'yes':
            continue
        rev = list(reversed(nds))
        for num, item in enumerate(rev):
            if num + 1 < len(rev):
                edges.setdefault(item.attrib['ref'], {}).setdefault(rev[num + 1].attrib['ref'], tags)

    return edges, nodes
    