#
# Check the status of the requested job, 
# if completed, call Spotify API to recommend songs
# Store the songs in database and return them to the user.
# 

import json
import boto3
import os
import base64
import datatier
import requests
import spotify

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: proj03_download**")

    #
    # setup AWS based on config file:
    #
    config_file = 'musicapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)
    
    bucketname = configur.get('s3', 'bucket_name')
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    #
    # configure for Spotify token
    #
    spotify_id = configur.get("spotify", "client_id")
    spotify_secret = configur.get("spotify", "client_secret")
    
    #
    # jobid from event: could be a parameter
    # or could be part of URL path ("pathParameters"):
    #
    if "jobid" in event:
      jobid = event["jobid"]
    elif "pathParameters" in event:
      if "jobid" in event["pathParameters"]:
        jobid = event["pathParameters"]["jobid"]
      else:
        raise Exception("requires jobid parameter in pathParameters")
    else:
        raise Exception("requires jobid parameter in event")
        
    print("jobid:", jobid)

    #
    # does the jobid exist?  What's the status of the job if so?
    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    #
    # first we need to make sure the userid is valid:
    #
    print("**Checking if jobid is valid**")
    
    sql = "SELECT * FROM jobs WHERE jobid = %s;"
    
    row = datatier.retrieve_one_row(dbConn, sql, [jobid])
    
    if row == ():  # no such job
      print("**No such job, returning...**")
      return {
        'statusCode': 400,
        'body': json.dumps("no such job...")
      }
    
    print(row)
    
    userid = row[1]
    status = row[2]
    valence = row[5]
    energy = row[6]
    
    print("")
    print("job status:", status)
    print("valence:", valence)
    print("energy:", energy)
    
    #
    # what's the status of the job? There should be 4 cases:
    #   uploaded
    #   processing - ...
    #   completed
    #   error
    #
    if status == "uploaded":
      print("**No results yet, returning...**")
      #
      return {
        'statusCode': 480,
        'body': json.dumps(status)
      }

    if status.startswith("processing"):
      print("**No results yet, returning...**")
      #
      return {
        'statusCode': 481,
        'body': json.dumps(status)
      }
    
    if status == "error":
      print("**Job errored, cannot recommend songs, returning...**")
      return {
        'statusCode': 481,
        'body': json.dumps(status)
      }
    
    #
    # job exists, get genres from params
    #
    genre = "pop,hip-hop,r-n-b,rock,electronic" # default seed genres

    if "genre" in event:
      genre = event["genre"]
    elif "pathParameters" in event:
      if "genre" in event["pathParameters"]:
        genre = event["pathParameters"]["genre"]
    
    print("Genres:", genre)
    
    #
    # completed, get spotify token
    #
    print("**Getting Spotify token...**")
    AUTH_URL = 'https://accounts.spotify.com/api/token'

    # POST
    auth_response = requests.post(AUTH_URL, {
      'grant_type': 'client_credentials',
      'client_id': spotify_id,
      'client_secret': spotify_secret,
    })

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    token = auth_response_data['access_token']
    # work-around
    # token = configur.get("spotify", "access_token")

    #
    # check if token is generated successfully
    #
    #if response.status_code != 200:
    #  print("**Token request failed...**")
    #  return
    #else:
    #  body = response.json()
    #  token = body["access_token"]
    #  print("Token: ", token)

    #
    # Call Spotify API
    #
    print("**Calling Spotify API...**")
    songs = spotify.get_song_recommendations(valence, energy, genre, token)
    
    if songs == []:
        return {
            'statusCode': 500,
            'body': "failed to get songs"
        }
    print("Songs: ", songs)

    print("**Adding songs to database...**")
    for song in songs:
      sql = '''INSERT INTO songs(userid, jobid, songname, songartist)
                           values(%s, %s, %s, %s);'''
      row = datatier.perform_action(dbConn, sql, [userid, jobid, song[0], song[1]])

    print("**DONE**")
    print("**Returning songs to client...")
    return {
      'statusCode': 200,
      'body': json.dumps(songs)
    }
    
  #
  # we end up here if an exception occurs:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
    
