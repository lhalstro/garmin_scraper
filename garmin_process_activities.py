""" Garmin Connect Activity Processor
Read and process 'Activities.csv' exported from Garmin Connect web app.

NOTE: To download Activities.csv from garmin, must first scroll down activity list to earliest activity to download entire set
"""

import os
import sys
import numpy as np
import pandas as pd
import datetime

# from mypylib import units
# ft2m = units.convert('ft', 'm')
# ft2mi = units.convert('ft','mi')
# m2mi = units.convert('m','mi')



#Columns in Garmin Connect Export CSV
raw_columns = "Activity Type,Date,Favorite,Title,Distance,Calories,Time,Avg HR,Max HR,Aerobic TE,Avg Bike Cadence,Max Bike Cadence,Avg Speed,Max Speed,Total Ascent,Total Descent,Avg Stride Length,Avg Vertical Ratio,Avg Vertical Oscillation,Avg Ground Contact Time,Avg GAP,Normalized Power® (NP®),Training Stress Score®,Avg Power,Max Power,Grit,Flow,Avg. Swolf,Avg Stroke Rate,Total Reps,Total Sets,Dive Time,Min Temp,Surface Interval,Decompression,Best Lap Time,Number of Laps,Max Temp,Moving Time,Elapsed Time,Min Elevation,Max Elevation".split(",")

#Columns to keep in exported data
    #value is raw column name, key is export name (None for blank column in export)
    #Omit raw column names to omit from export
    #Order is export column order
    #(side comments refer to the nature of the parameter in RunLog google sheet)
coldict = pd.Series({
        "Day":None,       #sheet formula
        "Start":None,     #will be parsed out of 'Date'
        "Date" :None,     #will be parsed out of 'Date'
        "Distance": "Distance",
        "h":None,         #sheet formula/hidden
        "m":None,         #sheet formula/hidden
        "s":None,         #sheet formula/hidden
        "Time" : None,    #will be assigned to either moving time or elapsed time, depending on activity
        "Mile Time":None, #sheet formula
        "Gain (ft)":'Total Ascent',
        "Grade":None, #sheet formula
        "Temp (F)":None, #garmin temperature recording is not representative of ambient
        "Rel. hum.":None,
        "Heat Index":None,
        "AQI":None,
        "Avg HR":'Avg HR',
        "Max HR":'Max HR',
        "Rating":None,
        "Fatigue":None,
        "Shoe":None,
        "Activity":'Activity Type',
        "Route/Description":'Title',
        "Location":None,
        "Who with":None,
        "Comments":None,
        "Excuses":None,
        "Injury":None,
        "BLANK1":None,
        "BLANK2":None,
        "Andrew's RunEffort Scale":None,
    })

def main():
    #original garmin data
    raw = pd.read_csv('data/Activities.csv')

    #data processing storage
    df = raw.copy()
    #convenient/common column names
    df = df.rename(columns={'Date':'datetime','Moving Time':'moving_time','Elapsed Time':'elapsed_time'}) #itermmediate calculation parameters
    df = df.rename(columns={v:k for k,v in coldict.dropna().items()}) #export parameters

    # # Make all walks into hikes for consistency
    # df['type'] = df['type'].replace('Walk','Hike')
    # # Create a distance in km column
    # df['distance_km'] = df['distance']/1e3

    # #GARMIN UNITS ALREADY IN IMPERIAL
    # for c in df.columns.values:
    #     if c == 'Total Ascent':
    #         df[c] /= ft2m
    #     elif c == 'Distance':
    #         df[c] *= m2mi
    #     elif 'speed' in c.lower():
    #         df[c] *= 1/ft2m * ft2mi

    #RENAME ACTIVITY TYPES
    activ = {'Hiking':'Hike','Running':'Run','Swimming':'Swim','Cycling':'Bike','Trail Running':'Run','Walking':'Walk'}
    df['Activity'] = [activ[a] if a in activ else a for a in df['Activity']]



    #GET ACTIVITY START DATE AND TIME
    # Convert dates to datetime type
    df['datetime'] = pd.to_datetime(df['datetime'])
    #Parse actual spreadsheet column inputs: Date and start time
    df['Date'] = [d.date()  for d in df['datetime']]
    df['Start'] = [d.time() for d in df['datetime']]

    #GET ACTIVITY DURATION
    # #parse raw times
    # for x in ['moving_time', 'elapsed_time']:
    #     # Convert times in seconds to timedeltas
    #     df[x] = pd.to_timedelta(df[x], unit='S')
    #     #Reduce activity duration time to only hours/minutes/seconds (no days)
    #     df[x] = [str(d).split('days')[-1].replace(" ","") for d in df[x]]
    #Choose Moving or Elapsed Time
    df['Time'] = [r['moving_time'] if r['Activity'] in ['Hike', 'Bike'] else r['elapsed_time'] for i,r in df.iterrows()]


    #EXPORT
    log = df.copy()

    #Add any missing spreadsheet columns as NaN
    for c in coldict.index.values:
        if c not in log: log[c] = None

    #Reorder: spreadsheet columns first (in order), then extra columns at the end
    log = log[list(coldict.index.values)+[c for c in log.columns.values if c not in coldict.index]]


    print(log)
    print(log.columns.values)

    os.makedirs('export', exist_ok=True)
    #save all relevant data to file
    log.dropna(axis=1,how='all').to_csv('export/log_all.csv', index=False)

    #ALSO DOWNSELECT TO DISTANCE-BASED ACTIVITIES ONLY
    # dontexpt = ['Workout', 'WeightTraining',]
    # expt = log[(log['Activity'] != 'Workout')&(log['Activity'] != 'WeightTraining')]
    expt = log.copy()
    dontexpt = ['Strength', 'Cardio', 'Swimming', 'Yoga']
    for dont in dontexpt:
        expt = expt[~expt['Activity'].str.contains(dont)]

    #save exact columns of google spreadsheet to file
    expt[list(coldict.index.values)].sort_values(['Date', 'Start']).to_csv('export/log.csv', index=False)






    # #spreadsheet columns to rename
    # logcol = coldict.dropna()
    # #addl columns to keep for calculations here
    # keepcol = ['datetime', 'moving_time', 'elapsed_time']
    # # print(logcol)
    # #Downselect and rename
    # log = df[list(logcol.values)+list(keepcol)].rename(columns={v:k for k,v in logcol.items()})

    # log['Date'] = [d.date()  for d in log['datetime']]
    # log['Start'] = [d.time() for d in log['datetime']]

    # for x in ['moving_time', 'elapsed_time']:
    #     log[x] = [str(d).split('days')[-1].replace(" ","") for d in log[x]]
    # log['Time'] = [r['moving_time'] if r['Activity'] in ['Hike', 'Ride'] else r['elapsed_time'] for i,r in log.iterrows()]
    # # log['Time'] = [str(d).split('days')[-1].replace(" ","") for d in log['Time']]


    # #Add any missing spreadsheet columns as NaN
    # for c in coldict.index.values:
    #     if c not in log: log[c] = None
    # #Reorder: spreadsheet columns first (in order), then extra columns at the end
    # log = log[list(coldict.index.values)+[c for c in log.columns.values if c not in coldict.index]]


    # print(log)
    # print(log.columns.values)

    # os.makedirs('export', exist_ok=True)
    # #save all relevant data to file
    # log.dropna(axis=1,how='all').to_csv('export/log.csv', index=False)



    # #downselect to distance-based activities
    # dontexpt = ['Workout', 'WeightTraining',]
    # expt = log[(log['Activity'] != 'Workout')&(log['Activity'] != 'WeightTraining')]

    # #save exact columns of google spreadsheet to file
    # expt.drop(columns=keepcol).sort_values('Date').to_csv('export/export_log.csv', index=False)


if __name__ == "__main__":
    main()
