# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Christian Ther
# 
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#  
#  1. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#  
#  2. Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOSR
#  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import time
import schedule
import configparser

import win32serviceutil
import win32service
import servicemanager

import version
import wingman as wm
from exceptions import *
from loggsys import log, log_conf_srv

logfile = 'c:\\fe2_wingman.log'
log_conf_srv(logfile)

class WingmanService(win32serviceutil.ServiceFramework):
    _svc_name_ = version.__name__
    _svc_display_name_ = version.__discr__

    def __init__(self, args):
        super().__init__(args)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        log.warning('Get signal to stop service...')
        self.__running = False

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.__wingman = None
        self.__running = True
        restart_delay = 10
        
        log.warning('*** Welcome to %s %s (%s) ***' % (version.__name__, version.__str__, version.__date__))

        config = configparser.ConfigParser()
        config.optionxform=str

        config_path = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(config_path, 'config.ini')

        config.read(config_file)

        if not len(config.sections()):
            log.critical("Can't load configuration from 'data/config.ini'!")
            self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)
            exit()
        log.warning('Configuration file loaded')

        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        while self.__running:
            try:
                self.ServiceWorker(config)
            except DatabaseError as error:
                log.critical(error)
                #del self.__wingman
                log.warning('Try to restart connection in %d sec.' % restart_delay)
                time.sleep(10)
            except Fe2ServerError as error:
                log.critical(error)
                #del self.__wingman
                log.warning('Try to restart connection in %d sec.' % restart_delay)
                time.sleep(10)
            except Exception as error:
                log.critical(error)
                self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)
                self.__running = False
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def ServiceWorker(self, config):

        env_db_url = config['server']['db_url']

        env_fe2_url = config['server']['fe2_url']
        env_fe2_sec = config['server']['fe2_secret']

        env_opt_units = True if config['opt_orga_units'].get('orga_units_enable', 'false') == 'true' else False

        env_opt_road_new = True if config['opt_roadblock'].get('roadblock_get_new', 'false') == 'true' else False
        env_opt_road_upcoming = True if config['opt_roadblock'].get('roadblock_get_upcoming', 'false') == 'true' else False
        env_opt_road_expiring = True if config['opt_roadblock'].get('roadblock_get_expiring', 'false') == 'true' else False

        env_opt_vehicle = True if config['opt_vehiclestate'].get('vehiclestate_enable', 'false') == 'true' else False
        env_opt_vehicle_skip_c = True if config['opt_vehiclestate'].get('vehiclestate_skip_c', 'false') == 'true' else False
        env_opt_vehicle_skip_0 = True if config['opt_vehiclestate'].get('vehiclestate_skip_0', 'false') == 'true' else False
        env_opt_vehicle_skip_5 = True if config['opt_vehiclestate'].get('vehiclestate_skip_5', 'false') == 'true' else False

        
        log.info('Database link: %s' % env_db_url)
        log.info('FE2 link: %s' % env_fe2_url)
        log.info('FE2 secret: %s' % env_fe2_sec)

        sender = version.__name__ + ' ' + version.__str__
        self.__wingman = wm.wingman(sender, env_db_url, env_fe2_url, env_fe2_sec)

        log.warning('Server connection established. FE2 version: %s' %  self.__wingman.get_server_version())


        if env_opt_units:
            units = dict()

            orga_units = config['orga_units']
            if not len(orga_units):
                self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)
                raise Exception('Get no items from configuration file!')

            log.warning('Add following units:')
            for id in orga_units:
                units[id] = orga_units[id]
                log.warning('  + %-15s : %s' % (id, units[id]))

            self.__wingman.add_units(units)
            log.warning('Unit ids loaded')


        scheduler = schedule.Scheduler()
        #scheduler.every(10).seconds.do(wingman.run_check)

        if env_opt_road_new:
            log.warning('Support for new/modified road blocks enabled')
            scheduler.every(1).minutes.do(self.__wingman.run_rb_new)
        
        if env_opt_road_upcoming:
            log.warning('Support for upcoming road blocks enabled')
            scheduler.every(1).minutes.do(self.__wingman.run_rb_upcoming)
        
        if env_opt_road_expiring:
            log.warning('Support for expiring road blocks enabled')
            scheduler.every(1).minutes.do(self.__wingman.run_rb_expiring)

        if env_opt_vehicle:
            log.warning('Support for vehicle states enabled')
            
            if env_opt_vehicle_skip_c:
                log.warning('Skip vehicle state C')
                self.__wingman.get_state_c(False)

            if env_opt_vehicle_skip_0:
                log.warning('Skip vehicle state 0')
                self.__wingman.get_state_0(False)

            if env_opt_vehicle_skip_5:
                log.warning('Skip vehicle state 5')
                self.__wingman.get_state_5(False)

            scheduler.every(5).seconds.do(self.__wingman.run_vs_new)

        log.warning('Running...')

        while self.__running:
            scheduler.run_pending()
            time.sleep(1)
        
        log.warning('Sopped')


if __name__ == '__main__':
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(WingmanService)
    servicemanager.StartServiceCtrlDispatcher()