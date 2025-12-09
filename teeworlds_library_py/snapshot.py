from .UUIDManager import UUIDManager, createTwMD5Hash
from .msg import MsgUnpacker
import struct
import re

___itemAppendix = [  # only used for the events underneath. the actual itemAppendix below this is only used for size
	{"type_id": 0, "size": 0, "name": "obj_ex"},
	{"type_id": 1, "size": 10, "name": "obj_player_input"},
	{"type_id": 2, "size": 6, "name": "obj_projectile"},
	{"type_id": 3, "size": 5, "name": "obj_laser"},
	{"type_id": 4, "size": 4, "name": "obj_pickup"},
	{"type_id": 5, "size": 3, "name": "obj_flag"},
	{"type_id": 6, "size": 8, "name": "obj_game_info"},
	{"type_id": 7, "size": 4, "name": "obj_game_data"},
	{"type_id": 8, "size": 15, "name": "obj_character_core"},
	{"type_id": 9, "size": 22, "name": "obj_character"},
	{"type_id": 10, "size": 5, "name": "obj_player_info"},
	{"type_id": 11, "size": 17, "name": "obj_client_info"},
	{"type_id": 12, "size": 3, "name": "obj_spectator_info"},
	{"type_id": 13, "size": 2, "name": "common"},  # event_common
	{"type_id": 14, "size": 2, "name": "explosion"},  # event_explosion
	{"type_id": 15, "size": 2, "name": "spawn"},  # event_spawn
	{"type_id": 16, "size": 2, "name": "hammerhit"},  # event_hammerhit
	{"type_id": 17, "size": 3, "name": "death"},  # event_death
	{"type_id": 18, "size": 3, "name": "sound_global"},  # event_sound_global
	{"type_id": 19, "size": 3, "name": "sound_world"},  # event_sound_world
	{"type_id": 20, "size": 3, "name": "damage_indicator"}  # event_damage_indicator
]

itemAppendix = [
	0,
	10,
	6,
	5,
	4,
	3,
	8,
	4,
	15,
	22,
	5,
	17,
	3,
	2,
	2,
	2,
	2,
	3,
	3,
	3,
	3,
]

class items:
	OBJ_EX = 0
	OBJ_PLAYER_INPUT = 1
	OBJ_PROJECTILE = 2
	OBJ_LASER = 3
	OBJ_PICKUP = 4
	OBJ_FLAG = 5
	OBJ_GAME_INFO = 6
	OBJ_GAME_DATA = 7
	OBJ_CHARACTER_CORE = 8
	OBJ_CHARACTER = 9
	OBJ_PLAYER_INFO = 10
	OBJ_CLIENT_INFO = 11
	OBJ_SPECTATOR_INFO = 12
	EVENT_COMMON = 13
	EVENT_EXPLOSION = 14
	EVENT_SPAWN = 15
	EVENT_HAMMERHIT = 16
	EVENT_DEATH = 17
	EVENT_SOUND_GLOBAL = 18
	EVENT_SOUND_WORLD = 19
	EVENT_DAMAGE_INDICATOR = 20

# https://github.com/ddnet/ddnet/blob/571b0b36de83d18f2524ee371fc3223d04b94135/datasrc/network.py#L236
supported_uuids = [
	"my-own-object@heinrich5991.de",
	"character@netobj.ddnet.tw",  # validate_size=False
	"player@netobj.ddnet.tw",
	"gameinfo@netobj.ddnet.tw",  # validate_size=False
	"projectile@netobj.ddnet.tw",
	"laser@netobj.ddnet.tw",
]

class Snapshot:
	def __init__(self, _client):
		self.deltas = []
		self.eSnapHolder = []
		self.crc_errors = 0
		self.client = _client
		self.uuid_manager = UUIDManager(32767, True)  # snapshot max_type

	def IntsToStr(self, pInts):
		pIntz = []
		for x in pInts:
			pIntz.append((((x) >> 24) & 0xff) - 128)
			pIntz.append((((x) >> 16) & 0xff) - 128)
			pIntz.append((((x) >> 8) & 0xff) - 128)
			pIntz.append(((x) & 0xff) - 128)

		if pIntz:
			del pIntz[-1]

		unsigned_pIntz = [(val + 256 if val < 0 else val) for val in pIntz]

		pStr = bytes(unsigned_pIntz).decode('utf-8', 'ignore')

		pStr = re.sub(r'\0.*', '', pStr)
		return pStr

	def parseItem(self, data, Type, id):
		_item = {}
		if Type >= 0x4000:  # offset uuid type
			lookup_result = self.uuid_manager.LookupType(Type)
			if lookup_result and lookup_result['name'] == "my-own-object@heinrich5991.de":
				_item = {
					"m_Test": data[0]
				}
			elif lookup_result and lookup_result['name'] == "character@netobj.ddnet.tw":
				_item = {
					"m_Flags": data[0],
					"m_FreezeEnd": data[1],
					"m_Jumps": data[2],
					"m_TeleCheckpoint": data[3],
					"m_StrongWeakID": data[4],
					# # New data fields for jump display, freeze bar and ninja bar
					# # Default values indicate that these values should not be used
					"m_JumpedTotal": data[5] if len(data) > 5 else None,
					"m_NinjaActivationTick": data[6] if len(data) > 6 else None,
					"m_FreezeStart": data[7] if len(data) > 7 else None,
					# # New data fields for improved target accuracy
					"m_TargetX": data[8] if len(data) > 8 else None,
					"m_TargetY": data[9] if len(data) > 9 else None,
					"id": id

				}
			elif lookup_result and lookup_result['name'] == "player@netobj.ddnet.tw":
				_item = {
					"m_Flags": data[0],
					"m_AuthLevel": data[1],
					"id": id
				}
			elif lookup_result and lookup_result['name'] == "gameinfo@netobj.ddnet.tw":
				_item = {
					"m_Flags": data[0],
					"m_Version": data[1],
					"m_Flags2": data[2]
				}
			elif lookup_result and lookup_result['name'] == "projectile@netobj.ddnet.tw":
				_item = {
					"m_X": data[0],
					"m_Y": data[1],
					"m_Angle": data[2],
					"m_Data": data[3],
					"m_Type": data[3],
					"m_StartTick": data[3]
				}
			elif lookup_result and lookup_result['name'] == "laser@netobj.ddnet.tw":
				_item = {
					"m_ToX": data[0],
					"m_ToY": data[1],
					"m_FromX": data[2],
					"m_FromY": data[3],
					"m_Owner": data[3],
					"m_Type": data[3]
				}
			return _item

		if Type == items.OBJ_EX:
			pass
		elif Type == items.OBJ_PLAYER_INPUT:
			_item = {
				"direction": data[0],
				"target_x": data[1],
				"target_y": data[2],
				"jump": data[3],
				"fire": data[4],
				"hook": data[5],
				"player_flags": data[6],
				"wanted_weapon": data[7],
				"next_weapon": data[8],
				"prev_weapon": data[9],
			}
		elif Type == items.OBJ_PROJECTILE:
			_item = {
				"x": data[0],
				"y": data[1],
				"vel_x": data[2],
				"vel_y": data[3],
				"type_": data[4],
				"start_tick": data[5],
			}
		elif Type == items.OBJ_LASER:
			_item = {
				"x": data[0],
				"y": data[1],
				"from_x": data[2],
				"from_y": data[3],
				"start_tick": data[4],
			}
		elif Type == items.OBJ_PICKUP:
			_item = {
				"x": data[0],
				"y": data[1],
				"type_": data[2],
				"subtype": data[3],
			}
		elif Type == items.OBJ_FLAG:
			_item = {
				"x": data[0],
				"y": data[1],
				"team": data[2],
			}
		elif Type == items.OBJ_GAME_INFO:
			_item = {
				"game_flags": data[0],
				"game_state_flags": data[1],
				"round_start_tick": data[2],
				"warmup_timer": data[3],
				"score_limit": data[4],
				"time_limit": data[5],
				"round_num": data[6],
				"round_current": data[7],

			}
		elif Type == items.OBJ_GAME_DATA:
			_item = {
				"teamscore_red": data[0],
				"teamscore_blue": data[1],
				"flag_carrier_red": data[2],
				"flag_carrier_blue": data[3],
			}
		elif Type == items.OBJ_CHARACTER_CORE:
			_item = {
				"tick": data[0],
				"x": data[1],
				"y": data[2],
				"vel_x": data[3],
				"vel_y": data[4],
				"angle": data[5],
				"direction": data[6],
				"jumped": data[7],
				"hooked_player": data[8],
				"hook_state": data[9],
				"hook_tick": data[10],
				"hook_x": data[11],
				"hook_y": data[12],
				"hook_dx": data[13],
				"hook_dy": data[14],
			}
		elif Type == items.OBJ_CHARACTER:
			_item = {
				"character_core": {
					"tick": data[0],
					"x": data[1],
					"y": data[2],
					"vel_x": data[3],
					"vel_y": data[4],
					"angle": data[5],
					"direction": data[6],
					"jumped": data[7],
					"hooked_player": data[8],
					"hook_state": data[9],
					"hook_tick": data[10],
					"hook_x": data[11],
					"hook_y": data[12],
					"hook_dx": data[13],
					"hook_dy": data[14],
				},
				"player_flags": data[15],
				"health": data[16],
				"armor": data[17],
				"ammo_count": data[18],
				"weapon": data[19],
				"emote": data[20],
				"attack_tick": data[21],
				"client_id": id
			}
		elif Type == items.OBJ_PLAYER_INFO:
			_item = {
				"local": data[0],
				"client_id": data[1],
				"team": data[2],
				"score": data[3],
				"latency": data[4],
			}
		elif Type == items.OBJ_CLIENT_INFO:
			_item = {
				"name": self.IntsToStr([data[0], data[1], data[2], data[3]]),
				"clan": self.IntsToStr([data[4], data[5], data[6]]),
				"country": data[7],
				"skin": self.IntsToStr([data[8], data[9], data[10], data[11], data[12], data[13]]),
				"use_custom_color": int(data[14]),
				"color_body": int(data[15]),
				"color_feet": int(data[16]),
				"id": id
			}
		elif Type == items.OBJ_SPECTATOR_INFO:
			_item = {
				"spectator_id": data[0],
				"x": data[1],
				"y": data[2],
			}
		elif Type == items.EVENT_COMMON:
			_item = {
				"x": data[0],
				"y": data[1],
			}
		elif Type == items.EVENT_EXPLOSION:
			_item = {
				"common": {
					"x": data[0],
					"y": data[1]
				}
			}
		elif Type == items.EVENT_SPAWN:
			_item = {
				"common": {
					"x": data[0],
					"y": data[1]
				}
			}
		elif Type == items.EVENT_HAMMERHIT:
			_item = {
				"common": {
					"x": data[0],
					"y": data[1]
				}
			}
		elif Type == items.EVENT_DEATH:
			_item = {
				"client_id": data[0],
				"common": {
					"x": data[1],
					"y": data[2]
				}
			}
		elif Type == items.EVENT_SOUND_GLOBAL:
			_item = {
				"common": {
					"x": data[0],
					"y": data[1]
				},
				"sound_id": data[2]
			}
		elif Type == items.EVENT_SOUND_WORLD:
			_item = {
				"common": {
					"x": data[0],
					"y": data[1]
				},
				"sound_id": data[2]
			}
		elif Type == items.EVENT_DAMAGE_INDICATOR:
			_item = {
				"angle": data[0],
				"common": {
					"x": data[0],
					"y": data[1]
				},
			}

		return _item

	def crc(self):
		checksum = 0
		for snap in self.deltas:
			for el in snap['data']:
				checksum += el

		return checksum & 0xffffffff

	def unpackSnapshot(self, snap, deltatick, recvTick, WantedCrc):
		unpacker = MsgUnpacker(snap)
		deltaSnaps = []
		if deltatick == -1:
			self.eSnapHolder = []
			self.deltas = []
		else:
			#deltaSnaps = [a for a in self.eSnapHolder if a['ack'] == deltatick]
			#self.eSnapHolder = [a for a in self.eSnapHolder if a['ack'] >= deltatick]
			self.eSnapHolder = [a for a in self.eSnapHolder if (deltaSnaps.append(a) if a['ack'] == deltatick else True) and a['ack'] >= deltatick]

		if len(snap) == 0:
			# empty snap, copy old one into new ack
			for snap in self.eSnapHolder:
				if snap['ack'] == deltatick:
					self.eSnapHolder.append({"Snapshot": snap['Snapshot'], "ack": recvTick})

			return {"items": [], "recvTick": recvTick}

		oldDeltas = self.deltas
		self.deltas = []

		_events = []

		num_removed_items = unpacker.unpackInt()
		num_item_deltas = unpacker.unpackInt()
		unpacker.unpackInt()  # _zero padding

		deleted = []
		for i in range(num_removed_items):
			deleted_key = unpacker.unpackInt()  # removed_item_keys
			deleted.append(deleted_key)

		if len(deltaSnaps) == 0 and deltatick >= 0:
			return {"items": [], "recvTick": -1}

		for i in range(num_item_deltas):
			type_id = unpacker.unpackInt()
			id = unpacker.unpackInt()
			key = (((type_id) << 16) | (id))

			if type_id > 0 and type_id < len(itemAppendix):
				_size = itemAppendix[type_id]
			else:
				_size = unpacker.unpackInt()

			data = []
			for j in range(_size):
				data.append(unpacker.unpackInt())

			changed = False
			if deltatick >= 0:
				delta = next((delta for delta in deltaSnaps if delta['Snapshot']['Key'] == key), None)
				if delta is not None:
					out = self.UndiffItem(delta['Snapshot']['Data'], data)
					data = out
					changed = True

			parsed = None
			if type_id != 0:
				if not changed:
					oldDelta = next((delta for delta in oldDeltas if delta['key'] == key), None)
					if oldDelta is not None and self.compareArrays(data, oldDelta['data']):
						parsed = oldDelta['parsed']
					else:
						parsed = self.parseItem(data, type_id, id)
				else:
					parsed = self.parseItem(data, type_id, id)

				self.eSnapHolder.append({"Snapshot": {"Data": data, "Key": key}, "ack": recvTick})

				self.deltas.append({
					"data": data,
					"key": key,
					"id": id,
					"type_id": type_id,
					"parsed": parsed
				})
				if items.EVENT_COMMON <= type_id <= items.EVENT_DAMAGE_INDICATOR:
					_events.append({"type_id": type_id, "parsed": parsed})
			else:
				self.eSnapHolder.append({"Snapshot": {"Data": data, "Key": key}, "ack": recvTick})

				self.deltas.append({
					"data": data,
					"key": key,
					"id": id,
					"type_id": type_id,
					"parsed": {}
				})

				def test(int_val):
					return [(int_val >> 24) & 0xff, (int_val >> 16) & 0xff, (int_val >> 8) & 0xff, int_val & 0xff]

				def test2(ints):
					return [item for sublist in [test(a) for a in ints] for item in sublist]

				targetUUID = bytes(test2(data))
				if not self.uuid_manager.LookupType(id):
					for i, a in enumerate(supported_uuids):
						uuid = createTwMD5Hash(a)
						if targetUUID == uuid:
							self.uuid_manager.RegisterName(a, id)
							supported_uuids.pop(i)
							break

		for newSnap in deltaSnaps:
			if newSnap['Snapshot']['Key'] in deleted:
				continue
			if not any(a['ack'] == recvTick and a['Snapshot']['Key'] == newSnap['Snapshot']['Key'] for a in self.eSnapHolder):
				self.eSnapHolder.append({"Snapshot": {"Data": newSnap['Snapshot']['Data'], "Key": newSnap['Snapshot']['Key']}, "ack": recvTick})
				oldDelta = next((delta for delta in oldDeltas if delta['key'] == newSnap['Snapshot']['Key']), None)
				if oldDelta is not None and self.compareArrays(newSnap['Snapshot']['Data'], oldDelta['data']):
					self.deltas.append(oldDelta)
				else:
					self.deltas.append({
						"data": newSnap['Snapshot']['Data'],
						"key": newSnap['Snapshot']['Key'],
						"id": newSnap['Snapshot']['Key'] & 0xffff,
						"type_id": (newSnap['Snapshot']['Key'] >> 16) & 0xffff,
						"parsed": self.parseItem(newSnap['Snapshot']['Data'], (newSnap['Snapshot']['Key'] >> 16) & 0xffff, newSnap['Snapshot']['Key'] & 0xffff)
					})

		_crc = self.crc()
		if _crc != WantedCrc:
			self.deltas = oldDeltas
			self.crc_errors += 1
			if self.crc_errors > 5:
				recvTick = -1
				self.crc_errors = 0
				self.eSnapHolder = []
				self.deltas = []
			else:
				recvTick = deltatick
		elif self.crc_errors > 0:
			self.crc_errors -= 1

		for a in _events:
			type_id = a['type_id']
			parsed = a['parsed']
			self.client.emit(globals()['___itemAppendix'][type_id]['name'], parsed)

		return {"items": self.deltas, "recvTick": recvTick}

	def compareArrays(self, first, second):
		if len(first) != len(second):
			return False
		for i in range(len(first)):
			if first[i] != second[i]:
				return False
		return True

	def UndiffItem(self, oldItem, newItem):
		out_length = max(len(oldItem), len(newItem))
		out = [0] * out_length

		for i in range(out_length):
			old_val = oldItem[i] if i < len(oldItem) else None
			new_val = newItem[i] if i < len(newItem) else None

			if old_val is not None and new_val is not None:
				out[i] = new_val + old_val
			elif new_val is not None:
				out[i] = new_val
		return out
