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

        self.__ep = ep.fe2_external_interface(sender, fe2_url, fe2_sec)
        self.__ep_rb = ep.roadblock(self.__ep)

        self.__ep_units_en = False
        self.__ep_std_units = None
        self.__ep_orga_units = None

        self.__rb_hour_offset = 0

    def add_units(self, units:dict):
            self.__ep_units_en = True
            self.__ep_orga_units = units

    def get_server_version(self):
        return self.__db.get_app_version()

    def run_check(self):
        ret = self.__ep.check_connection()
        if ret['status']:
            log.critical("Fe2 offline:", ret['msg'])
        else:
            log.warning("Fe2 online")

    def run_rb_new(self):
        log.info("Check for new/modified roadblocks...")
        ret = self.__db_rb.get_new()
        
        log.info("Walk through resoults...")
        for x in ret:

            if self.__ep_units_en:
                unit = self.__ep_orga_units.get(x.get('parent'), None)
                if unit == None:
                    log.error('No unit found. Skipping for %s' % unit)
                    return
                
                log.info('Use unit for %s' % x.get('parent'))
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
            
            subject = '\U0001F6A7 ' + x.get('name')

            message = list((
                '-- Verkehrsbehinderung --',
                'Status: ' + ('Aktiv' if status == 'ACTIVE' else 'Geplant'),
                'Stand: ' + ('Neu' if state == 'NEW' else 'Aktualisiert'),
                x.get('street',''),
                start + ' bis ' + end,
            ))
            if x.get('reason', '') != '':
                message.append('Grund: ' + x.get('reason'))
            if x.get('note', '') != '':
                message.append('Hinweis: ' + x.get('note'))

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

            self.__ep_rb.send(unit, state, x.get('type'), status, x.get('parent'), x.get('name'), x.get('city',''), x.get('street',''), start, end, center, subject, message)

        log.info("Run finished...")
        

    def run_rb_upcoming(self):
        log.info("Check for upcoming roadblocks...")
        ret = self.__db_rb.get_upcoming(self.__rb_hour_offset)
        
        log.info("Walk through resoults...")
        for x in ret:

            if self.__ep_units_en:
                unit = self.__ep_orga_units.get(x.get('parent'), None)
                if unit == None:
                    log.error('No unit found. Skipping for %s' % unit)
                    return
                
                log.info('Use unit for %s' % x.get('parent'))
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

            subject = '\U0001F6A7 ' + x.get('name')

            message = list((
                '-- Verkehrsbehinderung --',
                'Status: ' + ('Ist jetzt aktiv' if status == 'ACTIVE' else 'Wird heute eingerichtet'),
                x.get('street',''),
                start + ' bis ' + end,
            ))
            if x.get('reason', '') != '':
                message.append('Grund: ' + x.get('reason'))
            if x.get('note', '') != '':
                message.append('Hinweis: ' + x.get('note'))

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
            
            self.__ep_rb.send(unit, state, x.get('type'), status, x.get('parent'), x.get('name'), x.get('city',''), x.get('street',''), start, end, center, subject, message)

        log.info("Run finished...")


    def run_rb_expiring(self):
        log.info("Check for expiring roadblocks...")
        ret = self.__db_rb.get_expiring(self.__rb_hour_offset)
        
        log.info("Walk through resoults...")
        for x in ret:

            if self.__ep_units_en:
                unit = self.__ep_orga_units.get(x.get('parent'), None)
                if unit == None:
                    log.error('No unit found. Skipping for %s' % unit)
                    return
                
                log.info('Use unit for %s' % x.get('parent'))
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

            subject = '\U0001F6A7 ' + x.get('name')

            message = list((
                '-- Verkehrsbehinderung --',
                'Status: ' + ('Läuft heute aus' if status == 'ACTIVE' else 'Aufgehoben'),
                x.get('street',''),
                start + ' bis ' + end,
            ))
            if x.get('reason', '') != '':
                message.append('Grund: ' + x.get('reason'))
            if x.get('note', '') != '':
                message.append('Hinweis: ' + x.get('note'))

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

            self.__ep_rb.send(unit, state, x.get('type'), status, x.get('parent'), x.get('name'), x.get('city',''), x.get('street',''), start, end, center, subject, message)

        log.info("Run finished...")