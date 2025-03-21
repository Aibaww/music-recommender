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
