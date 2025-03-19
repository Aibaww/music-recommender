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
    # in case we get an exception, initial this filename
    # so we can write an error message if need be:
    #
    bucketkey_results_file = ""
    
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
    # this function is event-driven by a PDF being
    # dropped into S3. The bucket key is sent to 
    # us and obtain as follows:
    #
    bucketkey = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    print("bucketkey:", bucketkey)
      
    extension = pathlib.Path(bucketkey).suffix
    
    if extension != ".txt" : 
      raise Exception("expecting S3 document to have .txt extension")
    
    # create result file
    bucketkey_results_file = bucketkey[0:-4] + "-result.txt"
    
    print("bucketkey results file:", bucketkey_results_file)

    #
    # download PDF from S3 to LOCAL file system:
    #
    print("**DOWNLOADING '", bucketkey, "'**")

    #
    # download file to local system
    #
    local_txt = "/tmp/data.txt"
    
    bucket.download_file(bucketkey, local_txt)

    #
    # open LOCAL pdf file:
    #
    print("**PROCESSING local TXT**")
    input_text = ''
    with open(local_txt, 'r') as f:
      input_text = f.read()
    
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
    emotion_scores = emotion.get_emotion_scores(input_text)
    # 
    for item in emotion_scores:
      print("Label: ", item["label"], ", Score: ", item["score"])
    
    #
    # convert emotion scores to valence energy scores
    #
    ve_scores = emotion.map_emotions_to_valence_energy(emotion_scores)
    #
    print("Valence: ", ve_scores[0], ", Energy: ", ve_scores[1])

    #
    # analysis complete, write the results to local results file:
    #
    local_results_file = "/tmp/results.txt"

    print("local results file:", local_results_file)

    with open(local_results_file, 'w') as f:
      f.write(str(ve_scores[0]) + "\n")
      f.write(str(ve_scores[1]) + "\n")

    #
    # upload the results file to S3:
    #
    print("**UPLOADING to S3 file", bucketkey_results_file, "**")

    bucket.upload_file(local_results_file,
                       bucketkey_results_file,
                       ExtraArgs={
                         'ACL': 'public-read',
                         'ContentType': 'text/plain'
                       })
    
    #
    # update the database to change
    # the status of this job, and store the results
    # bucketkey for download
    #
    sql = "Update jobs Set status = %s, resultsfilekey = %s Where datafilekey = %s"
    datatier.perform_action(dbConn, sql, ["completed", bucketkey_results_file, bucketkey])
    print("**DONE, returning success**")
    
    return {
      'statusCode': 200,
      'body': json.dumps("success")
    }
  
  #
  # on an error, try to upload error message to S3:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    local_results_file = "/tmp/results.txt"
    outfile = open(local_results_file, "w")

    outfile.write(str(err))
    outfile.write("\n")
    outfile.close()
    
    if bucketkey_results_file == "": 
      #
      # we can't upload the error file:
      #
      pass
    else:
      # 
      # upload the error file to S3
      #
      print("**UPLOADING**")
      #
      bucket.upload_file(local_results_file,
                         bucketkey_results_file,
                         ExtraArgs={
                           'ACL': 'public-read',
                           'ContentType': 'text/plain'
                         })

    #
    # update jobs row in database:
    #
    # TODO #8 of 8: open connection, update job in database
    # to reflect that an error has occurred. The job is 
    # identified by the bucketkey --- datafilekey in the 
    # table. Set the status column to 'error' and set the
    # resultsfilekey column to the contents of the variable
    # bucketkey_results_file.
    #
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    #
    sql = "Update jobs Set status = %s, resultsfilekey = %s Where datafilekey = %s"
    datatier.perform_action(dbConn, sql, ["error", bucketkey_results_file, bucketkey])
    #

    #
    # done, return:
    #    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }


