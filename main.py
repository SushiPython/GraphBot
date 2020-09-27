import discord
from discord.ext import commands
import motor.motor_asyncio
import os
import time
import datetime
from flask import Flask, render_template
from threading import Thread
import pymongo
from pymongo import MongoClient

dbPass=os.getenv('dbPass')
token=os.getenv('token')

fp = open('pfp.png', 'rb')
pfp = fp.read()

motorClientData = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb+srv://dbUser:{dbPass}@cluster0-q9qdn.mongodb.net/test?retryWrites=true&w=majority', 27017)

mgclnt = pymongo.MongoClient(f'mongodb+srv://dbUser:{dbPass}@cluster0-q9qdn.mongodb.net/test?retryWrites=true&w=majority', 27017)

dbmg = mgclnt['main-db']
collmg = dbmg['main-collection']

db=motorClientData['main-db']
collection=db['main-collection']

bot = commands.Bot(command_prefix='g?')
app = Flask(__name__)

@app.route('/')
def main():
  return ''' 
<!DOCTYPE HTML> 
<html lang="en">
<head> 
<meta http-equiv="content-type" content="text/html; charset=utf-8"> 
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/kognise/water.css@latest/dist/dark.min.css">
<title>GraphBot</title> 
</head> 

<body>
  <center>
  <h1>GraphBot</h1>
  <p>
    A member count graphing bot developed by Sushi#4347.
  </p> 
  <button onClick="location = 'https://discord.com/api/oauth2/authorize?client_id=706719475067781160&permissions=8&scope=bot'">Invite to Server</button>
  </center>
</body> 

</html>
'''

@app.route("/<uid>/<name>")
def chart(uid, name):
  print(uid)
  dict = collmg.find_one({'guildId': int(uid)})
  print(dict)
  values = list(dict.values())[2:]
  print(values)
  labels = list(dict.keys())[2:]
  print(labels)
  legend = 'Member Count'
  name = name.replace('_', ' ')
  return render_template('chart.html', values=values, labels=labels, legend=legend, name=name)

@bot.command()
async def serverId(ctx):
  await ctx.send(ctx.guild.id)
  
@bot.command()
async def serverCount(ctx):
  x = 0
  for i in bot.guilds:
    x += 1
    print(i)
  await ctx.send(x)

@bot.command()
async def dictData(ctx):
  guildId = ctx.guild.id
  async for motorDict in collection.find({'guildId': guildId}):
    await ctx.send(motorDict)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="g?help | Developed by Sushi#4347"))
    await bot.user.edit(avatar=pfp)
    print(f'{bot.user.name} has connected to Discord!')
    

@bot.command()
async def amt(ctx):
  await ctx.send(ctx.guild.member_count)

@bot.command()
async def log(ctx):
  if ctx.message.author.guild_permissions.administrator or (str(ctx.author.id)=='614577566228938817'):
    uc=(ctx.guild.member_count)
    gn=(ctx.guild.name)
    gi=(ctx.guild.id)
    x = datetime.datetime.now()
    date=(x.strftime("%x"))
    await collection.insert_one({
      'guildId': gi,
      date: uc
    })
    await ctx.send('Started logging.')
  else:
    await ctx.send('You dont have perms!')

@bot.command()
async def members(ctx, date):
  async for mongoDict in collection.find({'guildId': ctx.guild.id}):
    await ctx.send(mongoDict[ctx])

@bot.command()
async def getId(ctx):
  await ctx.send(ctx.author.id)

@bot.command()
async def graph(ctx):
  id = ctx.guild.id
  name = ctx.guild.name
  name = name.replace(' ', '_')
  await ctx.send(f'Your graph can be found at https://graphbot.sushipython.repl.co/{id}/{name}')

@bot.command()
async def update(ctx):
  uc=(ctx.guild.member_count)
  gn=(ctx.guild.name)
  gi=(ctx.guild.id)
  x = datetime.datetime.now()
  date=(x.strftime("%x"))
  if ctx.message.author.guild_permissions.administrator or (str(ctx.author.id)=='614577566228938817'):
    await collection.update_one(
      {
        'guildId': gi,
      }, {
        '$set': {
          date: uc
        }
      },
      upsert=True
    )
    print(f'{ctx.author.name} updated user count for server {gn} with user count {uc} and ID of {gi}')
    await ctx.send('Member count updated for today.')
  else:
    await ctx.send('You must be an administrator to run this command.')
    print(f'{ctx.author.name} was unable to update server {gn} because they lack perms.')

@bot.command()
async def listData(ctx):
  async for dict in collection.find({'guildId': ctx.guild.id}):
    dates = list(dict.values())[2:]
    userCounts = list(dict.keys())[2:]

    await ctx.send(dates)
    await ctx.send(userCounts)
    await ctx.send('Done.')

@app.route('/update')
def updateDatabase():
  x = datetime.datetime.now()
  date=(x.strftime("%x"))
  for i in bot.guilds:
    collmg.update_one(
      {
        'guildId': i.id, 
      }, {
        '$set': {
          date: i.member_count
        }
      },
      upsert=True
    )
    print(f'Automatically updated user count for server {i.name} with user count {i.member_count} and ID of {i.id}')
  return 'Database updated!'



def start_bot():
  app.run(host="0.0.0.0",port="8000")
Thread(None, start_bot).start()
bot.run(token)
