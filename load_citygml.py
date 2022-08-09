from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET
import pandas as pd
from pandas.core.frame import DataFrame

codedict = {}

def tag(e: ET.Element) -> str:
    return e.tag.split('}')[-1]


def load_codespace(citygml_path: str, codepath: str) -> Dict:
    global codedict
    if codepath in codedict:
        return codedict[codepath]
    else:
        dictpath = Path(citygml_path).parent / Path(codepath)
        ns = {'gml': 'http://www.opengis.net/gml'}
        df = pd.read_xml(dictpath, xpath='///gml:Definition',
                         namespaces=ns).astype(str)
        code_dict = df.set_index('name')['description'].to_dict()
        codedict.update({codepath: code_dict})
        return codedict[codepath]


def load_buildings(building: ET.Element) -> Dict:
    dict_building = {}
    dict_building['id'] = building.attrib['{http://www.opengis.net/gml}id']
    for attr in building:
        attr_tag = tag(attr)
        if attr_tag == 'stringAttribute':
            dict_building[attr.attrib['name']] = list(attr)[0].text
        elif attr_tag == 'genericAttributeSet':
            genattrib = {}
            for elem in attr:
                genattrib[elem.attrib['name']] = list(elem)[0].text
            dict_building[attr.attrib['name']] = genattrib
        elif attr_tag == 'measuredHeight':
            dict_building[attr_tag] = attr.text
        elif attr_tag in ['lod0RoofEdge', 'address']:
            # めっちゃ深い階層にある
            elem = list(attr)
            while elem:
                elem = list(elem)[-1]
            else:
                dict_building[attr_tag] = elem.text
        elif attr_tag == 'buildingDetails':
            attr = list(attr)[0]
            for elem in attr:
                dict_building[tag(elem)] = elem.text
        elif attr_tag == 'extendedAttribute':
            key, value = list(list(attr)[0])
            key = load_codespace(citygml_path, key.attrib['codeSpace'])[key.text]
            value = load_codespace(citygml_path, value.attrib['codeSpace'])[value.text]
            dict_building[key] = value
        else:
            dict_building[attr_tag] = attr.text
    return dict_building

def load_Road(road: ET.Element) -> Dict:
    dict_road = {}
    dict_road['id'] = road.attrib['{http://www.opengis.net/gml}id']
    for attr in road:
        attr_tag = tag(attr)
        if attr_tag == 'stringAttribute':
            dict_road[attr.attrib['name']] = list(attr)[0].text
        elif attr_tag == 'lod1MultiSurface':
            # めっちゃ深い階層にある
            elem = list(attr)
            while elem:
                elem = list(elem)[-1]
            else:
                dict_road[attr_tag] = elem.text
        else:
            dict_road[attr_tag] = attr.text
    return dict_road

def load_citygml(citygml_path: str) -> List[Dict]:
    obj_list = []
    root = ET.parse(citygml_path).getroot()
    namespace = {'core': 'http://www.opengis.net/citygml/2.0'}
    for cityobject in root.findall('core:cityObjectMember', namespace):
        cityobject = list(cityobject)[0]
        if tag(cityobject) == 'Building':
            obj = load_buildings(cityobject)
        elif tag(cityobject) == 'Road':
            obj = load_Road(cityobject)
        else:
            raise NotImplementedError(tag(cityobject))
        obj_list.append(obj)
    return obj_list

def citygml_to_dataframe(file: str) -> DataFrame:
    return pd.DataFrame.from_dict(load_citygml(file))
