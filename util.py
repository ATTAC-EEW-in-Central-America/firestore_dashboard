#utilitary lib
import os, sys
import math
import csv

language = 'es-US'
def intToRoman(intVal):

    numbers = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    letters = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]

    if intVal < 1 or intVal > 3999 :
        return str(intVal)
    
    roman = ""
    for i in range(0,len(numbers),1):#(int i = 0; i < numbers.length; i++) {
        while intVal >= numbers[i]:
            roman += letters[i];
            intVal -= numbers[i];
        
    return roman

def intToColorDescription(intVal):
    
    if intVal >12 or intVal<0:
        intVal = -1
    colorDict = {
        -1: "--;#FFFFFF",
        0: "--;#D3D3D3",
        1: "I. No Sentido;#FFFFFF",
        2: "II. Muy Débil;#BFCCFF",
        3: "III. Leve;#9999FF",
        4: "IV. Moderado;#80FFFF",
        5: "V. Poco Fuerte;#7DF894",
        6: "VI. Fuerte;#FFFF00",
        7: "VII. Muy Fuerte;#FFC800",
        8: "VIII. Destructivo;#FF9100",
        9: "IX. Muy Destructivo;#FF0000",
        10: "X. Desastroso;#C80000",
        11: "XI. Muy Desastroso;#800000",
        12: "XII. Catastrófico;#000000"
    }
    
    return colorDict[intVal]

def ipe_allen2012_hyp(epiDistance, magnitude, depth):#hypoDistance km
    a = 2.085;
    b = 1.428;
    c = -1.402;
    d = 0.078;
    s = 1.0;
    m1=-0.209;
    m2=2.042;

    if depth<0 : 
        return -1
        

    #Obtaining the hypocentral distance
    #The form is a triangle - Can be improved(?)
    hypoDistance = math.sqrt(math.pow(epiDistance,2)+math.pow(depth,2))

    rm = m1+m2 * math.exp(magnitude-5)
    
    if hypoDistance <= 50 :
        I = a + b*magnitude + c* math.log( math.sqrt( math.pow(hypoDistance,2) + math.pow(rm,2)))+s    
    else:
        I = a + b*magnitude + c * math.log( math.sqrt( math.pow(hypoDistance,2) + math.pow(rm,2)))+d* math.log(hypoDistance/50)+s
    
    if hypoDistance <= 50 :
        I2 = a + b*magnitude + c * math.log( math.sqrt( math.pow(hypoDistance,2) + math.pow(rm,2)))+d* math.log(hypoDistance/50)+s
    else:
        I2 = a + b*magnitude + c* math.log( math.sqrt( math.pow(hypoDistance,2) + math.pow(rm,2)))+s    
        

    intensity = round(I) # intensity (MMI, float)
    intensity2 = round(I2) # intensity (MMI, float)
    #print("Values: ",I, I2,intensity, intensity2, depth, magnitude,hypoDistance, epiDistance)
    if intensity>12:
        return 12
    elif intensity<0:
        return 0
    else:
        return I

def ipe_allen2012_hyp_sigma(epiDistance, depth):
    #Constants
    s1 = 0.82
    s2 = 0.37
    s3 = 22.9
    hypoDistance = math.sqrt(math.pow(epiDistance,2)+math.pow(depth,2))
    
    sigma = s1 + s2/(1 + math.pow( hypoDistance / s3,2))
    
    return sigma
    

def distanceEpiToPoint(epiLat, epiLon, lat, lon):
    rEpiLat = math.radians(epiLat)
    rEpiLon = math.radians(epiLon)
    rLat = math.radians(lat)
    rLon = math.radians(lon)
    
    distance = math.acos( math.sin(rEpiLat) * math.sin(rLat) + math.cos(rEpiLat) * math.cos(rLat) * math.cos(rEpiLon-rLon))*6371;
    
    return int(distance)

def distanceHypoToPoint(epiLat, epiLon, depth, lat, lon):
    rEpiLat = math.radians(epiLat)
    rEpiLon = math.radians(epiLon)
    rLat = math.radians(lat)
    rLon = math.radians(lon)
    
    distance = math.acos( math.sin(rEpiLat) * math.sin(rLat) + math.cos(rEpiLat) * math.cos(rLat) * math.cos(rEpiLon-rLon))*6371;
    
    hypoDist = math.sqrt(distance*distance + depth*depth)
    
    return int(hypoDist)
    
def findNearestPlace( data, epiLat, epiLon ):
        try:
            return min( data, key=lambda p: distance( [epiLat, float(p['lat']), epiLon, float(p['lon'])] ) )
        except Exception as e:
            print(repr(e))
            return None
    
    
def azimuth( points ):
    #points is a list [refLat, epiLat, refLon, epiLon]
    refLat, epiLat, refLon, epiLon = map(math.radians, points)
    dist_lats = epiLat - refLat  
    dist_longs = epiLon - refLon 
    azRad = math.atan2( math.sin(dist_longs)*math.cos(epiLat) , math.cos( refLat)*math.sin( epiLat ) - math.sin( refLat ) * math.cos( epiLat ) * math.cos ( dist_longs) )
    azDeg = azRad * 180 / math.pi
            
    if azDeg < 0:
        azimuth = 360 + azDeg
    else:
        azimuth = azDeg
    return int(round(azimuth))

def direction(azVal, language ):
    
    if azVal >= 0 and azVal<10:
        return "N"
            
    elif azVal >= 10 and azVal < 40:
        return "NNE"
        
    elif azVal >= 40 and azVal < 50:
        return "NE"
        
    elif azVal >= 50 and azVal < 80:
        return "ENE"
        
    elif azVal >= 80 and azVal < 100:
        return "E"
    
    elif azVal >= 100 and azVal < 130:
        return "ESE"
    
    elif azVal >= 130 and azVal < 140:
        return "SE"
    
    elif azVal >= 140 and azVal < 170:
        return "SSE"
    
    elif azVal >= 170 and azVal < 190:
        return "S"
    
    elif azVal >= 190 and azVal < 220:
        if language == 'es-US':
            return "SSO"
        else:
            return "SSW"
            
    elif azVal >= 220 and azVal < 230:
        if language == 'es-US':
            return "SO"
        else:
            return "SW"
        
    elif azVal >= 230 and azVal < 260:
        if language == 'es-US':
            return "OSO"
        else:
            return "WSW"
            
    elif azVal >= 260 and azVal < 280:
        if language == 'es-US':
            return "O"
        else:
            return "W"
        
    elif azVal >= 280 and azVal < 310:
        if language == 'es-US':
            return "ONO"
        else:
            return "WNW"
        
    elif azVal >= 310 and azVal < 320:
        if language == 'es-US':
            return "NO"
        else:
            return "NW"
        
    elif azVal >= 320 and azVal < 350:
        if language == 'es-US':
            return "NNO"
        else:
            return "NNW"
        
    elif azVal >= 350 and azVal <= 360:
        return "N"

def location( distKm, azText, city, country, language ):
    
    if language == 'es-US':
        return str(distKm)+' km al '+ azText + ' de '+ city + ', '+ country
    else:
        return str(distKm)+' km '+ azText + ' of '+ city + ', '+ country

def distance( points ):
        #points is a list [refLat, epiLat, refLon, epiLon]
        
        refLat, epiLat, refLon, epiLon = map(math.radians, points)
        dist_lats = epiLat - refLat  
        dist_longs = epiLon - refLon 
        a = math.sin(dist_lats/2)**2 + math.cos(refLat) * math.cos(epiLat) * math.sin(dist_longs/2)**2
        c = 2 * math.atan2 ( math.sqrt(a), math.sqrt(1 - a) )
        radius_earth = 6371 # the Earth's radius 
        
        distance = c * radius_earth # distance in km
        #print(int(round(distance)))
        return int(round(distance))

def csvFile2dic( filename ):
    with open(filename, encoding = 'utf8') as f:
        file_data=csv.reader(f)
        headers=next(file_data)
        return [dict(zip(headers,i)) for i in file_data]
