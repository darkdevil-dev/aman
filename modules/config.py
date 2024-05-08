#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) ACE 

import os
from pyrogram import Client

class Config(object):
    # Define your configuration variables here
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    APP_ID = int(os.getenv("APP_ID"))
    API_HASH = os.getenv("API_HASH")
    OWNER_ID = os.getenv("OWNER_ID")
    MONGO_URI = os.getenv("MONGO_URI")
