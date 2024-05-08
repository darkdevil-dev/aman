#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) ACE 

import os
from pyrogram import Client

class Config(object):
    # Define your configuration variables here
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    API_ID = int(os.environ.get('APP_ID'))
    API_HASH = os.environ.get('API_HASH')
    OWNER_ID = int(os.environ.get('OWNER_ID'))
    MONGO_URI = os.environ.get('MONGO_URI')
    
    
  
