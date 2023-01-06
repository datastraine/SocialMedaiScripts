import os
import pandas as pd
import isodate
import random
from datetime import datetime, date, timedelta
from mastodon import Mastodon
from FediBotEnv import Masto, Goog # <-- your enviorment creds
from GetVidYT import get_channel_video_info_csv # <--- the script to build the YouTube Video Details data frame
from time import sleep

# create a location directory to save the dontsave file to by using os expanduser and assign location based on folder path
home = os.path.expanduser('~')
location = os.path.join(home, 'Documents/Scripts') # <-- replace with what ever you want

# set up mastodon.py API connection
m = Mastodon(access_token=Masto, api_base_url="https://federated.press/") # <-- replace with your mastodon instance url

# assign path obj to the direct path of the channel's info CSV
path = location + "VidInfo.csv" # <-- your video info URL

# assign a date to a rerunyt obj. This is used to determine if we need to pull the channel info again. I have it set to get the file every 3 days
rerunyt = datetime.fromtimestamp(os.path.getmtime(path)) + timedelta(days=3)

# use a simple if check to determine if the channel info needs to be rerun
if rerunyt < datetime.today():
    print("Updating CSV")
    # run the get_channel_video_info_csv scrip
    get_channel_video_info_csv('UCVQurupoN0sXYIUBZyneZQA')
    print("Done getting channel info")
    
else: print("No need to update CSV")

# read the channel info csv into a df
df = pd.read_csv(path)
# turn published column into a datetime object and localize time zone for easier use 
df["Published"] =  pd.to_datetime(df['Published']).dt.tz_localize(None)
# use apply and lambda with the isodate function to turn duration into seconds
df['Duration'] = df['Duration'].apply(lambda x: isodate.parse_duration(x).total_seconds())
# finally eliminate any video that is older than 28 days (lenght of cycle), remove live videos, and any video that is a short
df = df[(df['Published'] >= pd.Timestamp('today') - pd.offsets.Day(28)) & (df["Live"].isna()) & (df['Duration'] >= 60)].reset_index()

# assign all videos to a video id list and create an empty dontpost list
vidlist = list(df['Video ID'])
dontpost = []

# using try, try to open and read dontpost file and if it fails create a dontpost file with placeholder inside
try:
    with open(f"{location}\dontpost.txt", 'r') as fobj:
        # remove linebreak from a current name
        # linebreak is the last character of each line
        x = fobj[:-1]
        print("Dontpost file exist!")
        # add current item to the list

except: 
    print("Creating dontpost list")
    with open(f"{location}\dontpost.txt",  'a+') as fobj:
        if os.stat(f"{location}\dontpost.txt").st_size == 0:
            fobj.write('Placeholder')

# read the dontpost file into the dontpost list
with open(f"{location}\dontpost.txt", 'r') as fp:
    for line in fp:
        # remove linebreak from a current name
        # linebreak is the last character of each line
        x = line[:-1]

        # add current item to the list
        dontpost.append(x)

# compare the vidlist to the dontpost list and remove any video id that is in the dontpost list        
postit = [x for x in vidlist if x not in dontpost]

# create a post obj to store the result of the random choice in the future.
post = 'rando'

# check to ensure if the postit list has items in it. If it does, randomly select a video id from it. If it doesn't, randomly select a video id from the df
if len(postit) > 0:
    post = random.choice(postit) 
else:
    post = random.chocice(list(df['Video ID']))

# append the video ID to the dontpost list    
dontpost.append(post)

# use random choice to randomly pick a video from the postit list and then append that video to the dontpost list
        
# toot the description and the video link of the randomly choosen post video
# Note: The whole toot has to be under 500 characters for most mastodon instances. 
# If you aren't sure yours will be, replace the first part with whatever you want to say in your script
m.toot(f"{list(df[df['Video ID']==post]['Description'])[0]} {'https://www.youtube.com/watch?v=' + list(df[df['Video ID']==post]['Video ID'])[0]}")

print("Toot complete!")

# create a rerundontpost obj to store the date we want to delete the dontpost file to start over. I have it set to 14 days
rerundontpost = datetime.fromtimestamp(os.path.getmtime(f"{location}\dontpost.txt")) + timedelta(days=14)

# use an if else statement to check to see if dontpost video is old enough to replace 
if rerundontpost < datetime.today():
    # if it is delete the file and then append the last video posted to it
    print("Replacing dontrun")
    # run the get_channel_video_info_csv scrip
    os.remove(f"{location}\dontpost.txt") 
    with open(f"{location}\dontpost.txt", 'a+') as fobj:
        if not str(fobj).endswith('\n'):
            fobj.write('\n')
            fobj.write(post)
        else:
            fobj.write(post)

# else, simply append the post video 
else:
    print("Updating dontrun")
    with open(f"{location}\dontpost.txt", 'a+') as fobj:
        if not str(fobj).endswith('\n'):
            fobj.write('\n')
            fobj.write(post)
        else:
            fobj.write(post)

print("TootBot run complete")
sleep(2)