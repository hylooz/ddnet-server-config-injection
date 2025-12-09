from teeworlds_library_py import Client
import asyncio
import random

profile = {
	"identity": {
		"name": "test",
		"clan": "",
		"country": 0,
		"skin": "default",
		"use_custom_color": 1,
		"color_body": 0,
		"color_feet": 0,
	},
}

client = Client("127.0.0.1", 8303, "test", profile)

@client.on("connected")
def process_connected():
	print("connected!")

@client.on("motd")
def process_motd(data):
	for line in data.split("\\n"):
		print(f"[MOTD] {line}")

@client.on("message")
def process_message(data):
	if data['client_id'] == -1 or data['message'] == 'Do you know someone who uses a bot? Please report them to the moderators.':
		print(f"*** {data['message']}")
	else:
		client_id = data['client_id']
		message = data['message']
		ClientInfo = data['author']['ClientInfo']
		if ClientInfo:
			print(f"[{client_id}]{ClientInfo['name']}: {message}")
		else:
			print(f"[{client_id}]: {message}")
	if data["message"].startswith("*say"):
		client.game.Say(data["message"][5:])

@client.on("broadcast")
def process_broadcast(data):
	print(f"[BROADCAST] {data}")

@client.on("kill")
def process_kill(killmsg):
	print(f"[KILL] {killmsg}")

@client.on("snapshot")
def process_snapshot(data):
	#client.movement.SetAim(random.randint(-400, 400), random.randint(-400, 400))
	pass

@client.on("disconnect")
def process_disconnect(msg):
	print(f"disconnected. reason: {msg}")

async def main():
	await client.connect()
asyncio.run(main())
