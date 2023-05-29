import pandas as pd
import logging as Log

class ReadFDSNWS:
    def __init__(self,fdsnwsURL):
        self.fdsnwsURL = fdsnwsURL
		
    def getEventInfoByID(self, eventid):
        request = self.fdsnwsURL+"/fdsnws/event/1/query?format=csv&formatted=true&eventid="+eventid
        print("requesting to: "+request)
        df =  pd.DataFrame()
        try:
            df = pd.read_csv(request)
        except Exception as e:
            Log.error("No data or an error. See below:")
            Log.error(repr(e))
            return df
        return df
	
	
	#df.loc[df['eventid'].str.contains("ineter")].sort_values(by='eventid', ascending=False)['eventid'].unique()[1]
    def getLastEventOnFDSN(self):
        #limiting the last 
        request = self.fdsnwsURL+"/fdsnws/event/1/query?limit=1&format=csv&formatted=true"
        df = pd.DataFrame()
        try:
            df = pd.read_csv(request)
        except Exception as e:
            Log.error("No data or an error. See below:")
            Log.error(repr(e))
            return df
        return df
