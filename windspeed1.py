# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 18:05:41 2019

@author: Miska
"""
import os
import urllib.request
import requests
from datetime import datetime, timezone, timedelta
from dateutil import tz









supported_cities = {'Jyvaskyla': {'ilmatiet_place_url' : 'Jyv%C3%A4skyl%C3%A4', # Required
                                  'ilmatiet_actual_location': 'jkl lentoasema', # Required
                                  'weatherlink_url' : 'https://www.weatherlink.com/embeddablePage/summaryData/e4425b28ee934e28a5078100f2355ae1?', # Optional
                                  'weatherlink_actual_location': 'Juurikkasaaren weatherlink', # Optional
                                  'telegram_chat_id' : '-394429178', # Required
                                  'wind_speed_limit' : 4.5},# Required

                    'CityX' : {'ilmatiet_place_url' : None,
                             'ilmatiet_actual_location': None,
                             'weatherlink_url' : None,
                             'weatherlink_actual_location': None,
                             'telegram_chat_id': None,
                             'wind_speed_limit' : None}}







def telegram_bot_sendtext(bot_message, chat_id):
    bot_token = os.getenv('bot_token')
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=Markdown&text=' + bot_message
    print('Sending message: {}'.format(bot_message))
    requests.get(send_text)
    return

def get_latest_value_weatherlink(query_url):

    infp = urllib.request.urlopen(query_url)
    html = infp.read()
    a = str(html)
    
    query_str = '"sensorDataName":"Wind Speed","displayName":null,"value":'
    ind_start = a.find(query_str)
    ind_str = a[(ind_start+len(query_str)):(ind_start+len(query_str)+4)]
    wind_current_str = ind_str.replace(",","")
    
    query_str = '"sensorDataName":"2 Min Avg Wind Speed","displayName":null,"value":'
    ind_start = a.find(query_str)
    ind_str = a[(ind_start+len(query_str)):(ind_start+len(query_str)+4)]
    wind_2minavg_str = ind_str.replace(",","")
    
    query_str = '"sensorDataName":"10 Min Avg Wind Speed","displayName":null,"value":'
    ind_start = a.find(query_str)
    ind_str = a[(ind_start+len(query_str)):(ind_start+len(query_str)+4)]
    wind_10minavg_str = ind_str.replace(",","")
    
    query_str  = '"sensorDataName":"10 Min High Wind Speed","displayName":null,"value":'
    ind_start = a.find(query_str)
    ind_str = a[(ind_start+len(query_str)):(ind_start+len(query_str)+4)]
    wind_10minmax_str = ind_str.replace(",","")
    
    query_str = '"sensorDataName":"Wind Direction","displayName":null,"value":'
    ind_start = a.find(query_str)
    ind_str = a[(ind_start+len(query_str)):(ind_start+len(query_str)+4)]
    wind_dir_str = ind_str.replace(",","")
    
    query_str = '"ownerName":null,"lastReceived":'
    ind_start = a.find(query_str)
    ind_str = a[(ind_start+len(query_str)):(ind_start+len(query_str)+13)]
    time = ind_str.replace(",","")
    timestamp = int(time)
    measurement_time = datetime.fromtimestamp(timestamp/1000)
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Helsinki')
    utc = measurement_time.replace(tzinfo=from_zone)  
    # Convert time zone
    central = utc.astimezone(to_zone)
    local_time = datetime.strftime(central, '%Y-%m-%d %H:%M:%S')
    
    values = {'speed_cur' : wind_current_str, 'speed_2minavg':wind_2minavg_str, 'speed_10minavg':wind_10minavg_str, 'speed_10minmax':wind_10minmax_str,'dir':wind_dir_str}
    
    return values, local_time

def get_spot(wind_dir, city):
    
    location = False
    
    if city == 'Jyväskylä':
        if  250<wind_dir<290:
            location = 'verkkoniemi'
        if 300<wind_dir<315:
            location = 'pumppaamo'   
        if 0<wind_dir<50:
            location = 'saykki'   
        if 145<wind_dir<180:
            location = 'haikka' 
        
    if not location:
        spot = 'Mutta mikä spotti??' 
    if location:
        spot = 'Toimisko {}?'.format(location)
    return spot


def get_latest_value_ilmatiet(city_query_url):
    starttime = (datetime.now(timezone.utc)-timedelta(hours=0.2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = ['wd_10min', 'wg_10min','ws_10min']
    values = {}
    for param in params:
        query_url = 'http://opendata.fmi.fi/wfs/fin?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::timevaluepair&starttime={}&place=Jyv%C3%A4skyl%C3%A4&parameters={}'.format(starttime,param)
        infp = urllib.request.urlopen(query_url)
        html = infp.read()
        a = str(html)
        b = a[::-1]
        latest_value_ind = b.find('eulav')
        latest_time_ind = b.find('>emit:')
        latest_value_str = b[(latest_value_ind+12):latest_value_ind+17]
        latest_time_str = b[(latest_time_ind+12):latest_time_ind+32]
        is_long_value = latest_value_str.find('>')
        is_long_time = latest_time_str.find('>')
        if is_long_value != -1:
            latest_value_str = latest_value_str[:is_long_value]
        if is_long_time != -1:
            latest_time_str = latest_time_str[:is_long_time]
        latest_value = latest_value_str[::-1]
        measurement_time = latest_time_str[::-1]
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Helsinki')
        measurement_time = measurement_time.replace('Z','')
        measurement_time = measurement_time.replace('T',' ')
        utc = datetime.strptime(measurement_time, '%Y-%m-%d %H:%M:%S')
        utc = utc.replace(tzinfo=from_zone)  
        # Convert time zone
        central = utc.astimezone(to_zone)
        local_time = datetime.strftime(central, '%Y-%m-%d %H:%M:%S')
        values[param] = {'value':latest_value, 'time':local_time}
        
    return values, local_time

def lambda_handler(event, context):
 
    for city in supported_cities:
        city_query_url = supported_cities[city]['ilmatiet_place_url']
        if city_query_url:
            latest_value, latest_time_ilmat = get_latest_value_ilmatiet(city_query_url)
            wind_speed_alarm_limit = supported_cities[city]['wind_speed_limit']
            chat_id = supported_cities[city]['telegram_chat_id']
            if float(latest_value['ws_10min']['value'])>wind_speed_alarm_limit:
                utc = datetime.strptime(latest_value['ws_10min']['time'], '%Y-%m-%d %H:%M:%S')
                if 8 < utc.hour < 20:
                    alarm = True
                    wind_speed = (latest_value['ws_10min']['value'])
                    wind_gust = (latest_value['wg_10min']['value'])
                    wind_dir = (latest_value['wd_10min']['value'])
                    spot = get_spot(float(wind_dir),city)
            else:
                wind_speed = (latest_value['ws_10min']['value'])
                alarm = False   
                
            query_url = supported_cities[city]['weatherlink_url']
            values, latest_time_weatherlink = get_latest_value_weatherlink(query_url)
            
            if query_url:
                if alarm:
                    message = """Nyt tuulee {}
                    
                                *{}*
                                Mitattu: {}
                                Tuulennopeus (10min ka): {} m/s
                                Tuulennopeus (10min max): {} m/s
                                Tuulensuunta: {}
                                
                                *{}*
                                Mitattu: {}
                                Tuulennopeus (nykyhetki): {} m/s
                                Tuulennopeus (10min ka): {} m/s
                                Tuulennopeus (10min max): {} m/s
                                Tuulennopeus (2min ka): {} m/s
                                Tuulensuunta: {}
                                
                                *{}*
                    """.format(city,supported_cities[city]['ilmatiet_actual_location'],latest_time_ilmat,wind_speed,wind_gust,wind_dir,supported_cities[city]['weatherlink_actual_location'], latest_time_weatherlink, values['speed_cur'],values['speed_10minavg'],values['speed_10minmax'],values['speed_2minavg'],values['dir'],spot)
                    telegram_bot_sendtext(message, chat_id)
                else:
                    print('Not windy enough: {}'.format(wind_speed))
            else:
                if alarm:
                    message = """Nyt tuulee {}
                    
                                *{}*
                                Mitattu: {}
                                Tuulennopeus (10min ka): {} m/s
                                Tuulennopeus (10min max): {} m/s
                                Tuulensuunta: {}
                                
                                *{}*
                    """.format(city,latest_time_ilmat,wind_speed,wind_gust,wind_dir,spot)
                    telegram_bot_sendtext(message, chat_id)
                else:
                    print('Not windy enough: {}'.format(wind_speed))
        else:
            print('No url to query data from for city {}'.format(city))

    return