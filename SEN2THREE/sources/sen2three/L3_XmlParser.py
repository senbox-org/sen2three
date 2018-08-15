#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from numpy import *
import os, sys
from lxml import etree, objectify
from L3_Library import stdoutWrite, stderrWrite

class L3_XmlParser():
    ''' A parser for the assignment of xml based metadata to python configuration objects and vice versa.
        Performs also a validation of the metadata against the corresponding scheme.

            :param productStr: the product string for the given metadata (via __init__).
            :type productStr: a string.

    '''

    def __init__(self, config, productStr):
        self._config = config
        self._productStr = productStr
        self._xmlFn = None
        self._xmlName = None
        self._root = None
        self._tree = None
        self._scheme = None

        if (productStr == 'GIPP'):
            self._xmlFn = config.configFn
            self._scheme = config.gippScheme3
        elif (productStr == 'UP2A'):
            self._xmlFn = config.L2A_UP_MTD_XML
            self._scheme = config.upScheme2a
        elif (productStr == 'UP03'):
            self._xmlFn = config.L3_TARGET_MTD_XML
            self._scheme = config.upScheme3
        elif (productStr == 'DS2A'):
            self._xmlFn = config.L2A_DS_MTD_XML
            self._scheme = config.dsScheme2a
        elif (productStr == 'DS03'):
            self._xmlFn = config.L3_DS_MTD_XML
            self._scheme = config.dsScheme3
        elif (productStr == 'T2A'):
            self._xmlFn = config.L2A_TILE_MTD_XML
            self._scheme = config.tileScheme2a
        elif (productStr == 'T03'):
            self._xmlFn = config.L3_TILE_MTD_XML
            self._scheme = config.tileScheme3
        elif (productStr == 'Manifest'):
            self._xmlFn = config.L3_MANIFEST_SAFE
            self._scheme = config.manifestScheme
        else:
            config.logger.fatal('wrong product identifier for xml structure: ' + productStr)
            config.exitError()
        
        self.setRoot()
        return

    def getRoot(self, key=None):
        ''' Gets the root of an xml tree, addressed by the corresponding key.

            :param key: the search key
            :type key: a string

            :return: the tree
            :rtype: an element tree

        '''
        try:
            if key == None:
                return self._root
            else:
                root = self._root[key]
                return root
        except:
            return False

    def setRoot(self):
        ''' Sets the root of an xml tree.

            :return: true if succesful
            :rtype: bool

        '''

        if self._root is not None:
            return True
        try:
            doc = objectify.parse(self._xmlFn)
            self._root = doc.getroot()
            return True
        except:
            return False

    def getTree(self, key, subkey):
        ''' Gets the subtree of an xml tree, addressed by the corresponding key and subkey.

            :param key: the search key
            :type key: a string
            :param subkey: the search subkey
            :type subkey: a string
            :return: the tree
            :rtype: an element tree

        '''
        try:
            tree = self._root[key]    
            return tree['{}' + subkey]
        except:
            return False

    def setTree(self, key, subkey):
        ''' Sets the subtree of an xml tree, addressed by the corresponding key and subkey.

            :param key: the search key
            :type key: a string
            :param subkey: the search subkey
            :type subkey: a string
            :return: true if succesful
            :rtype: bool

        '''
        try:
            root = self._root[key]
        except:
            return False
        try:
            self._tree = root['{}' + subkey]
            return True
        except:
            self._tree = root
            if(self.append(subkey, '') == True):
                try:
                    self._tree = root['{}' + subkey]
                    self.export()
                    return True        
                except:
                    return False
        return False

    def validate(self):
        """ Validator for the metadata.

            :return: true, if metadata are valid.
            :rtype: boolean

        """
        fn = os.path.basename(self._xmlFn)
        self._config.logger.info('validating metadata file %s against scheme' % fn)
        err = 'unknown'
        try:
            schema = etree.XMLSchema(file = os.path.join(self._config.configDir, self._scheme))
            parser = etree.XMLParser(schema = schema)
            objectify.parse(self._xmlFn, parser)
            self._config.logger.info('metadata file is valid')
            ret = True
        except etree.XMLSyntaxError, err:
            stdoutWrite('Syntax error in metadata, see report file for details.\n')
            self._config.logger.error('Schema file: %s' % self._scheme)
            self._config.logger.error('Details: %s' % str(err))
            ret = False
        except etree.XMLSchemaError, err:
            stdoutWrite('Error in xml schema, see report file for details.\n')
            self._config.logger.error('Schema file: %s' % self._scheme)
            self._config.logger.error('Details: %s' % str(err))
            ret = False
        except etree.XMLSchemaParseError, err:
            stdoutWrite('Error in parsing xml schema, see report file for details.\n')
            self._config.logger.error('Schema file: %s' % self._scheme)
            self._config.logger.error('Details: %s' % str(err))
            ret = False
        except etree.XMLSchemaValidateError, err:
            stdoutWrite('Error in validating scheme, see report file for details.\n')
            self._config.logger.error('Schema file: %s' % self._scheme)
            self._config.logger.error('Details: %s' % str(err))
            ret = False
        except:
            stdoutWrite('Unspecific Error in metadata.\n')
            self._config.logger.error('unspecific error in metadata')
            ret = False

        if ret == False:
            print 'Parsing error:'
            print 'Schema file: %s' % self._scheme
            print 'Details: %s' % str(err)

        return ret


    def append(self, key, value):
        try:
            e = etree.Element(key)
            e.text = value
            self._tree.append(e)
            return True
        except:
            return False

    def export(self):
        import codecs
        outfile = codecs.open(self._xmlFn, 'w', 'utf-8')
        outfile.write('<?xml version="1.0"  encoding="UTF-8"?>')
        objectify.deannotate(self._root, xsi_nil=True, cleanup_namespaces=True)
        outstr = etree.tostring(self._root, pretty_print=True)
        outfile.write(outstr)        
        outfile.close()
        return self.setRoot()

    def convert(self):
        import codecs
        objectify.deannotate(self._root, xsi_nil=True, cleanup_namespaces=True)
        outstr = etree.tostring(self._root, pretty_print=True)
        if ('UP2A' in self._productStr) or ('T2A' in self._productStr):
            if 'LOW_PROBA_CLOUDS' in outstr:
                outstr = outstr.replace('BARE_SOILS', 'NOT_VEGETATED')
                outstr = outstr.replace('SC_BARE_SOIL_DESERT', 'SC_NOT_VEGETATED')
                outstr = outstr.replace('LOW_PROBA_CLOUDS', 'UNCLASSIFIED')
                outstr = outstr.replace('SC_CLOUD_LOW_PROBA', 'SC_UNCLASSIFIED')
            else:
                return 0
        elif '03' in self._productStr:
            outstr = outstr.replace('Level-2A', 'Level-3')
            outstr = outstr.replace('psd-12', 'psd-14')
            outstr = outstr.replace('psd-13', 'psd-14')
            outstr = outstr.replace('/DICO/12', 'DICO/')
            outstr = outstr.replace('L2A_Product_Info>', 'Product_Info>')
            outstr = outstr.replace('Granules', 'Granule')
            outstr = outstr.replace('IMAGE_ID_2A', 'IMAGE_FILE')
            outstr = outstr.replace('L2A_SCENE', 'SCENE')
            outstr = outstr.replace('L2A_Scene', 'Scene')
            outstr = outstr.replace('L2A_Product_Organisation>', 'Product_Organisation>')
            outstr = outstr.replace('L2A_Product_Image_Characteristics>', 'Product_Image_Characteristics>')
            outstr = outstr.replace('TILE_ID_2A', 'TILE_ID')
            outstr = outstr.replace('DATASTRIP_ID_2A', 'DATASTRIP_ID')
            outstr = outstr.replace('L1C_L2A_Quantification_Values_List', 'QUANTIFICATION_VALUES_LIST')
            outstr = outstr.replace('L2A_BOA_QUANTIFICATION_VALUE', 'BOA_QUANTIFICATION_VALUE')
            outstr = outstr.replace('L2A_AOT_QUANTIFICATION_VALUE', 'AOT_QUANTIFICATION_VALUE')
            outstr = outstr.replace('L2A_WVP_QUANTIFICATION_VALUE', 'WVP_QUANTIFICATION_VALUE')
            if self._productStr == 'UP03':
                outstr = outstr.replace('PRODUCT_URI_2A', 'PRODUCT_URI')
                outstr = outstr.replace('</PROCESSING_BASELINE>', '</PROCESSING_BASELINE><PROCESSING_ALGORITHM/><RADIOMETRIC_PREFERENCE/>')

        outfile = codecs.open(self._xmlFn, 'w', 'utf-8')
        outfile.write('<?xml version="1.0"  encoding="UTF-8"?>')
        outfile.write(outstr)
        outfile.close()
        return self.setRoot()

    def getIntArray(self, node):
        nrows = len(node)
        if nrows < 0:
            return False

        ncols = len(node[0].text.split())
        a = zeros([nrows,ncols],dtype=int)        

        for i in range(nrows):
            a[i,:] = array(node[i].text.split(),dtype(int))
        
        return a

    def getUintArray(self, node):
        nrows = len(node)
        if nrows < 0:
            return False
        
        ncols = len(node[0].text.split())
        a = zeros([nrows,ncols],dtype=uint)
        
        for i in range(nrows):
            a[i,:] = array(node[i].text.split(),dtype(uint))
            
        return a

    def getFloatArray(self, node):
        nrows = len(node)
        if nrows < 0:
            return False
        
        ncols = len(node[0].text.split())
        a = zeros([nrows,ncols],dtype=float32)
        
        for i in range(nrows):
            a[i,:] = array(node[i].text.split(),dtype(float32))
            
        return a

    def getStringArray(self, node):
        nrows = len(node)
        if nrows < 0:
            return False
        
        ncols = len(node[0].text.split())
        a = zeros([nrows,ncols],dtype=str)
        
        for i in range(nrows):
            a[i,:] = array(node[i].text.split(),dtype(str))

        return a

    def setArrayAsStr(self, node, a):
        set_printoptions(precision=6)
        if a.ndim == 1:
            nrows = a.shape[0]
            for i in nrows:
                node[i] = a[i],dtype=str
                        
        elif a.ndim == 2:
            nrows = a.shape[0]
            ncols = a.shape[1]
            for i in range(nrows):
                aStr = array_str(a[i,:]).strip('[]')
                node[i] = aStr
            return True
        else:
            return False

    def getViewingIncidenceAnglesArray(self, node, bandId, detectorId, _type='Zenith'):
        nrows = len(node)
        for i in range(nrows):
            if((int(node[i].bandId) == bandId) and (int(node[i].detectorId) == detectorId)):
                if _type == 'Zenith':
                    a = self.getFloatArray(node[i].Zenith.Values_List.VALUES)
                elif _type == 'Azimuth':
                    a = self.getFloatArray(node[i].Azimuth.Values_List.VALUES)

                return a
        return False

    def setViewingIncidenceAnglesArray(self, node, arr, bandId, detectorId, _type='Zenith'):
        nrows = len(node)
        for i in range(nrows):
            if((int(node[i].bandId) == bandId) and (int(node[i].detectorId) == detectorId)):
                if _type == 'Zenith':
                    return self.setArrayAsStr(node[i].Zenith.Values_List.VALUES, arr)
                elif _type == 'Azimuth':
                    return self.setArrayAsStr(node[i].Azimuth.Values_List.VALUES, arr)

        return False

    