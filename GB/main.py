import discord
import pymongo
import random
import sys
import json
o = open("config.json", "r")
data = o.read()
config = json.loads(data)
from datetime import timedelta, datetime
from discord_slash import SlashCommand
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import wait_for_component
from discord.ext import commands
client = commands.Bot(command_prefix="gb!")
slash = SlashCommand(client, sync_commands=True)
from Tools.MongoManager import MongoUtils as db
cluster = pymongo.MongoClient(config["MONGODB_URL"], serverSelectionTimeoutMS = 5000)
try:
	print("CONNECTING TO MONGODB CLUSTER...")
	cluster.server_info()
	print("SUCCESFULLY CONNECTED!")
except:
	print("FAILED TO CONNECT")
	sys.exit()
datab = cluster['Galaxy-Brawl']
collection = datab['Players']
bot_col = datab["Logs"]
cool_col = datab["Cooldown"]
guild_ids = config["GUILD_ID"] #this is to make slash commands work in a specific guilds, I used it because they may take more than an hour to be cashed globally
@slash.slash(name="login", guild_ids=guild_ids, description="Login with your Galaxy Brawl account")
async def _login(ctx, token):
	check = await ctx.send("verifying token...")
	args = {"Token": token}
	account = db.load_document(collection, args)
	check_acc_id = {"ID": ctx.author.id}
	check_acc_token = {"Token": token}
	check_id = db.load_document(bot_col, check_acc_id)
	check_token = db.load_document(bot_col, check_acc_token)
	if check_id:
		await ctx.send(f"<@{ctx.author.id}>, you are already logged in.")
		await check.delete()
	elif check_token:
		await ctx.send(f"<@{ctx.author.id}>, account with this token is already logged in.")
		await check.delete()
	elif account:
		acc_name = account["Name"]
		log_args = {"ID": ctx.author.id,
		"Token": token}
		cool_check = {"ID": ctx.author.id}
		cool_args = {"ID": ctx.author.id,
		"DailyTimer": datetime.now()}
		db.insert_data(bot_col, log_args)
		cooldown = db.load_document(cool_col, cool_check)
		if not cooldown:
			db.insert_data(cool_col, cool_args)
		else:
			pass
		await ctx.send(f"<@{ctx.author.id}>, succesfully logged in as `{acc_name}`.")
		await check.delete()
	elif not account:
		await ctx.send(f"<@{ctx.author.id}>, account with the given token was not found.")
		await check.delete()
@slash.slash(name="info", guild_ids=guild_ids, description="Get statistics of your Galaxy Brawl account")
#@client.command()
async def _info(ctx):
	check_acc_id = {"ID": ctx.author.id}
	check_id = db.load_document(bot_col, check_acc_id)
	if not check_id:
		await ctx.send(f"You are not logged in!\nUse the slash command /login to login with your Galaxy Brawl account.")
	else:
		token = check_id["Token"]
		args = {"Token": token}
		data = db.load_document(collection, args)
		name = data["Name"]
		trophies = data["Trophies"]
		gems = data["Gems"]
		gold = data["Resources"][1]["Amount"]
		brawl = data["Resources"][0]["Amount"]
		big = data["Resources"][2]["Amount"]
		list = discord.Embed(description=f"**__Name:__** {name}\n**__Trophies:__** {trophies}\n**__Brawl box tokens:__** {brawl}\n**__Big box tokens:__** {big}\n**__Gems:__** {gems}\n**__Coins:__** {gold}")
		await ctx.send(embed=list)
@slash.slash(name="logout", guild_ids=guild_ids, description="Log out from your Galaxy Brawl account.\nType CONFIRM to log out.")
async def _test(ctx, confirm):
	args = {"ID": ctx.author.id}
	acc = db.load_document(bot_col, args)
	if acc:
		if confirm == "CONFIRM":
			result = await ctx.send("LOGGING OUT...")
			db.delete_document(bot_col, args)
			await result.delete()
			await ctx.send(f"<@{ctx.author.id}>, you have succesfully logged out from your account.")
		else:
			result = await ctx.send("CANCELLING...")
			await result.delete()
			await ctx.send(f"<@{ctx.author.id}>, you have cancelled the request of logging out from your current account.")
	else:
		await ctx.send(f"You are not logged in!\nUse the slash command /login to login with your Galaxy Brawl account.")
@slash.slash(name="daily", guild_ids=guild_ids, description="Get your daily tokens reward")
#@client.command()
async def _daily(ctx):
	check_acc_id = {"ID": ctx.author.id}
	check_id = db.load_document(bot_col, check_acc_id)
	if not check_id:
		await ctx.send(f"You are not logged in!\nUse the slash command /login to login with your Galaxy Brawl account.")
	else:
		cool_args = {"ID": ctx.author.id}
		cooldown = db.load_document(cool_col, cool_args)
		gb = db.load_document(bot_col, check_acc_id)
		args = {"ID": ctx.author.id}
		tok = {"Token": gb["Token"]}
		acc = db.load_document(collection, tok)
		least = int(50)
		max = int(250)
		reward = random.randint(least, max)
		old_tok = acc["Resources"][0]['Amount']
		new_tok = old_tok + reward
		gold = acc["Resources"][1]['Amount']
		big_tok = acc["Resources"][2]['Amount']
		star = acc["Resources"][3]['Amount']
		res_args = [{'ID': 1, 'Amount': new_tok}, {'ID': 8, 'Amount': gold}, {'ID': 9, 'Amount': big_tok}, {'ID': 10, 'Amount': star}]
		wait_time = datetime.now() + timedelta(hours=24)
		if gb:
			if datetime.now() > cooldown["DailyTimer"]:
				await ctx.send(f"<@{ctx.author.id}> have collected {reward} brawl box tokens as there daily reward.")
				db.update_document(collection, tok, "Resources", res_args)
				db.update_document(cool_col, args, "DailyTimer", wait_time)
			else:
				await ctx.send(f"<@{ctx.author.id}>, you are on cooldown.")
print("BOT RUNNING")
client.run(config["BOT_TOKEN"])
