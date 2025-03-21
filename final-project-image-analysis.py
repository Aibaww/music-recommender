# Python program to open and process a txt file.
# Call hugging face inference API and perform computations
# to get valence and energy scores for Spotify API, and save
# the results to a text file.

import json
import boto3
import os
import pathlib
import datatier
import urllib.parse
import emotion

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: proj03_compute**")
    
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
    # this function is event-driven by a JPG being
    # dropped into S3. The bucket key is sent to 
    # us and obtain as follows:
    #
    bucketkey = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    print("bucketkey:", bucketkey)
      
    extension = pathlib.Path(bucketkey).suffix
    
    if extension not in [".jpg", ".jpeg"]: 
      raise Exception("expecting S3 document to have .jpg or .jpeg extension")
    
    #
    # update status column in DB for this job
    #
    print("**Opening DB connection**")
    #
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    #
    sql = "Update jobs Set status = %s Where datafilekey = %s"
    datatier.perform_action(dbConn, sql, ["processing - starting", bucketkey])

    #
    # call huggingface inference API to get emotion scores
    #
    print("**Calling Rekognition API**")
    region_name = configur.get('s3', 'region_name')
    rekognition = boto3.client('rekognition', region_name=region_name)
    response = rekognition.detect_labels(
          Features=['IMAGE_PROPERTIES'],
          Image={
            'S3Object': {
              'Bucket': bucket.name,
              'Name': bucketkey,
            },
          },
          Settings={
            'ImageProperties': {
                'MaxDominantColors': 5
            }
          })
    print(response)
    print("**Received response, analyzing colors...**")
    colors = response["ImageProperties"]["DominantColors"]
    (valence, energy) = emotion.map_colors_to_valence_energy(colors)

    #
    # analysis complete, update the database to change
    # the status of this job, and store the results
    #
    print("**Updating DB with result**")
    sql = "Update jobs Set status = %s, valence = %s, energy = %s Where datafilekey = %s"
    datatier.perform_action(dbConn, sql, ["completed", str(valence), str(energy), bucketkey])
    print("**DONE, returning success**")
    
    return {
      'statusCode': 200,
      'body': json.dumps("success")
    }
  
  #
  # on an error, try to upload error message to database:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    #
    # update jobs row in database:
    #
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    #
    sql = "Update jobs Set status = %s Where datafilekey = %s"
    datatier.perform_action(dbConn, sql, ["error", bucketkey])
    #

    #
    # done, return:
    #    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }



