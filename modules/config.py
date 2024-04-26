#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) ACE 

import os
from pyrogram import Client

class Config(object):
    # Define your configuration variables here
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7023286569:AAGI_wWdkZMQuF2K5PSfn-4KDX7fcymbG0I")
    APP_ID = int(os.environ.get("APP_ID", "24055031"))
    API_HASH = os.environ.get("API_HASH", "8421a60ca38e8dbe23feff45edd91688")
    OWNER_ID = "5631563685"
    MONGO_URI = "mongodb+srv://alonebeats:alonebeats@cluster0.vydighs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
