#This library is for data retrieving
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json, csv
import pandas as pd
import logging as Log
import shutil
import configparser
import datetime
import os, sys

#configuration class ##

class config:
    def __init__(self, configFile):
        self.configFile = configFile
        self.cfgObj = None
        self.keyFile = None
        self.eventsCollectName = None
        self.silentNotifCollectName = None
        self.fdsnwsurl = None
        self.isocode3 = None
        self.countrylatlon = None
        self.datacentercode = None
        self.citiesFile = None
        self.logoFile = None
    def readConfig(self):
        #Read config.ini file
        try:
            self.cfgObj = configparser.ConfigParser()
            self.cfgObj.read(self.configFile)
        except Exception as e:
            Log.error("Not possible to instance the configuration object")
            Log.error(repr(e))
            return
        
        try:
            fbParam = self.cfgObj["firebase"]
            self.keyFile = fbParam["fbCredentials"]
            self.eventsCollectName = fbParam['dbCollectionEvents']
            self.silentNotifCollectName = fbParam['dbCollectionSilentNotif']
            fbParam = self.cfgObj["fdsnws"]
            self.fdsnwsurl = fbParam['fdsnwsurl']
            fbParam = self.cfgObj["country"]
            self.isocode3 = fbParam['isocode3']
            self.countrylatlon = fbParam['countryLatLon']
            fbParam = self.cfgObj["datacenter"]
            self.datacentercode = fbParam['code']
            self.logoFile = fbParam['logo']
            fbParam = self.cfgObj["files"]
            self.citiesFile = fbParam['cities']
        except:
            Log.error("error collecting the parameters!")
            
class datahandler:    
    def __init__(self, configObj):
        #self.fSilentNotif = configObj.silentNotifCollectName
        #self.fDelays = fileDelaysfile
        #self.fAlertsIntensity = fileAlertsAndIntensity
        self.keyFile = configObj.keyFile
        self.eventCollection = configObj.eventsCollectName
        self.silentNotifCollection = configObj.silentNotifCollectName
        self.cred = None
        self.db = None
        
    def initCredentials(self):
        self.cred = credentials.Certificate(self.keyFile)
        if not firebase_admin._apps:
            self.cred = credentials.Certificate(self.keyFile)
        
            firebase_admin.initialize_app(self.cred)
        
            #self.db = firestore.client()
        else:
            Log.error("Firebase is already instanced")
            
    def getDataFirebaseForEvents(self):
        #this method will read the data from firestore db
        #related to events. It will create two csv files
        #One of the will be about delays for delays for each event and their updates.
        #the other one is about the intensity reports.
        
        self.initCredentials()
        #Read Data - Values for locations
        try:
            self.db = firestore.client()
        except Exception as e:
            Log.error("db cannot be instanced. ERROR!")
            return
        result = self.db.collection(self.eventCollection).get()
        
        delaysdata = []
        alertsAndIntensity = []
        header_events_delays = ['userid', 'updateno', 'delay', 'eventid']
        header_alerts_intensity = ['updateno','alert', 'lat', 'lon', 'intensity','timestamp','userid','eventid']
        
        for event in result:
            evt = event.to_dict()
            for user in evt:
                updates = evt[user]
                for updateno in updates:
                    diffvalue = evt[user][updateno]["diff"]
                    tmpDic = {
                        "userid":user,
                        "updateno": updateno,
                        "delay": diffvalue,
                        "eventid": event.id
                    }
                    delaysdata.append(tmpDic)
                    
                    tmpDic = {
                        'updateno': updateno,
                        'alert': None,
                        "lat": None,
                        "lon": None,
                        "intensity": None,
                        "timestamp": None,
                        "userid": user,
                        "eventid": event.id
                    }
                    #checking if the alert binary is on the keys
                    if "alert" in evt[user][updateno].keys():
                            tmpDic['alert']=evt[user][updateno]["alert"] 
                    #checking if the lat value is in the key values.
                    #if it is there, then the other parameters are collected
                    if "lat" in evt[user][updateno].keys():
                            tmpDic['lat'] = evt[user][updateno]["lat"] 
                            tmpDic['lon'] = evt[user][updateno]["lon"] 
                            tmpDic['intensity'] = evt[user][updateno]["intensity"]     
                            tmpDic['timestamp'] = evt[user][updateno]["timestamp"]
                    alertsAndIntensity.append(tmpDic)
        
        
        strTmp = str(datetime.datetime.utcnow()).replace(" ","").replace("-","_")
        if len(delaysdata)>0:
            #making a backup of the last  delaysbyevent.csv
            try:
                newfilename = "data/delaybyevents.csv.backup"
                shutil.copyfile("data/delaybyevents.csv", newfilename)
            except Exception as e:
                Log.error("Not possible to do a copy of the file: delaybyevents.csv")
                Log.error(repr(e))
                pass
            with open('data/delaybyevents.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = header_events_delays)
                writer.writeheader()
                writer.writerows(delaysdata)
        
        if len(alertsAndIntensity )>0:
            #making a backup of the last  alertsAndIntensity.csv
            try:
                newfilename = "data/alertsAndIntensity.csv.backup"
                shutil.copyfile("data/alertsAndIntensity.csv", newfilename)
            except Exception as e:
                Log.error("Not possible to do a copy of the file: alertsAndIntensity.csv")
                Log.error(repr(e))
                pass
            with open('data/alertsAndIntensity.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = header_alerts_intensity)
                writer.writeheader()
                writer.writerows(alertsAndIntensity)

    def getDataFirebaseForSilentNotif(self):
        #this method will get the data from silentnotification db  in firestore DB.
        #logging in
        self.initCredentials()
        try:
            self.db = firestore.client()
        except Exception as e:
            Log.error("db cannot be instanced. ERROR!")
            return
        #Read Data - Values for locations 
        result = self.db.collection(self.silentNotifCollection).get()
        
        allSilentData = []
        header_alerts_intensity = ['notifid',\
                                'userid', \
                                'userLat', \
                                'userLon', \
                                'userLocTime',\
                                'timesource',\
                                'senttime',\
                                'delay'
                                ]
        
        
        for notification in result:
            notif = notification.to_dict()
            for user in notif:
                if "timesource" not in notif[user].keys():
                    continue
                tmpDic = {
                        'notifid': notification.id,
                        'userid': user,
                        'userLat': None,
                        'userLon': None,
                        'userLocTime': None,
                        'timesource': notif[user]["timesource"],
                        'senttime': notif[user]["senttime"],
                    'delay': notif[user]["diff"]
                }
                if "userLat" and "userLon" in notif[user].keys():
                    tmpDic["userLat"] = notif[user]["userLat"]
                    tmpDic["userLon"] = notif[user]["userLon"]
                    tmpDic["userLocTime"] = notif[user]["userLocTime"]
                
                allSilentData.append(tmpDic)
                
                
        strTmp = str(datetime.datetime.utcnow()).replace(" ","").replace("-","_")
        if len(allSilentData)>0:
            #making a backup of the last  delaysbyevent.csv
            try:
                newfilename = "data/silentnotifdata.csv.backup"
                shutil.copyfile("data/silentnotifdata.csv", newfilename)
            except Exception as e:
                Log.error("Not possible to do a copy of the file: silentnotifdata.csv")
                Log.error(repr(e))
                pass
            #os.system("copy silentnotifdata.csv silentnotifdata.csv."+strTmp)
            with open('data/silentnotifdata.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = header_alerts_intensity)
                writer.writeheader()
                writer.writerows(allSilentData)

    def getDfDelaysEvents(self):
        df=pd.DataFrame()
        try:
            df = pd.read_csv('data/delaybyevents.csv')
        except:
            pass
        return df
    
    def getDfIntensityAlerts(self):
        df=pd.DataFrame()
        try:
            df = pd.read_csv('data/alertsAndIntensity.csv')
        except:
            pass
        return df
    
    def getDfSilentNotif(self):
        df=pd.DataFrame()
        try:
            df = pd.read_csv('data/silentnotifdata.csv')
        except Exception as e:
            Log.error("not possible to read file data/silentnotifdata.csv")
            Log.error(repr(e))
            pass
        return df
