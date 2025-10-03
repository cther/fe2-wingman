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

import wingman as wm
from loggsys import log


name = 'FE2 Wingman'
version = 'v0.0.10'
date = 'Oct. 2025'
sender = name + ' ' + version

env_opt_logging = True if os.getenv('WM_CONFIG_LOG_LEVEL', 'WARNING') == 'DEBUG' else False

env_db_url = os.getenv('WM_CONFIG_DB_URL')

env_fe2_url = os.getenv('WM_CONFIG_FE2_URL')
env_fe2_sec = os.getenv('WM_CONFIG_FE2_SECRET')

env_opt_units = True if os.getenv('WM_CONFIG_FE2_USE_UNIT_IDS', 'false') == 'true' else False

env_opt_road = True if os.getenv('WM_OPTION_ROADBLOCK_ENABLE', 'false') == 'true' else False
env_opt_road_new = True if os.getenv('WM_OPTION_ROADBLOCK_NEW', 'false') == 'true' else False
env_opt_road_upcoming = True if os.getenv('WM_OPTION_ROADBLOCK_UPCOMING', 'false') == 'true' else False
env_opt_road_expiring = True if os.getenv('WM_OPTION_ROADBLOCK_EXPIRING', 'false') == 'true' else False

#env_opt_vehicle = True if os.getenv('WM_OPTION_VEHICLE_ENABLE', 'false') == 'true' else False


print()
print(' +-----------------------+')
print(' |                       |')
print(' |      %s      |' % name)
print(' |                       |')
print(' |   %s  %s   |' % (version, date))
print(' |                       |')
print(' +-----------------------+')
print()
print('  - Config "Call units":', env_opt_units)
print()
print('  - Option "ROAD":   ', env_opt_road)
print('      - get new/modified: ', env_opt_road_new)
print('      - get upcomming:    ', env_opt_road_upcoming)
print('      - get expiring:     ', env_opt_road_expiring)
print()
#print('  - Option "VEHICLE":', env_opt_vehicle)
#print()


wingman = wm.wingman(sender, env_db_url, env_fe2_url, env_fe2_sec)
print(' FE2 server version:', wingman.get_server_version())
print()

if env_opt_units:
    units = dict()
    config = configparser.ConfigParser()
    config.optionxform=str

    config_path = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(config_path, 'unit_ids.ini')

    config.read(config_file)

    if not len(config.sections()):
         log.critical("Can't open unit config file in 'data/unit_ids.ini'!")
         exit()

    orga_units = config['orga_units']
    if not len(orga_units):
        log.critical('Get No items from config file!')
        exit()

    log.warning(' Add following units:')
    for id in orga_units:
        units[id] = orga_units[id]
        log.warning('  + %-15s : %s' % (id, units[id]))

    wingman.add_units(units)


scheduler = schedule.Scheduler()
#scheduler.every(10).seconds.do(wingman.run_check)

if env_opt_road:
    if env_opt_road_new:
        scheduler.every(1).minutes.do(wingman.run_rb_new)
    
    if env_opt_road_upcoming:
        scheduler.every(1).minutes.do(wingman.run_rb_upcoming)
    
    if env_opt_road_expiring:
        scheduler.every(1).minutes.do(wingman.run_rb_expiring)

#if env_opt_vehicle:
#    pass


while True:
    scheduler.run_pending()
    time.sleep(1)
