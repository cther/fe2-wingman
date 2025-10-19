#!/usr/bin/env python
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

from exceptions import *
from loggsys import log
import wingman as wm
import version


name = version.__name__
num = version.__str__
date = version.__date__
sender = name + ' ' + num

log.warning('*** Welcome to %s %s (%s) ***' % (name, num, date))


config = configparser.ConfigParser()
config.optionxform=str

config_path = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(config_path, 'config.ini')

config.read(config_file)

if not len(config.sections()):
     log.critical("Can't open configuration file from 'data/config.ini'!")
     exit()

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

log.warning('Configuration file loaded')

log.info('Database link: %s' % env_db_url)
log.info('FE2 link: %s' % env_fe2_url)
log.info('FE2 secret: %s' % env_fe2_sec)

try:
    wingman = wm.wingman(sender, env_db_url, env_fe2_url, env_fe2_sec)
except DatabaseError as error:
    log.critical(error)
    exit()
except Fe2ServerError as error:
    log.critical(error)
    exit()
else:
    log.warning('Server connection established. FE2 version: %s' %  wingman.get_server_version())


if env_opt_units:
    units = dict()

    orga_units = config['orga_units']
    if not len(orga_units):
        log.critical('Get no unit ids from configuration file!')
        exit()

    log.info('Add following units:')
    for id in orga_units:
        units[id] = orga_units[id]
        log.info('  + %-15s : %s' % (id, units[id]))

    wingman.add_units(units)
    log.warning('Unit ids loaded')


scheduler = schedule.Scheduler()
#scheduler.every(10).seconds.do(wingman.run_check)


if env_opt_road_new:
    log.warning('Support for new/modified road blocks enabled')
    scheduler.every(1).minutes.do(wingman.run_rb_new)

if env_opt_road_upcoming:
    log.warning('Support for upcomming road blocks enabled')
    scheduler.every(1).minutes.do(wingman.run_rb_upcoming)

if env_opt_road_expiring:
    log.warning('Support for expiring road blocks enabled')
    scheduler.every(1).minutes.do(wingman.run_rb_expiring)

if env_opt_vehicle:
    log.warning('Support for vehicle states enabled')

    if env_opt_vehicle_skip_c:
        log.warning('Skip vehicle state C')
        wingman.get_state_c(False)

    if env_opt_vehicle_skip_0:
        log.warning('Skip vehicle state 0')
        wingman.get_state_0(False)

    if env_opt_vehicle_skip_5:
        log.warning('Skip vehicke state 5')
        wingman.get_state_5(False)

    scheduler.every(5).seconds.do(wingman.run_vs_new)


while True:
    try:
        scheduler.run_pending()
    except DatabaseError as error:
        log.critical(error)
        exit()
    except Fe2ServerError as error:
        log.critical(error)
        exit()
    except Exception as error:
        log.critical('An unknown error has occurred: %s' % error)
    else:
        time.sleep(1)