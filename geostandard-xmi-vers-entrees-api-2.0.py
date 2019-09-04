# -*- coding: utf-8 -*-
"""
Created on Mon May 20 16:41:00 2019

@author: richard.mitanchey
"""

from lxml import etree
import regex as re
from collections import OrderedDict
import yaml
import yamlordereddictloader

many = re.compile(r'\.\.\*')

parser = etree.XMLParser()

from lxml import etree

def get_value(node, xpath):
    try:
        return node.xpath(xpath)[0]
    except:
        return ""
    
def prefix_attribute_name(nsmap, prefix, name):
    return '{' + nsmap[prefix] + '}' + name

def oas_200_response(nomobjet, description):
    one_response = OrderedDict()
    one_response['description'] = description
    one_response['schema'] = {
        "$ref": "#/definitions/{}".format(nomobjet)
         }
    return { 200: one_response }

def oas_4xx_response(code_4xx, description):
    one_response = OrderedDict()
    one_response['description'] = description
    one_response['schema'] = {
        "$ref": '#/definitions/Error'
        }
    return { code_4xx: one_response }

def print_connector(connector):
    ea_type = get_value(connector, 'properties/@ea_type')
    if ea_type in ["Dependency", "Realisation"]: return
    classeSource = get_value(connector, 'source/model/@name')
    classeDest = get_value(connector, 'target/model/@name')
    multSource = get_value(connector, 'source/type/@multiplicity')
    multDest = get_value(connector, 'target/type/@multiplicity')
    label = get_value(connector, 'labels/@mt')
    print("{} {}: {} ({}), {} ({})".format(ea_type, label, classeSource, multSource, classeDest, multDest))

def oas_path_connector(connector):
    ea_type = get_value(connector, 'properties/@ea_type')
    if ea_type in ["Dependency", "Realisation"]: return {}
    classeSource = get_value(connector, 'source/model/@name').__str__()
    classeDest = get_value(connector, 'target/model/@name').__str__()
    multSource = get_value(connector, 'source/type/@multiplicity').__str__()
    multDest = get_value(connector, 'target/type/@multiplicity').__str__()
    path = OrderedDict()
    basesummary = "liste non paginée des identifiants de {} d'un même objet {} que l'on spécifie par son propre identifiant"
    if many.search(multSource) != None:
        classeId = classeDest
        classeResult = classeSource
    elif many.search(multDest) != None:
        classeId = classeSource
        classeResult = classeDest
    else: return {}
    pathkey = '/'+ classeId + '/{id}/' + classeResult
    summary = basesummary.format(classeResult, classeId)
    path['summary'] = summary
    parameters = []
    one_parameter = OrderedDict()
    one_parameter['name'] = 'id'
    one_parameter['in'] = 'path'
    one_parameter['description'] = "identifiant de l'objet {}".format(classeId)
    one_parameter['required'] = True
    one_parameter['type'] = 'integer'
    parameters.append(one_parameter)
    path['parameters'] = parameters
    responses = OrderedDict()
    responses.update(oas_200_response(classeResult, summary))
    responses.update(oas_4xx_response(400, "Erreur. Requête mal formée"))
    responses.update(oas_4xx_response(404, "Erreur. Objet {} introuvable".format(classeResult)))
    path['responses'] = responses
    return { pathkey: { 'get': path } }

def oas_property(attribute):
    one_attribute_dict = OrderedDict()
    documentation = get_value(attribute, 'documentation/@value').__str__()
    typeattr = get_value(attribute, 'properties/@type').__str__()
    if typeattr in ['CharacterString', 'CharacterSetCode']:
        one_attribute_dict['type'] = 'string'
        one_attribute_dict['description'] = documentation
    elif typeattr in ['Date']:
        one_attribute_dict['type'] = 'string'
        one_attribute_dict['description'] = documentation
        one_attribute_dict['example'] = "2017-01-01"
        one_attribute_dict['format'] = 'date'
        one_attribute_dict['pattern'] = "YYYY-MM-DD"
        one_attribute_dict['minLength'] = 0
        one_attribute_dict['maxLength'] = 10
    elif typeattr in ['Boolean']:
        one_attribute_dict['type'] = 'boolean'
        one_attribute_dict['description'] = documentation
    elif typeattr in ['Decimal']:
        one_attribute_dict['type'] = 'number'
        one_attribute_dict['description'] = documentation
    elif typeattr in ['Integer']:
        one_attribute_dict['type'] = 'integer'
        one_attribute_dict['description'] = documentation
    elif typeattr in ['GM_Point','GM_Surface']:
        one_attribute_dict['type'] = 'object'
        one_attribute_dict['description'] = documentation
    else:
        one_attribute_dict['type'] = typeattr
        one_attribute_dict['description'] = documentation
    return one_attribute_dict

def oas_error_definition():
    definition = OrderedDict()
    definition['type'] = 'object'
    properties = OrderedDict()
    one_property_dict = OrderedDict()
    one_property_dict['type'] = 'integer'
    one_property_dict['description'] = "Code HTTP de l'erreur"
    properties['code'] = one_property_dict
    one_property_dict = OrderedDict()
    one_property_dict['type'] = 'string'
    one_property_dict['description'] = "Libellé de l'erreur"
    properties['message'] = one_property_dict
    one_property_dict = OrderedDict()
    one_property_dict['type'] = 'string'
    one_property_dict['description'] = "Explication"
    properties['description'] = one_property_dict
    definition['properties'] = properties
    return { 'Error': definition }

def oas_definition(element):
    stereotype = get_value(element, 'properties/@stereotype')
    if not stereotype in ['featureType']: return {}
    refid = element.get(prefix_attribute_name(nsmap, 'xmi', 'idref'))
    classe = tree.findall('/uml:Model/packagedElement/packagedElement[@xmi:id="{}"]'.format(refid), nsmap)
    properties = OrderedDict()
    attributes = element.findall('attributes/attribute')
    for attribute in attributes:
        one_property_dict = oas_property(attribute)
        properties.update( { attribute.get('name'): one_property_dict })
    definition = OrderedDict()
    definition['type'] = 'object'
    definition['description'] = classe[0].__str__()
    definition['properties'] = properties
    return { element.get('name'): definition }

def oas_path_liste(element):
    stereotype = get_value(element, 'properties/@stereotype')
    if not stereotype in ['featureType']: return {}
    classeResult = element.get('name')
    path = OrderedDict()
    summary = "liste paginée des objets de type {}".format(classeResult)
    path['summary'] = summary
    parameters = []
    one_parameter = OrderedDict()
    one_parameter['name'] = 'pagesize'
    one_parameter['in'] = 'query'
    one_parameter['description'] = "nombre d'objets {} par page".format(classeResult)
    one_parameter['required'] = True
    one_parameter['type'] = 'integer'
    parameters.append(one_parameter)
    one_parameter = OrderedDict()
    one_parameter['name'] = 'pageno'
    one_parameter['in'] = 'query'
    one_parameter['description'] = "Numéro de page"
    one_parameter['required'] = True
    one_parameter['type'] = 'integer'
    parameters.append(one_parameter)
    path['parameters'] = parameters
    responses = OrderedDict()
    responses.update(oas_200_response(classeResult, summary))
    responses.update(oas_4xx_response(400, "Erreur. Requête mal formée"))
    responses.update(oas_4xx_response(404, "Erreur. Objets {} introuvables".format(classeResult)))
    path['responses'] = responses
    return { '/'+element.get('name'): { 'get': path } }

def oas_path_byId(element):
    stereotype = get_value(element, 'properties/@stereotype')
    if not stereotype in ['featureType']: return {}
    classeResult = element.get('name')
    path = OrderedDict()
    summary = "objet de type {} à partir de son identifiant".format(classeResult)
    path['summary'] = summary
    parameters = []
    one_parameter = OrderedDict()
    one_parameter['name'] = 'id'
    one_parameter['in'] = 'path'
    one_parameter['description'] = "identifiant de l'objet {}".format(classeResult)
    one_parameter['required'] = True
    one_parameter['type'] = 'integer'
    parameters.append(one_parameter)
    path['parameters'] = parameters
    responses = OrderedDict()
    responses.update(oas_200_response(classeResult, summary))
    responses.update(oas_4xx_response(400, "Erreur. Requête mal formée"))
    responses.update(oas_4xx_response(404, "Erreur. Objet {} introuvable".format(classeResult)))
    path['responses'] = responses
    return { '/'+element.get('name')+'/{id}': { 'get': path } }
    
tree = etree.parse("EolienTerrestre-logique.xmi")
nsmap = {
       "uml":"http://www.omg.org/spec/UML/20110701",
       "xmi":"http://www.omg.org/spec/XMI/20110701",
       "thecustomprofile":"http://www.sparxsystems.com/profiles/thecustomprofile/1.0",
       "UML_Profile_for_INSPIRE_data_specifications":"http://www.sparxsystems.com/profiles/UML_Profile_for_INSPIRE_data_specifications/3.0-2"
       }

elements = tree.findall('.//xmi:Extension/elements/element[@xmi:type="uml:Class"]', nsmap)
definitions = OrderedDict()
definitions.update(oas_error_definition())
paths = {}
for element in elements:
    definitions.update(oas_definition(element))
    paths.update(oas_path_liste(element))
    paths.update(oas_path_byId(element))
connectors = tree.findall('.//xmi:Extension/connectors/connector', nsmap)
for connector in connectors:
    paths.update(oas_path_connector(connector))
    
oas = OrderedDict()
oas['swagger'] = "2.0"
info = OrderedDict()
info['version'] = '1.0.0'
info['title'] = 'API Eolien Terrestre'
info['description'] = 'Une API liée au géostandard COVADIS Eolien Terrestre v2.0'
info['license'] = {
    "name": "ODbL-1.0",
    "url": "https://spdx.org/licenses/ODbL-1.0.html"
  }
oas['info'] = info
oas['schemes'] = ['http']
oas['host'] = 'localhost:8181'
oas['basePath'] = '/eolien'
oas['paths'] = paths
oas['definitions'] = definitions

yaml.dump(
    oas,
    open('swagger.yaml', 'w', encoding='utf-8'),
    Dumper=yamlordereddictloader.Dumper,
    default_flow_style=False, allow_unicode=True)