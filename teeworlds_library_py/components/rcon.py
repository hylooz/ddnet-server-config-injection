import asyncio
import re
import socket
import time
from ..protocol import NETMSG
from ..msg import MsgUnpacker, MsgPacker, unpackString, unpackInt

class Rcon:
	CommandList = []

	def __init__(self, _client: "Client"):
		super().__init__()
		self._client = _client

	def auth(self, password, username = "") -> None:
		self._auth(username, password)

	def _auth(self, usernameOrPassword, password = None) -> None:
		if password is None:
			Username = ""
			Password = usernameOrPassword
		else:
			Username = usernameOrPassword
			Password = password
		rconAuthMsg = MsgPacker(NETMSG.System.NETMSG_RCON_AUTH, True, 1)
		rconAuthMsg.AddString(Username)
		rconAuthMsg.AddString(Password)
		rconAuthMsg.AddInt(1)
		self._send(rconAuthMsg)

	def rcon(self, cmds) -> None:
		_cmds: List[str]
		if isinstance(cmds, list):
			_cmds = cmds
		else:
			_cmds = [cmds]
		msgs = []
		for cmd in _cmds:
			rconCmdMsg = MsgPacker(NETMSG.System.NETMSG_RCON_CMD, True, 1)
			rconCmdMsg.AddString(cmd)
			msgs.append(rconCmdMsg)
		self._send(msgs)

	def _send(self, packer) -> None:
		if not self._client.options.get("lightweight"):
			self._client.QueueChunkEx(packer)
		else:
			self._client.SendMsgEx(packer)

	def _checkChunks(self, chunk) -> bool:
		if chunk["msgid"] == NETMSG.System.NETMSG_RCON_LINE:
			unpacker = MsgUnpacker(chunk["raw"])
			msg = unpacker.unpackString()
			self._client.emit('rcon_line', msg)
		elif chunk["msgid"] == NETMSG.System.NETMSG_RCON_AUTH_STATUS:
			unpacker = MsgUnpacker(chunk["raw"])
			AuthLevel = unpacker.unpackInt()
			ReceiveCommands = unpacker.unpackInt()
			self._client.emit('rcon_auth_status', {"AuthLevel": AuthLevel, "ReceiveCommands": ReceiveCommands})
		elif chunk["msgid"] == NETMSG.System.NETMSG_RCON_CMD_ADD:
			unpacker = MsgUnpacker(chunk["raw"])
			command = unpacker.unpackString()
			description = unpacker.unpackString()
			params = unpacker.unpackString()

			self.CommandList.append({"command": command, "description": description, "params": params})
			self._client.emit('rcon_cmd_add', {"command": command, "description": description, "params": params})
		elif chunk["msgid"] == NETMSG.System.NETMSG_RCON_CMD_REM:
			unpacker = MsgUnpacker(chunk["raw"])
			command = unpacker.unpackString()
			self._client.emit('rcon_cmd_rem', {"command": command})

			index = next((i for i, a in enumerate(self.CommandList) if a["command"] == command), -1)
			if index >= 0:
				self.CommandList.pop(index)
		else:
			return False
		return True
