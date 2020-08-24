#!/usr/bin/env python
# coding: utf-8

import spotipy
import spotipy.util as util
sp = spotipy.Spotify() 
from spotipy.oauth2 import SpotifyClientCredentials

from datetime import datetime
from datetime import timedelta

import pandas as pd

import os

from sh import git, cd
from git import Repo,remote


def push_to_github():
    #push to github

    # os.system("git -C /Users/tpainter/Desktop/personal-projects/spotify-mood add .")
    # os.system("git -C /Users/tpainter/Desktop/personal-projects/spotify-mood commit -m 'updating daily data'")
    # os.system("git -C /Users/tpainter/Desktop/personal-projects/spotify-mood push")

    # rw_dir = '/Users/tpainter/Desktop/personal-projects/spotify-mood'
    # repo = Repo(rw_dir)
    # origin = repo.remote(name='origin')
    # origin.push()

    dir_name = '/Users/tpainter/Desktop/personal-projects/spotify-mood/.git'
    # cd(dir_name)
    # git("add")
    # git("commit -m 'adding daily data'")
    # git("push -u origin master")
    try:
        cd(dir_name)
        repo = Repo(dir_name)
        repo.git.add(update=True)
        repo.index.commit('updating daiy data')
        origin = repo.remote(name='origin')
        origin.push()

        print("Pushed to github.\n")
    except Exception as e:
        print(e)
        print('Some error occured while pushing the code\n')

# ## spotify auth flow

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
    
    #break out of loop if the song was not played in the last hour
    try:
        time_played = datetime.strptime(song["played_at"],"%Y-%m-%dT%H:%M:%S.%fZ")
    except:
        pass        
    time_elapsed = time_played - datetime.now() 
    if time_elapsed < timedelta(hours=3, minutes=1):
        break
    
    #spotify has weird hours/time zone going on
    #and i need to make it pretty for the table
    adjusted_played_at = time_played - timedelta(hours=4)
    readable_time = adjusted_played_at.strftime("%H") + ":" + adjusted_played_at.strftime("%M")
    
    count+=1
    
    features = sp.audio_features(song["track"]["id"])
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


#add spotify data to csv
df = pd.DataFrame.from_dict(song_dict,orient='index').transpose()
#reorder rows to time
df = df.iloc[::-1]

filename = "~/Desktop/personal-projects/spotify-mood/daily-data/" + datetime.now().strftime('%Y-%m-%d/')[:10] + ".csv"

try:
    df.to_csv(filename, mode = 'a', header = False, index = False)
except:
    command = 'touch ' + filename
    os.system(command)  
    df.to_csv(filename, mode = 'a', header = False, index = False)

print("Rows: ", len(df.index))
print("Saved!\n")
push_to_github()





