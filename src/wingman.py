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

import database as db
import endpoint as ep
import coordinates as coord

from loggsys import log


class wingman:
    def __init__(self, sender, db_url, fe2_url, fe2_sec):
        self.__db = db.mongodb(db_url)
        self.__db_rb = db.roadblock(self.__db)
        self.__db_vs = db.vehiclestate(self.__db)

        self.__ep = ep.fe2_external_interface(sender, fe2_url, fe2_sec)
        self.__ep_rb = ep.roadblock(self.__ep)
        self.__ep_vs = ep.vehiclestate(self.__ep)

        self.__ep_units_en = False
        self.__ep_std_units = None
        self.__ep_orga_units = None

        self.__rb_hour_offset = 0

        self.__state_lut = {
            'STATUS_0' : {'num':'0', 'icon':'\U00000030\U0000FE0F\U000020E3'},
            'STATUS_1' : {'num':'1', 'icon':'\U00000031\U0000FE0F\U000020E3'},
            'STATUS_2' : {'num':'2', 'icon':'\U00000032\U0000FE0F\U000020E3'},
            'STATUS_3' : {'num':'3', 'icon':'\U00000033\U0000FE0F\U000020E3'},
            'STATUS_4' : {'num':'4', 'icon':'\U00000034\U0000FE0F\U000020E3'},
            'STATUS_5' : {'num':'5', 'icon':'\U00000035\U0000FE0F\U000020E3'},
            'STATUS_6' : {'num':'6', 'icon':'\U00000036\U0000FE0F\U000020E3'},
            'STATUS_7' : {'num':'7', 'icon':'\U00000037\U0000FE0F\U000020E3'},
            'STATUS_8' : {'num':'8', 'icon':'\U00000038\U0000FE0F\U000020E3'},
            'STATUS_9' : {'num':'9', 'icon':'\U00000039\U0000FE0F\U000020E3'},
            'STATUS_A' : {'num':'A', 'icon':'\U000026AA'},
            'STATUS_C' : {'num':'C', 'icon':'\U0001F534'},
            'STATUS_E' : {'num':'E', 'icon':'\U000026AB'},
            'STATUS_F' : {'num':'F', 'icon':'\U0001F535'},
            'STATUS_H' : {'num':'H', 'icon':'\U0001F7E1'},
            'STATUS_J' : {'num':'J', 'icon':'\U0000260E'},
        }

        self.run_check()
        
    def add_units(self, units:dict):
        self.__ep_units_en = True
        self.__ep_orga_units = units

    def get_state_c(self, switch=True):
        self.__db_vs.get_state_c(switch)

    def get_state_0(self, switch=True):
        self.__db_vs.get_state_0(switch)

    def get_state_5(self, switch=True):
        self.__db_vs.get_state_5(switch)

    def get_server_version(self):
        return self.__db.get_app_version()

    def run_check(self):
        try:
            ret = self.__ep.check_connection()
        except Exception as error:
            log.critical("Fe2 server connection error! %s" % error)
            exit()
        else:
            if ret['status']:
                log.critical("Fe2 offline: %s" % ret['msg'])
            else:
                log.info("Fe2 online")


    def run_rb_new(self):
        log.info("Check for new/modified roadblocks...")
        ret = self.__db_rb.get_new()
        
        log.info("Walk through resoults...")
        for x in ret:

            if self.__ep_units_en:
                unit = self.__ep_orga_units.get(x['parent'], None)
                if unit == None:
                    log.error('No unit found. Skipping for %s' % x['parent'])
                    return
                
                log.info('Use unit for %s' % x['parent'])
            else:
                unit = None
                log.info('Support for units disabeled')

            start = self.__db_rb.conv_tp(x['from']).strftime('%d.%m.%Y %H:%M')
            end = self.__db_rb.conv_tp(x['to']).strftime('%d.%m.%Y %H:%M')

            if x['creationTime'] == ['lastChanged'] or x['creationTime'] > self.__db_rb.get_last_run():
                state = 'NEW'
            else:
                state = 'UPDATE'

            if self.__db_rb.tp_lt_now(self.__db_rb.conv_tp(x['from'])):
                status = 'ACTIVE'
            else:
                status = 'PENDING'
            
            icon = '\U0001F6A7'

            message = list((
                '-- Verkehrsbehinderung --',
                'Status: ' + ('Aktiv' if status == 'ACTIVE' else 'Geplant'),
                'Stand: ' + ('Neu' if state == 'NEW' else 'Aktualisiert'),
                x.get('street',''),
                start + ' bis ' + end,
            ))
            if x.get('reason', '') != '':
                message.append('Grund: ' + x['reason'])
            if x.get('note', '') != '':
                message.append('Hinweis: ' + x['note'])

            log.warning('new/updated: %s' % message)

            log.info("Get:")
            log.info('+  State:  %s' % state)
            log.info('+  Orga:   %s' % x.get('parent'), '( id:', unit, ')' )
            log.info('+  Name:   %s' % x.get('name'))
            log.info('+  Reason: %s' % x.get('reason', ''))
            log.info('+  Note:   %s' % x.get('note', ''))
            log.info('+  Street: %s' % x.get('street', ''))
            log.info('+  City:   %s' % x.get('city', ''))
            log.info('+  Type:   %s' % x.get('type'))
            log.info('+  Status: %s' % status)
            log.info('+  From:   %s' % start)
            log.info('+  To:     %s' % end)
            
            center = None
            if 'jsonGeometry' in x:
                if x['jsonGeometry']['type'] == 'Point':
                    center = x['jsonGeometry']['coordinates']
                    log.info('+  Center: %s' % center)
                if x['jsonGeometry']['type'] == 'LineString':
                    t = coord.track(x['jsonGeometry']['coordinates'])
                    center = t.get_midle()
                    log.info('+  Center: %s' % center)

            self.__ep_rb.send(unit, state, x.get('type'), status, x.get('parent'), x.get('name'), x.get('city',''), x.get('street',''), start, end, center, icon, message)

        log.info("Run finished...")
        

    def run_rb_upcoming(self):
        log.info("Check for upcoming roadblocks...")
        ret = self.__db_rb.get_upcoming(self.__rb_hour_offset)
        
        log.info("Walk through resoults...")
        for x in ret:

            if self.__ep_units_en:
                unit = self.__ep_orga_units.get(x['parent'], None)
                if unit == None:
                    log.error('No unit found. Skipping for %s' % x['parent'])
                    return
                
                log.info('Use unit for %s' % x['parent'])
            else:
                unit = None
                log.info('Support for units disabeled')

            start = self.__db_rb.conv_tp(x['from']).strftime('%d.%m.%Y %H:%M')
            end = self.__db_rb.conv_tp(x['to']).strftime('%d.%m.%Y %H:%M')
            
            state = 'STEADY'

            if self.__db_rb.tp_lt_now(self.__db_rb.conv_tp(x['from'])):
                status = 'ACTIVE'
            else:
                status = 'PENDING'

            icon = '\U0001F6A7'

            message = list((
                '-- Verkehrsbehinderung --',
                'Status: ' + ('Ist jetzt aktiv' if status == 'ACTIVE' else 'Wird heute eingerichtet'),
                x.get('street',''),
                start + ' bis ' + end,
            ))
            if x.get('reason', '') != '':
                message.append('Grund: ' + x['reason'])
            if x.get('note', '') != '':
                message.append('Hinweis: ' + x['note'])

            log.warning('upcoming: %s' % message)

            log.info("Get:")
            log.info('+  State:  %s' % state)
            log.info('+  Orga:   %s' % x.get('parent'), '( id:', unit, ')' )
            log.info('+  Name:   %s' % x.get('name'))
            log.info('+  Reason: %s' % x.get('reason', ''))
            log.info('+  Note:   %s' % x.get('note', ''))
            log.info('+  Street: %s' % x.get('street', ''))
            log.info('+  City:   %s' % x.get('city', ''))
            log.info('+  Type:   %s' % x.get('type'))
            log.info('+  Status: %s' % status)
            log.info('+  From:   %s' % start)
            log.info('+  To:     %s' % end)
            
            center = None
            if 'jsonGeometry' in x:
                if x['jsonGeometry']['type'] == 'Point':
                    center = x['jsonGeometry']['coordinates']
                    log.info('+  Center: %s' % center)
                if x['jsonGeometry']['type'] == 'LineString':
                    t = coord.track(x['jsonGeometry']['coordinates'])
                    center = t.get_midle()
                    log.info('+  Center: %s' % center)
            
            self.__ep_rb.send(unit, state, x.get('type'), status, x.get('parent'), x.get('name'), x.get('city',''), x.get('street',''), start, end, center, icon, message)

        log.info("Run finished...")


    def run_rb_expiring(self):
        log.info("Check for expiring roadblocks...")
        ret = self.__db_rb.get_expiring(self.__rb_hour_offset)
        
        log.info("Walk through resoults...")
        for x in ret:

            if self.__ep_units_en:
                unit = self.__ep_orga_units.get(x['parent'], None)
                if unit == None:
                    log.error('No unit found. Skipping for %s' % x['parent'])
                    return
                
                log.info('Use unit for %s' % x['parent'])
            else:
                unit = None
                log.info('Support for units disabeled')

            start = self.__db_rb.conv_tp(x['from']).strftime('%d.%m.%Y %H:%M')
            end = self.__db_rb.conv_tp(x['to']).strftime('%d.%m.%Y %H:%M')
            
            state = 'STEADY'

            if self.__db_rb.tp_lt_now(self.__db_rb.conv_tp(x['to'])):

                status = 'EXPIRED'
            else:
                status = 'ACTIVE'

            icon = '\U0001F6A7'

            message = list((
                '-- Verkehrsbehinderung --',
                'Status: ' + ('Läuft heute aus' if status == 'ACTIVE' else 'Aufgehoben'),
                x.get('street',''),
                start + ' bis ' + end,
            ))
            if x.get('reason', '') != '':
                message.append('Grund: ' + x['reason'])
            if x.get('note', '') != '':
                message.append('Hinweis: ' + x['note'])

            log.warning('expiring: %s' % message)

            log.info("Get:")
            log.info('+  State:  %s' % state)
            log.info('+  Orga:   %s' % x.get('parent'), '( id:', unit, ')' )
            log.info('+  Name:   %s' % x.get('name'))
            log.info('+  Reason: %s' % x.get('reason', ''))
            log.info('+  Note:   %s' % x.get('note', ''))
            log.info('+  Street: %s' % x.get('street', ''))
            log.info('+  City:   %s' % x.get('city', ''))
            log.info('+  Type:   %s' % x.get('type'))
            log.info('+  Status: %s' % status)
            log.info('+  From:   %s' % start)
            log.info('+  To:     %s' % end)
            
            center = None
            if 'jsonGeometry' in x:
                if x['jsonGeometry']['type'] == 'Point':
                    center = x['jsonGeometry']['coordinates']
                    log.info('+  Center: %s' % center)
                if x['jsonGeometry']['type'] == 'LineString':
                    t = coord.track(x['jsonGeometry']['coordinates'])
                    center = t.get_midle()
                    log.info('+  Center: %s' % center)

            self.__ep_rb.send(unit, state, x.get('type'), status, x.get('parent'), x.get('name'), x.get('city',''), x.get('street',''), start, end, center, icon, message)

        log.info("Run finished...")
    

    def run_vs_new(self):
        log.info("Check for new vehicle states...")
        ret = self.__db_vs.get_new()

        log.info("Walk through resoults...")
        for x in ret:
            icon = self.__state_lut[x['status']]['icon']
            definition = self.__db_vs.get_state_definition(x['status'])

            state = self.__state_lut[x['status']]['num']
            prestate = self.__state_lut[self.__db_vs.get_previous_state(x['vehicle_id'], x['timestamp'])]['num']

            vehicle = self.__db_vs.get_vehicle_details(x['vehicle_id'])
            orga = self.__db_vs.get_vehicle_orga_list(x['vehicle_id'])

            message = 'Statuswechsel %s. Aktueller Status %s (Vorher: %s)' % (vehicle['name'], state, prestate)

            log.warning('state: %s' % message)

            if self.__ep_units_en:
                units = []
                for i in orga:
                    unit = self.__ep_orga_units.get(i, None)
                    if unit == None:
                        log.warning('No id found for unit \'%s\'. Skipping...' % i)
                        continue
                    
                    log.info('Use unit for %s' % i)
                    units.append(unit)
                
                if len(units) == 0:
                    units = None
            else:
                units = None
                log.info('Support for units disabeled')
            
            orga = ','.join(map(str, orga))

            log.info("Get:")
            log.info('+  Address:     %s' % vehicle['code'])
            log.info('+  Name:        %s' % vehicle['name'])
            log.info('+  ShortName:   %s' % vehicle['shortName'])
            log.info('+  Orga:        %s' % orga)
            log.info('+  Icon:        %s' % icon)
            log.info('+  Definition:  %s' % definition)
            log.info('+  Status:      %s' % state)
            log.info('+  PreState:    %s' % prestate)

            self.__ep_vs.send(units, vehicle['code'], vehicle['name'], vehicle['shortName'], orga, state, prestate, icon, definition, message)

        log.info("Run finished...")