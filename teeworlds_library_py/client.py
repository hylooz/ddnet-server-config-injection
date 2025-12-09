from .huffman import Huffman
from .protocol import States, NETMSG, SnapshotItemIDs
from .UUIDManager import UUIDManager
from .snapshot import Snapshot
from .components import Game
from .components import Movement
from .components import Rcon
from .components import SnapshotWrapper
from .msg import MsgPacker, MsgUnpacker, unpackString, unpackInt
import threading
import asyncio
import inspect
import signal
import socket
import struct
import zlib
import uuid
import time
import sys
import re

huff = Huffman()

messageTypes = [
	["none, starts at 1", "SV_MOTD", "SV_BROADCAST", "SV_CHAT", "SV_KILL_MSG", "SV_SOUND_GLOBAL", "SV_TUNE_PARAMS", "SV_EXTRA_PROJECTILE", "SV_READY_TO_ENTER", "SV_WEAPON_PICKUP", "SV_EMOTICON", "SV_VOTE_CLEAR_OPTIONS", "SV_VOTE_OPTION_LIST_ADD", "SV_VOTE_OPTION_ADD", "SV_VOTE_OPTION_REMOVE", "SV_VOTE_SET", "SV_VOTE_STATUS", "CL_SAY", "CL_SET_TEAM", "CL_SET_SPECTATOR_MODE", "CL_START_INFO", "CL_CHANGE_INFO", "CL_KILL", "CL_EMOTICON", "CL_VOTE", "CL_CALL_VOTE", "CL_IS_DDNET", "SV_DDRACE_TIME", "SV_RECORD", "UNUSED", "SV_TEAMS_STATE", "CL_SHOW_OTHERS_LEGACY", "SV_DDRACE_TIME"],
	["none, starts at 1", "INFO", "MAP_CHANGE", "MAP_DATA", "CON_READY", "SNAP", "SNAP_EMPTY", "SNAP_SINGLE", "INPUT_TIMING", "RCON_AUTH_STATUS", "RCON_LINE", "READY", "ENTER_GAME", "INPUT", "RCON_CMD", "RCON_AUTH", "REQUEST_MAP_DATA", "PING", "PING_REPLY", "RCON_CMD_ADD", "RCON_CMD_REMOVE"]
]
#[
	#["none, starts at 1", "SV_MOTD", "SV_BROADCAST", "SV_CHAT", "SV_KILL_MSG", "SV_SOUND_GLOBAL", "SV_TUNE_PARAMS", "SV_EXTRA_PROJECTILE", "SV_READY_TO_ENTER", "SV_WEAPON_PICKUP", "SV_EMOTICON", "SV_VOTE_CLEAR_OPTIONS", "SV_VOTE_OPTION_LIST_ADD", "SV_VOTE_OPTION_ADD", "SV_VOTE_OPTION_REMOVE", "SV_VOTE_SET", "SV_VOTE_STATUS", "CL_SAY", "CL_SET_TEAM", "CL_SET_SPECTATOR_MODE", "CL_START_INFO", "CL_CHANGE_INFO", "CL_KILL", "CL_EMOTICON", "CL_VOTE", "CL_CALL_VOTE", "CL_IS_DDNET", "SV_DDRACE_TIME", "SV_RECORD", "UNUSED", "SV_TEAMS_STATE", "CL_SHOW_OTHERS_LEGACY"],
	#["none, starts at 1", "INFO", "MAP_CHANGE", "MAP_DATA", "CON_READY", "SNAP", "SNAP_EMPTY", "SNAP_SINGLE", "SNAPSMALL", "INPUT_TIMING", "RCON_AUTH_STATUS", "RCON_LINE", "AUTH_CHALLANGE", "AUTH_RESULT", "READY", "ENTER_GAME", "INPUT", "RCON_CMD", "RCON_AUTH", "REQUEST_MAP_DATA", "AUTH_START", "AUTH_RESPONSE", "PING", "PING_REPLY", "ERROR", "RCON_CMD_ADD", "RCON_CMD_REMOVE"]
#]


libVersion = "1.0"

class Client:
	rcon = None
	host = None
	port = None
	name = None
	State = None # 0 = offline; 1 = STATE_CONNECTING = 1, STATE_LOADING = 2, STATE_ONLINE = 3
	ack = None
	clientAck = None
	lastCheckedChunkAck = None
	receivedSnaps = None # wait for 2 ss before seeing self as connected
	socket = None
	TKEN = bytes()
	time = None
	SnapUnpacker = None

	SnapshotUnpacker = None

	PredGameTick = None
	AckGameTick = None

	SnapshotParts = None
	currentSnapshotGameTick = None

	snaps = bytes()

	sentChunkQueue = bytes()
	queueChunkEx = bytes()
	lastSendTime = None
	lastRecvTime = None

	lastSentMessages = []

	VoteList = None

	options = None
	requestResend = False;

	UUIDManager = None;

	def __init__(self, ip, port, nickname, options = None):
		self.host = ip;
		self.port = port;
		self.name = nickname;
		self.AckGameTick = 0;
		self.PredGameTick = 0;
		self.currentSnapshotGameTick = 0;

		self.SnapshotParts = 0;
		self.rcon = Rcon(self);
		self.SnapUnpacker = Snapshot(self);
		self.requestResend = False;

		self.VoteList = [];

		if(options):
			self.options = options;
		else:
			self.options = {}

		self.snaps = [];

		self.sentChunkQueue = [];
		self.queueChunkEx = [];

		self.State = States.STATE_OFFLINE; # 0 = offline; 1 = STATE_CONNECTING = 1, STATE_LOADING = 2, STATE_ONLINE = 3
		self.ack = 0; # ack of messages the client has received
		self.clientAck = 0; # ack of messages the client has sent
		self.lastCheckedChunkAck = 0; # this.ack gets reset to this when flushing - used for resetting tick on e.g. map change
		self.receivedSnaps = 0; # wait for 2 snaps before seeing self as connected

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(('0.0.0.0', 0))
		self.sock.setblocking(False)

		self.recieving = True

		self.TKEN = bytes([255, 255, 255, 255])
		self.time = time.time() + 2; # time (used for keepalives, start to send keepalives after 2 seconds)
		self.lastSendTime = time.time()
		self.lastRecvTime = time.time()

		self.last_pred = 0
		self.last_connect = 0
		self.last_input = 0
		self.last_resend = 0
		self.last_timeout = 0

		self.is_pred = True
		self.is_connecting = True
		self.is_input = True
		self.is_resending = True

		self.lastSentMessages = [];

		self.movement = Movement();

		self.game = Game(self);
		self.SnapshotUnpacker = SnapshotWrapper(self);

		self.UUIDManager = UUIDManager();

		self.UUIDManager.RegisterName("what-is@ddnet.tw", NETMSG.System.NETMSG_WHATIS);
		self.UUIDManager.RegisterName("it-is@ddnet.tw", NETMSG.System.NETMSG_ITIS);
		self.UUIDManager.RegisterName("i-dont-know@ddnet.tw", NETMSG.System.NETMSG_IDONTKNOW);

		self.UUIDManager.RegisterName("rcon-type@ddnet.tw", NETMSG.System.NETMSG_RCONTYPE);
		self.UUIDManager.RegisterName("map-details@ddnet.tw", NETMSG.System.NETMSG_MAP_DETAILS);
		self.UUIDManager.RegisterName("capabilities@ddnet.tw", NETMSG.System.NETMSG_CAPABILITIES);
		self.UUIDManager.RegisterName("clientver@ddnet.tw", NETMSG.System.NETMSG_CLIENTVER);
		self.UUIDManager.RegisterName("ping@ddnet.tw", NETMSG.System.NETMSG_PING);
		self.UUIDManager.RegisterName("pong@ddnet.tw", NETMSG.System.NETMSG_PONGEX);
		self.UUIDManager.RegisterName("checksum-request@ddnet.tw", NETMSG.System.NETMSG_CHECKSUM_REQUEST);
		self.UUIDManager.RegisterName("checksum-response@ddnet.tw", NETMSG.System.NETMSG_CHECKSUM_RESPONSE);
		self.UUIDManager.RegisterName("checksum-error@ddnet.tw", NETMSG.System.NETMSG_CHECKSUM_ERROR);
		self.UUIDManager.RegisterName("redirect@ddnet.org", NETMSG.System.NETMSG_REDIRECT);


		self.UUIDManager.RegisterName("rcon-cmd-group-start@ddnet.org", NETMSG.System.NETMSG_RCON_CMD_GROUP_START) # not implemented
		self.UUIDManager.RegisterName("rcon-cmd-group-end@ddnet.org", NETMSG.System.NETMSG_RCON_CMD_GROUP_END) # not implemented
		self.UUIDManager.RegisterName("map-reload@ddnet.org", NETMSG.System.NETMSG_MAP_RELOAD) # not implemented
		self.UUIDManager.RegisterName("reconnect@ddnet.org", NETMSG.System.NETMSG_RECONNECT) # implemented
		self.UUIDManager.RegisterName("sv-maplist-add@ddnet.org", NETMSG.System.NETMSG_MAPLIST_ADD) # not implemented
		self.UUIDManager.RegisterName("sv-maplist-start@ddnet.org", NETMSG.System.NETMSG_MAPLIST_GROUP_START) # not implemented
		self.UUIDManager.RegisterName("sv-maplist-end@ddnet.org", NETMSG.System.NETMSG_MAPLIST_GROUP_END) # not implemented

		self.UUIDManager.RegisterName("i-am-npm-package@swarfey.gitlab.io", NETMSG.System.NETMSG_I_AM_NPM_PACKAGE);

		self.handlers = {}

	def OnEnterGame(self):
		self.snaps = {};
		self.SnapUnpacker = Snapshot(self);
		self.SnapshotParts = 0;
		self.receivedSnaps = 0;
		self.SnapshotUnpacker = SnapshotWrapper(self);
		self.currentSnapshotGameTick = 0;
		self.AckGameTick = -1;
		self.PredGameTick = 0;

	def ResendAfter(self, lastAck):
		self.clientAck = lastAck;

		toResend = []
		for msg in self.lastSentMessages:
			if msg["ack"] > lastAck:
				toResend.append(msg["msg"])
		for a in toResend:
			a.flag = 1 | 2
		self.SendMsgEx(toResend);

	def Unpack(self, packet):
		unpacked = {"twprotocol": {"flags": packet[0] >> 4, "ack": ((packet[0] & 0xf) << 8) | packet[1], "chunkAmount": packet[2], "size": len(packet) - 3}, "chunks": []}

		if packet[:4] == b'\xff\xff\xff\xff':
			return unpacked

		if unpacked["twprotocol"]["flags"] & 4:
			self.ResendAfter(unpacked["twprotocol"]["ack"])

		packet = packet[3:]

		if unpacked["twprotocol"]["flags"] & 8 and not (unpacked["twprotocol"]["flags"] & 1):
			try:
				packet = huff.decompress(packet)
				if not isinstance(packet, bytes):
					return unpacked
			except:
				return unpacked
			if len(packet) == 1 and packet[0] == -1:
				return unpacked

		for i in range(unpacked["twprotocol"]["chunkAmount"]):
			chunk = {}
			chunk["bytes"] = ((packet[0] & 0x3f) << 4) | (packet[1] & ((1 << 4) - 1))
			chunk["flags"] = (packet[0] >> 6) & 3

			if chunk["flags"] & 1:
				chunk["seq"] = ((packet[1] & 0xf0) << 2) | packet[2]
				packet = packet[3:]
			else:
				packet = packet[2:]

			chunk["sys"] = bool(packet[0] & 1)
			chunk["msgid"] = (packet[0] - (packet[0] & 1)) // 2
			try:
				chunk["msg"] = messageTypes[packet[0] & 1][chunk["msgid"]]
			except IndexError as e:
				chunk["msg"] = None
			chunk["raw"] = packet[1:chunk["bytes"]+1]
			if chunk["msgid"] == 0 and len(chunk["raw"]) >= 16:
				_uuid = self.UUIDManager.LookupUUID(chunk["raw"][:16])
				if _uuid is not None:
					chunk["extended_msgid"] = _uuid["hash"]
					chunk["msg"] = _uuid["name"]
					chunk["raw"] = chunk["raw"][16:]
					chunk["msgid"] = _uuid["type_id"]

			packet = packet[chunk["bytes"]:]
			unpacked["chunks"].append(chunk)

		return unpacked

	def SendControlMsg(self, msg, ExtraMsg = ""):
		self.lastSendTime = time.time()
		if self.sock:
			latestBuf = bytes([0x10 + (((16 << 4) & 0xf0) | ((self.ack >> 8) & 0xf)), self.ack & 0xff, 0x00, msg])
			latestBuf = b''.join([latestBuf, ExtraMsg.encode("utf-8"), self.TKEN])
			self.sock.sendto(latestBuf, (self.host, self.port))

	def SendMsgEx(self, Msgs, flags = 0):
		if self.State == States.STATE_OFFLINE:
			return
		if not self.sock:
			return

		if isinstance(Msgs, list):
			_Msgs = Msgs
		else:
			_Msgs = [Msgs]

		if len(self.queueChunkEx) > 0:
			_Msgs.extend(self.queueChunkEx)
			self.queueChunkEx = []

		self.lastSendTime = time.time()
		header = []
		if self.clientAck == 0:
			self.lastSentMessages = []

		for index, Msg in enumerate(_Msgs):
			header.append(bytearray((3 if (Msg.flag & 1) else 2)))
			header[index][0] = ((Msg.flag & 3) << 6) | ((Msg.size >> 4) & 0x3f)
			header[index][1] = (Msg.size & 0xf)

			if Msg.flag & 1:
				self.clientAck = (self.clientAck + 1) % (1 << 10)
				if self.clientAck == 0:
					self.lastSentMessages = []
				header[index][1] |= (self.clientAck >> 2) & 0xf0
				header[index][2] = self.clientAck & 0xff
				header[index][0] = (((Msg.flag | 2) & 3) << 6) | ((Msg.size >> 4) & 0x3f)  # 2 is resend flag (ugly hack for queue)
				if (Msg.flag & 2) == 0:
					self.sentChunkQueue.append(b''.join([bytes(header[index]), Msg.buffer]))
				header[index][0] = (((Msg.flag) & 3) << 6) | ((Msg.size >> 4) & 0x3f)
				if (Msg.flag & 2) == 0:
					self.lastSentMessages.append({"msg": Msg, "ack": self.clientAck})

		if self.requestResend:
			flags |= 4

		packetHeader = bytearray([((flags << 4) & 0xf0) | ((self.ack >> 8) & 0xf), self.ack & 0xff, len(_Msgs)])
		chunks = bytearray()
		skip = False

		for index, Msg in enumerate(_Msgs):
			if skip:
				continue
			if len(chunks) < 1300:
				chunks = bytearray(b''.join([bytes(chunks), bytes(header[index]), Msg.buffer]))
			else:
				skip = True
				self.SendMsgEx(_Msgs[index:])

		packet = b''.join([bytes(packetHeader), bytes(chunks), self.TKEN])
		if len(chunks) < 0:
			return

		self.sock.sendto(packet, (self.host, self.port))


	def QueueChunkEx(self, Msg):
		if isinstance(Msg, list):
			for chunk in Msg:
				self.QueueChunkEx(chunk)
			return
		if len(self.queueChunkEx) > 0:
			total_size = 0
			for chunk in self.queueChunkEx:
				total_size += chunk.size
			if total_size + Msg.size + 3 > 1394 - 4:
				self.Flush()
		self.queueChunkEx.append(Msg)
		if Msg.flag & 4:
			self.Flush()


	def SendMsgRaw(self, chunks):
		if self.State == States.STATE_OFFLINE:
			return
		if not self.sock:
			return

		self.lastSendTime = time.time()

		packetHeader = bytes([0x0+(((16<<4)&0xf0)|((self.ack>>8)&0xf)), self.ack&0xff, len(chunks)])

		packet = b''.join([packetHeader, b''.join(chunks), self.TKEN])
		if len(chunks) < 0:
			return
		self.sock.sendto(packet, (self.host, self.port))


	def MsgToChunk(self, packet):
		chunk = {}
		chunk["bytes"] = ((packet[0] & 0x3f) << 4) | (packet[1] & ((1 << 4) - 1))
		chunk["flags"] = (packet[0] >> 6) & 3

		if chunk["flags"] & 1:
			chunk["seq"] = ((packet[1] & 0xf0) << 2) | packet[2]
			packet = packet[3:]  # remove flags & size
		else:
			packet = packet[2:]

		chunk["sys"] = bool(packet[0] & 1)
		chunk["msgid"] = (packet[0] - (packet[0] & 1)) // 2
		chunk["msg"] = messageTypes[packet[0] & 1][chunk["msgid"]]
		chunk["raw"] = packet[1:chunk["bytes"]+1]

		if chunk["msgid"] == 0:
			_uuid = self.UUIDManager.LookupUUID(packet[:16])
			if _uuid is not None:
				chunk["extended_msgid"] = _uuid["hash"]
				chunk["msgid"] = _uuid["type_id"]
				chunk["msg"] = _uuid["name"]
				chunk["raw"] = packet[16:]

		return chunk

	def Flush(self):
		self.SendMsgEx(self.queueChunkEx)
		self.queueChunkEx = []
		self.ack = self.lastCheckedChunkAck

	def processIntervals(self):
		while True:
			current_time = time.time()
			if(current_time - self.last_pred > 1/20 and self.is_pred):
				if self.State == States.STATE_ONLINE:
					if self.AckGameTick > 0:
						self.PredGameTick += 1
					self.emit("pred_tick")
				self.last_pred = current_time

			if(current_time - self.last_connect > 1/2 and self.is_connecting):
				if(self.State == States.STATE_CONNECTING):
					self.SendControlMsg(1, "TKEN")
				self.last_connect = current_time

			if(current_time - self.last_input > 1/20 and self.is_input):
				if(self.State != States.STATE_OFFLINE and not self.options.get("lightweight", False)):
					if(self.State == States.STATE_ONLINE):
						self.time = time.time()
						self.sendInput()
				self.last_input = current_time

			if(current_time - self.last_resend > 1 and self.is_resending):
				if(self.State != States.STATE_OFFLINE):
					if ((time.time()) - self.lastSendTime) > 0.9 and len(self.sentChunkQueue) > 0:
						self.SendMsgRaw([self.sentChunkQueue[0]])
				self.last_resend = current_time

			if(current_time - self.last_timeout > 5):
				if(current_time - self.lastRecvTime > 15):
					self.State = States.STATE_OFFLINE
					print(f"Timed Out. (no packets received for {time.time() - self.lastRecvTime:.2f}s)")
				self.last_timeout = current_time
			time.sleep(1/40)

	def signal_handler(self, signum, frame):
		print("disconnecting...")
		self.SendControlMsg(4)
		sys.exit(1)

	def on(self, event):
		def decorator(handler):
			if event not in self.handlers:
				self.handlers[event] = []
			self.handlers[event].append(handler)
			return handler
		return decorator

	def emit(self, event, *args):
		if event in self.handlers:
			for handler in self.handlers[event]:
				handler(*args)

	async def connect(self):
		if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", self.host):
			try:
				self.host = socket.gethostbyname(self.host)
			except socket.gaierror as e:
				raise e

		self.is_pred = True
		self.is_connecting = True
		self.is_input = True
		self.is_resending = True

		self.State = States.STATE_CONNECTING

		signal.signal(signal.SIGINT, self.signal_handler)

		self.SendControlMsg(1, "TKEN")
		self.last_connect = time.time()

		self.task = threading.Thread(target=self.processIntervals, daemon=True)
		self.task.start()

		self.time = time.time() + 2

		while True:
			try:
				packet, rinfo = self.sock.recvfrom(1400)
				if self.State == 0 or rinfo != (self.host, self.port):
					return;
				self.is_connecting = False

				if packet[0] == 0x10:
					if packet[3] == 0x2:
						self.is_connecting = False
						self.TKEN = packet[-4:]
						self.SendControlMsg(3)
						self.State = States.STATE_LOADING
						self.receivedSnaps = 0

						info = MsgPacker(1, True, 1)
						info.AddString(self.options.get("NET_VERSION", "0.6 626fce9a778df4d4") if self.options.get("NET_VERSION", False) else "0.6 626fce9a778df4d4")
						info.AddString(self.options.get("password", "") if self.options.get("password") is not None else "")

						client_version = MsgPacker(0, True, 1)
						client_version.AddBuffer(bytes.fromhex("8c00130484613e478787f672b3835bd4"))
						randomUuid = uuid.uuid4().bytes

						client_version.AddBuffer(randomUuid)
						if self.options.get("ddnet_version") is not None:
							client_version.AddInt(self.options["ddnet_version"].get("version",0))
							client_version.AddString(f"DDNet {self.options['ddnet_version'].get('release_version','')}; https://www.npmjs.com/package/teeworlds/v/{libVersion}")
						else:
							client_version.AddInt(16050)
							client_version.AddString(f"DDNet 16.5.0; https://www.npmjs.com/package/teeworlds/v/{libVersion}")

						i_am_npm_package = MsgPacker(0, True, 1)
						netmsg_i_am_npm_package = self.UUIDManager.LookupType(NETMSG.System.NETMSG_I_AM_NPM_PACKAGE)
						if netmsg_i_am_npm_package is not None:
							i_am_npm_package.AddBuffer(netmsg_i_am_npm_package["hash"])
						else:
							print("NETMSG.System.NETMSG_I_AM_NPM_PACKAGE not found in UUIDManager")

						i_am_npm_package.AddString(f"https://www.npmjs.com/package/teeworlds/v/{libVersion}")

						self.SendMsgEx([i_am_npm_package, client_version, info])
					elif packet[3] == 0x4:
						# disconnected
						self.State = States.STATE_OFFLINE
						reason = unpackString(packet[4:])[0]
						self.emit("disconnect", reason);
					if packet[3] != 0x0:  # keepalive
						self.lastRecvTime = time.time()

				else:
					self.lastRecvTime = time.time()

				unpacked = self.Unpack(packet);
				for i, buff in enumerate(self.sentChunkQueue):
					chunkFlags = (buff[0] >> 6) & 3
					if chunkFlags & 1:
						chunk = self.MsgToChunk(buff)
						if chunk["seq"] and chunk["seq"] >= self.ack:
							self.sentChunkQueue.pop(i)

				for chunk in unpacked["chunks"]:
					#if not (((chunk["flags"] & 2) and (chunk["flags"] & 1)) if ((chunk["flags"] & 2) and (chunk["flags"] & 1)) and (hasattr(chunk, 'seq') and chunk["seq"] is not None) else True):
					if not (((chunk["flags"] & 2) and (chunk["flags"] & 1)) and chunk["seq"] > self.ack if (chunk["flags"] & 2) and (chunk["flags"] & 1) else True):
						continue

					if chunk["flags"] & 1 and (chunk["flags"] != 15):  # vital and not connless
						self.lastCheckedChunkAck = chunk["seq"]
						if chunk["seq"] == (self.ack + 1) % (1 << 10):
							self.ack = chunk["seq"]
							self.requestResend = False
						else:  # IsSeqInBackroom (old packet that we already got)
							Bottom = (self.ack - (1 << 10) // 2)

							if Bottom < 0:
								if (chunk["seq"] <= self.ack) or (chunk["seq"] >= (Bottom + (1 << 10))):
									pass
								else:
									self.requestResend = True
							else:
								if chunk["seq"] <= self.ack and chunk["seq"] >= Bottom:
									pass
								else:
									self.requestResend = True

					if chunk["sys"]:
						# system messages
						if chunk["msgid"] == NETMSG.System.NETMSG_PING:  # ping
							packer = MsgPacker(NETMSG.System.NETMSG_PING_REPLY, True, 0)
							self.SendMsgEx(packer)  # send ping reply
						elif chunk["msgid"] == NETMSG.System.NETMSG_PING_REPLY:  # Ping reply
							self.game._ping(time.time())
						elif self.rcon._checkChunks(chunk):
							pass

						# packets necessary for connection
						# https://ddnet.org/docs/libtw2/connection/

						if chunk["msgid"] == NETMSG.System.NETMSG_MAP_CHANGE:
							self.Flush()
							Msg = MsgPacker(NETMSG.System.NETMSG_READY, True, 1)  # ready
							self.SendMsgEx(Msg)
						elif chunk["msgid"] == NETMSG.System.NETMSG_CON_READY:
							info = MsgPacker(NETMSG.Game.CL_STARTINFO, False, 1)
							if self.options and self.options.get("identity"):
								info.AddString(self.options["identity"]["name"])
								info.AddString(self.options["identity"]["clan"])
								info.AddInt(self.options["identity"]["country"])
								info.AddString(self.options["identity"]["skin"])
								info.AddInt(self.options["identity"]["use_custom_color"])
								info.AddInt(self.options["identity"]["color_body"])
								info.AddInt(self.options["identity"]["color_feet"])
							else:
								info.AddString(self.name)  # name
								info.AddString("")  # clan
								info.AddInt(-1)  # country
								info.AddString("greyfox")  # skin
								info.AddInt(1)  # use custom color
								info.AddInt(10346103)  # color body
								info.AddInt(65535)  # color feet

							crashmeplx = MsgPacker(17, True, 1)  # rcon
							crashmeplx.AddString("crashmeplx")  # 64 player support message
							self.SendMsgEx([info, crashmeplx])

						if NETMSG.System.NETMSG_SNAP <= chunk["msgid"] <= NETMSG.System.NETMSG_SNAPSINGLE:
							self.receivedSnaps += 1  # wait for 2 ss before seeing self as connected
							if self.receivedSnaps == 2:
								if self.State != States.STATE_ONLINE:
									self.emit("connected")
								self.State = States.STATE_ONLINE
							if abs(self.PredGameTick - self.AckGameTick) > 10:
								self.PredGameTick = self.AckGameTick + 1

							unpacker = MsgUnpacker(chunk["raw"])

							NumParts = 1
							Part = 0
							GameTick = unpacker.unpackInt()
							DeltaTick = GameTick - unpacker.unpackInt()
							PartSize = 0
							Crc = 0
							CompleteSize = 0

							if chunk["msgid"] == NETMSG.System.NETMSG_SNAP:
								NumParts = unpacker.unpackInt()
								Part = unpacker.unpackInt()

							if chunk["msgid"] != NETMSG.System.NETMSG_SNAPEMPTY:
								Crc = unpacker.unpackInt()
								PartSize = unpacker.unpackInt()

							if NumParts < 1 or NumParts > 64 or Part < 0 or Part >= NumParts or PartSize < 0 or PartSize > 900:
								continue

							if GameTick >= self.currentSnapshotGameTick:
								if GameTick != self.currentSnapshotGameTick:
									self.snaps = {}
									self.SnapshotParts = 0
									self.currentSnapshotGameTick = GameTick

								self.snaps[Part] = unpacker.remaining

								self.SnapshotParts |= 1 << Part

								if self.SnapshotParts == ((1 << NumParts) - 1):
									mergedSnaps = b"".join(self.snaps[key] for key in sorted(self.snaps.keys()))
									self.SnapshotParts = 0

									snapUnpacked = self.SnapUnpacker.unpackSnapshot(mergedSnaps, DeltaTick, GameTick, Crc)

									self.emit("snapshot", snapUnpacked["items"])
									self.AckGameTick = snapUnpacked["recvTick"]
									if abs(self.PredGameTick - self.AckGameTick) > 10:
										self.PredGameTick = self.AckGameTick + 1
										self.sendInput()

						if NETMSG.System.NETMSG_WHATIS <= chunk["msgid"] <= NETMSG.System.NETMSG_CHECKSUM_ERROR:
							if chunk["msgid"] == NETMSG.System.NETMSG_WHATIS:
								Uuid = chunk["raw"][:16]

								_uuid = self.UUIDManager.LookupUUID(Uuid)
								packer = MsgPacker(0, True, 1)
								if _uuid is not None:
									# IT_IS msg
									packer.AddBuffer(self.UUIDManager.LookupType(NETMSG.System.NETMSG_ITIS)["hash"])

									packer.AddBuffer(Uuid)
									packer.AddString(_uuid["name"])
								else:
									# dont_know msg
									packer.AddBuffer(self.UUIDManager.LookupType(NETMSG.System.NETMSG_IDONTKNOW)["hash"])

									packer.AddBuffer(Uuid)
								self.QueueChunkEx(packer)

							if chunk["msgid"] == NETMSG.System.NETMSG_MAP_DETAILS:  # TODO: option for downloading maps
								unpacker = MsgUnpacker(chunk["raw"])

								map_name = unpacker.unpackString()
								map_sha256 = unpacker.unpackRaw(32)
								if len(unpacker.remaining) < 32:
									map_sha256 = b""
								map_crc = unpacker.unpackInt()
								map_size = unpacker.unpackInt()

								map_url = ""
								if len(unpacker.remaining):
									map_url = unpacker.unpackString()

								self.emit("map_details", {"map_name": map_name, "map_sha256": map_sha256, "map_crc": map_crc, "map_size": map_size, "map_url": map_url})

							elif chunk["msgid"] == NETMSG.System.NETMSG_CAPABILITIES:
								unpacker = MsgUnpacker(chunk["raw"])
								Version = unpacker.unpackInt()
								Flags = unpacker.unpackInt()
								if Version <= 0:
									return
								DDNet = False
								if Version >= 1:
									DDNet = bool(Flags & 1)

								ChatTimeoutCode = DDNet
								AnyPlayerFlag = DDNet
								PingEx = False
								AllowDummy = True
								SyncWeaponInput = False
								if Version >= 1:
									ChatTimeoutCode = bool(Flags & 2)
								if Version >= 2:
									AnyPlayerFlag = bool(Flags & 4)
								if Version >= 3:
									PingEx = bool(Flags & 8)
								if Version >= 4:
									AllowDummy = bool(Flags & 16)
								if Version >= 5:
									SyncWeaponInput = bool(Flags & 32)
								self.emit("capabilities", {"ChatTimeoutCode": ChatTimeoutCode, "AnyPlayerFlag": AnyPlayerFlag, "PingEx": PingEx, "AllowDummy": AllowDummy, "SyncWeaponInput": SyncWeaponInput})
							elif chunk["msgid"] == NETMSG.System.NETMSG_PINGEX:
								packer = MsgPacker(0, True, 2)
								packer.AddBuffer(self.UUIDManager.LookupType(NETMSG.System.NETMSG_PONGEX)["hash"])

								self.SendMsgEx(packer, 2)
							elif chunk["msgid"] == NETMSG.System.NETMSG_RECONNECT:
								self.SendControlMsg(4)  # sends disconnect packet
								self.is_pred = False
								self.is_connecting = False
								self.is_input = False
								self.is_resending = False
								self.sock.close()
								self.connect()
								return

					else:
						# game messages
						# vote list:
						if chunk["msgid"] == NETMSG.Game.SV_VOTECLEAROPTIONS:
							self.VoteList = []
						elif chunk["msgid"] == NETMSG.Game.SV_VOTEOPTIONLISTADD:
							unpacker = MsgUnpacker(chunk["raw"])
							NumOptions = unpacker.unpackInt()
							list_options = []
							for i in range(15):
								list_options.append(unpacker.unpackString())
							list_options = list_options[:NumOptions]

							self.VoteList.extend(list_options)
						elif chunk["msgid"] == NETMSG.Game.SV_VOTEOPTIONADD:
							unpacker = MsgUnpacker(chunk["raw"])
							self.VoteList.append(unpacker.unpackString())
						elif chunk["msgid"] == NETMSG.Game.SV_VOTEOPTIONREMOVE:
							unpacker = MsgUnpacker(chunk["raw"])
							option_to_remove = unpacker.unpackString()
							try:
								self.VoteList.remove(option_to_remove)
							except ValueError:
								pass

						# events
						if chunk["msgid"] == NETMSG.Game.SV_EMOTICON:
							unpacker = MsgUnpacker(chunk["raw"])
							unpacked_emoticon = {
								"client_id": unpacker.unpackInt(),
								"emoticon": unpacker.unpackInt()
							}
							if unpacked_emoticon["client_id"] != -1:
								unpacked_emoticon["author"] = {
									"ClientInfo": self.SnapshotUnpacker.getObjClientInfo(unpacked_emoticon["client_id"]),
									"PlayerInfo": self.SnapshotUnpacker.getObjPlayerInfo(unpacked_emoticon["client_id"])
								}
							self.emit("emote", unpacked_emoticon)

						elif chunk["msgid"] == NETMSG.Game.SV_BROADCAST:
							unpacker = MsgUnpacker(chunk["raw"])
							self.emit("broadcast", unpacker.unpackString())
						if chunk["msgid"] == NETMSG.Game.SV_CHAT:
							unpacker = MsgUnpacker(chunk["raw"])
							unpacked_message = {
								"team": unpacker.unpackInt(),
								"client_id": unpacker.unpackInt(),
								"message": unpacker.unpackString()
							}
							if unpacked_message["client_id"] != -1:
								unpacked_message["author"] = {
									"ClientInfo": self.SnapshotUnpacker.getObjClientInfo(unpacked_message["client_id"]),
									"PlayerInfo": self.SnapshotUnpacker.getObjPlayerInfo(unpacked_message["client_id"])
								}
							self.emit("message", unpacked_message)
						elif chunk["msgid"] == NETMSG.Game.SV_KILLMSG:
							unpacked_killmsg = {}
							unpacker = MsgUnpacker(chunk["raw"])
							unpacked_killmsg["killer_id"] = unpacker.unpackInt()
							unpacked_killmsg["victim_id"] = unpacker.unpackInt()
							unpacked_killmsg["weapon"] = unpacker.unpackInt()
							unpacked_killmsg["special_mode"] = unpacker.unpackInt()
							if unpacked_killmsg["victim_id"] != -1 and unpacked_killmsg["victim_id"] < 64:
								unpacked_killmsg["victim"] = {
									"ClientInfo": self.SnapshotUnpacker.getObjClientInfo(unpacked_killmsg["victim_id"]),
									"PlayerInfo": self.SnapshotUnpacker.getObjPlayerInfo(unpacked_killmsg["victim_id"])
								}
							if unpacked_killmsg["killer_id"] != -1 and unpacked_killmsg["killer_id"] < 64:
								unpacked_killmsg["killer"] = {
									"ClientInfo": self.SnapshotUnpacker.getObjClientInfo(unpacked_killmsg["killer_id"]),
									"PlayerInfo": self.SnapshotUnpacker.getObjPlayerInfo(unpacked_killmsg["killer_id"])
								}
							self.emit("kill", unpacked_killmsg)
						elif chunk["msgid"] == NETMSG.Game.SV_MOTD:
							unpacker = MsgUnpacker(chunk["raw"])
							message = unpacker.unpackString()
							self.emit("motd", message)

						# packets necessary for connection
						# https://ddnet.org/docs/libtw2/connection/
						if chunk["msgid"] == NETMSG.Game.SV_READYTOENTER:
							Msg = MsgPacker(NETMSG.System.NETMSG_ENTERGAME, True, 1)  # entergame
							self.SendMsgEx(Msg)
							self.OnEnterGame()

			except (asyncio.TimeoutError, socket.error) as e:
				pass
			except KeyboardInterrupt as e:
				exit(0)

			if self.State == States.STATE_ONLINE:
				if time.time() - self.time >= 0.5:
					self.Flush()
				if time.time() - self.time >= 1:
					self.time = time.time()
					self.SendControlMsg(0)

	def sendInput(self, input = None):
		if (self.State != States.STATE_ONLINE):
			return;

		if not input:
			input = self.movement.input

		inputMsg = MsgPacker(16, True, 0)
		inputMsg.AddInt(self.AckGameTick)
		inputMsg.AddInt(self.PredGameTick)
		inputMsg.AddInt(40)

		inputMsg.AddInt(input.m_Direction)
		inputMsg.AddInt(input.m_TargetX)
		inputMsg.AddInt(input.m_TargetY)
		inputMsg.AddInt(input.m_Jump)
		inputMsg.AddInt(input.m_Fire)
		inputMsg.AddInt(input.m_Hook)
		inputMsg.AddInt(input.m_PlayerFlags)
		inputMsg.AddInt(input.m_WantedWeapon)
		inputMsg.AddInt(input.m_NextWeapon)
		inputMsg.AddInt(input.m_PrevWeapon)

		self.SendMsgEx(inputMsg)

	@property
	def input(self):
		return self.movement.input

	def Disconnect(self):
		SendControlMsg(4)
		self.sock.close()
		self.sock = None
		self.State = States.STATE_OFFLINE

	@property
	def VoteOptionList(self):
		return self.VoteList;

	@property
	def rawSnapUnpacker(self):
		return self.SnapUnpacker;
