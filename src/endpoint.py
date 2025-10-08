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

import json
import datetime
import requests

from loggsys import log


class fe2_external_interface:
    def __init__(self, sender, url, secret):
        self.__url = url
        self.__secret = secret
        self.__sender = sender
    
    def check_connection(self):
        api = self.__url + '/rest/status'
        header = {'Content-type': 'application/json'}

        ret =json.loads(requests.get(api, None, headers=header).text)
        
        if ret['fe2'] == 'OK' and ret['gae'] == 'OK':
            return {'status': False}
        else:
            return {'status': True, 'msg': 'No response'}
    
    def send_alarm(self, data:dict):
        return self.__send('ALARM', self.__url + '/rest/external/http/alarm/v2', data)

    def send_status(self):
        pass

    def send_position(self):
        pass

    def send_diary(self):
        pass

    def __send(self, type, api, data):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + "+00:00"

        header = {'Content-type': 'application/json'}
        package = {
            "type": type,
            "timestamp": timestamp,
            "sender": self.__sender,
            "authorization": self.__secret,
            "data": data
        }

        return json.loads(requests.post(api, data=json.dumps(package), headers=header).text)


class roadblock:
    def __init__(self, fe2_ext_iface):
        self.__fe2_ext_iface = fe2_ext_iface

    def send(self, unit, state, type, status, orga, name, city, street, start, end, coordinate:list, icon, message:list):
        location = {}
        payload = {}
        
        payload["keyword"] = icon + ' ' + name

        if coordinate != None:
            location['coordinate'] = [
                    coordinate[0],
                    coordinate[1]
                ]
        location['city'] = city
        location['street'] = street

        if message != None:
            payload["message"] = message

        payload["location"] = location

        if unit != None:
            payload["units"] = [
                dict(
                    address = unit
                ),
            ]

        payload["custom"]  = {
            'wm_function': 'roadblock',
            'wm_rb_name': name,
            'wm_rb_state': state,
            'wm_rb_type': type,
            'wm_rb_status': status,
            'wm_rb_orga': orga,
            'wm_rb_start': start,
            'wm_rb_end': end,
            'wm_rb_icon': icon
        }

        log.info('Send roadblock.data to Fe2: %s' % payload)
        log.warning('roadblock.send: %s' % self.__fe2_ext_iface.send_alarm(payload))
        
        
class vehiclestate:
    def __init__(self, fe2_ext_iface):
        self.__fe2_ext_iface = fe2_ext_iface
        
    def send(self, units:list, address, name, shortname, source, orga, state, prestate, icon, definition, message):
        payload = {}

        payload["keyword"] = icon + ' ' + definition

        if message != None:
            payload["message"] = [message]

        if units != None:
            payload["units"] = []
            for i in units:
                payload["units"].append({'address' : i})

        payload["custom"]  = {
            'wm_function': 'vehiclestate',
            'wm_vs_address': address,
            'wm_vs_name': name,
            'wm_vs_short_name': shortname,
            'wm_vs_source': source,
            'wm_vs_orga': orga,
            'wm_vs_state_from': prestate,
            'wm_vs_state_to': state,
            'wm_vs_icon': icon,
            'wm_vs_definition': definition
        }

        log.info('Send vehiclestate to Fe2: %s' % payload)
        log.warning('vehiclestate.send: %s' % self.__fe2_ext_iface.send_alarm(payload))