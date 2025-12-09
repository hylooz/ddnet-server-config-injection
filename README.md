# Teeworlds Python Client
Incomplete python version of [typescript library](https://github.com/swarfeya/teeworlds-library-ts)
# Usage
Here is a basic usage:
```
from teeworlds_library_py import Client
import asyncio

profile = {
	"identity": {
		"name": "nameless",
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
	if data["message"].startswith("*say"):
		client.game.Say(data["message"][1:])

@client.on("broadcast")
def process_broadcast(data):
	print(f"[BROADCAST] {data}")

@client.on("kill")
def process_kill(killmsg):
	print(f"[KILL] {killmsg}")

@client.on("disconnect")
def process_disconnect(msg):
	print(f"disconnected. reason: {msg}")

	await client.connect()

asyncio.run(main())
```
# Known issues and problems
* snapshot.py: parseItem: "Unknown Type:"
* General: snapshot unpacking for some reason works every other time (up to 5 times per second instead of 25)
* General: high consumption of CPU (~30-50%)
