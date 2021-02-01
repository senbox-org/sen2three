#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os, fnmatch
import glymur
from PIL import Image
from scipy import ndimage

from numpy import *
from tables import *
from lxml import etree, objectify
from tables.description import *
from distutils.dir_util import mkpath
from distutils.file_util import copy_file
from L3_XmlParser import L3_XmlParser
from L3_Library import showImage

class Particle(IsDescription):
    bandName = StringCol(8)
    projectionRef = StringCol(512)
    geoTransformation = Int32Col(shape=6)
    rasterXSize = UInt16Col()
    rasterYSize = UInt16Col()
    rasterCount = UInt8Col()

class L3_Tables(object):
    ''' A support class, managing the conversion of the JPEG-2000 based input data
        to an internal format based on HDF5 (pyTables). Provide a high performance
        access to the image data for all bands of all tiles to be processed.
        
        :param config: the config object for the current tile.
        :type config: a reference to the L3_Config object.

    '''

    def __init__(self, product):
        self._product = product
        self._config = product.config

        AUX_DATA = 'AUX_DATA'
        IMG_DATA = 'IMG_DATA'
        QI_DATA = 'QI_DATA'
        GRANULE = 'GRANULE'

        if os.name == 'posix':
            self._DEV0 = ' > /dev/null'
        else:
            self._DEV0 = ' > NUL'

        # Resolution:
        self._resolution = int(self._config.resolution)
        if(self._resolution == 10):
            self._bandIndex = [1,2,3,7]
            self._nBands = 4
            bandDir = 'R10m'
        elif(self._resolution == 20):
            self._bandIndex = [1,2,3,4,5,6,8,11,12]
            self._nBands = 9
            bandDir = 'R20m'
        elif(self._resolution == 60):
            self._bandIndex = [0,1,2,3,4,5,6,8,9,11,12]
            self._nBands = 11
            bandDir = 'R60m'

        BANDS = bandDir
        self._rows = None
        self._cols = None
        self._granuleType = None
        # generate new Tile ID:
        # check whether a tile with same ORBIT ID already exists, if yes use this folder.
        # else create a new tile folder with corresponding orbit ID
        L2A_TILE_ID = self._config.L2A_TILE_ID
        L3_TILE_MSK = 'L03_*'
        strList = L2A_TILE_ID.split('_')
        if self._config.namingConvention == 'SAFE_STANDARD':
            ORBIT_ID = strList[-2]
        else:
            ORBIT_ID = strList[1]
        L3_TARGET_ID = self._config.L3_TARGET_ID
        tiles = os.path.join(self._config.targetDir, L3_TARGET_ID, GRANULE)
        files = sorted(os.listdir(tiles))
        reinit = False
        for L3_TILE_ID in files:
            if fnmatch.fnmatch(L3_TILE_ID, L3_TILE_MSK):
                if ORBIT_ID in L3_TILE_ID:
                 # target exists, will be used:
                    product.reinitL2A_Tile()
                    product.reinitL3_Tile(L3_TILE_ID)
                    reinit = True
                    break
        # target does not exist, must be created:
        if reinit == False:
            product.createL3_Tile(L2A_TILE_ID)

        L3_TILE_ID = self.config.L3_TILE_ID
        if self.config.namingConvention == 'SAFE_STANDARD':
            L3_TILE_ID_SHORT = self.config.L3_TILE_ID[:55]
        else:
            L3_TILE_ID_SHORT = self.config.L3_TILE_ID

        L2A_TILE_ID = os.path.join(self.config.L2A_UP_DIR, GRANULE, L2A_TILE_ID)
        L3_TILE_ID = os.path.join(self.config.L3_TARGET_DIR, GRANULE, L3_TILE_ID)
        self._L2A_ImgDataDir = os.path.join(L2A_TILE_ID, IMG_DATA)
        self._L3_ImgDataDir = os.path.join(L3_TILE_ID, IMG_DATA)
        self._L2A_bandDir = os.path.join(self._L2A_ImgDataDir, BANDS)
        self._L3_bandDir = os.path.join(self._L3_ImgDataDir, BANDS)

        if not os.path.exists(self._L3_bandDir):
            mkpath(self._L3_bandDir)

        self._L2A_QualityDataDir = os.path.join(L2A_TILE_ID, QI_DATA)
        self._L3_QualityDataDir = os.path.join(L3_TILE_ID, QI_DATA)
        self._L3_AuxDataDir = os.path.join(L3_TILE_ID, AUX_DATA)

        if not os.path.exists(self._L3_AuxDataDir):
            mkpath(self._L3_AuxDataDir)
            # copy configuration to AUX dir:
            basename = os.path.basename(self._config.L3_TILE_MTD_XML)
            fnAux = basename.replace('MTD', 'GIP')
            target = os.path.join(self._L3_AuxDataDir, fnAux)
            copy_file(self._config.configFn, target)

        if not os.path.exists(self._L3_QualityDataDir):
            mkpath(self._L3_QualityDataDir)

        self._imageDatabase = os.path.join(self._L3_bandDir, '.database.h5')
        self._TmpFile = os.path.join(self._L3_bandDir, '.tmpfile_')

        self._L3_Tile_PLT_File = os.path.join(self._L3_QualityDataDir,
            L3_TILE_ID_SHORT + '_PLT_' + str(self.config.getNrTilesProcessed()+1) + '.png')

        # Product Levels:
        self._productLevel = ['L2A','L3']
        
        # the mapping of the product levels
        self._L2A = 1
        self._L03 = 2

        # Band Names:
        self._bandNames = ['B01','B02','B03','B04','B05','B06','B07','B08','B8A',\
                        'B09','B10','B11','B12','DEM','SCL','SNW','CLD','AOT',\
                        'WVP','VIS','SCM','PRV','ILU','SLP','ASP','HAZ','SDW',\
                        'DDV','HCW','ELE', 'PWC', 'MSL', 'OZO', 'TCI', 'MSC']
        
        # the mapping of the bands
        self._B01 = 0
        self._B02 = 1
        self._B03 = 2
        self._B04 = 3
        self._B05 = 4
        self._B06 = 5
        self._B07 = 6
        self._B08 = 7
        self._B8A = 8
        self._B09 = 9
        self._B10 = 10
        self._B11 = 11
        self._B12 = 12
        self._DEM = 13
        self._SCL = 14
        self._SNW = 15
        self._CLD = 16
        self._AOT = 17
        self._WVP = 18
        self._VIS = 19
        self._SCM = 20
        self._PRV = 21
        self._ILU = 22
        self._SLP = 23
        self._ASP = 24
        self._HAZ = 25
        self._SDW = 26
        self._DDV = 27
        self._HCW = 28
        self._ELE = 29
        self._PWC = 30
        self._MSL = 31
        self._OZO = 32
        self._TCI = 33
        self._MSC = 34

        self._geobox = None
        self._config.logger.debug('Module L3_Tables initialized with resolution %d' % self._resolution)

        return

    def get_l_3_tile_plt_file(self):
        return self._L3_Tile_PLT_File


    def set_l_3_tile_plt_file(self, value):
        self._L3_Tile_PLT_File = value


    def del_l_3_tile_plt_file(self):
        del self._L3_Tile_PLT_File


    def get_msc(self):
        return self._MSC


    def set_msc(self, value):
        self._MSC = value


    def del_msc(self):
        del self._MSC


    def get_aot(self):
        return self._AOT


    def set_aot(self, value):
        self._AOT = value


    def del_aot(self):
        del self._AOT


    def getBandNameFromIndex(self, bandIndex):
        return self._bandNames[bandIndex]


    def get_band_bandIndex(self):
        return self._bandIndex


    def get_n_bands(self):
        return self._nBands


    def get_db_name(self):
        return self._dbName


    def set_band_bandIndex(self, value):
        self._bandIndex = value


    def set_n_bands(self, value):
        self._nBands = value


    def set_db_name(self, value):
        self._dbName = value


    def del_band_bandIndex(self):
        del self._bandIndex


    def del_n_bands(self):
        del self._nBands


    def del_db_name(self):
        del self._dbName


        # end mapping of bands

    def __exit__(self):
        sys.exit(-1)


    def __del__(self):
        self.config.logger.debug('Module L3_Tables deleted')


    def get_config(self):
        return self._config


    def set_config(self, value):
        self._config = value


    def del_config(self):
        del self._config


    def get_product(self):
        return self._product


    def set_product(self, value):
        self._product = value


    def del_product(self):
        del self._product

    def get_b01(self):
        return self._B01


    def get_b02(self):
        return self._B02


    def get_b03(self):
        return self._B03


    def get_b04(self):
        return self._B04


    def get_b05(self):
        return self._B05


    def get_b06(self):
        return self._B06


    def get_b07(self):
        return self._B07


    def get_b08(self):
        return self._B08


    def get_b8a(self):
        return self._B8A


    def get_b09(self):
        return self._B09


    def get_b10(self):
        return self._B10


    def get_b11(self):
        return self._B11


    def get_b12(self):
        return self._B12


    def get_scl(self):
        return self._SCL


    def get_qsn(self):
        return self._SNW


    def get_qcl(self):
        return self._CLD


    def get_prv(self):
        return self._PRV


    def get_tci(self):
        return self._TCI


    def set_b01(self, value):
        self._B01 = value


    def set_b02(self, value):
        self._B02 = value


    def set_b03(self, value):
        self._B03 = value


    def set_b04(self, value):
        self._B04 = value


    def set_b05(self, value):
        self._B05 = value


    def set_b06(self, value):
        self._B06 = value


    def set_b07(self, value):
        self._B07 = value


    def set_b08(self, value):
        self._B08 = value


    def set_b8a(self, value):
        self._B8A = value


    def set_b09(self, value):
        self._B09 = value


    def set_b10(self, value):
        self._B10 = value


    def set_b11(self, value):
        self._B11 = value


    def set_b12(self, value):
        self._B12 = value


    def set_dem(self, value):
        self._DEM = value


    def set_scl(self, value):
        self._SCL = value


    def set_qsn(self, value):
        self._SNW = value


    def set_qcl(self, value):
        self._CLD = value


    def set_prv(self, value):
        self._PRV = value


    def set_tci(self, value):
        self._TCI = value


    def del_b01(self):
        del self._B01


    def del_b02(self):
        del self._B02


    def del_b03(self):
        del self._B03


    def del_b04(self):
        del self._B04


    def del_b05(self):
        del self._B05


    def del_b06(self):
        del self._B06


    def del_b07(self):
        del self._B07


    def del_b08(self):
        del self._B08


    def del_b8a(self):
        del self._B8A


    def del_b09(self):
        del self._B09


    def del_b10(self):
        del self._B10


    def del_b11(self):
        del self._B11


    def del_b12(self):
        del self._B12


    def del_scl(self):
        del self._SCL


    def del_qsn(self):
        del self._SNW


    def del_qcl(self):
        del self._CLD


    def del_prv(self):
        del self._PRV


    def del_tci(self):
        del self._TCI


    AOT = property(get_aot, set_aot, del_aot)
    B01 = property(get_b01, set_b01, del_b01)
    B02 = property(get_b02, set_b02, del_b02)
    B03 = property(get_b03, set_b03, del_b03)
    B04 = property(get_b04, set_b04, del_b04)
    B05 = property(get_b05, set_b05, del_b05)
    B06 = property(get_b06, set_b06, del_b06)
    B07 = property(get_b07, set_b07, del_b07)
    B08 = property(get_b08, set_b08, del_b08)
    B8A = property(get_b8a, set_b8a, del_b8a)
    B09 = property(get_b09, set_b09, del_b09)
    B10 = property(get_b10, set_b10, del_b10)
    B11 = property(get_b11, set_b11, del_b11)
    B12 = property(get_b12, set_b12, del_b12)
    SCL = property(get_scl, set_scl, del_scl)
    SNW = property(get_qsn, set_qsn, del_qsn)
    CLD = property(get_qcl, set_qcl, del_qcl)
    MSC = property(get_msc, set_msc, del_msc)
    PRV = property(get_prv, set_prv, del_prv)
    TCI = property(get_tci, set_tci, del_tci)
    L3_Tile_PLT_File = property(get_l_3_tile_plt_file, set_l_3_tile_plt_file, del_l_3_tile_plt_file)

    config = property(get_config, set_config, del_config)
    product = property(get_product, set_product, del_product)
    bandIndex = property(get_band_bandIndex, set_band_bandIndex, del_band_bandIndex)
    nBands = property(get_n_bands, set_n_bands, del_n_bands)
    dbName = property(get_db_name, set_db_name, del_db_name)
    
    def init(self):
        ''' Checks the existence of a L3 target database for the processed tile.
            If the database exists, the given tile will be imported. If the database does not exist
            it will be created and the current tile will become the base for the subsequent processing.
        '''
        self._config.logger.info('Checking existence of L3 target database')
        try:
            h5file = open_file(self._imageDatabase)
            h5file.close()
        except:
            self.initDatabase()
            self.importBandList('L3')
            return
        self.importBandList('L2A')
        return

    def exportTile(self, L3_TILE_ID):
        ''' Prepare the export of a synthesized tile.
        
           :param identifier: the tile ID.
           :type identifier: str
           
        '''

        AUX_DATA = 'AUX_DATA'
        IMG_DATA = 'IMG_DATA'
        QI_DATA = 'QI_DATA'
        GRANULE = 'GRANULE'
        # Resolution:
        self._resolution = int(self.config.resolution)
        if self._resolution == 10:
            bandDir = 'R10m'
        elif self._resolution == 20:
            bandDir = 'R20m'
        elif self._resolution == 60:
            bandDir = 'R60m'
        BANDS = bandDir
        L3_TARGET_ID = self.config.L3_TARGET_ID
        strList = L3_TILE_ID.split('_')
        L3_TILE_ID_SHORT = strList[1] + '_' + strList[3]
        self.config.reinitTile(L3_TILE_ID)
        L3_TILE_ID = os.path.join(self.config.targetDir, L3_TARGET_ID, GRANULE, L3_TILE_ID)
        self._L3_ImgDataDir = os.path.join(L3_TILE_ID, IMG_DATA)
        self._L3_bandDir = os.path.join(self._L3_ImgDataDir, BANDS)
        self._L3_QualityDataDir = os.path.join(L3_TILE_ID, QI_DATA)
        self._L3_AuxDataDir = os.path.join(L3_TILE_ID, AUX_DATA)
        #
        # the File structure,
        # L3 files are always in SAFE_COMPACT format:
        #-------------------------------------------------------
        self._L3_Tile_BND_File = os.path.join(self._L3_bandDir,
            L3_TILE_ID_SHORT + '_BXX_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_AOT_File = os.path.join(self._L3_bandDir,
            L3_TILE_ID_SHORT + '_AOT_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_WVP_File = os.path.join(self._L3_bandDir,
            L3_TILE_ID_SHORT + '_WVP_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_TCI_File = os.path.join(self._L3_bandDir,
            L3_TILE_ID_SHORT + '_TCI_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_SCL_File = os.path.join(self._L3_bandDir,
            L3_TILE_ID_SHORT + '_SCL_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_CLD_File = os.path.join(self._L3_QualityDataDir,
            L3_TILE_ID_SHORT + '_CLD_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_SNW_File = os.path.join(self._L3_QualityDataDir,
            L3_TILE_ID_SHORT + '_SNW_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_MSC_File = os.path.join(self._L3_QualityDataDir,
            L3_TILE_ID_SHORT + '_MSC_' + str(self._resolution) + 'm.jp2')
        self._L3_Tile_PLT_File = os.path.join(self._L3_QualityDataDir,
            L3_TILE_ID_SHORT + '_PLT_' + str(self.config.getNrTilesProcessed()+1) + '.png')
        self._L3_Tile_PVI_File = os.path.join(self._L3_QualityDataDir,
            L3_TILE_ID_SHORT + '_PVI.jp2')

        self._imageDatabase = os.path.join(self._L3_bandDir, '.database.h5')
        self.config.logger.debug('Module L3_Tables reinitialized with resolution %d' % self._resolution)
        self.exportBandList('L3')
        return
    
    def initDatabase(self):
        ''' Initialize H5 target database for usage.
        '''
        try:
            h5file = open_file(self._imageDatabase, mode='a', title =  str(self._resolution) + 'm bands')
            # remove all existing L2A tables as they will be replaced by the new data set
            h5file.create_group('/', 'L2A', 'bands L2A')
            h5file.create_group('/', 'L3', 'bands L3')
            result = True
        except:
            self.config.logger.fatal('error in initialization of database: %s:' % self._imageDatabase)
            self.config.exitError()
            result = False
        h5file.close()
        return result
    
    def importBandList(self, productLevel):
        ''' Import all bands of current tile.
            
            :param productLevel: [L2A | L3].
            :type productLevel: str
            :rtype: none.
            
        '''        
        self.config.timestamp('L3_Tables: start import, source product version is: ' + str(self.config.productVersion))
        self._productLevel = productLevel        
        bandDir = self._L2A_bandDir
        os.chdir(bandDir)
        dirs = sorted(os.listdir(bandDir))
        bands = self._bandIndex
        for i in bands:
            for filename in dirs:  
                bandName = self.getBandNameFromIndex(i)
                if self.config.productVersion == 13.1:
                    filemask = '*_L2A_*_B%2s_??m.jp2' % bandName[1:3]
                elif self.config.productVersion == 14.2:
                    filemask = 'L2A_T*_B%2s_??m.jp2' % bandName[1:3]
                elif self.config.productVersion == 14.5:
                    filemask = 'T*_B%2s_??m.jp2' % bandName[1:3]
                if not fnmatch.fnmatch(filename, filemask):
                    continue

                self.importBand(i, os.path.join(bandDir,filename))

                #
                # the File structure:
                # -------------------------------------------------------
                if (self.config.productVersion == 13.1) and (bandName == 'B02'):
                    # B02 is always present:
                    L2A_TILE_ID_SHORT = self.config.L2A_TILE_ID[:55]
                    pre = L2A_TILE_ID_SHORT[:8]
                    post = L2A_TILE_ID_SHORT[12:]
                    self._L2A_Tile_BND_File = os.path.join(self._L2A_bandDir,
                        L2A_TILE_ID_SHORT + '_BXX_' + str(self._resolution) + 'm.jp2')
                    self._L2A_Tile_AOT_File = os.path.join(self._L2A_bandDir,
                        pre + '_AOT' + post + '_' + str(self._resolution) + 'm.jp2')
                    self._L2A_Tile_WVP_File = os.path.join(self._L2A_bandDir,
                        pre + '_WVP' + post + '_' + str(self._resolution) + 'm.jp2')
                    self._L2A_Tile_SCL_File = os.path.join(self._L2A_ImgDataDir,
                        pre + '_SCL' + post + '_' + str(self._resolution) + 'm.jp2')
                    self._L2A_Tile_CLD_File = os.path.join(self._L2A_QualityDataDir,
                        pre + '_CLD' + post + '_' + str(self._resolution) + 'm.jp2')
                    self._L2A_Tile_SNW_File = os.path.join(self._L2A_QualityDataDir,
                        pre + '_SNW' + post + '_' + str(self._resolution) + 'm.jp2')
                    self._L2A_Tile_PVI_File = os.path.join(self._L2A_QualityDataDir,
                        pre + '_PVI' + post + '.jp2')
                elif (self.config.productVersion > 13.1) and (bandName == 'B02'):
                    self._L2A_Tile_BND_File = os.path.join(bandDir, filename.replace('B02', 'BXX'))
                    self._L2A_Tile_AOT_File = os.path.join(bandDir, filename.replace('B02', 'AOT'))
                    self._L2A_Tile_WVP_File = os.path.join(bandDir, filename.replace('B02', 'AOT'))
                    self._L2A_Tile_SCL_File = os.path.join(bandDir, filename.replace('B02', 'SCL'))
                # if (self.config.productVersion == 14.2) and (bandName == 'B02'):
                #     self._L2A_Tile_CLD_File = os.path.join(self._L2A_QualityDataDir, filename.replace('B02', 'CLD'))
                #     self._L2A_Tile_SNW_File = os.path.join(self._L2A_QualityDataDir, filename.replace('B02', 'SNW'))
                # elif (self.config.productVersion > 14.2) and (bandName == 'B02'):
                #     filename = 'MSK_CLDPRB_' + str(self._resolution) + 'm.jp2'
                #     self._L2A_Tile_CLD_File = os.path.join(self._L2A_QualityDataDir, filename)
                #     filename = 'MSK_SNWPRB_' + str(self._resolution) + 'm.jp2'
                #     self._L2A_Tile_SNW_File = os.path.join(self._L2A_QualityDataDir, filename)

        if self.config.resolution > 10:
            if os.path.isfile(self._L2A_Tile_AOT_File):
                self.importBand(self.AOT, self._L2A_Tile_AOT_File)
            if os.path.isfile(self._L2A_Tile_SCL_File):
                self.importBand(self.SCL, self._L2A_Tile_SCL_File)
            # if os.path.isfile(self._L2A_Tile_CLD_File):
            #     self.importBand(self.CLD, self._L2A_Tile_CLD_File)
            return
        else: # 10m bands only: perform an up sampling of SCL and AOT from 20 m channels to 10:
            self.config.logger.info('perform up sampling of SCL from 20m channels to 10m')
            srcResolution = '_20m'

            channel = 17 # import AOT:
            if self.config.productVersion == 13.1:
                filemask = '*_L2A_*_AOT_??m.jp2'
            elif self.config.productVersion == 14.2:
                filemask = 'L2A_*_AOT_??m.jp2'
            else:
                filemask = 'T*_AOT_??m.jp2'

            sourceDir = self._L2A_bandDir.replace('R10m', 'R20m')
            dirs = sorted(os.listdir(sourceDir))
            for filename in dirs:
                if not fnmatch.fnmatch(filename, filemask):
                    continue
                self.importBand(channel, os.path.join(sourceDir, filename))
                break

            channel = 14 # import SCL:
            if self.config.productVersion == 13.1:
                # scene class is in different directory:
                sourceDir = self._L2A_ImgDataDir
                filemask = '*_L2A_*_SCL_??m.jp2'
            elif self.config.productVersion == 14.2:
                sourceDir = self._L2A_bandDir.replace('R10m', 'R20m')
                filemask = 'L2A_*_SCL_??m.jp2'
            else:
                sourceDir = self._L2A_bandDir.replace('R10m', 'R20m')
                filemask = 'T*_SCL_??m.jp2'

            dirs = sorted(os.listdir(sourceDir))
            for filename in dirs:
                if not fnmatch.fnmatch(filename, filemask):
                    continue
                self.importBand(channel, os.path.join(sourceDir, filename))
                return

    def getBand(self, productLevel, bandIndex):
        ''' Get a single band from database.

            :param productLevel: [ L2A | L3].
            :type productLevel: str            
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :param dataType: data type of band.
            :type dataType: default: unsigned int 16
            :return: the pixel data.
            :rtype: a 2 dimensional numpy array (row x column) of type unsigned int 16 
            
        '''
        self.verifyProductId(productLevel)
        bandName = self.getBandNameFromIndex(bandIndex)
        try:
            h5file = open_file(self._imageDatabase)
            node = h5file.get_node('/' + productLevel, bandName)
            result = node.read()
        except NoSuchNodeError:
            self.config.logger.debug('%s: Band %s is missing', productLevel, self.getBandNameFromIndex(bandIndex))
            result = False
        h5file.close()
        return result

    def importBand(self, bandIndex, filename):
        ''' convert JPEG-2000 input file to internal H5 file format.
        
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :param filename: file name of JPEG-2000 input image.
            :type filename: str
            :return: false if error occurred during import.
            :rtype: boolean
            
        '''
        from skimage.transform import resize as skit_resize
        # convert JPEG-2000 input file to H5 file format
        self.verifyProductId(self._productLevel)
        warnings.filterwarnings("ignore")
        indataset = glymur.Jp2k(filename)
        ncols = indataset.shape[1]
        indataArr = indataset[:]
        # fix for SIIMPC-558.2, UMW:
        # update the geobox for own resolution:
        if (bandIndex == 0) | (bandIndex == 1) | (bandIndex == 5):
            self._geobox = indataset.box[3]
            # end fix for SIIMPC-558.2

        if self.config.resolution == 10:
        # upsampling is required, order 3 is for cubic spline:
            if (bandIndex == self.SCL) | (bandIndex == self.CLD):
                size = self.getBandSize('L3', self.B02)
                ncols = size[0]
                indataArr = (skit_resize(indataArr.astype(uint8), size, order=1) * 255.).round().astype(uint8)
            elif bandIndex == self.AOT:
                size = self.getBandSize('L3', self.B02)
                ncols = size[0]
                indataArr = (skit_resize(indataArr.astype(uint16), size, order=1) * 255.).round().astype(uint16)

        indataset = None
        # Create new arrays:
        database = self._imageDatabase
        nodeStr = self._productLevel
        bandName = self.getBandNameFromIndex(bandIndex)
        try:
            if self.testBand(self._productLevel, bandIndex) == True:
                self.delBand(self._productLevel, bandIndex)
            h5file = open_file(database, mode='a')
            if not (h5file.__contains__('/' + nodeStr)):
                self.config.logger.fatal('table initialization, wrong node %s:' % nodeStr)
                self.config.exitError()
                return False

            if self._productLevel == 'L2A':
                locator = h5file.root.L2A
            elif self._productLevel == 'L3':
                locator = h5file.root.L3

            dtOut = self.mapDataType(indataArr.dtype)
            filters = Filters(complib="zlib", complevel=1)
            node = h5file.create_earray(locator, bandName, dtOut, (0, ncols), bandName, filters=filters)
            node.append(indataArr)
            self.config.timestamp('L3_Tables: Level ' + self._productLevel + ' band ' + bandName + ' imported')
            result = True
        except:
            indataArr = None
            self.config.logger.fatal('error in import of band %s in productLevel %s.' % (bandName, self._productLevel))
            self.config.exitError()
            result = False

        indataArr = None
        h5file.close()
        return result


    def exportBandList(self, productLevel):
        ''' Export all bands of current tile.
            converts all bands from hdf5 to JPEG-2000.
            
            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :return: false if error occurred during export.
            :rtype: boolean           

        '''     
        bandDir = self._L3_bandDir
        # converts all bands from hdf5 to JPEG 2000
        if(os.path.exists(bandDir) == False):
            self.config.logger.fatal('missing directory %s:' % bandDir)
            self.config.exitError()
            return False

        os.chdir(bandDir)
        self.config.timestamp(productLevel + '_Tables: start export')
        if (self._resolution == 10):
            bandIndex = [1, 2, 3, 7, 14, 34]

        elif (self._resolution == 20):
            bandIndex = [1, 2, 3, 4, 5, 6, 8, 11, 12, 14, 34]

        elif (self._resolution == 60):
            bandIndex = [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 14, 34]

        xp = L3_XmlParser(self.config, 'UP2A')
        if self.config.productVersion < 14.5:
            pi = xp.getTree('General_Info', 'L2A_Product_Info')
            try: # 14.2:
                gr2a = pi.L2A_Product_Organisation.Granule_List.Granule
            except: # 13.1:
                gr2a = pi.L2A_Product_Organisation.Granule_List.Granules
        else: # 14.5:
            pi = xp.getTree('General_Info', 'Product_Info')
            gr2a = pi.Product_Organisation.Granule_List.Granule

        gi2a = gr2a.attrib['granuleIdentifier']
        ds2a = gr2a.attrib['datastripIdentifier']
        l3TileId_split = self.config.L3_TILE_ID.split('_')
        gi3 = gi2a.replace('_L2A_', '_L03_')
        ds3 = ds2a.replace('_L2A_', '_L03_')
        if self.config.productVersion < 14.5:
            gi3 = gi3[:41] + l3TileId_split[2] + '_' + l3TileId_split[1] + gi3[-7:]
        else:
            gi3 = gi3[:41] + l3TileId_split[2] + '_' + l3TileId_split[1] + gi3[-7:]
        gi3 = gi3.replace('USER', 'OPER')
        ds3 = ds3.replace('USER', 'OPER')
        Granule = objectify.Element('Granule')
        Granule.attrib['granuleIdentifier'] = gi3
        Granule.attrib['datastripIdentifier'] = ds3
        Granule.attrib['imageFormat'] = 'JPEG2000'

        gl = objectify.Element('Granule_List')
        gl.append(Granule)
        for index in bandIndex:
            bandName = self.getBandNameFromIndex(index)
            if index == self.SCL:
                filename = self._L3_Tile_SCL_File
            elif index == self.MSC:
                filename = self._L3_Tile_MSC_File
            else:
                filename = self._L3_Tile_BND_File.replace('BXX', bandName)
            if self.testBand(productLevel, index):
                band = self.getBand(productLevel, index)
            else:
                # create mosaic map if first tile:
                scl = self.getBand(productLevel, self.SCL)
                scl[scl > 0] = 1
                self.setBand(productLevel, self.MSC)
            # Median Filter:
            mf = self.config.medianFilter
            if(mf > 0):
                band = ndimage.filters.median_filter(band, (mf,mf))

            if (index == self.SCL) or (index == self.MSC):
                self.glymurWrapper(filename, band.astype(uint8))
            else:
                self.glymurWrapper(filename, band.astype(uint16))
            self.config.logger.info('Band ' + bandName + ' exported')
            self.config.timestamp('L3_Tables: band ' + bandName + ' exported')
            filename = os.path.basename(filename.strip('.jp2'))
            imageFile3 = etree.Element('IMAGE_FILE')
            # by intention os.path.join is not used here, as otherwise validation on windows fails:
            resolution = 'R' + str(self.config.resolution) + 'm/'
            imageFile3.text = 'GRANULE/' + self.config.L3_TILE_ID + '/IMG_DATA/' + resolution + filename
            Granule.append(imageFile3)

        self.createTci('L3')
        xp = L3_XmlParser(self.config, 'UP03')
        pi = xp.getTree('General_Info', 'Product_Info')
        po = pi.Product_Organisation
        po.append(gl)
        xp.export()
        
        #update on tile level
        xp = L3_XmlParser(self.config, 'T03')
        ti3 = xp.getTree('General_Info', 'TILE_ID')
        ti3._setText(gi3)
        di3 = xp.getTree('General_Info', 'DATASTRIP_ID')
        di3._setText(ds3)

        # clean up and post processing actions:
        pxlQI = objectify.Element('Pixel_Level_QI')
        pxlQI.attrib['resolution'] = str(self.config.resolution)
        pxlQI.append(objectify.Element('TILE_CLASSIFICATION_MASK'))
        pxlQI.append(objectify.Element('TILE_MOSAIC_MASK'))

        pxlQI.TILE_CLASSIFICATION_MASK = os.path.basename(self._L3_Tile_SCL_File).replace('.jp2', '')
        pxlQI.TILE_MOSAIC_MASK = os.path.basename(self._L3_Tile_MSC_File).replace('.jp2', '')

        qiiL3 = xp.getTree('Quality_Indicators_Info', 'Pixel_Level_QI')
        qiiL3Len = len(qiiL3)
        for i in range(qiiL3Len):
            if int(qiiL3[i].attrib['resolution']) == self.config.resolution:
                qiiL3[i] = pxlQI
                break

        xp.export()
        self.config.timestamp(productLevel + '_Tables: stop export')
        return True

    def scalePreview(self, arr):
        ''' Scale image array for preview. Helper function used by createRgbImage().

            :param arr: the image array.
            :type arr: 2 dimensional numpy array (nrow x ncols).
            :return: false if image cannot be created, else true.            
            :rtype: boolean
            
        '''
        if(arr.ndim) != 2:
            self.config.logger.fatal('must be a 2 dimensional array')
            self.config.exitError()
            return False
        arr = arr / self.config.L2A_BOA_QUANTIFICATION_VALUE
        arrclip = arr.copy()
        min_ = 0.0
        max_ = 0.250
        scale = 255.0
        arr = clip(arrclip, min_, max_)
        #SIITBX-50: wrong scale was used: 
        scaledArr = uint8(arr*scale/max_)
        return scaledArr

    def scaleTci(self, arr):
        ''' Scale TCI array. Helper function used by createTci().

            :param arr: the image array.
            :type arr: 2 dimensional numpy array (nrow x ncols).
            :return: false if image cannot be created, else true.
            :rtype: boolean

        '''
        if (arr.ndim) != 2:
            self.logger.fatal('must be a 2 dimensional array')
            return False

        arr = arr / self.config.L2A_BOA_QUANTIFICATION_VALUE
        arrclip = arr.copy()
        min_ = 0.0
        max_ = 0.250
        scale = 255.0
        arr = clip(arrclip, min_, max_)
        scaledArr = uint8(arr * scale / max_)
        return scaledArr

    def setBand(self, productLevel, bandIndex, arr):
        ''' Set a single band from numpy array to H5 database.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :param arr: the pixel data.
            :type arr: a 2 dimensional numpy array (row x column) of type unsigned int 16.            
            :return: false if error occurred during setting of band.            
            :rtype: boolean
            
        '''  
        self.verifyProductId(productLevel)
        try:
            if self.testBand(productLevel, bandIndex) == True:
                self.delBand(productLevel, bandIndex)
            h5file = open_file(self._imageDatabase, mode='a')
            bandName = self.getBandNameFromIndex(bandIndex)
            dtIn = self.mapDataType(arr.dtype)
            filters = Filters(complib="zlib", complevel=1)
            # create new group and append node:
            if productLevel == 'L2A':
                locator = h5file.root.L2A
            elif productLevel == 'L3':
                locator = h5file.root.L3

            node = h5file.create_earray(locator, bandName, dtIn, (0,arr.shape[1]), bandName, filters=filters)
            self.config.logger.debug('%s: Band %02d %s added to table', productLevel, bandIndex, self.getBandNameFromIndex(bandIndex))
            node.append(arr)
            result = True
        except NoSuchNodeError:
            self.config.logger.debug('%s: Band %s cannot be set', productLevel, self.getBandNameFromIndex(bandIndex))
            result = False
        h5file.close()
        return result

    def delBand(self, productLevel, bandIndex):
        ''' Delete a single band from H5 database.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :return: false if error occurred during deletion of band.            
            :rtype: boolean
            
        '''  
        self.verifyProductId(productLevel)
        try:
            h5file = open_file(self._imageDatabase, mode='a')
            bandName = self.getBandNameFromIndex(bandIndex)
            if(h5file.__contains__('/' + productLevel + '/' + bandName)):
                node = h5file.get_node('/' + productLevel, bandName)
                node.remove()
                self.config.logger.debug('%s: Band %02d %s removed from table', productLevel, bandIndex, self.getBandNameFromIndex(bandIndex))
            result = True
        except NoSuchNodeError:
            self.config.logger.debug('%s: Band %s cannot be removed', productLevel, self.getBandNameFromIndex(bandIndex))
            result = False
        h5file.close()
        return result

    def delBandList(self, productLevel):
        ''' Delete the complete list of bands from H5 database.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :return: false if error occurred during deletion of band.            
            :rtype: boolean
            
        ''' 
        try:
            h5file = open_file(self._imageDatabase, mode='a')
            if(h5file.__contains__('/' + productLevel)):
                node = h5file.get_node('/' + productLevel)
                del node
                self.config.logger.debug('%s: Bands removed from table', productLevel)
            result = True
        except NoSuchNodeError:
            self.config.logger.debug('%s: Bands cannot be removed', productLevel)
            result = False          
        h5file.close()
        return result            
        
    def delDatabase(self):
        ''' Delete the H5 database.

            :return: true if succeeds, false if database does not exist.            
            :rtype: boolean
            
        ''' 
        database = self._imageDatabase
        if os.path.isfile(database):
            os.remove(database)
            self.config.logger.debug('%s: removed', database)
            return True
        else:
            self.config.logger.debug('%s: does not exist', database)
            return False

    def createPreviewImage(self, productLevel):
        ''' Create an RGB preview image from bands 2-4.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :return: false if image cannot be created, else true.            
            :rtype: boolean
            
        '''

        self.config.logger.debug('Creating Preview Image')
        b = self.getBand(productLevel, self.B02)
        g = self.getBand(productLevel, self.B03)
        r = self.getBand(productLevel, self.B04)

        # Median Filter:
        mf = self.config.medianFilter
        if (mf > 0):
            b = ndimage.filters.median_filter(b, (mf, mf))
            g = ndimage.filters.median_filter(g, (mf, mf))
            r = ndimage.filters.median_filter(r, (mf, mf))

        b1 = self.scalePreview(b)
        g1 = self.scalePreview(g)
        r1 = self.scalePreview(r)

        b1 = Image.fromarray(b1)
        g1 = Image.fromarray(g1)
        r1 = Image.fromarray(r1)

        try:
            out = Image.merge('RGB', (r1,g1,b1))
            a = array(out)
            if productLevel == 'L2A':
                pvi = self._L2A_Tile_PVI_File
            else:
                pvi = self._L3_Tile_PVI_File
            self.glymurWrapper(pvi, a.astype(uint8))
            self.config.logger.debug('Preview Image created')
            return True
        except:
            self.config.logger.fatal('Preview Image creation failed')
            return False

    def createTci(self, productLevel):
        ''' Create an RGB TCI image from bands 2-4.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :return: false if image cannot be created, else true.
            :rtype: boolean

        '''

        self.config.logger.debug('Creating TCI Image')
        b = self.getBand(productLevel, self.B02)
        g = self.getBand(productLevel, self.B03)
        r = self.getBand(productLevel, self.B04)

        b1 = self.scaleTci(b)
        g1 = self.scaleTci(g)
        r1 = self.scaleTci(r)

        b1 = Image.fromarray(b1)
        g1 = Image.fromarray(g1)
        r1 = Image.fromarray(r1)

        try:
            out = Image.merge('RGB', (r1, g1, b1))
            a = array(out)
            tci = self._L3_Tile_TCI_File
            self.glymurWrapper(tci, a.astype(uint8))
            self.config.timestamp('L3_Tables: band TCI exported')
            return True
        except:
            self.logger.fatal('TCI image export failed')
            self.config.timestamp('L3_Tables: TCI image export failed')
            return False

    def testDb(self):
        ''' Test consistency of database.
        
            :param: none.
            :return: false if database is inconsistent, else true.            
            :rtype: boolean
            
        '''
        result = False
        try:
            h5file = open_file(self._imageDatabase)
            h5file.get_node('/L3', 'B02')
            h5file.get_node('/L3', 'B03')
            h5file.get_node('/L3', 'B04')
            status = 'Database ' + self._imageDatabase + ' exists and can be used'
            result = True
        except:
            status = 'Database  ' + self._imageDatabase + ' will be removed due to corruption'
            self.removeDatabase()
            result = False
        h5file.close()
        self.config.logger.info(status)
        return result
    
    def verifyProductId(self, productLevel):
        ''' Verify the product ID.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :return: true if product level exists, else false.            
            :rtype: boolean
            
        '''
        if productLevel != 'L2A' and productLevel != 'L3':
            self.config.logger.fatal('Wrong product ID %s', productLevel)
            self.config.exitError()
        return True
    
    def testBand(self, productLevel, bandIndex):
        ''' Test if band exists in database.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :return: true if band exists, else false.            
            :rtype: boolean
            
        '''
        self.verifyProductId(productLevel)
        bandName = self.getBandNameFromIndex(bandIndex)
        try:
            h5file = open_file(self._imageDatabase)
            h5file.get_node('/' + productLevel , bandName)
            self.config.logger.debug('%s: Band %s is present', productLevel, self.getBandNameFromIndex(bandIndex))
            result = True
        except NoSuchNodeError:
            self.config.logger.debug('%s: Band %s is missing', productLevel, self.getBandNameFromIndex(bandIndex))
            result = False
        h5file.close()
        return result

    def getBandSize(self, productLevel, bandIndex):
        ''' Get size of image array.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :return: image size (nrows x ncols)            
            :rtype: data tuple (unsigned int).
            
        '''
        self.verifyProductId(productLevel)
        bandName = self.getBandNameFromIndex(bandIndex)
        try:
            h5file = open_file(self._imageDatabase)
            node = h5file.get_node('/' + productLevel, bandName)
            arr = node.read()
            ncols = arr.shape[1]
            nrows = arr.shape[0]
            result = (nrows, ncols)
        except NoSuchNodeError:
            self.config.logger.debug('%s: Band %s is missing', productLevel, self.getBandNameFromIndex(bandIndex))
            result = False            
        h5file.close()
        return result

    def getDataType(self, productLevel, bandIndex):
        ''' Get data type of image array.

            :param productLevel: [ L2A | L3].
            :type productLevel: str
            :param bandIndex: the band index.
            :type bandIndex: unsigned int
            :return: data type.          
            :rtype: str
            
        '''
        self.verifyProductId(productLevel)
        bandName = self.getBandNameFromIndex(bandIndex)
        try:
            h5file = open_file(self._imageDatabase)
            node = h5file.get_node('/' + productLevel, bandName)
            result = node.dtype
        except NoSuchNodeError:
            self.config.logger.debug('%s: Band %s is missing', productLevel, self.getBandNameFromIndex(bandIndex))
            result = False            
        h5file.close()
        return result
        
    def mapDataType(self, dtIn):
        if(dtIn == uint8):
            dtOut = UInt8Atom()
        elif(dtIn == uint16):
            dtOut = UInt16Atom()
        elif(dtIn == int16):
            dtOut = Int16Atom()
        elif(dtIn == uint32):
            dtOut = UInt32Atom()
        elif(dtIn == int32):
            dtOut = Int32Atom()
        elif(dtIn == float32):
            dtOut = Float32Atom()
        elif(dtIn == float64):
            dtOut = Float64Atom()
        elif(dtIn == GDT_Byte):
            dtOut = UInt8Atom()
        elif(dtIn == GDT_UInt16):
            dtOut = UInt16Atom()
        elif(dtIn == GDT_Int16):
            dtOut = Int16Atom()
        elif(dtIn == GDT_UInt32):
            dtOut = UInt32Atom()
        elif(dtIn == GDT_Int32):
            dtOut = Int32Atom()
        elif(dtIn == GDT_Float32):
            dtOut = Float32Atom()
        elif(dtIn == GDT_Float64):
            dtOut = Float64Atom()

        return dtOut

    def glymurWrapper(self, filename, band):
        # fix for SIIMPC-687, UMW
        if self.config.resolution == 60:
            kwargs = {"tilesize": (192, 192), "prog": "RPCL"}
        elif self.config.resolution == 20:
            kwargs = {"tilesize": (640, 640), "prog": "RPCL"}
        elif self.config.resolution == 10:
            kwargs = {"tilesize": (1024, 1024), "prog": "RPCL"}
        # end fix for SIIMPC-687
        # fix for SIIMPC-558.3, UMW
        glymur.Jp2k(filename, band, **kwargs)
        jp2_L2A = glymur.Jp2k(filename)
        boxes_L2A = jp2_L2A.box
        boxes_L2A.insert(3, self._geobox)
        boxes_L2A[1] = glymur.jp2box.FileTypeBox(brand='jpx ', compatibility_list=['jpxb', 'jp2 '])
        file_L3_geo = os.path.splitext(filename)[0] + '_geo.jp2'
        jp2_L2A.wrap(file_L3_geo, boxes=boxes_L2A)
        os.remove(filename)
        os.rename(file_L3_geo, filename)
        # end fix for SIIMPC-558.3
        return
