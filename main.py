'''
Client Side Music Recommendation App
'''
import requests
import json
import random

import uuid
import pathlib
import logging
import sys
import os
import base64
import time
from configparser import ConfigParser

############################################################
#
# classes
#
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.username = row[1]
    self.pwdhash = row[2]


class Job:

  def __init__(self, row):
    self.jobid = row[0]
    self.userid = row[1]
    self.status = row[2]
    self.originaldatafile = row[3]
    self.datafilekey = row[4]
    self.valence = row[5]
    self.energy = row[6]

class Song:
  
  def __init__(self, row):
    self.songid = row[0]
    self.userid = row[1]
    self.jobid = row[2]
    self.songname = row[3]
    self.songartist = row[4]

def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None

###################################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number
  
  Parameters
  ----------
  None
  
  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """

  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => upload text")
    print("   2 => upload image")
    print("   3 => get result")
    print("   4 => get recommendations")
    print("   5 => get playlist")

    cmd = int(input())
    return cmd

  except Exception as e:
    print("ERROR")
    print("ERROR: invalid input")
    print("ERROR")
    return -1
  
############################################################
#
# upload
#
def upload(baseurl, file_type):
  """
  Prompts the user for a local filename and user id, 
  and uploads that asset to S3 for processing. 

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    print(f"Enter {file_type} filename>")
    local_filename = input()

    if not pathlib.Path(local_filename).is_file():
      print(f"{file_type} file '", local_filename, "' does not exist...")
      return

    print("Enter user id>")
    userid = input()

    #
    # build the data packet. First step is read the file
    # as raw bytes:
    #
    infile = open(local_filename, "rb")
    bytes = infile.read()
    infile.close()

    #
    # now encode the file as base64. Note b64encode returns
    # a bytes object, not a string. So then we have to convert
    # (decode) the bytes -> string, and then we can serialize
    # the string as JSON for upload to server:
    #
    data = base64.b64encode(bytes)
    datastr = data.decode("utf-8")

    data = {"filename": local_filename, "data": datastr}

    #
    # call the web service:
    #

    url = baseurl + f"/{file_type}/" + userid
    
    res = requests.post(url, json=data)
    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    elif res.status_code == 400: # no such user
      body = res.json()
      print(body)
      return
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # success, extract jobid:
    #
    body = res.json()

    jobid = body

    print("file uploaded, job id =", jobid)
    return

  except Exception as e:
    logging.error("**ERROR: upload() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# get_result
#
def get_result(baseurl):
  """
  Prompts the user for the job id, and gets
  the valence and energy scores.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  
  try:
    print("Enter job id>")
    jobid = input()
    
    #
    # call the web service:
    #

    url = baseurl + "/result/" + jobid

    res = web_service_get(url)
    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    elif res.status_code == 400: # no such job
      body = res.json()
      print(body)
      return
    elif res.status_code in [480, 481, 482]:  # uploaded
      msg = res.json()
      print("No results available yet...")
      print("Job status:", msg)
      return
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return
      
    #
    # if we get here, status code was 200, so we
    # have results to display:
    #
    
    body = res.json() # should be a row from jobs table
    result = Job(body)
    valence = result.valence
    energy = result.energy

    print(f"Valence: {valence}\nEnergy: {energy}")
    return

  except Exception as e:
    logging.error("**ERROR: get_result() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# get_recommendations
#
def get_recommendations(baseurl):
  """
  Prompts the user for the job id, and gets
  the valence and energy scores.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  
  try:
    print("Enter job id>")
    jobid = input()
    
    #
    # call the web service:
    #

    url = baseurl + "/recommendations/" + jobid

    res = web_service_get(url)
    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    elif res.status_code == 400: # no such job
      body = res.json()
      print(body)
      return
    elif res.status_code in [480, 481, 482]:  # uploaded
      msg = res.json()
      print("No results available yet...")
      print("Job status:", msg)
      return
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return
      
    #
    # if we get here, status code was 200, so we
    # have results to display:
    #
    
    body = res.json() # should be a list of tuples (songname, songartist)

    print("Recommended tracks:")
    for song in body:
      print(f"  Name: {song[0]}, Artist: {song[1]}")
    return

  except Exception as e:
    logging.error("**ERROR: get_recommendations() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# get_playlist
#
def get_playlist(baseurl):
  """
  Prompts the user for the job id, and gets
  the valence and energy scores.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  
  try:
    print("Enter user id>")
    userid = input()
    
    print("Enter max length of playlist, Press Enter for default>")
    length = input()

    url = baseurl + "/playlist/" + userid

    if length != "":
      if not length.isnumeric():
        print("ERROR: Length must be a number")
        return
      else:
        url = url + "?length=" + length
    #
    # call the web service:
    #
    res = web_service_get(url)
    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    elif res.status_code == 400: # no such job
      body = res.json()
      print(body)
      return
    elif res.status_code in [480, 481, 482]:  # uploaded
      msg = res.json()
      print("No results available yet...")
      print("Job status:", msg)
      return
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return
      
    #
    # if we get here, status code was 200, so we
    # have results to display:
    #
    
    rows = res.json() # should be rows of songs

    print("Playlist:")
    for row in rows:
      song = Song(row)
      print(f"  Name: {song.songname}, Artist: {song.songartist}")
    return

  except Exception as e:
    logging.error("**ERROR: get_recommendations() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
# main
#
try:
  print('** Welcome to MusicApp **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # what config file should we use for this session?
  #
  config_file = 'musicapp-client-config.ini'

  print("Config file to use for this session?")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config_file = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]

  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1:
      upload(baseurl, "text")
    elif cmd == 2:
      upload(baseurl, "image")
    elif cmd == 3:
      get_result(baseurl)
    elif cmd == 4:
      get_recommendations(baseurl)
    elif cmd == 5:
      get_playlist(baseurl)
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
