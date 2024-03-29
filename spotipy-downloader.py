#!/usr/bin/env python
# coding: utf-8

import spotipy
import spotipy.util as util
sp = spotipy.Spotify() 
from spotipy.oauth2 import SpotifyClientCredentials

from datetime import datetime
from datetime import timedelta
import pytz

import pandas as pd

import os
import csv

from sh import git, cd
# from git import Repo,remote

def push_to_github():
    #push to github

    try:
        os.system("git -C ~/Desktop/GitHub/spotify-mood add .")
        os.system("git -C ~/Desktop/GitHub/spotify-mood commit -m 'updating daily data "+ str(datetime.now())+ "'")
        os.system("git -C ~/Desktop/GitHub/spotify-mood push")
    except Exception as e:
        print("FAT FAILURE PUSHING")
        print(str(e))

    # rw_dir = '/Users/tpainter/Desktop/personal-projects/spotify-mood'
    # repo = Repo(rw_dir)
    # origin = repo.remote(name='origin')
    # origin.push()

    # dir_name = '~/Desktop/GitHub/spotify-mood/.git'
    # cd(dir_name)
    # git("add")
    # git("commit -m 'adding daily data'")
    # git("push -u origin master")

    # try:
    #     cd(dir_name)
    #     repo = Repo(dir_name)
    #     repo.git.add(up=True)
    #     repo.index.commit('updating daiy data')
    #     origin = repo.remote(name='origin')
    #     origin.push()

    #     print("Pushed to github.\n")
    # except Exception as e:
    #     print(e)
    #     print('Some error occured while pushing the code\n')

# ## spotify auth flow

def is_dst ():
    """Determine whether or not Daylight Savings Time (DST)
    is currently in effect"""

    x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern')) # Jan 1 of this year
    y = datetime.now(pytz.timezone('US/Eastern'))

    # if DST is in effect, their offsets will be different
    return not (y.utcoffset() == x.utcoffset())

print(datetime.now())

cid ="1c7e8aed94914da78a7b264590d7fc21" 
secret = "c2113b0c6e3543d282adb8c61e4abede"
username = "trudypaintet"
redirect_uri="http://localhost:3000"

client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret) 
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

print("Auth happening...")

scope = 'user-read-recently-played'
token = util.prompt_for_user_token(username,scope,cid,secret,redirect_uri)
if token:
    sp = spotipy.Spotify(auth=token)
else:
    print("Can't get token for", username)


# ## download recently played songs
# 1. collect songs info
#     - name, id, time played
# 2. filter for UNINDEXED songs from TODAY
#     - script will run every hour and add new entries to a csv for the date

print("Getting songs")
recent_songs = sp.current_user_recently_played()

count = 0
track_ids = []
mood_avgs = []

print("Creating dataframe...")
#creating data frame to add to the csv
song_dict = {'image':[],
        'song_name': [],
        'album_name':[],
        'artist_name': [],
        'track_id':[],

        'played_at':[],
        'valence':[],
        'danceability':[],
        'energy':[],
        'mood_avg':[]}

for song in recent_songs["items"]:
    print(song["track"]["name"])
    
    #break out of loop if the song was not played in the last hour
    try:
        time_played = datetime.strptime(song["played_at"],"%Y-%m-%dT%H:%M:%S.%fZ")
    except:
        pass        
    time_elapsed = time_played - datetime.now()

    #to account for daylight savings time - need to change
    daylight_savings = 1
    if is_dst():
        daylight_savings = 0
    
    
    if time_elapsed < timedelta(hours=3 + daylight_savings, minutes=1):
        print("time elapsed incorrect!")
        break
    
    #spotify has weird hours/time zone going on
    #and i need to make it pretty for the table
    adjusted_played_at = time_played - timedelta(hours=3 + daylight_savings)
    readable_time = adjusted_played_at.strftime("%H") + ":" + adjusted_played_at.strftime("%M")
    
    count+=1
    
    features = sp.audio_features(str(song["track"]["id"]))
    try:
        valence = float(features[0]["valence"])
        dance = float(features[0]["danceability"])
        energy = float(features[0]["energy"])
        avg = (valence*0.4) + (dance*0.4) + (energy*0.2)
        mood_avgs.append(avg)
    
        #adding songs to dictionary to be put into dataframe
        song_dict['image'].append(song['track']['album']['images'][0]['url'])
        song_dict['song_name'].append(song["track"]["name"])
        song_dict['album_name'].append(song["track"]["album"]["name"])
        song_dict['artist_name'].append(song["track"]["artists"][0]["name"])
        song_dict['track_id'].append(song["track"]["id"])
        song_dict['played_at'].append(readable_time)
        song_dict['valence'].append(valence)
        song_dict['danceability'].append(dance)
        song_dict['energy'].append(energy)
        song_dict['mood_avg'].append(round(avg, 3))
    except Exception as err:
        print('**ERROR adding ', song["track"]["name"])
        print(err)
        pass

print("GOT THESE SONGS")
print(song_dict)

#add spotify data to csv
df = pd.DataFrame.from_dict(song_dict, orient='index').transpose()
#reorder rows to time
df = df.iloc[::-1]

#reorder the columns to make csv compatible for flask
cols = df.columns.to_list()
df = df[['image',  'song_name', 'album_name', 'artist_name', 'track_id', 'played_at', 'valence', 'mood_avg', 'danceability', 'energy']]
print(df)

filename = "/Users/trudypainter/Desktop/GitHub/spotify-mood/daily-data/" + datetime.now().strftime('%Y-%m-%d/')[:10] + ".csv"

# add the dataframe to a csv
try:
    df.to_csv(filename, mode = 'a', header = False, index = False)
except:
    command = 'touch ' + filename
    os.system(command)  
    df.to_csv(filename, mode = 'a', header = False, index = False)

# remove duplicates if there are any
def remove_duplicates(filename):
    
    print("checking", filename, " for duplicates....")
    # make tuple of songs
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        line_count=0
        unique_songs = tuple()
        for row in csv_reader:
            line_count+=1  
            row_tup = tuple(row)
            if row_tup not in unique_songs:
                unique_songs += (row_tup,)
          
        if line_count == len(unique_songs):
            print("There were no duplicates!\n")
            return None
        
        print("DUPLICATES FOR ", filename)
        print(line_count)
        print(len(unique_songs)) 
        
    # delete songs
    open(filename, 'w').close()
    
    # rewrite data
    with open(filename, mode='w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for song in unique_songs:
            writer.writerow(song)  
        num_removed = line_count-len(unique_songs)     
    print("Completed removal of", num_removed, "duplicates!\n ")

remove_duplicates(filename)

print("Rows: ", len(df.index))
print("Saved!\n")
push_to_github()





