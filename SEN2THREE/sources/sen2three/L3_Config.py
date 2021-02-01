#!/usr/bin/env python

from numpy import *
import sys, os, time, fnmatch
import logging, inspect
import ConfigParser
from lxml import etree, objectify
from time import strftime
from datetime import datetime, date

from L3_Borg import Borg
from L3_Library import stdoutWrite, stderrWrite
from L3_XmlParser import L3_XmlParser


def getScriptDir(follow_symlinks=True):
    if getattr(sys, 'frozen', False):  # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(getScriptDir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


class L3_Config(Borg):
    ''' Provide the configuration input of the GIPP (via __init__).
        
    :param resolution: the requested resolution from command line.
    :type resolution: string
    :param sourceDir: the user product base directory.
    :type sourceDir: string
    :param configFile: the path of the processors GIPP.
    :type configFile: string

    '''
    _shared = {}
    def __init__(self, resolution, sourceDir=None, configFile='L3_GIPP'):

        if (sourceDir):
            if os.name == 'nt' and not '\\\\?\\' in sourceDir:
                # special treatment for windows for long pathnames:
                sourceDir = u'\\'.join([u'\\\\?', sourceDir])
            try:
                self._home = os.environ['SEN2THREE_HOME']
            except:
                self._home = os.path.dirname(getScriptDir())
            try:
                scriptDir = os.environ['SEN2THREE_BIN']
            except:
                scriptDir = getScriptDir()

            self._sourceDir = sourceDir
            self._configDir = os.path.join(scriptDir, 'cfg')
            self._configFn = os.path.join(self._home, 'cfg', configFile + '.xml')
            self._libDir = os.path.join(scriptDir, 'lib')
            self._logDir = os.path.join(self._home, 'log')
            if not os.path.exists(self._logDir):
                os.mkdir(self._logDir)
            self._processorVersion = None
            self._productVersion = 14.5
            self._tEstimation = 0.0
            self._tEst60 = 150.0
            self._tEst20 = self._tEst60 * 8.0
            self._tEst10 = self._tEst60 * 8.0
            self._processingStatusFn = os.path.join(self._logDir, '.progress')
            self._processingEstimationFn = os.path.join(self._logDir, '.estimation')
            if os.path.isfile(self._processingEstimationFn) == False:
            # init processing estimation file:
                config = ConfigParser.RawConfigParser()
                config.add_section('time estimation')
                config.set('time estimation','t_est_60', self._tEst60)
                config.set('time estimation','t_est_20', self._tEst20)
                config.set('time estimation','t_est_10', self._tEst10)
                with open(self._processingEstimationFn, 'a') as configFile:
                    config.write(configFile)
            self._resolution = resolution
            self._ncols = -1
            self._nrows = -1
            self._nbnds = -1
            self._tTotal = 0.0
            self._solaz = None
            self._solaz_arr = None
            self._solze = None
            self._solze_arr = None
            self._vaa_arr = None
            self._vza_arr = None            
            self._GIPP = ''
            self._ECMWF = ''
            self._DEM = ''
            self._L2A_BOA_QUANTIFICATION_VALUE = 10000.0
            self._L2A_WVP_QUANTIFICATION_VALUE = 1000.0
            self._L2A_AOT_QUANTIFICATION_VALUE = 1000.0
            self._dnScale = 10000.0
            self._radScale = 1.0
            self._timestamp = datetime.now()
            self._logger = None
            self._fnLog = None
            self._displayData = False
            self._creationDate = None
            self._acquisitionDate = None
            self._classifier = None
            self._minTime = None
            self._maxTime = None
            self._algorithm = 'MOST_RECENT'
            self._radiometricPreference = 'AOT'
            self._cirrusRemoval = True
            self._shadowRemoval = True
            self._snowRemoval = True
            self._maxCloudProbability = None
            self._maxInvalidPixelsPercentage = None
            self._maxAerosolOpticalThickness = None
            self._maxSolarZenithAngle = None
            self._medianFilter = None
            self._targetDir = None
            self._cleanTarget = False
            self._c0 = None
            self._c1 = None
            self._e0 = None
            self._d2 = None
            self._L2A_INSPIRE_XML = None
            self._L2A_MANIFEST_SAFE = None
            self._L2A_UP_MTD_XML = None
            self._L2A_DS_MTD_XML = None
            self._L2A_TILE_MTD_XML = None
            self._L2A_UP_ID = None
            self._L2A_UP_ID_first = None
            self._L2A_DS_ID = None
            self._L2A_TILE_ID = None
            self._L2A_UP_DIR = None
            self._L3_TARGET_MTD_XML = None
            self._L3_DS_MTD_XML = None
            self._L3_TILE_MTD_XML = None
            self._L3_TARGET_ID = None
            self._L3_DS_ID = None
            self._L3_TILE_ID = None
            self._cloudsPercentage = None
            self._badPixelPercentage = None
            self._namingConvention = None
            self._upScheme2a = None
            self._upScheme3 = None
            self._tileScheme2a = None
            self._tileScheme3 = None
            self._dsScheme2a = None
            self._dsScheme3 = None
            self._gippScheme3 = None
            self._manifestScheme = None


    def get_up_scheme_2a(self):
        return self._upScheme2a


    def get_up_scheme_3(self):
        return self._upScheme3


    def get_tile_scheme_2a(self):
        return self._tileScheme2a


    def get_tile_scheme_3(self):
        return self._tileScheme3


    def get_ds_scheme_2a(self):
        return self._dsScheme2a


    def get_ds_scheme_3(self):
        return self._dsScheme3


    def get_gipp_scheme_3(self):
        return self._gippScheme3


    def get_manifest_scheme(self):
        return self._manifestScheme


    def set_up_scheme_2a(self, value):
        self._upScheme2a = value


    def set_up_scheme_3(self, value):
        self._upScheme3 = value


    def set_tile_scheme_2a(self, value):
        self._tileScheme2a = value


    def set_tile_scheme_3(self, value):
        self._tileScheme3 = value


    def set_ds_scheme_2a(self, value):
        self._dsScheme2a = value


    def set_ds_scheme_3(self, value):
        self._dsScheme3 = value


    def set_gipp_scheme_3(self, value):
        self._gippScheme3 = value


    def set_manifest_scheme(self, value):
        self._manifestScheme = value


    def del_up_scheme_2a(self):
        del self._upScheme2a


    def del_up_scheme_3(self):
        del self._upScheme3


    def del_tile_scheme_2a(self):
        del self._tileScheme2a


    def del_tile_scheme_3(self):
        del self._tileScheme3


    def del_ds_scheme_2a(self):
        del self._dsScheme2a


    def del_ds_scheme_3(self):
        del self._dsScheme3


    def del_gipp_scheme_3(self):
        del self._gippScheme3


    def del_manifest_scheme(self):
        del self._manifestScheme
        
        
    def get_clouds_percentage(self):
        return self._cloudsPercentage


    def set_clouds_percentage(self, value):
        self._cloudsPercentage = value


    def del_clouds_percentage(self):
        del self._cloudsPercentage


    def get_bad_pixel_percentage(self):
        return self._badPixelPercentage


    def set_bad_pixel_percentage(self, value):
        self._badPixelPercentage = value


    def del_bad_pixel_percentage(self):
        del self._badPixelPercentage


    def get_tile_filter(self):
        return self._tileFilter


    def set_tile_filter(self, value):
        self._tileFilter = value


    def del_tile_filter(self):
        del self._tileFilter


    def get_clean_target(self):
        return self._cleanTarget


    def set_clean_target(self, value):
        self._cleanTarget = value


    def del_clean_target(self):
        del self._cleanTarget


    def get_median_filter(self):
        return self._medianFilter


    def set_median_filter(self, value):
        self._medianFilter = value


    def del_median_filter(self):
        del self._medianFilter

    def get_rad_scale(self):
        return self._radScale


    def set_rad_scale(self, value):
        self._radScale = value


    def del_rad_scale(self):
        del self._radScale


    def get_target_dir(self):
        return self._targetDir


    def set_target_dir(self, value):
        self._targetDir = value


    def del_target_dir(self):
        del self._targetDir


    def get_processor_version(self):
        return self._processorVersion


    def set_processor_version(self, value):
        self._processorVersion = value


    def del_processor_version(self):
        del self._processorVersion


    def get_product_version(self):
        return self._productVersion


    def set_product_version(self, value):
        self._productVersion = value


    def del_product_version(self):
        del self._productVersion


    def get_solaz(self):
        return self._solaz


    def get_solaz_arr(self):
        return self._solaz_arr


    def get_solze(self):
        return self._solze


    def get_solze_arr(self):
        return self._solze_arr


    def get_vaa_arr(self):
        return self._vaa_arr


    def get_vza_arr(self):
        return self._vza_arr


    def set_solaz(self, value):
        self._solaz = value


    def set_solaz_arr(self, value):
        self._solaz_arr = value


    def set_solze(self, value):
        self._solze = value


    def set_solze_arr(self, value):
        self._solze_arr = value


    def set_vaa_arr(self, value):
        self._vaa_arr = value


    def set_vza_arr(self, value):
        self._vza_arr = value


    def del_solaz(self):
        del self._solaz


    def del_solaz_arr(self):
        del self._solaz_arr


    def del_solze(self):
        del self._solze


    def del_solze_arr(self):
        del self._solze_arr


    def del_vaa_arr(self):
        del self._vaa_arr


    def del_vza_arr(self):
        del self._vza_arr


    def set_logLevel(self, level):
        self.logger.info('Log level will be updated to: %s', level)
        if (level == 'DEBUG'):
            self.logger.setLevel(logging.DEBUG)
        elif (level == 'INFO'):
            self.logger.setLevel(logging.INFO)
        elif (level == 'WARNING'):
            self.logger.setLevel(logging.WARNING)
        elif (level == 'ERROR'):
            self.logger.setLevel(logging.ERROR)
        elif  (level == 'CRITICAL'):
            self.logger.setLevel(logging.CRITICAL)
        else:
            self.logger.setLevel(logging.NOTSET)

    def get_logLevel(self):
        if(self.logger.getEffectiveLevel() == logging.DEBUG):
            return 'DEBUG'
        elif(self.logger.getEffectiveLevel() == logging.INFO):
            return 'INFO'
        elif(self.logger.getEffectiveLevel() == logging.WARNING):
            return 'WARNING'
        elif(self.logger.getEffectiveLevel() == logging.ERROR):
            return 'ERROR'
        elif(self.logger.getEffectiveLevel() == logging.CRITICAL):
            return 'CRITICAL'
        else:
            return 'NOTSET'  
    

    def __exit__(self):
        sys.exit(-1)


    def get_logger(self):
        return self._logger


    def set_logger(self, value):
        self._logger = value


    def del_logger(self):
        del self._logger


    def get_shared(self):
        return self._shared


    def get_home(self):
        return self._home


    def get_source_dir(self):
        return self._sourceDir


    def get_config_dir(self):
        return self._configDir


    def get_bin_dir(self):
        return self._binDir


    def get_lib_dir(self):
        return self._libDir


    def get_log_dir(self):
        return self._logDir


    def get_config_fn(self):
        return self._configFn


    def get_processing_status_fn(self):
        return self._processingStatusFn


    def get_processing_estimation_fn(self):
        return self._processingEstimationFn


    def get_ncols(self):
        return self._ncols


    def get_nrows(self):
        return self._nrows


    def get_nbnds(self):
        return self._nbnds


    def get_t_total(self):
        return self._tTotal


    def get_gipp(self):
        return self._GIPP


    def get_ecmwf(self):
        return self._ECMWF


    def get_dem(self):
        return self._DEM


    def get_l_2_a_boa_quantification_value(self):
        return self._L2A_BOA_QUANTIFICATION_VALUE


    def get_l_2_a_wvp_quantification_value(self):
        return self._L2A_WVP_QUANTIFICATION_VALUE


    def get_l_2_a_aot_quantification_value(self):
        return self._L2A_AOT_QUANTIFICATION_VALUE


    def get_dn_scale(self):
        return self._dnScale


    def get_timestamp(self):
        return self._timestamp


    def get_creation_date(self):
        return self._creationDate


    def get_acquisition_date(self):
        return self._acquisitionDate


    def set_shared(self, value):
        self._shared = value


    def set_home(self, value):
        self._home = value


    def set_source_dir(self, value):
        self._sourceDir = value


    def set_config_dir(self, value):
        self._configDir = value


    def set_bin_dir(self, value):
        self._binDir = value


    def set_lib_dir(self, value):
        self._libDir = value


    def set_log_dir(self, value):
        self._logDir = value


    def set_config_fn(self, value):
        self._configFn = value


    def set_processing_status_fn(self, value):
        self._processingStatusFn = value


    def set_processing_estimation_fn(self, value):
        self._processingEstimationFn = value


    def set_ncols(self, value):
        self._ncols = value


    def set_nrows(self, value):
        self._nrows = value


    def set_nbnds(self, value):
        self._nbnds = value


    def set_t_total(self, value):
        self._tTotal = value


    def set_gipp(self, value):
        self._GIPP = value


    def set_ecmwf(self, value):
        self._ECMWF = value


    def set_dem(self, value):
        self._DEM = value


    def set_l_2_a_boa_quantification_value(self, value):
        self._L2A_BOA_QUANTIFICATION_VALUE = value


    def set_l_2_a_wvp_quantification_value(self, value):
        self._L2A_WVP_QUANTIFICATION_VALUE = value


    def set_l_2_a_aot_quantification_value(self, value):
        self._L2A_AOT_QUANTIFICATION_VALUE = value


    def set_dn_scale(self, value):
        self._dnScale = value


    def set_timestamp(self, value):
        self._timestamp = value


    def set_creation_date(self, value):
        self._creationDate = value


    def set_acquisition_date(self, value):
        self._acquisitionDate = value


    def del_shared(self):
        del self._shared


    def del_home(self):
        del self._home


    def del_source_dir(self):
        del self._sourceDir


    def del_config_dir(self):
        del self._configDir


    def del_bin_dir(self):
        del self._binDir


    def del_lib_dir(self):
        del self._libDir


    def del_log_dir(self):
        del self._logDir


    def del_config_fn(self):
        del self._configFn


    def del_processing_status_fn(self):
        del self._processingStatusFn


    def del_processing_estimation_fn(self):
        del self._processingEstimationFn


    def del_ncols(self):
        del self._ncols


    def del_nrows(self):
        del self._nrows


    def del_nbnds(self):
        del self._nbnds


    def del_t_total(self):
        del self._tTotal


    def del_gipp(self):
        del self._GIPP


    def del_ecmwf(self):
        del self._ECMWF


    def del_dem(self):
        del self._DEM


    def del_l_2_a_boa_quantification_value(self):
        del self._L2A_BOA_QUANTIFICATION_VALUE


    def del_l_2_a_wvp_quantification_value(self):
        del self._L2A_WVP_QUANTIFICATION_VALUE


    def del_l_2_a_aot_quantification_value(self):
        del self._L2A_AOT_QUANTIFICATION_VALUE


    def del_dn_scale(self):
        del self._dnScale


    def del_timestamp(self):
        del self._timestamp


    def del_creation_date(self):
        del self._creationDate


    def del_acquisition_date(self):
        del self._acquisitionDate


    def del_l_3_up_dir(self):
        del self._L3_UP_DIR
        

    def get_resolution(self):
        return self._resolution


    def set_resolution(self, value):
        self._resolution = value


    def del_resolution(self):
        del self._resolution


    def get_classifier(self):
        return self._classifier


    def set_classifier(self, value):
        self._classifier = value


    def del_classifier(self):
        del self._classifier


    def get_min_time(self):
        return self._minTime


    def get_max_time(self):
        return self._maxTime


    def get_algorithm(self):
        return self._algorithm


    def get_cirrus_removal(self):
        return self._cirrusRemoval


    def get_shadow_removal(self):
        return self._shadowRemoval


    def get_snow_removal(self):
        return self._snowRemoval


    def get_max_cloud_probability(self):
        return self._maxCloudProbability


    def get_max_invalid_pixels_percentage(self):
        return self._maxInvalidPixelsPercentage


    def get_max_aerosol_optical_thickness(self):
        return self._maxAerosolOpticalThickness


    def get_max_solar_zenith_angle(self):
        return self._maxSolarZenithAngle


    def get_max_viewing_angle(self):
        return self._maxViewingAngle


    def set_min_time(self, value):
        self._minTime = value


    def set_max_time(self, value):
        self._maxTime = value


    def set_algorithm(self, value):
        self._algorithm = value


    def set_cirrus_removal(self, value):
        self._cirrusRemoval = value


    def set_shadow_removal(self, value):
        self._shadowRemoval = value


    def set_snow_removal(self, value):
        self._snowRemoval = value


    def set_max_cloud_probability(self, value):
        self._maxCloudProbability = value


    def set_max_invalid_pixels_percentage(self, value):
        self._maxInvalidPixelsPercentage = value


    def set_max_aerosol_optical_thickness(self, value):
        self._maxAerosolOpticalThickness = value


    def set_max_solar_zenith_angle(self, value):
        self._maxSolarZenithAngle = value


    def set_max_viewing_angle(self, value):
        self._maxViewingAngle = value


    def del_min_time(self):
        del self._minTime


    def del_max_time(self):
        del self._maxTime


    def del_algorithm(self):
        del self._algorithm


    def del_cirrus_removal(self):
        del self._cirrusRemoval


    def del_shadow_removal(self):
        del self._shadowRemoval


    def del_snow_removal(self):
        del self._snowRemoval


    def del_max_cloud_probability(self):
        del self._maxCloudProbability


    def del_max_invalid_pixels_percentage(self):
        del self._maxInvalidPixelsPercentage


    def del_max_aerosol_optical_thickness(self):
        del self._maxAerosolOpticalThickness


    def del_max_solar_zenith_angle(self):
        del self._maxSolarZenithAngle


    def del_max_viewing_angle(self):
        del self._maxViewingAngle


    def get_fn_log(self):
        return self._fnLog


    def set_fn_log(self, value):
        self._fnLog = value


    def del_fn_log(self):
        del self._fnLog


    def get_display_data(self):
        return self._displayData


    def get_radiometric_preference(self):
        return self._radiometricPreference


    def set_display_data(self, value):
        self._displayData = value


    def set_radiometric_preference(self, value):
        self._radiometricPreference = value


    def del_display_data(self):
        del self._displayData


    def del_radiometric_preference(self):
        del self._radiometricPreference


    def get_d_2(self):
        return self._d2


    def get_c_0(self):
        return self._c0


    def get_c_1(self):
        return self._c1


    def get_e_0(self):
        return self._e0


    def set_d_2(self, value):
        self._d2 = value


    def set_c_0(self, value):
        self._c0 = value


    def set_c_1(self, value):
        self._c1 = value


    def set_e_0(self, value):
        self._e0 = value


    def del_d_2(self):
        del self._d2


    def del_c_0(self):
        del self._c0


    def del_c_1(self):
        del self._c1


    def del_e_0(self):
        del self._e0

    def get_l_2_a_up_dir(self):
        return self._L2A_UP_DIR


    def set_l_2_a_up_dir(self, value):
        self._L2A_UP_DIR = value


    def del_l_2_a_up_dir(self):
        del self._L2A_UP_DIR



    def get_l_2_a_inspire_xml(self):
        return self._L2A_INSPIRE_XML


    def get_l_2_a_manifest_safe(self):
        return self._L2A_MANIFEST_SAFE


    def get_l_2_a_up_mtd_xml(self):
        return self._L2A_UP_MTD_XML


    def get_l_2_a_ds_mtd_xml(self):
        return self._L2A_DS_MTD_XML


    def get_l_2_a_tile_mtd_xml(self):
        return self._L2A_TILE_MTD_XML


    def get_l_2_a_up_id(self):
        return self._L2A_UP_ID


    def get_l_2_a_up_id_first(self):
        return self._L2A_UP_ID_first

    def get_l_2_a_ds_id(self):
        return self._L2A_DS_ID


    def get_l_2_a_tile_id(self):
        return self._L2A_TILE_ID


    def get_l_3_target_mtd_xml(self):
        return self._L3_TARGET_MTD_XML


    def get_l_3_ds_mtd_xml(self):
        return self._L3_DS_MTD_XML


    def get_l_3_tile_mtd_xml(self):
        return self._L3_TILE_MTD_XML


    def get_l_3_target_id(self):
        return self._L3_TARGET_ID


    def get_l_3_ds_id(self):
        return self._L3_DS_ID


    def get_l_3_tile_id(self):
        return self._L3_TILE_ID


    def get_l_3_target_dir(self):
        return self._L3_TARGET_DIR


    def set_l_2_a_inspire_xml(self, value):
        self._L2A_INSPIRE_XML = value


    def set_l_2_a_manifest_safe(self, value):
        self._L2A_MANIFEST_SAFE = value


    def set_l_2_a_up_mtd_xml(self, value):
        self._L2A_UP_MTD_XML = value


    def set_l_2_a_ds_mtd_xml(self, value):
        self._L2A_DS_MTD_XML = value


    def set_l_2_a_tile_mtd_xml(self, value):
        self._L2A_TILE_MTD_XML = value


    def set_l_2_a_up_id(self, value):
        self._L2A_UP_ID = value


    def set_l_2_a_up_id_first(self, value):
        self._L2A_UP_ID_first = value


    def set_l_2_a_ds_id(self, value):
        self._L2A_DS_ID = value


    def set_l_2_a_tile_id(self, value):
        self._L2A_TILE_ID = value


    def set_l_3_target_mtd_xml(self, value):
        self._L3_TARGET_MTD_XML = value


    def set_l_3_ds_mtd_xml(self, value):
        self._L3_DS_MTD_XML = value


    def set_l_3_tile_mtd_xml(self, value):
        self._L3_TILE_MTD_XML = value


    def set_l_3_target_id(self, value):
        self._L3_TARGET_ID = value


    def set_l_3_ds_id(self, value):
        self._L3_DS_ID = value


    def set_l_3_tile_id(self, value):
        self._L3_TILE_ID = value


    def set_l_3_target_dir(self, value):
        self._L3_TARGET_DIR = value


    def del_l_2_a_inspire_xml(self):
        del self._L2A_INSPIRE_XML


    def del_l_2_a_manifest_safe(self):
        del self._L2A_MANIFEST_SAFE


    def del_l_2_a_up_mtd_xml(self):
        del self._L2A_UP_MTD_XML


    def del_l_2_a_ds_mtd_xml(self):
        del self._L2A_DS_MTD_XML


    def del_l_2_a_tile_mtd_xml(self):
        del self._L2A_TILE_MTD_XML


    def del_l_2_a_up_id(self):
        del self._L2A_UP_ID


    def del_l_2_a_up_id_first(self):
        del self._L2A_UP_ID_first


    def del_l_2_a_ds_id(self):
        del self._L2A_DS_ID


    def del_l_2_a_tile_id(self):
        del self._L2A_TILE_ID


    def del_l_3_target_mtd_xml(self):
        del self._L3_TARGET_MTD_XML


    def del_l_3_ds_mtd_xml(self):
        del self._L3_DS_MTD_XML


    def del_l_3_tile_mtd_xml(self):
        del self._L3_TILE_MTD_XML


    def del_l_3_target_id(self):
        del self._L3_TARGET_ID


    def del_l_3_ds_id(self):
        del self._L3_DS_ID


    def del_l_3_tile_id(self):
        del self._L3_TILE_ID


    def del_l_3_target_dir(self):
        del self._L3_TARGET_DIR


    def get_naming_convention(self):
        return self._namingConvention


    def set_naming_convention(self, value):
        self._namingConvention = value


    def del_naming_convention(self):
        del self._namingConvention

    fnLog = property(get_fn_log, set_fn_log, del_fn_log)
    processorVersion = property(get_processor_version, set_processor_version, del_processor_version)
    productVersion = property(get_product_version, set_product_version, del_product_version)
    minTime = property(get_min_time, set_min_time, del_min_time)
    maxTime = property(get_max_time, set_max_time, del_max_time)
    algorithm = property(get_algorithm, set_algorithm, del_algorithm)
    cirrusRemoval = property(get_cirrus_removal, set_cirrus_removal, del_cirrus_removal)
    shadowRemoval = property(get_shadow_removal, set_shadow_removal, del_shadow_removal)
    snowRemoval = property(get_snow_removal, set_snow_removal, del_snow_removal)
    maxCloudProbability = property(get_max_cloud_probability, set_max_cloud_probability, del_max_cloud_probability)
    maxInvalidPixelsPercentage = property(get_max_invalid_pixels_percentage, set_max_invalid_pixels_percentage, del_max_invalid_pixels_percentage)
    maxAerosolOpticalThickness = property(get_max_aerosol_optical_thickness, set_max_aerosol_optical_thickness, del_max_aerosol_optical_thickness)
    maxSolarZenithAngle = property(get_max_solar_zenith_angle, set_max_solar_zenith_angle, del_max_solar_zenith_angle)
    cloudsPercentage = property(get_clouds_percentage, set_clouds_percentage, del_clouds_percentage)
    badPixelPercentage = property(get_bad_pixel_percentage, set_bad_pixel_percentage, del_bad_pixel_percentage)
    maxViewingAngle = property(get_max_viewing_angle, set_max_viewing_angle, del_max_viewing_angle)
    resolution = property(get_resolution, set_resolution, del_resolution)
    shared = property(get_shared, set_shared, del_shared)
    classifier = property(get_classifier, set_classifier, del_classifier)
    tileFilter = property(get_tile_filter, set_tile_filter, del_tile_filter)
    medianFilter = property(get_median_filter, set_median_filter, del_median_filter)
    home = property(get_home, set_home, del_home)
    sourceDir = property(get_source_dir, set_source_dir, del_source_dir)
    configDir = property(get_config_dir, set_config_dir, del_config_dir)
    binDir = property(get_bin_dir, set_bin_dir, del_bin_dir)
    libDir = property(get_lib_dir, set_lib_dir, del_lib_dir)
    logDir = property(get_log_dir, set_log_dir, del_log_dir)
    configFn = property(get_config_fn, set_config_fn, del_config_fn)
    processingStatusFn = property(get_processing_status_fn, set_processing_status_fn, del_processing_status_fn)
    processingEstimationFn = property(get_processing_estimation_fn, set_processing_estimation_fn, del_processing_estimation_fn)
    ncols = property(get_ncols, set_ncols, del_ncols)
    nrows = property(get_nrows, set_nrows, del_nrows)
    nbnds = property(get_nbnds, set_nbnds, del_nbnds)
    tTotal = property(get_t_total, set_t_total, del_t_total)
    displayData = property(get_display_data, set_display_data, del_display_data)
    radiometricPreference = property(get_radiometric_preference, set_radiometric_preference, del_radiometric_preference)
    GIPP = property(get_gipp, set_gipp, del_gipp)
    ECMWF = property(get_ecmwf, set_ecmwf, del_ecmwf)
    DEM = property(get_dem, set_dem, del_dem)
    L2A_BOA_QUANTIFICATION_VALUE = property(get_l_2_a_boa_quantification_value, set_l_2_a_boa_quantification_value, del_l_2_a_boa_quantification_value)
    L2A_WVP_QUANTIFICATION_VALUE = property(get_l_2_a_wvp_quantification_value, set_l_2_a_wvp_quantification_value, del_l_2_a_wvp_quantification_value)
    L2A_AOT_QUANTIFICATION_VALUE = property(get_l_2_a_aot_quantification_value, set_l_2_a_aot_quantification_value, del_l_2_a_aot_quantification_value)
    cleanTarget = property(get_clean_target, set_clean_target, del_clean_target)
    dnScale = property(get_dn_scale, set_dn_scale, del_dn_scale)
    radScale = property(get_rad_scale, set_rad_scale, del_rad_scale)
    timestamp = property(get_timestamp, set_timestamp, del_timestamp)
    creationDate = property(get_creation_date, set_creation_date, del_creation_date)
    acquisitionDate = property(get_acquisition_date, set_acquisition_date, del_acquisition_date)
    d2 = property(get_d_2, set_d_2, del_d_2)
    c0 = property(get_c_0, set_c_0, del_c_0)
    c1 = property(get_c_1, set_c_1, del_c_1)
    e0 = property(get_e_0, set_e_0, del_e_0)
    loglevel = property(get_logLevel, set_logLevel)
    logger = property(get_logger, set_logger, del_logger)
    solaz = property(get_solaz, set_solaz, del_solaz)
    solaz_arr = property(get_solaz_arr, set_solaz_arr, del_solaz_arr)
    solze = property(get_solze, set_solze, del_solze)
    solze_arr = property(get_solze_arr, set_solze_arr, del_solze_arr)
    vaa_arr = property(get_vaa_arr, set_vaa_arr, del_vaa_arr)
    vza_arr = property(get_vza_arr, set_vza_arr, del_vza_arr)
    targetDir = property(get_target_dir, set_target_dir, del_target_dir)
    L2A_INSPIRE_XML = property(get_l_2_a_inspire_xml, set_l_2_a_inspire_xml, del_l_2_a_inspire_xml)
    L2A_MANIFEST_SAFE = property(get_l_2_a_manifest_safe, set_l_2_a_manifest_safe, del_l_2_a_manifest_safe)
    L2A_UP_MTD_XML = property(get_l_2_a_up_mtd_xml, set_l_2_a_up_mtd_xml, del_l_2_a_up_mtd_xml)
    L2A_DS_MTD_XML = property(get_l_2_a_ds_mtd_xml, set_l_2_a_ds_mtd_xml, del_l_2_a_ds_mtd_xml)
    L2A_TILE_MTD_XML = property(get_l_2_a_tile_mtd_xml, set_l_2_a_tile_mtd_xml, del_l_2_a_tile_mtd_xml)
    L2A_UP_ID = property(get_l_2_a_up_id, set_l_2_a_up_id, del_l_2_a_up_id)
    L2A_UP_ID_first = property(get_l_2_a_up_id_first, set_l_2_a_up_id_first, del_l_2_a_up_id_first)
    L2A_DS_ID = property(get_l_2_a_ds_id, set_l_2_a_ds_id, del_l_2_a_ds_id)
    L2A_TILE_ID = property(get_l_2_a_tile_id, set_l_2_a_tile_id, del_l_2_a_tile_id)
    L3_TARGET_MTD_XML = property(get_l_3_target_mtd_xml, set_l_3_target_mtd_xml, del_l_3_target_mtd_xml)
    L3_DS_MTD_XML = property(get_l_3_ds_mtd_xml, set_l_3_ds_mtd_xml, del_l_3_ds_mtd_xml)
    L3_TILE_MTD_XML = property(get_l_3_tile_mtd_xml, set_l_3_tile_mtd_xml, del_l_3_tile_mtd_xml)
    L3_TARGET_ID = property(get_l_3_target_id, set_l_3_target_id, del_l_3_target_id)
    L3_DS_ID = property(get_l_3_ds_id, set_l_3_ds_id, del_l_3_ds_id)
    L3_TILE_ID = property(get_l_3_tile_id, set_l_3_tile_id, del_l_3_tile_id)
    L3_TARGET_DIR = property(get_l_3_target_dir, set_l_3_target_dir, del_l_3_target_dir)
    L2A_UP_DIR = property(get_l_2_a_up_dir, set_l_2_a_up_dir, del_l_2_a_up_dir)
    upScheme2a = property(get_up_scheme_2a, set_up_scheme_2a, del_up_scheme_2a)
    upScheme3 = property(get_up_scheme_3, set_up_scheme_3, del_up_scheme_3)
    tileScheme2a = property(get_tile_scheme_2a, set_tile_scheme_2a, del_tile_scheme_2a)
    tileScheme3 = property(get_tile_scheme_3, set_tile_scheme_3, del_tile_scheme_3)
    dsScheme2a = property(get_ds_scheme_2a, set_ds_scheme_2a, del_ds_scheme_2a)
    dsScheme3 = property(get_ds_scheme_3, set_ds_scheme_3, del_ds_scheme_3)
    gippScheme3 = property(get_gipp_scheme_3, set_gipp_scheme_3, del_gipp_scheme_3)
    manifestScheme = property(get_manifest_scheme, set_manifest_scheme, del_manifest_scheme)
    namingConvention = property(get_naming_convention, set_naming_convention, del_naming_convention)
    
    def initLogger(self):
        ''' Initialises the logging system.
        '''
        dt = datetime.now()
        self._creationDate = strftime('%Y%m%dT%H%M%S', dt.timetuple())
        logname = 'L3_' + self._creationDate
        self._logger = logging.Logger(logname)
        self._fnLog = os.path.join(self._logDir, logname + '_report.xml')
        f = open(self._fnLog, 'w')
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<Sen2Three_Level-3_Report_File>\n')
        f.close()
        lHandler = logging.FileHandler(self._fnLog)
        lFormatter = logging.Formatter('<check>\n<inspection execution=\"%(asctime)s\" level=\"%(levelname)s\" module=\"%(module)s\" function=\"%(funcName)s\" line=\"%(lineno)d\"/>\n<message contentType=\"Text\">%(message)s</message>\n</check>')
        lHandler.setFormatter(lFormatter)
        self._logger.addHandler(lHandler)
        self._logger.level = logging.INFO
        self._logger.info('Application started')
        self._logger.info('Logging system initialized with level: INFO')
        self._logger.info('Application initialized with root level %s', self._home)
        self._logger.info('Report file opened for results')
        self._logger.debug('Module L3_Config initialized')
        return

    def readGipp(self):
        ''' Reads the GIPP file and performs initialisation of the configuration properties.
        '''
        xp = L3_XmlParser(self, 'GIPP')
        xp.export()
        xp.validate()
        try:
            doc = objectify.parse(self._configFn)
            root = doc.getroot()
            cs = root.Common_Section
            self.loglevel = cs.Log_Level.text
            self._targetDir = cs.Target_Directory.text
        except:
            self._logger.fatal('Error in parsing configuration file.')
            self.exitError();

        try:
            self._displayData = cs.Display_Data
            l3s = root.L3_Synthesis
            self._minTime = l3s.Min_Time.text
            self._maxTime = l3s.Max_Time.text
            self._tileFilter = l3s.Tile_Filter.text.split()
            self._algorithm = l3s.Algorithm.text
            self._radiometricPreference = l3s.Radiometric_Preference.text
            self._cirrusRemoval = l3s.Cirrus_Removal.pyval
            self._shadowRemoval = l3s.Shadow_Removal.pyval
            self._snowRemoval = l3s.Snow_Removal.pyval
            self._maxCloudProbability = l3s.Max_Cloud_Probability.pyval
            self._maxInvalidPixelsPercentage = l3s.Max_Invalid_Pixels_Percentage.pyval
            self._maxAerosolOpticalThickness = l3s.Max_Aerosol_Optical_Thickness.pyval
            self._maxSolarZenithAngle = l3s.Max_Solar_Zenith_Angle.pyval
            self._medianFilter = l3s.Median_Filter.pyval
            
            cl = root.Classificators
            self._classifier =  {'NO_DATA'              : cl.NO_DATA.pyval,
                                'SATURATED_DEFECTIVE'   : cl.SATURATED_DEFECTIVE.pyval,
                                'DARK_FEATURES'         : cl.DARK_FEATURES.pyval,
                                'CLOUD_SHADOWS'         : cl.CLOUD_SHADOWS.pyval,
                                'VEGETATION'            : cl.VEGETATION.pyval,
                                'NOT_VEGETATED'         : cl.NOT_VEGETATED.pyval,
                                'WATER'                 : cl.WATER.pyval,
                                'UNCLASSIFIED'          : cl.UNCLASSIFIED.pyval,
                                'MEDIUM_PROBA_CLOUDS'   : cl.MEDIUM_PROBA_CLOUDS.pyval,
                                'HIGH_PROBA_CLOUDS'     : cl.HIGH_PROBA_CLOUDS.pyval,
                                'THIN_CIRRUS'           : cl.THIN_CIRRUS.pyval,
                                'SNOW_ICE'              : cl.SNOW_ICE.pyval,
                                'URBAN_AREAS'           : cl.URBAN_AREAS.pyval
                                }
        except:
            self._logger.fatal('Error in parsing configuration file.')
            self.exitError();
        return True

    def init(self, processorVersion):
        ''' Perform the base initialization.

            :param processorVersion: the version string.
            :type processorVersion: str         
            
        '''
        self._processorVersion = processorVersion
        self.initLogger()
        self.setSchemes()
        self.readGipp()
        self.setTimeEstimation(self.resolution)
        return

    def setTimeEstimation(self, resolution):
        ''' Set the time estimation for the current processing.

            :param resolution: the selected resolution.
            :type resolution: unsigned int    
            
        '''
        try:
            f = open(self.processingStatusFn, 'w')
            f.write('0.0\n')
            f.close()
        except:
            self.exitError('cannot create process status file: %s\n' % self.processingStatusFn)
            return

        factor = self.getNrTilesToProcess()

        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.read(self._processingEstimationFn)
        self._tEst60 = config.getfloat('time estimation','t_est_60') * factor
        self._tEst20 = config.getfloat('time estimation','t_est_20') * factor
        self._tEst10 = config.getfloat('time estimation','t_est_10') * factor
        if(resolution == 60):
            self._tEstimation = self._tEst60
        elif(resolution == 20):
            self._tEstimation = self._tEst20
        elif(resolution == 10):
            self._tEstimation = self._tEst10

        return

    def getNrTilesToProcess(self):
        ''' Get the number of tiles to process.

            :return: number of processed tiles.
            :rtype: unsigned int

        '''
        upList = sorted(os.listdir(self.sourceDir))
        tileFilter = self.tileFilter
        nrTiles = 0

        for L2A_UP_ID in upList:
            L2A_mask = '*_MSIL2A_*'

            if not fnmatch.fnmatch(L2A_UP_ID, L2A_mask):
                continue
            if not self.checkTimeRange(L2A_UP_ID):
                continue

            GRANULE = os.path.join(self.sourceDir, L2A_UP_ID, 'GRANULE')
            if self.productVersion == 13.1:
                L2A_mask = '*_MSI_L2A_*'
            else:
                L2A_mask = 'L2A_*'
            tilelist = sorted(os.listdir(GRANULE))
            for tile in tilelist:
                # process only L2A tiles:
                if not fnmatch.fnmatch(tile, L2A_mask):
                    continue
                # ignore already processed tiles:
                if self.tileExists(tile):
                    continue
                # apply tile filter:
                if not self.tileIsSelected(tile, tileFilter):
                    continue
                if not self.checkTileConsistency(GRANULE, tile):
                    continue
                nrTiles += 1

        return nrTiles

    def writeTimeEstimation(self, resolution, tMeasure):
        ''' Store the time estimation for the current processing.

            :param resolution: the selected resolution.
            :type resolution: unsigned int
            :param tMeasure: the measured performance data in seconds + fractions.
            :type tMeasure: float 32
            
        '''
        config = ConfigParser.RawConfigParser()
        config.read(self._processingEstimationFn)

        if(self.resolution == 60):
            tEst = config.getfloat('time estimation','t_est_60')
            tMeasureAsString = str((tEst + tMeasure) / 2.0 )
            config.set('time estimation','t_est_60', tMeasureAsString)

        elif(self.resolution == 20):
            tEst = config.getfloat('time estimation','t_est_20')
            tMeasureAsString = str((tEst + tMeasure) / 2.0 )
            config.set('time estimation','t_est_20', tMeasureAsString)

        elif(self.resolution == 10):
            tEst = config.getfloat('time estimation','t_est_10')
            tMeasureAsString = str((tEst + tMeasure) / 2.0 )
            config.set('time estimation','t_est_10', tMeasureAsString)

        with open(self._processingEstimationFn, 'w') as configFile:
            config.write(configFile)
        return

    def timestamp(self, procedure):
        ''' Marks a time stamp for the duration of the previous procedure.

            :param procedure: the previous procedure.
            :type procedure: str
            
        '''
        tNow = datetime.now()
        tDelta = tNow - self._timestamp
        self._timestamp = tNow
        self.logger.info('Procedure: ' + procedure + ', elapsed time[s]: %0.3f' % tDelta.total_seconds())
        if(self.logger.getEffectiveLevel() != logging.NOTSET):
            stdoutWrite('Procedure %s, elapsed time[s]: %0.3f\n' % (procedure, tDelta.total_seconds()))
        #else:
        if self._tEstimation == 0:
            self._tEstimation = 1.0
        increment = tDelta.total_seconds() / self._tEstimation
        f = open(self._processingStatusFn, 'r')
        tTotal = float(f.readline()) * 0.01
        f.close()
        tTotal += increment
        if tTotal > 1.0:
            tWeighted = 100.0 - exp(-tTotal)
        elif tTotal > 0.98:
            tWeighted = tTotal * 100.0 - exp(-tTotal)
        else:
            tWeighted = tTotal * 100.0

        stdoutWrite('Progress[%%]: %03.2f : ' % tWeighted)
        f = open(self._processingStatusFn, 'w')
        f.write(str(tWeighted) + '\n')
        f.close()
        return

    def checkTimeRange(self, userProduct):
        ''' Check if current user product is within configured time range.

            :param userProduct: the user product ID.
            :type userProduct: str
            :return: true, if within time range, false else.
            :rtype: boolean
            
        '''
        def replace(string):
            for ch in ['-',':', 'Z']:
                if ch in string:
                    string=string.replace(ch, '')
            return string

        cfgMinTimeS = replace(self.minTime)
        cfgMaxTimeS = replace(self.maxTime)
        cfgMinTime = time.mktime(datetime.strptime(cfgMinTimeS, '%Y%m%dT%H%M%S').timetuple())
        cfgMaxTime = time.mktime(datetime.strptime(cfgMaxTimeS, '%Y%m%dT%H%M%S').timetuple())
        prdMinTimeS = userProduct[47:62]
        prdMaxTimeS = userProduct[63:78]
        try: # check if its' a V13.1 product:
            prdMinTime = time.mktime(datetime.strptime(prdMinTimeS,'%Y%m%dT%H%M%S').timetuple())
            prdMaxTime = time.mktime(datetime.strptime(prdMaxTimeS,'%Y%m%dT%H%M%S').timetuple())
            self.namingConvention = 'SAFE_STANDARD'
            self.productVersion = 13.1
        except:
            prdMinTimeS = userProduct[45:60]
            try: # check if its' a V14.2 product:
                prdMinTime = time.mktime(datetime.strptime(prdMinTimeS,'%Y%m%dT%H%M%S').timetuple())
                prdMaxTime = prdMinTime
                self.namingConvention = 'SAFE_COMPACT'
                prdBaseline = int(userProduct[28:32])
                if  prdBaseline < 207:
                    self.productVersion = 14.2
                else:
                    self.productVersion = 14.5
            except: # nothing of both, exit now.
                self.exitError('error in parsing timestamp of user product: %s' % prdMinTimeS)

        self.setSchemes()
        self.minTime = cfgMinTimeS
        self.maxTime = cfgMaxTimeS
      
        if prdMinTime < cfgMinTime:
            return False
        elif prdMaxTime > cfgMaxTime:
            return False
        else:
            return True

    def readTileMetadata(self, tileID):
        ''' Read the metadata for the given tile ID.

            :param tileID: the tile ID.
            :type tileID: str
            
        '''
        xp = L3_XmlParser(self, tileID)
        ang = xp.getTree('Geometric_Info', 'Tile_Angles')
        azimuthAnglesList = ang.Sun_Angles_Grid.Azimuth.Values_List.VALUES
        solaz_arr = xp.getFloatArray(azimuthAnglesList)
        zenithAnglesList = ang.Sun_Angles_Grid.Zenith.Values_List.VALUES
        solze_arr = xp.getFloatArray(zenithAnglesList)
        # images may be not squared - this is the case for the current testdata used
        # angle arrays have to be adapted, otherwise the bilinear interpolation is misaligned.
        imgSizeList = xp.getTree('Geometric_Info', 'Tile_Geocoding')
        size = imgSizeList.Size
        sizelen = len(size)
        nrows = None
        ncols = None
        for i in range(sizelen):
            if int(size[i].attrib['resolution']) == self._resolution:
                nrows = int(size[i].NROWS)
                ncols = int(size[i].NCOLS)
                break

        if(nrows == None or ncols == None):
            self.exitError('no image dimension in metadata specified, please correct')

        if(nrows < ncols):
            last_row = int(solaz_arr[0].size * float(nrows)/float(ncols) + 0.5)
            saa = solaz_arr[0:last_row,:]
            sza = solze_arr[0:last_row,:]
        elif(ncols < nrows):
            last_col = int(solaz_arr[1].size * float(ncols)/float(nrows) + 0.5)
            saa = solaz_arr[:,0:last_col]
            sza = solze_arr[:,0:last_col]
        else:
            saa = solaz_arr
            sza = solze_arr

        if(saa.max() < 0):
            saa *= -1
        self.saaArray = clip(saa, 0, 360.0)

        sza = absolute(sza)
        self.solze_arr = clip(sza, 0, 70.0)

        self.nrows = nrows
        self.ncols = ncols
        solze = float32(ang.Mean_Sun_Angle.ZENITH_ANGLE.text)
        solaz = float32(ang.Mean_Sun_Angle.AZIMUTH_ANGLE.text)

        self._solze = absolute(solze)
        if self._solze > 70.0:
            self._solze = 70.0

        if solaz < 0:
            solaz *= -1
        if solaz > 360.0:
            solaz = 360.0
        self._solaz = solaz

        #
        # ATCOR employs the Lamberts reflectance law and assumes a constant viewing angle per tile (sub-scene)
        # as this is not given, this is a workaround, which have to be improved in a future version
        #
        viewAnglesList = ang.Mean_Viewing_Incidence_Angle_List.Mean_Viewing_Incidence_Angle
        arrlen = len(viewAnglesList)
        vaa = zeros(arrlen, float32)
        vza = zeros(arrlen, float32)
        for i in range(arrlen):
            vaa[i] = float32(viewAnglesList[i].AZIMUTH_ANGLE.text)
            vza[i] = float32(viewAnglesList[i].ZENITH_ANGLE.text)

        _min = vaa.min()
        _max = vaa.max()
        if _min < 0: _min += 360
        if _max < 0: _max += 360
        vaa_arr = array([_min,_min,_max,_max])
        self.vaa_arr = vaa_arr.reshape(2,2)

        _min = absolute(vza.min())
        _max = absolute(vza.max())
        if _min > 40.0: _min = 40.0
        if _max > 40.0: _max = 40.0
        vza_arr = array([_min,_min,_max,_max])
        self.vza_arr = vza_arr.reshape(2,2)
        return

    def parNotFound(self, parameter):
        ''' Throw a fatal error message if a configuration parameter is not found and terminate the application.
        '''
        self.logger.fatal('Configuration parameter %s not found in %s', parameter, self._configFn)
        stderrWrite('Configuration parameter <%s> not found in %s\n' % (parameter, self._configFn))
        stderrWrite('Program is forced to terminate.')
        self.__exit__()

    def exitError(self, reason = None):
        ''' Throw an error message if a fatal error occurred and and terminate the application.
        '''        
        stderrWrite('Fatal error occurred, application will terminate.')
        if reason: stderrWrite('\nReason: ' + reason)
        self.__exit__()

    def _getDoc(self):
        from xml.etree import ElementTree as ET
        try:
            tree = ET.parse(self.configFn)
        except Exception, inst:
            self.logger.exception("Unexpected error opening %s: %s", self.configFn, inst)
            self.exitError('Error in XML document')
        doc = tree.getroot()
        return doc

    def getInt(self, label, key):
        ''' Low level routine for getting an int value from configuration file.

            :param label: the doc string within xml tree.
            :type label: str
            :param key: the parameter key.
            :type key: str
            :return: the parameter value.
            :rtype: int
            
        '''
        doc = self._getDoc()
        parameter = label + '/' + key
        par = doc.find(parameter)
        if par is None: self.parNotFound(parameter)
        return int(par.text)

    def getFloat(self, label, key):
        ''' Low level routine for getting a flot32 value from configuration file.

            :param label: the doc string within xml tree.
            :type label: str
            :param key: the parameter key.
            :type key: str
            :return: the parameter value.
            :rtype: float32
            
        '''
        doc = self._getDoc()
        parameter = label + '/' + key
        par = doc.find(parameter)
        if par is None: self.parNotFound(parameter)
        return float32(par.text)

    def getStr(self, label, key):
        ''' Low level routine for getting a string value from configuration file.

            :param label: the doc string within xml tree.
            :type label: str
            :param key: the parameter key.
            :type key: str
            :return: the parameter value.
            :rtype: string
            
        '''
        doc = self._getDoc()
        parameter = label + '/' + key
        par = doc.find(parameter)
        if par is None: self.parNotFound(parameter)
        return par.text

    def getIntArray(self, node):
        ''' Low level routine for getting an integer array from configuration file.

            :param node: the parameter node.
            :type node: str
            :return: the parameter array.
            :rtype: numpy array
            
        '''
        nrows = len(node)
        if nrows < 0:
            return False

        ncols = len(node[0].split())
        a = zeros([nrows,ncols],dtype=int)

        for i in range(nrows):
            a[i,:] = array(node[i].split(),dtype(int))

        return a

    def getUintArray(self, node):
        ''' Low level routine for getting an unsigned integer array from configuration file.

            :param node: the parameter node.
            :type node: str
            :return: the parameter array.
            :rtype: numpy array
            
        '''
        nrows = len(node)
        if nrows < 0:
            return False

        ncols = len(node[0].split())
        a = zeros([nrows,ncols],dtype=int)

        for i in range(nrows):
            a[i,:] = array(node[i].split(),dtype(int))

        return a

        nrows = len(node)
        if nrows < 0:
            return False

        ncols = len(node[0].split())
        a = zeros([nrows,ncols],dtype=uint)

        for i in range(nrows):
            a[i,:] = array(node[i].split(),dtype(uint))

        return a

    def getFloatArray(self, node):
        ''' Low level routine for getting a float32 array from configuration file.

            :param node: the parameter node.
            :type node: str
            :return: the parameter array.
            :rtype: numpy array
            
        '''
        nrows = len(node)
        if nrows < 0:
            return False

        ncols = len(node[0].split())
        a = zeros([nrows,ncols],dtype=float32)

        for i in range(nrows):
            a[i,:] = array(node[i].split(),dtype(float32))

        return a

    def putArrayAsStr(self, a, node):
        ''' Low level routine for setting a numpy array as string into configuration file.
            Can be one or two dimensional.

            :param a: the numpy array
            :type a: numpy array
            :param node: the parameter node.
            :type node: str
            :return: false, if array exceeds two dimensions.
            :rtype: boolean
            
        '''        
        if a.ndim == 1:
            nrows = a.shape[0]
            for i in nrows:
                node[i] = a[i],dtype=str

        elif a.ndim == 2:
            nrows = a.shape[0]
            for i in range(nrows):
                aStr = array_str(a[i,:]).strip('[]')
                node[i] = aStr
        else:
            return False
        
    def tileIsSelected(self, tile, tileFilter):
        """ Low level routine for determine if tile should be processed

            :param tile: the current tile ID
            :type tile: str
            :param tileFilter: list of accepted tiles.
            :type tileFilter: an array of strings
            :return: false, if tile not in filter list
            :rtype: boolean

        """

        if tileFilter == ['*']:
            return True
        for item in tileFilter:
            if item in tile:
                return True
            else:
                return False

    def getNrTilesProcessed(self):
        ''' Get the number of processed tiles.

            :return: number of processed tiles.
            :rtype: unsigned int

        '''

        tileId = self.L2A_TILE_ID.split('_')
        if len(tileId) == 4:
            tileId = tileId[3] + '_' + tileId[1] + '_' + str(self.resolution)
        else:
            tileId = tileId[7] + '_' + tileId[9] + '_' + str(self.resolution)
        processedFn = os.path.join(self.sourceDir, 'processed')

        tileIdSub = tileId[-9:]
        try:  # read list already processed same tiles of same resolution
            f = open(processedFn, 'r')
            processedTiles = f.read()
            f.close()
            return processedTiles.count(tileIdSub)
        except:
            return 0

    def tileExists(self, tileId):
        ''' Check if a tile is present in the product history.

            :param tileId: the tile identifier.
            :type tileId: str
            :return: true, if present.
            :rtype: boolean

        '''

        tileId = tileId.split('_')
        if len(tileId) == 4:
            tileId = tileId[3] + '_' + tileId[1] + '_' + str(self.resolution)
        else:
            tileId = tileId[7] + '_' + tileId[9] + '_' + str(self.resolution)
        processedFn = os.path.join(self.sourceDir, 'processed')

        try:  # read list of tiles already processed
            f = open(processedFn, 'r')
            processedTiles = f.read()
            if tileId in processedTiles:
                return True
        except:
            pass

        return False

    def appendTile(self):
        ''' Append a tile to the product history.

            :return: true, if operation successful.
            :rtype: boolean

        '''
        tileId = self.L2A_TILE_ID.split('_')
        if len(tileId) == 4:
            tileId = tileId[3] + '_' + tileId[1] + '_' + str(self.resolution)
        else:
            tileId = tileId[7] + '_' + tileId[9] + '_' + str(self.resolution)
        processedTile = tileId + '\n'
        processedFn = os.path.join(self.sourceDir, 'processed')

        try:
            f = open(processedFn, 'a')
            f.write(processedTile)
            f.flush()
            f.close()
        except:
            stderrWrite('Could not update processed tile history.\n')
            self.exitError()
            return False

        return True

    def reinitTile(self, L3_TILE_ID):
        ''' reinit tile after change has been performed
            :param L3_TILE_ID: the current L3 tile ID
            :type tile: str

            :return: true, if present.
            :rtype: boolean

        '''
        self.L3_TILE_ID = L3_TILE_ID
        L3_MTD_MASK = 'MTD_TL.xml'

        GRANULE = 'GRANULE'
        L3_TILE_ID = os.path.join(self.L3_TARGET_DIR, GRANULE, self.L3_TILE_ID)
        dirlist = sorted(os.listdir(L3_TILE_ID))
        for L3_TILE_MTD_XML in dirlist:
            if fnmatch.fnmatch(L3_TILE_MTD_XML, L3_MTD_MASK):
                self.L3_TILE_MTD_XML = os.path.join(L3_TILE_ID, L3_TILE_MTD_XML)
                return True

        return False

    def checkTileConsistency(self, tilePath, tileId):
        """ Low level routine for determine if tile should be processed

            :param tilePath: the tile path
            :type tile: str
            :param tileId: the current tile ID
            :type tile: str
            :return: true, if conditions are fulfilled
            :rtype: boolean

        """
        test = False
        GRANULE = 'GRANULE'
        IMG_DATA = 'IMG_DATA'

        if self.resolution == 10:
            bandDir = 'R10m'
        elif self.resolution == 20:
            bandDir = 'R20m'
        elif self.resolution == 60:
            bandDir = 'R60m'

        L2A_TileDir = os.path.join(tilePath, tileId)
        L2A_ImgDataDir = os.path.join(L2A_TileDir, IMG_DATA)
        L2A_BandDir = os.path.join(L2A_ImgDataDir, bandDir)

        B02_OK = False
        SCL_OK = False
        AOT_OK = False
        fmB02 = '*_B02_*.jp2'
        fmSCL = '*_SCL_*.jp2'
        fmAOT = '*_AOT_*.jp2'
        dirs = sorted(os.listdir(L2A_BandDir))
        for filename in dirs:
            if fnmatch.fnmatch(filename, fmB02) == True:
                B02_OK = True
            if fnmatch.fnmatch(filename, fmSCL) == True:
                SCL_OK = True
            if fnmatch.fnmatch(filename, fmAOT) == True:
                AOT_OK = True

        # B02 always must be present:
        if B02_OK == False:
            self.logger.error('Band 02 is not present, resolution will be ignored.')
            return False

        # check that AOT map is present if AOT algorithm is selected:
        if self.algorithm == 'RADIOMETRIC_QUALITY' and self.radiometricPreference == 'AEROSOL_OPTICAL_THICKNESS':
            if AOT_OK == False:
                self.logger.error('AOT map is not present, algorithm will be ignored.')
                return False

        # SCL is only present for resolutions > 10:
        if self.resolution > 10:
            if self.namingConvention == 'SAFE_COMPACT':
                test = SCL_OK
            else: # for SAFE_STANDARD scene classification is in IMG_DATA folder:
                dirs = sorted(os.listdir(L2A_ImgDataDir))
                for filename in dirs:
                    if fnmatch.fnmatch(filename, fmSCL) == True:
                        test = True
                        break
        else:
            test = True # 10 m has no Scene Classification
        if test == False:
            self.logger.error('Scene classification for resolution %d is not present, resolution will be ignored.' % self.resolution)
        return test


    def setProductVersion(self):
        ''' Sets the product version from metadata.

            :return: true, if operation successful.
            :rtype: boolean

        '''

        # get the product version from metadata:
        filelist = sorted(os.listdir(self.sourceDir))
        if self.namingConvention == 'SAFE_STANDARD':
            filemask = 'S2?_OPER_MTD_SAFL2A*.xml'
        else:
            filemask = 'MTD_MSIL2A.xml'

        for filename in filelist:
            if(fnmatch.fnmatch(filename, filemask) == True):
                doc = objectify.parse(os.path.join(self.sourceDir, filename))
                root = doc.getroot()
                url = root.nsmap['n1']
                self.productVersion = int(url[12:14])
                return True

        return False


    def setSchemes(self):
        try:
            doc = objectify.parse(self.configFn)
            root = doc.getroot()
            psd = root.Common_Section.PSD_Scheme
            psdLen = len(psd)
            for i in range(psdLen):
                # this implements the version dependency for the PSD:
                if (psd[i].attrib['PSD_Version']) == str(self.productVersion):
                    prefix = psd[i].attrib['PSD_Reference']
                    self._upScheme2a = os.path.join(prefix, psd[i].UP_Scheme_2A.text)
                    self._upScheme3 = os.path.join(prefix, psd[i].UP_Scheme_3.text)
                    self._tileScheme2a = os.path.join(prefix, psd[i].Tile_Scheme_2A.text)
                    self._tileScheme3 = os.path.join(prefix, psd[i].Tile_Scheme_3.text)
                    self._dsScheme2a = os.path.join(prefix, psd[i].DS_Scheme_2A.text)
                    self._dsScheme3 = os.path.join(prefix, psd[i].DS_Scheme_3.text)
                    break

            self._gippScheme3 = 'L3_GIPP.xsd'
            self._manifestScheme = os.path.join(prefix[:-6] + 'SAFE', 'resources', \
                'xsd', 'int', 'esa', 'safe', 'sentinel', '1.2', \
                'sentinel-2', 'msi', 'archive_l2a_user_product', 'xfdu.xsd')
        except:
            self.logger.fatal('wrong identifier for xml structure: ' + product)

        return
