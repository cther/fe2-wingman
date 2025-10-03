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

import math

"""
Latitude (X-Achse)
Longitude (Y-Achse)
"""
GL_CORD_LAT_INDEX=0
GL_CORD_LNG_INDEX=1


class track:
    def __init__(self, points:list):
        self.__sectors = list()
        self.__midle = [0.0, 0.0]
        self.__length = 0.0

        if len(points) == 0:
            self.__midle = None
            return
        
        if len(points) == 1:
            self.__midle = points[0]
            return
        
        for point in points[:-1]:
            vector = [ points[points.index(point)+1][GL_CORD_LAT_INDEX] - point[GL_CORD_LAT_INDEX], points[points.index(point)+1][GL_CORD_LNG_INDEX] - point[GL_CORD_LNG_INDEX] ]
            length = math.sqrt(vector[0]**2 + vector[1]**2)

            self.__sectors.append(dict(point = [point[GL_CORD_LAT_INDEX], point[GL_CORD_LNG_INDEX]], vector = vector, length = length))
            self.__length += length
        
        #print(self.__sectors)

        half_length = self.__length / 2.0
        for sector in self.__sectors:
            if half_length > sector['length']:
                half_length -= sector['length']
            else:
                magnitude = half_length / sector['length']
                
                self.__midle[GL_CORD_LAT_INDEX] = sector['point'][GL_CORD_LAT_INDEX] + sector['vector'][GL_CORD_LAT_INDEX] * magnitude
                self.__midle[GL_CORD_LNG_INDEX] = sector['point'][GL_CORD_LNG_INDEX] + sector['vector'][GL_CORD_LNG_INDEX] * magnitude

                break

    def get_length(self):
        return self.__length

    def get_midle(self):
        return self.__midle