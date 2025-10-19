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

import pymongo
import pytz
from datetime import datetime, timedelta

from exceptions import *
from loggsys import log


class mongodb:
    def __init__(self, url):
        self.__connected = False
        
        try:
            self.__host = pymongo.MongoClient(url, serverSelectionTimeoutMS=1000)
            self.__host.server_info()
        except Exception as error:
            raise DatabaseError('FE2 db connection error', error)
        else:
            self.__connected = True

    def not_connected(self):
        return not self.__connected

    def get_host(self):
        if self.__connected:
            return self.__host
        else:
            return None

    def get_app_version(self):
        if self.__connected:
            table = self.__host['de_alamos_fe2']['versionComponents']
            res = table.find({})
            return res[0].get('fullVersion')
        else:
            return None
        
    def check_connection(self):
        try:
            self.__host.server_info()
        except Exception as error:
            raise DatabaseError('FE2 db connection error', error)


class roadblock:
    def __init__(self, db_host):
        self.__host = db_host.get_host()

        self.__table = self.__host['de_alamos_fe2']['roadblockV2']

        self.__tz_utc = pytz.timezone('Etc/UTC')

        self.__tp_last_run = int(datetime.now(self.__tz_utc).timestamp()*1000)
        self.__tp_pre_run = self.__tp_last_run
    
    def reset_last_run(self):
        self.__tp_last_run = 0
        self.__tp_pre_run = 0

    def get_last_run(self):
        return self.__tp_pre_run

    def conv_tp(self, tp):
        tmp_utc = self.__tz_utc.localize(tp)
        return tmp_utc.astimezone()

    def conv_tp_iso(self, tp):
        tmp_utc = self.__tz_utc.localize(datetime.strptime(tp, '%Y-%m-%dT%H:%M:%SZ'))
        tmp = tmp_utc.astimezone()
        return tmp
    
    def conv_tp_unix(self, tp):
        return datetime.fromtimestamp(tp/1000).astimezone()

    def tp_lt_now(self, tp):
        now = datetime.now().astimezone()
        return True if tp < now else False
    
    def tp_date_eq_now(self, tp):
        now = datetime.now().astimezone()
        return True if tp.date() == now.date() else False
    
    def tp_date_eq(self, tp1, tp2):
        return True if tp1.date() == tp2.date() else False

    def query(self, query):        
        return self.__table.find(query)
    
    def get_all(self):
        return self.__table.find({})

    def get_new(self):
        self.__tp_pre_run = self.__tp_last_run
        log.info('Get new entries')
        ret = self.__table.find({'lastChanged' : {'$gt': self.__tp_last_run}})            
        self.__tp_last_run = int(datetime.now(self.__tz_utc).timestamp()*1000)
        log.info('Finished, update tp: %d' % self.__tp_last_run)
        return ret
    
    def get_upcoming(self, offset=0):
        now = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=offset)
        log.info('Get events that are starting at: %s' % now)
        ret = self.__table.find({'from' : {'$eq' : now.astimezone(self.__tz_utc) } })
        log.info('Finished')
        return ret
    
    def get_expiring(self, offset=0):
        now = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=offset)
        log.info('Get events that are ending at: %s' % now)
        ret = self.__table.find({'to' : {'$eq' : now.astimezone(self.__tz_utc) } })
        log.info('Finished')
        return ret
    

class vehiclestate:
    def __init__(self, db_host):
        self.__host = db_host.get_host()

        self.__tb_vehicle = self.__host['de_alamos_fe2']['vehicle']
        self.__tb_states = self.__host['de_alamos_fe2']['statusEntry']
        self.__tb_statedefs = self.__host['de_alamos_fe2']['statusDefinition']
        self.__tb_usermap = self.__host['de_alamos_fe2']['vehicleUserMapping']
        self.__tb_user = self.__host['de_alamos_fe2']['user']

        self.__tz_utc = pytz.timezone('Etc/UTC')

        self.__tp_last_run = int(datetime.now(self.__tz_utc).timestamp()*1000)

        self.__skip_state_c = False
        self.__skip_state_0 = False
        self.__skip_state_5 = False

    def reset_last_run(self):
        self.__tp_last_run = 0
    
    def get_state_c(self, switch:bool):
        self.__skip_state_c = not switch

    def get_state_0(self, switch:bool):
        self.__skip_state_0 = not switch

    def get_state_5(self, switch:bool):
        self.__skip_state_5 = not switch

    def __add_skip_list(self, base:dict):

        if self.__skip_state_c or self.__skip_state_0 or self.__skip_state_5:
            skip = []
            if self.__skip_state_c:
                log.info('Skip state c')
                skip.append({'$ne': 'STATUS_C'})
            if self.__skip_state_0:
                log.info('Skip state 1')
                skip.append({'$ne': 'STATUS_0'})
            if self.__skip_state_5:
                log.info('Skip state 5')
                skip.append({'$ne': 'STATUS_5'})

            if len(skip) == 1:
                base['status'] = skip[0] 
            else:
                base['$and'] = []
                for i in skip:
                    base['$and'].append({'status': i})
        return base
    
    def get_new(self):
        log.info('Get new entries')
        query = self.__add_skip_list({'timestamp' : {'$gt': self.__tp_last_run}})
        ret = self.__tb_states.find(query).sort({'timestamp': 1})
        self.__tp_last_run = int(datetime.now(self.__tz_utc).timestamp()*1000)
        log.info('Finished, update tp: %s' % self.__tp_last_run)
        return ret

    def get_previous_state(self, vid, timestamp):
        log.info('Get previous state for vid: %s' % vid)
        query = self.__add_skip_list({'vehicle_id': vid, 'timestamp' : {'$lt': timestamp}})
        ret = self.__tb_states.find(query).sort({'timestamp': -1}).limit(1)
        return ret[0]['status']

    def get_state_definition(self, state):
        log.info('Get definition for state: %s' % state)
        ret = self.__tb_statedefs.find({'_id' : {'$eq': state}})
        return ret[0]['translation']

    def get_vehicle_details(self, vid):
        log.info('Get vehicle information for vid: %s' % vid)
        ret = self.__tb_vehicle.find({'_id' : vid})
        return ret[0]
    
    def get_vehicle_orga_list(self, vid):
        ret = []
        log.info('Get orga list for vid: %s' % vid)
        uids = self.__tb_usermap.find({'vehicleId' : vid})

        for x in uids:
            uid = x['userId']
            uname = self.__tb_user.find({'_id' : uid})[0]['name']
            log.info('    + %s' % uname)
            ret.append(uname)

        return ret