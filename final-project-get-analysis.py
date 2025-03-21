#
# Check the status of the requested job, 
# if completed, return the row.
# 

import json
import boto3
import os
import base64
import datatier
import requests

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
    # job is done, return row
    #
    print("**DONE, returning row**")
    
    return {
      'statusCode': 200,
      'body': json.dumps(row)
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