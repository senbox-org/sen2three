#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

processorName = 'Sentinel-2 Level 3 Processor (Sen2Three)'
processorVersion = '1.2.0'
processorDate = '2019.01.31'
productVersion = '14.5'

from tables import *
import sys, os
import fnmatch
from time import time
from L3_Library import stdoutWrite, stderrWrite
from L3_Config import L3_Config
from L3_Product import L3_Product
from L3_Tables import L3_Tables
from L3_Synthesis import L3_Synthesis

def sortObservationStartTime(dirList):
    UP_mask = '*_MSIL2A_*'

    products = {}
    for item in dirList:
        if not fnmatch.fnmatch(item, UP_mask):
            continue
        items = item.split('_')
        if items[1] == 'USER': # it's a V13.1 product ..
            products[items[8].split('.')[0]] = item
        else: # a V14.2 product:
            products[items[6].split('.')[0]] = item
    rows = sorted(products.items())
    return [x[1] for x in rows]


class L3_Process(object):
    ''' The main processor module, which coordinates the interaction between the other modules.
        
            :param config: the config object for the current tile (via __init__)
            :type config: a reference to the config object
    
    '''
    def __init__(self, config):
        ''' Perform the L3 base initialisation.
        
            :param config: the config object for the current tile
            :type config: a reference to the config object
                     
        '''

        self._config = config
        self.l3Synthesis = L3_Synthesis(config)

    def get_tables(self):
        return self._tables


    def set_tables(self, value):
        self._tables = value


    def del_tables(self):
        del self._tables


    def get_config(self):
        return self._config


    def set_config(self, value):
        self._config = value


    def del_config(self):
        del self._config


    def __exit__(self):
            sys.exit(-1)

    config = property(get_config, set_config, del_config)
    tables = property(get_tables, set_tables, del_tables)

    def process(self, tables):
        ''' Perform the L3 processing.
        
            :param tables: the table object for the current tile
            :type tables: a reference to the table object
            :return: true if processing succeeds, false else
            :rtype: bool
            
        '''
        self._tables = tables
        product = tables.product
        astr = 'L3_Process: processing with resolution ' + str(self.config.resolution) + ' m'
        self.config.timestamp(astr)
        self.config.timestamp('L3_Process: start of Pre Processing')
        if(self.preProcessing() == False):
            return self, -1
        
        self.config.timestamp('L3_Process: start of Spatio Temporal Processing')
        self.config.logger.info('Performing Spatio Temporal Processing with resolution %d m', self.config.resolution)
        if(self.l3Synthesis.process(self._tables) == False):
            return self, -1

        # append processed tile to list
        self.config.appendTile()
        if product.checkCriteriaForTermination():
            return self, 1
        else:
            return self, 0

    def preProcessing(self):
        ''' Perform the L3 pre processing,
            currently empty.
        '''

        self.config.logger.info('Pre-processing with resolution %d m', self.config.resolution)
        return True

    def postProcessing(self):
        ''' Perform the L3 post processing,
            triggers the export of L3 product, tile metadata and bands
            
            :return: true if export succeeds, false else
            :rtype: bool

        '''

        self.config.timestamp('L3_Process: start of Post Processing')
        self.config.logger.info('Post-processing with resolution %d m', self.config.resolution)

        GRANULE = 'GRANULE'
        GRANULE_DIR = os.path.join(self.config.targetDir, self.config.L3_TARGET_ID, GRANULE)
        tilelist = sorted(os.listdir(GRANULE_DIR))
        L3_TILE_MSK = 'L03_T*'
        res = False
        for tile in tilelist:
            if fnmatch.fnmatch(tile, L3_TILE_MSK) == False:
                continue
            res = self.tables.exportTile(tile)
        if res == False:
            return res

        self.l3Synthesis.postProcessing()
        return True

def doTheLoop(config):
    ''' Initializes a product and processor object. Cycles through all input products and granules
        and calls the sequential processing of the individual tiles if the criteria for processing are fulfilled.

        :param config: the config object
        :type config: a reference to the config object
        :return: the processor object, for doing the preprocessing, -1 if processing error occurred.
        :rtype: processor object or -1

    '''
    HelloWorld = processorName + ', ' + processorVersion + ', created: ' + processorDate
    stdoutWrite('\n%s started with %dm resolution ...\n' % (HelloWorld, config.resolution))
    dirlist = os.listdir(config.sourceDir)
    upList = sortObservationStartTime(dirlist)
    tileFilter = config.tileFilter

    # Process all unprocessed L2A products:
    UP_mask = '*_MSIL2A_*'
    product = L3_Product(config)
    processor = L3_Process(config)
    proc = None
    for L2A_UP_ID in upList:
        if not config.checkTimeRange(L2A_UP_ID):
            continue
        product.updateUserProduct(L2A_UP_ID)
        if config.productVersion == 13.1:
            Tile_mask = '*L2A_*'
        else:
            Tile_mask = 'L2A_*'
        GRANULE = os.path.join(config.sourceDir, L2A_UP_ID, 'GRANULE')
        tilelist = sorted(os.listdir(GRANULE))
        for tile in tilelist:
            # process only L2A tiles:
            if not fnmatch.fnmatch(tile, Tile_mask):
                continue
            # ignore already processed tiles:
            if config.tileExists(tile):
                continue
            # apply tile filter:
            if not config.tileIsSelected(tile, tileFilter):
                continue
            if not config.checkTileConsistency(GRANULE, tile):
                continue

            tStart = time()
            product.config.L2A_TILE_ID = tile
            tables = L3_Tables(product)
            tables.init()
            # no processing if first initialisation:
            # check existence of Bands - B2 is always present:
            if not tables.testBand('L2A', tables.B02):
                # append processed tile to list
                if not config.appendTile():
                    config.exitError()
                continue
            proc, result = processor.process(tables)
            if result == -1:
                stderrWrite('Application terminated with errors, see log file and traces.\n')
                return result
            elif result == 1:
                return proc
            elif result == 0:
                tMeasure = time() - tStart
                config.writeTimeEstimation(config.resolution, tMeasure)

    return proc


def main(args=None):
    ''' Processes command line,
        initializes the config and product modules and starts sequentially
        the L3 processing
    '''
    import argparse
    descr = processorName +', '+ processorVersion +', created: '+ processorDate + \
        ', supporting Level-2A product version: ' + productVersion + '.'
     
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('directory', help='Directory where the Level-2A input files are located')
    parser.add_argument('--resolution', type=int, choices=[10, 20, 60], help='Target resolution, can be 10, 20 or 60m. If omitted, all resolutions will be processed')
    parser.add_argument('--clean', action='store_true', help='Removes the L3 product in the target directory before processing. Be careful!')
    args = parser.parse_args()

    # SIITBX-49: directory should not end with '/':
    directory = args.directory
    if directory[-1] == '/':
        directory = directory[:-1]

    # check if directory argument starts with a relative path. If not, expand: 
    if not os.path.isabs(directory):
        cwd = os.getcwd()
        directory = os.path.join(cwd, directory)
    directory = os.path.normpath(directory)
    if not os.path.exists(directory):
        stderrWrite('directory "%s" does not exist\n.' % directory)
        return False

    if not args.resolution:
        resolutions = [60,20,10]
    else:
        resolutions = [args.resolution]

    cleanDone = False # do only one clean up of target, if requested.
    for resolution in resolutions:
        config = L3_Config(resolution, directory)
        result = False
        processedFn = os.path.join(directory, 'processed')

        if args.clean and not cleanDone:
            stdoutWrite('Cleaning target directory ...\n')
            config.cleanTarget = True
            try:
                os.remove(processedFn)
            except:
                stdoutWrite('No history file present ...\n')
            cleanDone = True

        config.init(processorVersion)
        processor = doTheLoop(config)
        if processor == -1:
            stderrWrite('Application terminated with errors, see log file and traces.\n')
            return 1
        elif processor == None:
            stdoutWrite('All tiles already processed.\n')
        else:
            processor.postProcessing()

    stdoutWrite('Application terminated successfully.\n')
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
