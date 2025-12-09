from ..msg import MsgPacker
from ..protocol import NETMSG
import time

class Game:
	def __init__(self, _client):
		self._client = _client
		self._ping = lambda _time: None

	def send(self, packer):
		if not self._client.options or not self._client.options.get("lightweight"):
			self._client.QueueChunkEx(packer)
		else:
			self._client.SendMsgEx(packer)

	def Say(self, message, team = False):
		packer = MsgPacker(NETMSG.Game.CL_SAY, False, 1)
		packer.AddInt(1 if team else 0)  # team
		packer.AddString(message)
		self.send(packer)

	def SetTeam(self, team):
		packer = MsgPacker(NETMSG.Game.CL_SETTEAM, False, 1)
		packer.AddInt(team)
		self.send(packer)

	def SpectatorMode(self, SpectatorID):
		packer = MsgPacker(NETMSG.Game.CL_SETSPECTATORMODE, False, 1)
		packer.AddInt(SpectatorID)
		self.send(packer)

	def ChangePlayerInfo(self, playerInfo):
		packer = MsgPacker(NETMSG.Game.CL_CHANGEINFO, False, 1)
		packer.AddString(playerInfo.name)
		packer.AddString(playerInfo.clan)
		packer.AddInt(playerInfo.country)
		packer.AddString(playerInfo.skin)
		packer.AddInt(1 if playerInfo.use_custom_color else 0)
		packer.AddInt(playerInfo.color_body)
		packer.AddInt(playerInfo.color_feet)
		self.send(packer)

	def Kill(self):
		packer = MsgPacker(NETMSG.Game.CL_KILL, False, 1)
		self.send(packer)

	def Emote(self, emote):
		packer = MsgPacker(NETMSG.Game.CL_EMOTICON, False, 1)
		packer.AddInt(emote)
		self.send(packer)

	def Vote(self, vote):
		packer = MsgPacker(NETMSG.Game.CL_VOTE, False, 1)
		packer.AddInt(1 if vote else -1)
		self.send(packer)

	def CallVote(self, Type, Value, Reason):
		packer = MsgPacker(NETMSG.Game.CL_CALLVOTE, False, 1)
		packer.AddString(Type)
		packer.AddString(str(Value))
		packer.AddString(Reason)
		self.send(packer)

	def CallVoteOption(self, Value, Reason):
		self.CallVote("option", Value, Reason)

	def CallVoteKick(self, PlayerID, Reason):
		self.CallVote("kick", PlayerID, Reason)

	def CallVoteSpectate(self, PlayerID, Reason):
		self.CallVote("spectate", PlayerID, Reason)

	def IsDDNetLegacy(self):
		packer = MsgPacker(NETMSG.Game.CL_ISDDNETLEGACY, False, 1)
		self.send(packer)

	def Ping(self) -> float:
		startTime = time.time()

		packer = MsgPacker(22, True, 0)
		self.send(packer)

		def _callback(_time: float) -> None:
			self._ping = lambda _time_val: None

		self._ping = _callback

		return startTime
