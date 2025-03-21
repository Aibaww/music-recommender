#
# Retrieves and returns a randomized playlist
# of custom length for a player
#

import json
import boto3
import os
import datatier
import requests
import random

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: proj03_jobs**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'musicapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    #
    # get userid to search songs for
    #
    print("**Get user info from params**")
    if "userid" in event:
      userid = event["userid"]
    elif "pathParameters" in event:
      if "userid" in event["pathParameters"]:
        userid = event["pathParameters"]["userid"]
      else:
        raise Exception("ERROR: userid is required")
    else:
      raise Exception("ERROR: userid is required")
    
    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    #
    # check if this user exists
    #
    print("**Looking up user...**")
    
    print("userid: ", userid)

    #
    # get optional playlist length param
    #
    length = 10
    if "length" in event:
      length = event["length"]
    elif "pathParameters" in event:
      if "length" in event["pathParameters"]:
        length = event["pathParameters"]["length"]
    print("length: ", length)

    sql = "SELECT * FROM users WHERE userid = %s"
    
    row = datatier.retrieve_one_row(dbConn, sql, [userid])
    if row == ():  # no such user
      print("**No such user, returning...**")
      return {
        'statusCode': 400,
        'body': json.dumps("no such user...")
      }
    
    #
    # retrieve jobs of the logged in user:
    #
    print("**Retrieving song data for user**")
    
    sql = "SELECT * FROM songs WHERE userid = %s ORDER BY songname"
    
    rows = datatier.retrieve_all_rows(dbConn, sql, [userid])
    
    for row in rows:
      print(row)

    #
    # Randomize songs
    #
    print("**Randomizing songs**")
    rows = list(rows)
    random.shuffle(rows)
    if length > len(rows):
      rows = rows[:length]
    playlist = [{"songname": row[3], "songartist": row[4]} for row in rows]

    for song in playlist:
      print(song)

    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning rows**")
    
    return {
      'statusCode': 200,
      'body': json.dumps(playlist)
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
