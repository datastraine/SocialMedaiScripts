import os
import googleapiclient.discovery
import pandas as pd
import numpy as np
import json
import re
from FediBotEnv import Goog # <-- your dev key location
from datetime import datetime, timedelta

def get_channel_video_info_csv(channelId):
    '''
    Using the YouTube API v3 and youtube_transcript_api get the following into a single DF
    * A channel's upload ID and each video's ID and Title 'Video ID', 'Description', 'Published', 'Duration', Number of Comments, 
      and whether the video in question was a live stream or not for each video using the snippet, contentDetails, liveStreamingDetails, and statistics from the YouTube API v3
    '''

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # building blocks for the api call 
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = Goog

    # create the call object using google discovery
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)
   
    # execute the reponse and get the kinds of data we need (content details)
    response = youtube.channels().list(
        id=channelId,
        part="contentDetails"
    ).execute()

    # from the executed response, save the uploads playlist id. This will be used to get the videos. 
    # This is not always the same as the channel Id
    uploadId = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    
    # create an empty video list to store the video dict obs
    videos = []
    # create a next page token object and give it a none value to be used in the first itteration
    npt = None
    
    # use a while loop to continiously run the script it contains until it gets through all pages to grab all video links
    while 1:
        
        # execute the playlistitems reponse using the paramaters provided
        response = youtube.playlistItems().list(playlistId = uploadId,
                                                part="snippet",
                                                maxResults=50,
                                                pageToken = npt
                                               ).execute()
        
        # append the reponse items to the videos list
        videos += response['items']
        
        # reassign the next page token to what is found
        npt = response.get('nextPageToken')
        
        # if npt is none break out of the while loop
        if npt is None:
            break   
    
    # create a vid_df from the normalized videos list of dicts that we created above
    vid_df = pd.json_normalize(videos) 
    
    # reduce the vid_df obj to only the vid and channel information and the rename the columns
    vid_df = vid_df[['snippet.videoOwnerChannelId', 'snippet.channelTitle', 'snippet.title', 'snippet.resourceId.videoId', 'snippet.playlistId']]
    vid_df.columns = ['Channel ID', 'Channel Title', 'Video Title', 'Video ID', 'Playlist ID']
   
    # create an empty df 
    vid_deets = pd.DataFrame()    
    
    # create a for loop for on the list of Video IDs from our vid_df
    for vid in vid_df['Video ID']:
        
        # then for each vid, execute the videos().list() to get the vid information
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics, liveStreamingDetails",
            id=vid).execute()

        # normalize the response of each vid
        df = pd.json_normalize(response['items']) 
             
        # append the resulting df
        vid_deets = vid_deets.append(df)
        
    # once the vid_deets df is fully created created, pair down the df to the columns we only care about, rename the columns, and reset the index
    vid_deets = vid_deets[['id', 'snippet.description', 'snippet.publishedAt', 'contentDetails.duration','statistics.viewCount',
         'statistics.likeCount', 'snippet.tags', 'statistics.commentCount', 'liveStreamingDetails.actualStartTime']]
    
    vid_deets.columns = ['Video ID', 'Description', 'Published', 'Duration',
           'Views', 'Likes', 'Tags', 'Comment Count', 'Live']
    vid_deets.reset_index(drop=True, inplace=True)
                    
    # merge the vid_deets and vid_df together and export the CSV                    
    vid_df = vid_df.merge(vid_deets, on='Video ID')
    vid_df.to_csv(re.sub(r"^\s+", "", vid_df['Channel Title'][0]) + "_VidInfo.csv", index=False)