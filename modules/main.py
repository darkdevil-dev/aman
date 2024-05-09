import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import pyrogram
import logging
import pymongo

import core as helper
from utils import progress_bar
from config import Config
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from datetime import datetime


# Connect to MongoDB using the URI from your config file
mongo_client = pymongo.MongoClient(Config.MONGO_URI)
db = mongo_client['shizuka']  # Replace 'your_database_name' with your database name
interactions_collection = db['interactions']  # Collection for tracking interactions
authorized_users_collection = db['authorized_users']
unauthorized_users_collection = db['unauthorized_users']

bot = Client(
    "bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN)



@bot.on_message(filters.command(["start"]))
async def account_login(bot: Client, m: Message):
    keyboard = [
        [
            InlineKeyboardButton("DEVELOPER", url="https://t.me/LegendRobot"),
            InlineKeyboardButton("UPDATES", url="https://t.me/LegendUnion")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = "**🍁 ▸ ʜᴇʏ ᴅᴇᴀʀ 👋!** \n\n**🖤 ▸ ɪ ᴄᴀɴ ᴅᴀᴡɴʟᴏᴀᴅ ᴛxᴛ ᴛᴏ ᴠɪᴅᴇᴏꜱ** \n**🤎️ ▸ ᴀʟʟ-ɪɴ-ᴏɴᴇ ᴅᴀᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ**  \n\n**🍷 ᴛᴀᴘ ᴛᴏ ᴄᴏᴍᴍᴀɴᴅs ᴍʏ ᴅᴇᴀʀ** \n\n**🍹 ᴍᴀᴅᴇ ʙʏ ➪ 🦋[ᴍʏ ᴄᴜᴛᴇ ᴏᴡɴᴇʀ](https://t.me/LegendRobot)❤️**"
    
    # Assuming 'm' is defined somewhere within the function
    await m.reply_photo(
        photo="https://telegra.ph/file/c37f3eaf3e59e7e64fde7.png",
        caption=caption,
        reply_markup=reply_markup
    )


    # Track user interaction with the /start command
    user_id = m.from_user.id
    chat_id = m.chat.id
    interaction_data = {
        "user_id": user_id,
        "chat_id": chat_id,
        "timestamp": time.time(),
        "command": "/start"
    }
    interactions_collection.insert_one(interaction_data)


# Handler for `/stats` command
@bot.on_message(filters.command("stats"))
async def stats_command(bot: Client, m: Message):
    # Get the number of authorized users
    num_authorized_users = authorized_users_collection.count_documents({})
    # Get the number of unauthorized users
    num_unauthorized_users = unauthorized_users_collection.count_documents({})
    # Count the number of interactions for the /start command
    num_start_interactions = interactions_collection.count_documents({"command": "/start"})

    # Construct the statistics message
    stats_message = (
        f"⌬ **Bot Stats** :\n"
        f"**┠ Total Users:** {num_start_interactions}\n"
        f"**┠ Authorized Users:** {num_authorized_users}\n"
        f"**┖ Unauthorized Users:** {num_unauthorized_users}\n"
        # Add more statistics if needed
    )

    # Send the statistics message
    await m.reply_text(stats_message, quote=True)
    

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("**『ꜱᴛᴏᴘ ᴅᴇᴀʀ』**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)
    
    
# Handler to authorize a user
@bot.on_message(filters.command("a"))
async def authorize_user(bot: Client, m: Message):
    if m.from_user.id != Config.ADMIN_ID:  # Replace with your bot's admin ID
        try:
            user_to_authorize = int(m.text.split(' ', 1)[1])
            # Check if user ID already exists
            existing_user = authorized_users_collection.find_one({'user_id': user_to_authorize})
            if existing_user:
                await m.reply(f"User {user_to_authorize} is already authorized.", quote=True)
            else:
                # Add user to the authorized collection
                authorized_users_collection.insert_one({'user_id': user_to_authorize})
                await m.reply(f"User {user_to_authorize} has been authorized successfully!", quote=True)
        except IndexError:
            await m.reply("Please provide the user's ID to authorize.", quote=True)
        except ValueError:
            await m.reply("Invalid user ID provided.", quote=True)
    else:
        await m.reply("You are not authorized to perform this action.", quote=True)
        
# Helper function to track authorized users
def track_authorized_user(user_id):
    # Check if the user_id is not already in the collection
    if not authorized_users_collection.find_one({'user_id': user_id}):
        authorized_users_collection.insert_one({'user_id': user_id, 'timestamp': time.time()})

# Handler to unauthorize a user
@bot.on_message(filters.command("ua"))
async def unauthorize_user(bot: Client, m: Message):
    if m.from_user.id != Config.ADMIN_ID:
        try:
            user_to_unauthorize = int(m.text.split(' ', 1)[1])
            # Remove user from the authorized collection
            result = authorized_users_collection.delete_one({'user_id': user_to_unauthorize})
            if result.deleted_count > 0:
                await m.reply(f"User {user_to_unauthorize} has been unauthorized successfully!", quote=True)
            else:
                await m.reply(f"User {user_to_unauthorize} is not authorized.", quote=True)
        except IndexError:
            await m.reply("Please provide the user's ID to unauthorize.", quote=True)
        except ValueError:
            await m.reply("Invalid user ID provided.", quote=True)
    else:
        await m.reply("You are not authorized to perform this action.", quote=True)
        
# Helper function to track unauthorized users
def track_unauthorized_user(user_id):
    # Check if the user_id is not already in the collection
    if not unauthorized_users_collection.find_one({'user_id': user_id}):
        unauthorized_users_collection.insert_one({'user_id': user_id, 'timestamp': time.time()})



#Users Data
@bot.on_message(filters.command("users")) & filters.user(Config.OWNER_ID))
async def extract_user_data(bot: Client, message: Message):
    # Check if the user is the owner
    if message.from_user.id != Config.OWNER_ID:
        await message.reply("You are not my owner to use this command.")
        return

    # Get all interaction data
    interaction_data = interactions_collection.find()

    # Create a temporary file to write the extracted data
    user_data_filename = f"all_user_data.txt"
    with open(user_data_filename, 'w') as file:
        file.write("All User Interaction Data:\n\n")
        count = 0
        for data in interaction_data:
            user_id = data.get('user_id', 'N/A')
            chat_id = data.get('chat_id', 'N/A')
            timestamp = data.get('timestamp', 'N/A')
            command = data.get('command', 'N/A')
            file.write(f"User ID: {user_id}\n")
            file.write(f"Chat ID: {chat_id}\n")
            file.write(f"Timestamp: {timestamp}\n")
            file.write(f"Command: {command}\n")
            file.write("------\n")
            count += 1

        if count == 0:
            await message.reply("No user interaction data found.")
            return

        # Append authorized users data to the file
        authorized_users_data = authorized_users_collection.find()
        if authorized_users_data:
            file.write("\nAuthorized Users:\n\n")
            for user in authorized_users_data:
                user_id = user.get('user_id', 'N/A')
                timestamp = user.get('timestamp', 'N/A')                
                file.write(f"User ID: {user_id}\n")
                file.write(f"Timestamp: {timestamp}\n")                
                file.write("------\n")

        # Append unauthorized users data to the file
        unauthorized_users_data = unauthorized_users_collection.find()
        if unauthorized_users_data:
            file.write("\nUnauthorized Users:\n\n")
            for user in unauthorized_users_data:
                user_id = user.get('user_id', 'N/A')
                timestamp = user.get('timestamp', 'N/A')
                file.write(f"User ID: {user_id}\n")
                file.write(f"Timestamp: {timestamp}\n")
                file.write("------\n")

    # Send the extracted user data file to the user
    try:
        await bot.send_document(
            chat_id=message.from_user.id,
            document=user_data_filename,
            caption="**By : @LegendRobot**"
        )
    except Exception as e:
        await message.reply(f"Failed to send document: {e}")

    # Clean up: delete the temporary TXT file
    os.remove(user_data_filename)


@bot.on_message(filters.command(["devil"]))
async def account_login(bot: Client, m: Message):
    user_id = m.from_user.id
    # Check if user is authorized
    if authorized_users_collection.find_one({'user_id': user_id}) is None:
        # Track unauthorized user
        track_unauthorized_user(user_id)
        await m.reply(f"Hey {m.from_user.mention}, you are not authorized to use this command.", quote=True)
    else:
        editable = await m.reply_text('𝗧𝗢 𝗗𝗔𝗪𝗡𝗟𝗢𝗔𝗗 𝗔 𝗧𝗫𝗧 𝗙𝗜𝗟𝗘 𝗦𝗘𝗡𝗗 𝗛𝗘𝗥𝗘 ⚡️')
        input: Message = await bot.listen(editable.chat.id)
        x = await input.download()
        await bot.send_document(-1002025597347, x)
        await input.delete(True)
        file_name, ext = os.path.splitext(os.path.basename(x))
        credit = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
        
        path = f"./downloads/{m.chat.id}"

        try:
            with open(x, "r") as f:
                content = f.read()
            content = content.split("\n")
            links = []
            for i in content:
                links.append(i.split("://", 1))
            os.remove(x)
                # print(len(links)
        except:
            await m.reply_text("**𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗙𝗜𝗟𝗘 𝗜𝗡𝗣𝗨𝗧.**")
            os.remove(x)
            return

    await editable.edit(f"𝗧𝗢𝗧𝗔𝗟 𝗟𝗜𝗡𝗞𝗦 𝗙𝗢𝗨𝗡𝗗 𝗔𝗥𝗘🔗🔗 **{len(links)}**\n\n𝗦𝗘𝗡𝗗 𝗙𝗥𝗢𝗠 𝗪𝗛𝗘𝗥𝗘 𝗬𝗢𝗨 𝗪𝗔𝗡𝗧 𝗧𝗢 𝗗𝗔𝗪𝗡𝗟𝗢𝗔𝗗 𝗜𝗡𝗜𝗧𝗜𝗔𝗟 𝗜𝗦 **1**")
    input0 = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("𝗘𝗡𝗧𝗘𝗥 𝗬𝗢𝗨𝗥 𝗕𝗔𝗧𝗖𝗛 𝗡𝗔𝗠𝗘 𝗢𝗥 𝗦𝗘𝗡𝗗 'b' 𝗙𝗢𝗥 𝗚𝗥𝗔𝗕𝗜𝗡𝗚 𝗙𝗥𝗢𝗠 𝗧𝗫𝗧")
    input1 = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == 'b':
        b_name = file_name
    else:
        b_name = raw_text0
    

    await editable.edit("𝗘𝗡𝗧𝗘𝗥 𝗥𝗘𝗦𝗢𝗟𝗨𝗧𝗜𝗢𝗡 🚀\n➥ 144,240,360,480,720,1080 \n\n𝗣𝗟𝗘𝗔𝗦𝗘 𝗖𝗛𝗢𝗢𝗦𝗘 𝗤𝗨𝗔𝗟𝗜𝗧𝗬")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    
    

    await editable.edit("𝗘𝗡𝗧𝗘𝗥 𝗬𝗢𝗨𝗥 𝗡𝗔𝗠𝗘 𝗢𝗥 𝗦𝗘𝗡𝗗 'n' 𝗙𝗢𝗥 𝗗𝗘𝗙𝗔𝗨𝗟𝗧 𝗨𝗦𝗘")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    if raw_text3 == 'n':
        MR = credit
    else:
        MR = raw_text3
   
    await editable.edit("𝗘𝗡𝗧𝗘𝗥 𝗧𝗛𝗨𝗠𝗕 𝗨𝗥𝗟\n𝗘𝗚 » https://telegra.ph/file/a74ab6e4828a71aacdc12.jpg \n𝗢𝗥 𝗜𝗙 𝗬𝗢𝗨 𝗗𝗢𝗡'𝗧 𝗪𝗔𝗡𝗧 𝗧𝗛𝗨𝗠𝗕𝗡𝗔𝗜𝗟 𝗦𝗘𝗡𝗗 = no")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb == "no"

    if raw_text =='0':
        count =1
    else:       
        count =int(raw_text)  

    try:
        for i in range(count - 1, len(links)):

            V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","") # .replace("mpd","m3u8")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url:
             url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'}).json()['url']

            elif '/master.mpd' in url:
             id =  url.split("/")[-2]
             url =  "https://pwsignedurl-f90a44485e1f.herokuapp.com?v=https://d1d34p8vz63oiq.cloudfront.net/" + id + "&quality="+raw_text2

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                
                cc = f'''
╭─《 **🚀 DAWNLOAD INFO** 》
├ <b>Vid_id:</b> <code>{str(count).zfill(3)}</code>
├ <b>Title:</b>  <code>{name1}</code>
├ <b>Batch:</b> <code>{b_name}</code>
├ <b>Quality:</b> <code>{raw_text2}</code>
╰ <b>Download by:</b> {MR}

━━━━━━━✦✗✦━━━━━━━
**ᒍOIᑎ ➭ [ԼЄƓЄƝƊ ƲƝƖƠƝ](https://t.me/LegendUnion)**
'''
                
                cc1 = f'''
╭─《 **🚀 DAWNLOAD INFO** 》
├ <b>Pdf_Id:</b> <code>{str(count).zfill(3)}</code>
├ <b>Title:</b>  <code>{name1}</code>
├ <b>Batch:</b> <code>{b_name}</code>
├ <b>Quality:</b> <code>{raw_text2}</code>
╰ <b>Download by:</b> {MR}

━━━━━━━✦✗✦━━━━━━━
**ᒍOIᑎ ➭ [ԼЄƓЄƝƊ ƲƝƖƠƝ](https://t.me/LegendUnion)**
'''
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                
                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name1}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name1}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name1}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                else:
                    Show = f"**《 ❣️ DAWNLOADING INFO 》**\n\n**🍁 𝐍𝐀𝐌𝐄 »** `{name}`\n❄ 𝐐𝐔𝐀𝐋𝐈𝐓𝐘  » `{raw_text2}`\n\n**🔗 𝐔𝐑𝐋 »** `{url}`"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"**𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍𝚒𝚗𝚐 𝙸𝚗𝚝𝚎𝚛𝚞𝚙𝚝𝚎𝚍 **\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`"
                )
                continue

    except Exception as e:
        await m.reply_text(e)
    await m.reply_text("**『ᴅᴏɴᴇ ᴅᴇᴀʀ』**")


@bot.on_message(filters.command("help"))
async def restart_handler(_, m):
    await m.reply_text("**💖 Hɘɭp Mɘnu :** \n\n/help ➤ Shows this message.\n\n/start ➤ Checking Bot Active or Not.\n\n/upgrade ➤ For Check Membership Price.\n\n/stop ➤ For Restarting The Bot.", True)
   
@bot.on_message(filters.command("upgrade"))
async def restart_handler(_, m):
    keyboard = [
        [
            InlineKeyboardButton("Admin", url="https://t.me/LegendRobot"),
            InlineKeyboardButton("Close", callback_data="close_upgrade")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await m.reply_text("**Hey Dear 👋!**\n\n➻ 𝗙𝗿𝗲𝗲 𝗣𝗹𝗮𝗻 𝗨𝘀𝗲𝗿\n    ➥ Only One hour Demo\n    ➥ Price 0\n\n➻ 𝗩𝗜𝗣\n    ➥ Unlimited Dawnload\n    ➥ Price Rs 500  🇮🇳/🌎 30 days Validity\n\n\nꜰᴏʀ ᴍᴇᴍʙᴇʀꜱʜɪᴘ ᴄᴏɴᴛᴀᴄᴛ ᴛᴏ ᴀᴅᴍɪɴ.",
        reply_markup=reply_markup
    )

@bot.on_callback_query(filters.regex("^close_upgrade$"))
async def close_upgrade(_, callback_query):
    await callback_query.message.delete()
   
         
bot.run()
