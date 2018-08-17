#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os, fnmatch, tables, shutil
from time import strftime
from datetime import datetime
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
from lxml import etree, objectify
from numpy import *
from L3_XmlParser import L3_XmlParser
from L3_Library import stderrWrite

class Particle(tables.IsDescription):
    TILE_ID = tables.StringCol(itemsize=9)
    RESOLUTION = tables.UInt32Col()
    TILES_COUNT = tables.UInt32Col()
    TOTAL_PIXELS = tables.UInt32Col()
    DATA_PIXELS = tables.UInt32Col()
    NODATA_PIXELS = tables.UInt32Col()
    GOOD_PIXELS = tables.UInt32Col()
    BAD_PIXELS = tables.UInt32Col()
    SAT_DEF_PIXELS = tables.UInt32Col()
    DARK_PIXELS = tables.UInt32Col()
    CLOUD_SHADOWS = tables.UInt32Col()
    VEGETATION = tables.UInt32Col()
    NOT_VEGETATED = tables.UInt32Col()
    WATER = tables.UInt32Col()
    UNCLASSIFIED = tables.UInt32Col()
    MED_PROBA_CLOUDS = tables.UInt32Col()
    HIGH_PROBA_CLOUDS = tables.UInt32Col()
    THIN_CIRRUS = tables.UInt32Col()
    SNOW_ICE = tables.UInt32Col()

class BestVal(tables.IsDescription):
    AOT_MEAN = tables.Float32Col()
    SZA_MEAN = tables.Float32Col()
    DATE_TIME = tables.Float32Col()

class L3_Product(object):
    '''
        :param config: the config object for the current tile (via __init__)
        :type config: a reference to the L3_Config object

    '''

    _shared = {}
    def __init__(self, config):
        self._config = config


    def get_config(self):
        return self._config


    def set_config(self, value):
        self._config = value


    def del_config(self):
        del self._config

    config = property(get_config, set_config, del_config)

    def existL3_TargetProduct(self, userProduct):
        ''' Check if an L3 target product already exists. If not,
            trigger the creation, else trigger the reinitialisation of the existing one

            :return: true if succesful
            :rtype: bool

        '''
        self.config.logger.info('Checking existence of L3 target product ...')
        L3_TARGET_MASK = '*L03_*'
        if self.config.targetDir == 'DEFAULT':
            L3_TARGET_DIR = self.config.sourceDir
            self.config.targetDir = L3_TARGET_DIR
        else:
            if os.name == 'nt' and not '\\\\?\\' in self.config.targetDir:
                self.config.targetDir = u'\\'.join([u'\\\\?', self.config.targetDir])
            L3_TARGET_DIR = self.config.targetDir
        try:
            os.stat(L3_TARGET_DIR)
        except:
            os.mkdir(L3_TARGET_DIR)
        dirlist = sorted(os.listdir(L3_TARGET_DIR))
        for L3_TARGET_ID in dirlist:
            if fnmatch.fnmatch(L3_TARGET_ID, L3_TARGET_MASK):
                self.config.logger.info('L3 target product already exists.')
                if self.config.cleanTarget:
                    self.config.logger.info('Clean option selected: L3 target product will be cleaned.')
                    l3Target = os.path.join(self.config.targetDir, L3_TARGET_ID)
                    try:
                        shutil.rmtree(l3Target)
                    except:
                        pass
                    self.config.cleanTarget = False
                    break
                self.config.L3_TARGET_ID = L3_TARGET_ID
                return self.reinitL3_TargetProduct()
            else:
                continue

        # no L3 target exists, will be created:
        self.config.L2A_UP_ID_first = userProduct
        self.config.logger.info('L3 target product will be created.')
        return self.createL3_TargetProduct()

    def createL3_TargetProduct(self):
        ''' Create the L3 target product.

            :return: true if succesful
            :rtype: bool

        '''

        self.config.logger.info('Creating L3 target product ...')
        L2A_UP_MASK = '*L2A_*'
        #L2A_UP_DIR = os.path.join(self.config.sourceDir, self.config.L2A_UP_ID)
        L2A_UP_DIR = self.config.L2A_UP_DIR
        # detect the filename for the datastrip metadata:
        L2A_DS_DIR = os.path.join(L2A_UP_DIR, 'DATASTRIP')
        if os.path.exists(L2A_DS_DIR) == False:
            stderrWrite('directory "%s" does not exist.\n' % L2A_DS_DIR)
            self.config.exitError()
            return False

        if self.config.namingConvention == 'SAFE_STANDARD':
            L2A_DS_MASK = 'S2?_USER_MSI_L2A_DS_*'
        else:
            L2A_DS_MASK = 'DS_*'
        dirlist = sorted(os.listdir(L2A_DS_DIR))
        found = False
        
        for dirname in dirlist:
            if(fnmatch.fnmatch(dirname, L2A_DS_MASK) == True):
                found = True
                break

        L2A_DS_DIR = os.path.join(L2A_DS_DIR, dirname)
        if self.config.namingConvention == 'SAFE_STANDARD':
            L2A_DS_MTD_XML = (dirname[:-7]+'.xml').replace('_MSI_', '_MTD_')
        else:
            L2A_DS_MTD_XML = 'MTD_DS.xml'
        L2A_DS_MTD_XML = os.path.join(L2A_DS_DIR, L2A_DS_MTD_XML)
        if found == False:
            stderrWrite('No metadata in datastrip\n.')
            self.config.exitError()

        dirname, basename = os.path.split(L2A_UP_DIR)
        if(fnmatch.fnmatch(basename, L2A_UP_MASK) == False):
            stderrWrite(basename + ': identifier "%s" is missing.' % L2A_UP_MASK)
            self.config.exitError()
            return False

        GRANULE = os.path.join(L2A_UP_DIR, 'GRANULE')
        if os.path.exists(GRANULE) == False:
            stderrWrite('directory "' + GRANULE + '" does not exist.')
            self.config.exitError()
            return False
        #
        # the product (directory) structure:
        #-------------------------------------------------------
        L3_TARGET_ID = basename
        L3_TARGET_ID = L3_TARGET_ID.replace('L2A_', 'L03_')
        strList = L3_TARGET_ID.split('_')
        if self.config.namingConvention == 'SAFE_STANDARD':
            L3_TARGET_ID = strList[0] + '_' + strList[3] + '_' + strList[5] + '_' + 'N0000_R000_T00XXX_' + self.config.minTime + '.SAFE'
        else:
            L3_TARGET_ID = L3_TARGET_ID.replace(strList[6], self.config.minTime + '.SAFE')

        if self.config.targetDir != 'DEFAULT':
            targetDir = self.config.targetDir
            if os.name == 'nt' and not '\\\\?\\' in targetDir:
                targetDir = u'\\'.join([u'\\\\?', targetDir])
            if(os.path.exists(targetDir) == False):
                os.mkdir(targetDir)
        else:
            targetDir = dirname
        self.config.targetDir = targetDir

        L3_TARGET_DIR = os.path.join(targetDir, L3_TARGET_ID)
        self.config.L3_TARGET_DIR = L3_TARGET_DIR
        self.config.L3_TARGET_ID = L3_TARGET_ID

        L2A_INSPIRE_XML = os.path.join(L2A_UP_DIR, 'INSPIRE.xml')
        L2A_MANIFEST_SAFE = os.path.join(L2A_UP_DIR, 'manifest.safe')

        L3_INSPIRE_XML = os.path.join(L3_TARGET_DIR, 'INSPIRE.xml')
        L3_MANIFEST_SAFE = os.path.join(L3_TARGET_DIR, 'manifest.safe')

        AUX_DATA = 'AUX_DATA'
        DATASTRIP = 'DATASTRIP'
        GRANULE = 'GRANULE'
        HTML = 'HTML'
        REP_INFO = 'rep_info'

        self.config.L2A_DS_MTD_XML = L2A_DS_MTD_XML
        xp = L3_XmlParser(self.config, 'DS2A')
        xp.export()
        xp.validate()

        copy_tree(os.path.join(L2A_UP_DIR, AUX_DATA), os.path.join(L3_TARGET_DIR, AUX_DATA))
        copy_tree(os.path.join(L2A_UP_DIR, DATASTRIP), os.path.join(L3_TARGET_DIR, DATASTRIP))
        copy_tree(os.path.join(L2A_UP_DIR, HTML), os.path.join(L3_TARGET_DIR, HTML))
        copy_tree(os.path.join(L2A_UP_DIR, REP_INFO), os.path.join(L3_TARGET_DIR, REP_INFO))
        copy_file(L2A_INSPIRE_XML, L3_INSPIRE_XML)
        copy_file(L2A_MANIFEST_SAFE, L3_MANIFEST_SAFE)
        if not os.path.exists(os.path.join(L3_TARGET_DIR, GRANULE)):
            os.mkdir(os.path.join(L3_TARGET_DIR, GRANULE))

        self.config.L3_INSPIRE_XML = L2A_INSPIRE_XML
        self.config.L3_MANIFEST_SAFE = L2A_MANIFEST_SAFE
        self.config.L3_TARGET_DIR = L3_TARGET_DIR

        #create user product:
        if self.config.namingConvention == 'SAFE_STANDARD':
            S2A_mask = 'S2?_USER_MTD_SAFL2A_*.xml'
        else:
            S2A_mask = 'MTD_MSIL2A.xml'
        filelist = sorted(os.listdir(L2A_UP_DIR))
        found = False
        for filename in filelist:
            if(fnmatch.fnmatch(filename, S2A_mask) == True):
                found = True
                break
        if found == False:
            stderrWrite('No metadata for user product')
            self.config.exitError()

        # prepare L3 User Product metadata file
        fn_L2A = os.path.join(L2A_UP_DIR, filename)
        fn_L3 = 'MTD_MSIL03.xml'
        fn_L3 = os.path.join(L3_TARGET_DIR, fn_L3)
        self.config.L2A_UP_MTD_XML = fn_L2A
        xp = L3_XmlParser(self.config, 'UP2A')
        if  xp.convert() != 0:
            xp = L3_XmlParser(self.config, 'UP2A')
        xp.validate()
        self.config.L3_TARGET_MTD_XML = fn_L3
        # copy L2A schemes from config_dir into rep_info:    
        upScheme3 = self.config.upScheme3
        basename = os.path.basename(upScheme3)
        copy_file(os.path.join(self.config.configDir, upScheme3), os.path.join(L3_TARGET_DIR, REP_INFO, basename))
        tileScheme3 = self.config.tileScheme3
        basename = os.path.basename(tileScheme3)
        copy_file(os.path.join(self.config.configDir, tileScheme3), os.path.join(L3_TARGET_DIR, REP_INFO, basename))
        dsScheme3 = self.config.dsScheme3
        basename = os.path.basename(dsScheme3)
        copy_file(os.path.join(self.config.configDir, dsScheme3), os.path.join(L3_TARGET_DIR, REP_INFO, basename))

        # copy L3 User Product metadata file:
        copy_file(fn_L2A, fn_L3)
        
        # remove old L2A entries from L3_TARGET_MTD_XML:
        xp = L3_XmlParser(self.config, 'UP03')
        if(xp.convert() == False):
            self.logger.fatal('error in converting user product metadata to level 3')
            stderrWrite('Error in converting user product metadata to level 3')
            self.config.exitError()
        xp = L3_XmlParser(self.config, 'UP03')
        pi = xp.getTree('General_Info', 'Product_Info')
        # update L2A entries from L2A_UP_MTD_XML:
        tmin = self.config.minTime
        tmax = self.config.maxTime
        pi.PRODUCT_START_TIME = tmin[:4]+'-'+tmin[4:6]+'-'+tmin[6:11]+':'+tmin[11:13]+':'+tmin[13:15]+'.000Z'
        pi.PRODUCT_STOP_TIME = tmax[:4]+'-'+tmax[4:6]+'-'+tmax[6:11]+'-'+tmax[11:13]+':'+tmax[13:15]+'.000Z'
        # update L2A and L3 entries from L2A_UP_MTD_XML:
        try:
            del pi.PRODUCT_URI_1C
        except:
            pass
        pi.PRODUCT_URI = self.config.L3_TARGET_ID
        pi.PROCESSING_LEVEL = 'Level-3p'
        pi.PRODUCT_TYPE = 'S2MSI3p'
        pi.PROCESSING_ALGORITHM = self.config.algorithm
        pi.RADIOMETRIC_PREFERENCE = self.config.radiometricPreference
        dt = datetime.utcnow()
        pi.GENERATION_TIME = strftime('%Y-%m-%dT%H:%M:%SZ', dt.timetuple())
        if self.config.namingConvention == 'SAFE_STANDARD':
            try:
                qo = pi.Query_Options
                del qo[:]
                qo = objectify.Element('Query_Options')
                qo.attrib['completeSingleTile'] = "false"
                qo.append(objectify.Element('PRODUCT_FORMAT'))
                qo.PRODUCT_FORMAT = 'SAFE_COMPACT'
                pi.append(qo)
            except:
                pass
        try:
            gl = pi.Product_Organisation.Granule_List
            del gl[:]
        except:
            pass
        try:
            pic = xp.getTree('General_Info', 'Product_Image_Characteristics')
            del pic.QUANTIFICATION_VALUES_LIST.L1C_TOA_QUANTIFICATION_VALUE
        except:
            pass
        try:
            aux = xp.getRoot('L2A_Auxiliary_Data_Info')
            del aux[:]
        except:
            pass
        try:
            aux = xp.getRoot('Auxiliary_Data_Info')
            aux.clear()
            node = objectify.Element('GIPP_LIST')
            aux.append(node)
        except:
            pass
        try:
            qii = xp.getRoot('L2A_Quality_Indicators_Info')
            del qii[:]
        except:
            pass
        try:
            qii = xp.getRoot('Quality_Indicators_Info')
            qii.clear()
            node = objectify.Element('Classification_QI')
            node.attrib['resolution'] = str(self.config.resolution)
            qii.append(node)
        except:
            pass
        xp.export()

        #create datastrip ID:
        L3_DS_DIR = os.path.join(L3_TARGET_DIR, DATASTRIP)
        dirlist = sorted(os.listdir(L3_DS_DIR))
        found = False
        for dirname in dirlist:
            if(fnmatch.fnmatch(dirname, L2A_DS_MASK) == True):
                found = True
                break
        if found == False:
            stderrWrite('No subdirectory in datastrip')
            self.config.exitError()

        if self.config.namingConvention == 'SAFE_STANDARD':
            L3_DS_ID = dirname[17:-7]
            L3_DS_OLD = os.path.join(L3_DS_DIR, dirname)
            L3_DS_DIR = os.path.join(L3_DS_DIR, L3_DS_ID)
            os.rename(L3_DS_OLD, L3_DS_DIR)
        else:
            L3_DS_ID = dirname
            L3_DS_DIR = os.path.join(L3_DS_DIR, L3_DS_ID)

        self.config.L3_DS_ID = L3_DS_ID
        filelist = sorted(os.listdir(L3_DS_DIR))
        found = False
        L2A_DS_MTD_MSK ='S2?_USER_MTD_L2A_DS_*.xml'
        for filename in filelist:
            if (fnmatch.fnmatch(filename, L2A_DS_MTD_MSK) == True):
                L3_DS_OLD = os.path.join(L3_DS_DIR, filename)
                L3_DS_MTD = os.path.join(L3_DS_DIR, 'MTD_DS.xml')
                os.rename(L3_DS_OLD, L3_DS_MTD)
                filename = 'MTD_DS.xml'
                found = True
            elif(fnmatch.fnmatch(filename, 'MTD_DS.xml') == True):
                found = True
                break
        if found == False:
            stderrWrite('No metadata in datastrip')
            self.config.exitError()
        self.config.L3_DS_MTD_XML = os.path.join(L3_DS_DIR, filename)
        xp = L3_XmlParser(self.config, 'DS03')
        if(xp.convert() == False):
            stderrWrite('Error in converting datastrip metadata to level 3.')
            self.logger.fatal('error in converting datastrip metadata to level 3.')
            self.config.exitError()
        xp = L3_XmlParser(self.config, 'DS03')
        ti = xp.getTree('Image_Data_Info', 'Tiles_Information')
        del ti.Tile_List.Tile[:]

        ri = xp.getTree('Image_Data_Info', 'Radiometric_Info')
        qvl = objectify.Element('QUANTIFICATION_VALUES_LIST')
        qvl.BOA_QUANTIFICATION_VALUE = str(int(self.config.dnScale))
        qvl.BOA_QUANTIFICATION_VALUE.attrib['unit'] = 'none'
        qvl.AOT_QUANTIFICATION_VALUE = str(self.config.L2A_AOT_QUANTIFICATION_VALUE)
        qvl.AOT_QUANTIFICATION_VALUE.attrib['unit'] = 'none'
        qvl.WVP_QUANTIFICATION_VALUE = str(self.config.L2A_WVP_QUANTIFICATION_VALUE)
        qvl.WVP_QUANTIFICATION_VALUE.attrib['unit'] = 'cm'
        ri.QUANTIFICATION_VALUES_LIST = qvl

        auxinfo = xp.getRoot('Auxiliary_Data_Info')
        if (xp.getTree('Auxiliary_Data_Info', 'GRI_List')) == False:
            gfn = xp.getTree('Auxiliary_Data_Info', 'GRI_FILENAME')
            del gfn[:]
            gl = etree.Element('GRI_List')
            gl.append(gfn)
            auxinfo.append(gl)
        if (xp.getTree('Auxiliary_Data_Info', 'LUT_List')) == False:
            ll = etree.Element('LUT_List')
            auxinfo.append(ll)
        if (xp.getTree('Auxiliary_Data_Info', 'SNOW_CLIMATOLOGY_MAP')) == False:
            ll = etree.Element('SNOW_CLIMATOLOGY_MAP')
            ll.text = 'None'
            auxinfo.append(ll)
        if (xp.getTree('Auxiliary_Data_Info', 'ESACCI_WaterBodies_Map')) == False:
            ll = etree.Element('ESACCI_WaterBodies_Map')
            ll.text = 'None'
            auxinfo.append(ll)
        if (xp.getTree('Auxiliary_Data_Info', 'ESACCI_LandCover_Map')) == False:
            ll = etree.Element('ESACCI_LandCover_Map')
            ll.text = 'None'
            auxinfo.append(ll)
        if (xp.getTree('Auxiliary_Data_Info', 'ESACCI_SnowCondition_Map_Dir')) == False:
            ll = etree.Element('ESACCI_SnowCondition_Map_Dir')
            ll.text = 'None'
            auxinfo.append(ll)

        xp.export()
        self.createTable()
        return True

    def reinitL3_TargetProduct(self):
        ''' Reinit the L3 target product

            :return: true if succesful
            :rtype: bool

        '''

        L3_DS_ID = None
        L3_TARGET_MASK = '*L03_*'
        dirlist = sorted(os.listdir(self.config.targetDir))
        for L3_TARGET_ID in dirlist:
            if fnmatch.fnmatch(L3_TARGET_ID, L3_TARGET_MASK) == True:
                self.config.L3_TARGET_ID = L3_TARGET_ID
                self.config.L3_TARGET_DIR = os.path.join(self.config.targetDir, L3_TARGET_ID)
                break

        # create user product:
        filelist = sorted(os.listdir(self.config.L3_TARGET_DIR ))
        found = False
        for filename in filelist:
            if (fnmatch.fnmatch(filename, 'MTD_MSIL03.xml') == True):
                found = True
                break
        if found == False:
            stderrWrite('No metadata for user product')
            self.config.exitError()
        self.config.L3_TARGET_MTD_XML = os.path.join(self.config.L3_TARGET_DIR, filename)

        xp = L3_XmlParser(self.config, 'UP03')
        l3qii = xp.getRoot('Quality_Indicators_Info')
        node = objectify.Element('Classification_QI')
        node.attrib['resolution'] = str(self.config.resolution)
        if self.insert(l3qii, node):
            xp.export()

        L3_DS_MASK = 'DS_*'
        DATASTRIP = 'DATASTRIP'
        L3_DS_DIR = os.path.join(self.config.targetDir, L3_TARGET_ID, DATASTRIP)
        dirlist = sorted(os.listdir(L3_DS_DIR))
        for L3_DS_ID in dirlist:
            if fnmatch.fnmatch(L3_DS_ID, L3_DS_MASK) == True:
                self.config.L3_DS_ID = L3_DS_ID
                break
        
        if L3_DS_ID is not None:
            L3_DS_MTD_XML = 'MTD_DS.xml'
            self.config.L3_DS_MTD_XML = os.path.join(L3_DS_DIR, L3_DS_ID, L3_DS_MTD_XML)
            return True
        
        return False

    def createL3_Tile(self, tileId):
        ''' Create an L3 tile

            :param tileId: the tile ID
            :type tileId: string

        '''

        L2A_TILE_ID = tileId
        if self.config.namingConvention == 'SAFE_STANDARD':
            strList = L2A_TILE_ID.split('_')
            L3_TILE_ID = 'L03_' + strList[-2] + '_' + strList[-3] + '_' + strList[-4]
        else:
            L3_TILE_ID = L2A_TILE_ID.replace('L2A_', 'L03_')
            L3_TILE_ID = L3_TILE_ID.replace('USER', 'OPER')

        self.config.L3_TILE_ID = L3_TILE_ID
        sourceDir = self.config.sourceDir
        L2A_UP_ID = self.config.L2A_UP_ID
        L3_TARGET_DIR = self.config.L3_TARGET_DIR
        GRANULE = 'GRANULE'
        QI_DATA = 'QI_DATA'
        L2A_TILE_ID = os.path.join(sourceDir, L2A_UP_ID, GRANULE, L2A_TILE_ID)
        L3_TILE_ID = os.path.join(L3_TARGET_DIR, GRANULE, L3_TILE_ID)

        try:
            os.mkdir(L3_TILE_ID)
            os.mkdir(os.path.join(L3_TILE_ID, QI_DATA))
            self.config.logger.info('new working directory is: ' + L3_TILE_ID)
        except:
            pass

        filelist = sorted(os.listdir(L2A_TILE_ID))
        found = False
        if self.config.namingConvention == 'SAFE_STANDARD':
            L2A_UP_MASK = '*_MTD_L2A_TL_*.xml'
        else:
            L2A_UP_MASK = 'MTD_TL.xml'
        for filename in filelist:
            if(fnmatch.fnmatch(filename, L2A_UP_MASK) == True):
                found = True
                break
        if found == False:
            self.config.logger.fatal('No metadata in tile')
            self.config.exitError()

        assert isinstance(filename, object)
        L2A_TILE_MTD_XML = os.path.join(L2A_TILE_ID, filename)
        L3_TILE_MTD_XML = 'MTD_TL.xml'
        L3_TILE_MTD_XML = os.path.join(L3_TILE_ID, L3_TILE_MTD_XML)
        copy_file(L2A_TILE_MTD_XML, L3_TILE_MTD_XML)
        self.config.L2A_TILE_MTD_XML = L2A_TILE_MTD_XML
        xp = L3_XmlParser(self.config, 'T2A')
        TILE_ID_2A = xp.getTree('General_Info', 'TILE_ID')
        if TILE_ID_2A == False:
            # it's a version 14.2 metadata:
            TILE_ID_2A = xp.getTree('General_Info', 'TILE_ID_2A')

        self.config.TILE_ID_2A = TILE_ID_2A.text
        if xp.convert() != 0:
            xp = L3_XmlParser(self.config, 'T2A')
        xp.validate()
        self.config.L3_TILE_MTD_XML = L3_TILE_MTD_XML

        #update tile and datastrip id in metadata file.
        xp = L3_XmlParser(self.config, 'T03')
        if(xp.convert() == False):
            self.logger.fatal('error in converting tile metadata to level 3')
            self.exitError()
        xp = L3_XmlParser(self.config, 'T03')
        try:
            tree = xp.getTree('General_Info', 'L1C_TILE_ID')
            del tree[:]
        except:
            pass
        try:
            # remove all QI items from the past, as they will be calculated
            # directly from contents of images
            tree = xp.getTree('Quality_Indicators_Info', 'L1C_Image_Content_QI')
            del tree[:]
            tree = xp.getTree('Quality_Indicators_Info', 'L2A_Image_Content_QI')
            del tree[:]
            tree = xp.getTree('Quality_Indicators_Info', 'L1C_Pixel_Level_QI')
            del tree[:]
            tree = xp.getTree('Quality_Indicators_Info', 'L2A_Pixel_Level_QI')
            del tree[:]
            tree = xp.getTree('Quality_Indicators_Info', 'PVI_FILENAME')
            del tree[:]
        except:
            try:
                # test on version 14.5 data:
                tree = xp.getTree('Quality_Indicators_Info', 'Image_Content_QI')
                del tree[:]
                tree = xp.getTree('Quality_Indicators_Info', 'Pixel_Level_QI')
                del tree[:]
                tree = xp.getTree('Quality_Indicators_Info', 'PVI_FILENAME')
                del tree[:]
            except:
                pass
        xp.export()

        # read updated file and append new items:
        # create the first three enties of the Quality Measures:
        xp = L3_XmlParser(self.config, 'T03')
        root = xp.getRoot('Quality_Indicators_Info')

        tree = objectify.Element('Pixel_Level_QI')
        tree.attrib['resolution'] = str(self.config.resolution)
        root.append(tree)

        tree = objectify.Element('Classification_QI')
        tree.attrib['resolution'] = str(self.config.resolution)
        root.append(tree)

        tree = objectify.Element('Mosaic_QI')
        tree.attrib['resolution'] = str(self.config.resolution)
        root.append(tree)

        xp.export()

        #update tile id in ds metadata file.
        xp = L3_XmlParser(self.config, 'UP2A')
        if self.config.productVersion > 14.2:
            pi = xp.getTree('General_Info', 'Product_Info')
            gr2a = pi.Product_Organisation.Granule_List.Granule
        else:
            pi = xp.getTree('General_Info', 'L2A_Product_Info')
            try:
                gr2a = pi.L2A_Product_Organisation.Granule_List.Granule
            except: # it's a boring old 13.1 product:
                gr2a = pi.L2A_Product_Organisation.Granule_List.Granules
        gi2a = gr2a.attrib['granuleIdentifier']
        gi03 = gi2a.replace('L2A_', 'L03_')
        xp = L3_XmlParser(self.config, 'DS03')
        ti = xp.getTree('Image_Data_Info', 'Tiles_Information')
        ti.Tile_List.append(objectify.Element('Tile', tileId = gi03))
        xp.export()
        return
    
    def reinitL2A_Tile(self):
        ''' Reinit an L2A tile

            :param tileId: the tile ID
            :type tileId: string

        '''

        if self.config.namingConvention == 'SAFE_STANDARD':
            L2A_MTD_MASK = 'S2?_*_MTD_L2A_TL_*.xml'
        else:
            L2A_MTD_MASK = 'MTD_TL.xml'

        L2A_UP_DIR = self.config.L2A_UP_DIR
        GRANULE = 'GRANULE'
        L2A_TILE_ID = os.path.join(L2A_UP_DIR, GRANULE, self.config.L2A_TILE_ID)
        dirlist = sorted(os.listdir(L2A_TILE_ID))
        for L2A_TILE_MTD_XML in dirlist:
            if fnmatch.fnmatch(L2A_TILE_MTD_XML, L2A_MTD_MASK):
                self.config.L2A_TILE_MTD_XML = os.path.join(L2A_TILE_ID, L2A_TILE_MTD_XML)
                break
        return
    
    def reinitL3_Tile(self, tileId):
        ''' Reinit an L3 tile

            :param tileId: the tile ID
            :type tileId: string

        '''

        L3_MTD_MASK = 'MTD_TL.xml'
        L3_TARGET_DIR = self.config.L3_TARGET_DIR
        GRANULE = 'GRANULE'
        self.config.L3_TILE_ID = tileId
        xp = L3_XmlParser(self.config, 'T2A')
        TILE_ID_2A = xp.getTree('General_Info', 'TILE_ID')
        if TILE_ID_2A == False:
            # its' a PSD 14.2 tile:
            TILE_ID_2A = xp.getTree('General_Info', 'TILE_ID_2A')

        self.config.TILE_ID_2A = TILE_ID_2A.text
        L3_TILE_ID = os.path.join(L3_TARGET_DIR, GRANULE, tileId)
        dirlist = sorted(os.listdir(L3_TILE_ID))
        for L3_TILE_MTD_XML in dirlist:
            if fnmatch.fnmatch(L3_TILE_MTD_XML, L3_MTD_MASK):
                self.config.L3_TILE_MTD_XML = os.path.join(L3_TILE_ID, L3_TILE_MTD_XML)
                break

        # append the QI headers for the new resolutions:
        xp = L3_XmlParser(self.config, 'T03')
        qii = xp.getRoot('Quality_Indicators_Info')

        node = objectify.Element('Pixel_Level_QI')
        if self.insert(qii, node):
            xp.export()
        node = objectify.Element('Classification_QI')
        if self.insert(qii, node):
            xp.export()
        node = objectify.Element('Mosaic_QI')
        if self.insert(qii, node):
            xp.export()

        return

    def insert(self, tree, node):
        ''' A support class, inserting a new node at the correct location in the given tree.

            :param tree: the QI subtree.
            :type tree: an Objectify Element.
            :param node: the QI node to insert.
            :type node: an Objectify Element.
            :return: true if succesful
            :rtype: bool

        '''

        selfRes = self.config.resolution
        node.attrib['resolution'] = str(selfRes)
        maxRes = 60
        count = -1

        for e in tree.getchildren():
            count += 1
            if e.tag == node.tag:
                for i in range(len(e)):
                    resolution = int(e[i].attrib['resolution'])
                    if selfRes == resolution:
                        return False

                i = len(e)
                resolution = int(e[0].attrib['resolution'])
                try:
                    if selfRes < resolution:
                        tree.insert(count, node)
                        break
                    elif selfRes < maxRes:
                        tree.insert(count+1, node)
                        break
                    else:
                        tree.insert(count+i, node)
                        break
                except:
                    return False

        return True

    def updateUserProduct(self, userProduct):
        ''' Update the current user product.
            Check if at target product is present.

            :param userProduct: the user product identifier.
            :type userProduct: str
            :return: true, if target product exists.
            :rtype: boolean

        '''
        self.config.L2A_UP_ID = userProduct
        self.config.L2A_UP_DIR = os.path.join(self.config.sourceDir, userProduct)
        if self.config.namingConvention == 'SAFE_STANDARD':
            filelist = sorted(os.listdir(self.config.L2A_UP_DIR))
            filemask = 'S2A_USER_MTD_*.xml'
            for file in filelist:
                if fnmatch.fnmatch(file, filemask):
                    self.config.L2A_UP_MTD_XML = os.path.join(self.config.L2A_UP_DIR, file)
                    break
        else:
            self.config.L2A_UP_MTD_XML = os.path.join(self.config.L2A_UP_DIR, 'MTD_MSIL2A.xml')

        if self.existL3_TargetProduct(userProduct) == False:
            stderrWrite('directory "%s" L3 target product is missing\n.' % self.config.targetDir)
            self.config.exitError()
        return True

    def postProcessing(self):
        ''' update the user product and product metadata,
            copy the logfile to QI data as a report,
            Check if at target product is present.

        '''

        self.updateProductMetadata()
        xp = L3_XmlParser(self.config, 'UP03')
        gipp = xp.getTree('Auxiliary_Data_Info', 'GIPP_LIST')
        filename = 'L3_GIPP'
        gippFn = etree.Element('GIPP_FILENAME', type='GIP_L3', version='%04d' % long(self.config.processorVersion.replace('.', '')))
        gippFn.text = filename
        gipp.append(gippFn)
        xp.export()

        dirname, basename = os.path.split(self.config.L3_TILE_MTD_XML)
        report = basename.replace('.xml', '_Report.xml')
        report = os.path.join(dirname, 'QI_DATA', report)
        
        if((os.path.isfile(self.config.fnLog)) == False):
            self.logger.fatal('Missing file: ' + self.config.fnLog)
            self.config.exitError()

        f = open(self.config.fnLog, 'a')
        f.write('</Sen2Three_Level-3_Report_File>')
        f.flush()
        f.close()
        copy_file(self.config.fnLog, report)

        return

    def createTable(self):
        ''' Create a HDF5 table
        '''

        dbname = os.path.join(self.config.L3_TARGET_DIR, '.database.h5')
        h5file = tables.open_file(dbname, mode="w", title='Product')
        grp = h5file.create_group("/", 'group1', 'Statistics')
        h5file.create_table(grp, 'classes', Particle, 'Classes')
        h5file.create_table(grp, 'bestval', BestVal, 'Best Values')
        table = h5file.root.group1.bestval
        row = table.row
        row['AOT_MEAN'] = 1.0
        row['SZA_MEAN'] = 0.0
        row['DATE_TIME'] = 0.0
        row.append()
        h5file.close()
        return

    def setTableVal(self, key, value):
        ''' Check if one of the two criteria for termination is reached:
            :param key: the search key.
            :type key: str
            :param value: the value to be passed.
            :type value: float
            :return: false if wrong key
            :rtype: bool
        '''
        result = True
        dbname = os.path.join(self.config.L3_TARGET_DIR, '.database.h5')
        h5file = tables.open_file(dbname, mode='a')
        table = h5file.root.group1.bestval # default
        try:
            for row in table:
                row[key] = value
                row.update()
        except:
            result = False
        finally:
            table.flush()
            h5file.close()
            return result

    def getTableVal(self, key):
        ''' Check if one of the two criteria for termination is reached:
            :param key: the search key.
            :type key: str
            :return: the value
            :rtype: bool
        '''
        dbname = os.path.join(self.config.L3_TARGET_DIR, '.database.h5')
        h5file = tables.open_file(dbname, mode='a')
        table = h5file.root.group1.bestval # default
        try:
            for row in table.iterrows():
                result = row[key]
        except:
            result = False
        finally:
            table.flush()
            h5file.close()
            return result

    def updateTableRow(self, classification):
        ''' Update the statistics of a row in the table.

            :param classification: the statistics
            :type classification: an Objectify element

        '''
        dbname = os.path.join(self.config.L3_TARGET_DIR, '.database.h5')
        tileID = self.config.L3_TILE_ID[-13:-7] + '_' + str(self.config.resolution)
        h5file = tables.open_file(dbname, mode='a')
        table = h5file.root.group1.classes # default
        tileFound = False

        for row in table:
            if row['TILE_ID'] == tileID:
                tileFound = True
                row['TILES_COUNT'] += 1
                row['TOTAL_PIXELS'] = classification.TOTAL_PIXEL_COUNT.pyval
                row['DATA_PIXELS'] = classification.DATA_PIXEL_COUNT.pyval
                row['NODATA_PIXELS'] = classification.NODATA_PIXEL_COUNT.pyval
                row['GOOD_PIXELS'] = classification.GOOD_PIXEL_COUNT.pyval
                row['BAD_PIXELS'] = classification.BAD_PIXEL_COUNT.pyval
                row['SAT_DEF_PIXELS'] = classification.SATURATED_DEFECTIVE_PIXEL_COUNT.pyval
                row['DARK_PIXELS'] = classification.DARK_FEATURES_COUNT.pyval
                row['CLOUD_SHADOWS'] = classification.CLOUD_SHADOWS_COUNT.pyval
                row['VEGETATION'] = classification.VEGETATION_COUNT.pyval
                row['NOT_VEGETATED'] = classification.NOT_VEGETATED_COUNT.pyval
                row['WATER'] = classification.WATER_COUNT.pyval
                row['UNCLASSIFIED'] = classification.UNCLASSIFIED_COUNT.pyval
                row['MED_PROBA_CLOUDS'] = classification.MEDIUM_PROBA_CLOUDS_COUNT.pyval
                row['HIGH_PROBA_CLOUDS'] = classification.HIGH_PROBA_CLOUDS_COUNT.pyval
                row['THIN_CIRRUS'] = classification.THIN_CIRRUS_COUNT.pyval
                row['SNOW_ICE'] = classification.SNOW_ICE_COUNT.pyval
                row.update()

        if not tileFound:
            row = table.row
            row['TILE_ID'] = tileID
            row['RESOLUTION'] = self.config.resolution
            row['TILES_COUNT'] = 1
            row['TOTAL_PIXELS'] = classification.TOTAL_PIXEL_COUNT.pyval
            row['DATA_PIXELS'] = classification.DATA_PIXEL_COUNT.pyval
            row['NODATA_PIXELS'] = classification.NODATA_PIXEL_COUNT.pyval
            row['GOOD_PIXELS'] = classification.GOOD_PIXEL_COUNT.pyval
            row['BAD_PIXELS'] = classification.BAD_PIXEL_COUNT.pyval
            row['SAT_DEF_PIXELS'] = classification.SATURATED_DEFECTIVE_PIXEL_COUNT.pyval
            row['DARK_PIXELS'] = classification.DARK_FEATURES_COUNT.pyval
            row['CLOUD_SHADOWS'] = classification.CLOUD_SHADOWS_COUNT.pyval
            row['VEGETATION'] = classification.VEGETATION_COUNT.pyval
            row['NOT_VEGETATED'] = classification.NOT_VEGETATED_COUNT.pyval
            row['WATER'] = classification.WATER_COUNT.pyval
            row['UNCLASSIFIED'] = classification.UNCLASSIFIED_COUNT.pyval
            row['MED_PROBA_CLOUDS'] = classification.MEDIUM_PROBA_CLOUDS_COUNT.pyval
            row['HIGH_PROBA_CLOUDS'] = classification.HIGH_PROBA_CLOUDS_COUNT.pyval
            row['THIN_CIRRUS'] = classification.THIN_CIRRUS_COUNT.pyval
            row['SNOW_ICE'] = classification.SNOW_ICE_COUNT.pyval
            row.append()

        table.flush()
        h5file.close()
        return

    def checkCriteriaForTermination(self):
        ''' Check if one of the two criteria for termination is reached:

            :return: true if reached
            :rtype: bool
        '''

        dbname = os.path.join(self.config.L3_TARGET_DIR, '.database.h5')
        h5file = tables.open_file(dbname, mode='r')
        table = h5file.root.group1.classes
        dataPixelCount = 0
        badPixelCount = 0
        lowProbaCloudsCount = 0
        medProbaCloudsCount = 0
        hiProbaCloudsCount = 0
        for row in table.iterrows():
            if row['RESOLUTION'] == self.config.resolution:
                dataPixelCount += row['DATA_PIXELS']
                badPixelCount += row['BAD_PIXELS']
                lowProbaCloudsCount += row['UNCLASSIFIED']
                medProbaCloudsCount += row['MED_PROBA_CLOUDS']
                hiProbaCloudsCount += row['HIGH_PROBA_CLOUDS']

        table.flush()
        h5file.close()

        dataPixelCount = float(dataPixelCount) * 0.01
        badPixelPercentage = float32(badPixelCount) / dataPixelCount
        lowProbaCloudsPercentage = float32(lowProbaCloudsCount) / dataPixelCount
        medProbaCloudsPercentage = float32(medProbaCloudsCount) / dataPixelCount
        hiProbaCloudsPercentage = float32(hiProbaCloudsCount) / dataPixelCount

        if self.config.maxCloudProbability > lowProbaCloudsPercentage and \
            self.config.maxCloudProbability > medProbaCloudsPercentage and \
            self.config.maxCloudProbability > hiProbaCloudsPercentage:
            self.config.timestamp('L3_Process: cloud probability reached configured limit')
            return True
        elif self.config.maxInvalidPixelsPercentage > badPixelPercentage:
            self.config.timestamp('L3_Process: invalid pixel percentage reached configured limit')
            return True

        return False

    def updateProductMetadata(self):
        ''' Update the product metadata for each new synthesis.
        '''

        dbname = os.path.join(self.config.L3_TARGET_DIR, '.database.h5')
        h5file = tables.open_file(dbname, mode='a')
        table = h5file.root.group1.classes
        
        totalPixelCount = 0
        dataPixelCount = 0
        nodataPixelCount = 0
        goodPixelCount = 0
        badPixelCount = 0
        satDefPixelCount = 0
        darkFeaturesCount = 0
        cloudShadowsCount = 0
        vegetationCount = 0
        bareSoilsCount = 0
        waterCount = 0
        lowProbaCloudsCount = 0
        medProbaCloudsCount = 0
        hiProbaCloudsCount = 0
        thinCirrusCount = 0
        snowIceCount = 0

        for row in table.iterrows():
            if row['RESOLUTION'] == self.config.resolution:
                totalPixelCount += row['TOTAL_PIXELS']
                dataPixelCount += row['DATA_PIXELS']
                nodataPixelCount += row['NODATA_PIXELS']
                goodPixelCount += row['GOOD_PIXELS']
                badPixelCount += row['BAD_PIXELS']
                satDefPixelCount += row['SAT_DEF_PIXELS']
                darkFeaturesCount += row['DARK_PIXELS']
                cloudShadowsCount +=row['CLOUD_SHADOWS']
                vegetationCount += row['VEGETATION']
                bareSoilsCount += row['NOT_VEGETATED']
                waterCount += row['WATER']
                lowProbaCloudsCount += row['UNCLASSIFIED']
                medProbaCloudsCount += row['MED_PROBA_CLOUDS']
                hiProbaCloudsCount += row['HIGH_PROBA_CLOUDS']
                thinCirrusCount += row['THIN_CIRRUS']
                snowIceCount += row['SNOW_ICE']

        table.flush()
        h5file.close()

        totalPixelCount = float(totalPixelCount) * 0.01
        dataPixelCount = float(dataPixelCount) * 0.01
        dataPixelPercentage = float32(dataPixelCount) / totalPixelCount * 100
        nodataPixelPercentage = float32(nodataPixelCount) / totalPixelCount
        goodPixelPercentage = float32(goodPixelCount) / dataPixelCount
        badPixelPercentage = float32(badPixelCount) / dataPixelCount
        satDefPixelPercentage = float32(satDefPixelCount) / dataPixelCount
        darkFeaturesPercentage = float32(darkFeaturesCount) / dataPixelCount
        cloudShadowsPercentage = float32(cloudShadowsCount) / dataPixelCount
        vegetationPercentage = float32(vegetationCount) / dataPixelCount
        bareSoilsPercentage = float32(bareSoilsCount) / dataPixelCount
        waterPercentage = float32(waterCount) / dataPixelCount
        lowProbaCloudsPercentage = float32(lowProbaCloudsCount) / dataPixelCount
        medProbaCloudsPercentage = float32(medProbaCloudsCount) / dataPixelCount
        hiProbaCloudsPercentage = float32(hiProbaCloudsCount) / dataPixelCount
        thinCirrusPercentage = float32(thinCirrusCount) / dataPixelCount
        snowIcePercentage = float32(snowIceCount) / dataPixelCount


        classificationQI = objectify.Element('Classification_QI')
        classificationQI.attrib['resolution'] = str(self.config.resolution)
        classificationQI.append(objectify.Element('TOTAL_PIXEL_COUNT'))
        classificationQI.append(objectify.Element('DATA_PIXEL_COUNT'))
        classificationQI.append(objectify.Element('DATA_PIXEL_PERCENTAGE'))
        classificationQI.append(objectify.Element('NODATA_PIXEL_COUNT'))
        classificationQI.append(objectify.Element('NODATA_PIXEL_PERCENTAGE'))
        classificationQI.append(objectify.Element('GOOD_PIXEL_COUNT'))
        classificationQI.append(objectify.Element('GOOD_PIXEL_PERCENTAGE'))
        classificationQI.append(objectify.Element('BAD_PIXEL_COUNT'))
        classificationQI.append(objectify.Element('BAD_PIXEL_PERCENTAGE'))
        classificationQI.append(objectify.Element('SATURATED_DEFECTIVE_PIXEL_COUNT'))
        classificationQI.append(objectify.Element('SATURATED_DEFECTIVE_PIXEL_PERCENTAGE'))
        classificationQI.append(objectify.Element('DARK_FEATURES_COUNT'))
        classificationQI.append(objectify.Element('DARK_FEATURES_PERCENTAGE'))
        classificationQI.append(objectify.Element('CLOUD_SHADOWS_COUNT'))
        classificationQI.append(objectify.Element('CLOUD_SHADOWS_PERCENTAGE'))
        classificationQI.append(objectify.Element('VEGETATION_COUNT'))
        classificationQI.append(objectify.Element('VEGETATION_PERCENTAGE'))
        classificationQI.append(objectify.Element('NOT_VEGETATED_COUNT'))
        classificationQI.append(objectify.Element('NOT_VEGETATED_PERCENTAGE'))
        classificationQI.append(objectify.Element('WATER_COUNT'))
        classificationQI.append(objectify.Element('WATER_PERCENTAGE'))
        classificationQI.append(objectify.Element('UNCLASSIFIED_COUNT'))
        classificationQI.append(objectify.Element('UNCLASSIFIED_PERCENTAGE'))
        classificationQI.append(objectify.Element('MEDIUM_PROBA_CLOUDS_COUNT'))
        classificationQI.append(objectify.Element('MEDIUM_PROBA_CLOUDS_PERCENTAGE'))
        classificationQI.append(objectify.Element('HIGH_PROBA_CLOUDS_COUNT'))
        classificationQI.append(objectify.Element('HIGH_PROBA_CLOUDS_PERCENTAGE'))
        classificationQI.append(objectify.Element('THIN_CIRRUS_COUNT'))
        classificationQI.append(objectify.Element('THIN_CIRRUS_PERCENTAGE'))
        classificationQI.append(objectify.Element('SNOW_ICE_COUNT'))
        classificationQI.append(objectify.Element('SNOW_ICE_PERCENTAGE'))

        classificationQI.TOTAL_PIXEL_COUNT = int(totalPixelCount * 100)
        classificationQI.DATA_PIXEL_COUNT = int(dataPixelCount * 100)
        classificationQI.DATA_PIXEL_PERCENTAGE = dataPixelPercentage
        classificationQI.NODATA_PIXEL_COUNT = nodataPixelCount
        classificationQI.NODATA_PIXEL_PERCENTAGE = nodataPixelPercentage
        classificationQI.GOOD_PIXEL_COUNT = goodPixelCount
        classificationQI.GOOD_PIXEL_PERCENTAGE = goodPixelPercentage
        classificationQI.BAD_PIXEL_COUNT = badPixelCount
        classificationQI.BAD_PIXEL_PERCENTAGE = badPixelPercentage
        classificationQI.SATURATED_DEFECTIVE_PIXEL_COUNT = satDefPixelCount
        classificationQI.SATURATED_DEFECTIVE_PIXEL_PERCENTAGE = satDefPixelPercentage
        classificationQI.DARK_FEATURES_COUNT = darkFeaturesCount
        classificationQI.DARK_FEATURES_PERCENTAGE = darkFeaturesPercentage
        classificationQI.CLOUD_SHADOWS_COUNT = cloudShadowsCount
        classificationQI.CLOUD_SHADOWS_PERCENTAGE = cloudShadowsPercentage
        classificationQI.VEGETATION_COUNT = vegetationCount
        classificationQI.VEGETATION_PERCENTAGE = vegetationPercentage
        classificationQI.NOT_VEGETATED_COUNT = bareSoilsCount
        classificationQI.NOT_VEGETATED_PERCENTAGE = bareSoilsPercentage
        classificationQI.WATER_COUNT = waterCount
        classificationQI.WATER_PERCENTAGE = waterPercentage
        classificationQI.UNCLASSIFIED_COUNT = lowProbaCloudsCount
        classificationQI.UNCLASSIFIED_PERCENTAGE = lowProbaCloudsPercentage
        classificationQI.MEDIUM_PROBA_CLOUDS_COUNT = medProbaCloudsCount
        classificationQI.MEDIUM_PROBA_CLOUDS_PERCENTAGE = medProbaCloudsPercentage
        classificationQI.HIGH_PROBA_CLOUDS_COUNT = hiProbaCloudsCount
        classificationQI.HIGH_PROBA_CLOUDS_PERCENTAGE = hiProbaCloudsPercentage
        classificationQI.THIN_CIRRUS_COUNT = thinCirrusCount
        classificationQI.THIN_CIRRUS_PERCENTAGE = thinCirrusPercentage
        classificationQI.SNOW_ICE_COUNT = snowIceCount
        classificationQI.SNOW_ICE_PERCENTAGE = snowIcePercentage

        xp = L3_XmlParser(self.config, 'UP03')
        l3qi = xp.getTree('Quality_Indicators_Info', 'Classification_QI')
        l3qiLen = len(l3qi)
        for i in range(l3qiLen):
            if int(l3qi[i].attrib['resolution']) == self.config.resolution:
                l3qi[i].clear()
                l3qi[i] = classificationQI
                xp.export()
                break

        return True
