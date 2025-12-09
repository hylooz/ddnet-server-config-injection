from ..protocol import SnapshotItemIDs

class SnapshotWrapper:
	def __init__(self, _client):
		super().__init__()
		self._client = _client

	def getParsed(self, type_id, id):
		if type_id == -1:
			return None
		for delta in self._client.rawSnapUnpacker.deltas:
			if delta['type_id'] == type_id and delta['id'] == id:
				return delta['parsed']
		return None

	def getAll(self, type_id):
		_all = []
		if type_id == -1:
			return _all
		for delta in self._client.rawSnapUnpacker.deltas:
			if delta['type_id'] == type_id:
				_all.append(delta['parsed'])
		return _all

	def getObjPlayerInput(self, player_id):
		return self.getParsed(SnapshotItemIDs.OBJ_PLAYER_INPUT, player_id)

	@property
	def AllObjPlayerInput(self):
		return self.getAll(SnapshotItemIDs.OBJ_PLAYER_INPUT)

	def getObjProjectile(self, id):
		return self.getParsed(SnapshotItemIDs.OBJ_PROJECTILE, id)

	@property
	def AllProjectiles(self):
		return self.getAll(SnapshotItemIDs.OBJ_PROJECTILE)

	def getObjLaser(self, id):
		return self.getParsed(SnapshotItemIDs.OBJ_LASER, id)

	@property
	def AllObjLaser(self):
		return self.getAll(SnapshotItemIDs.OBJ_LASER)

	def getObjPickup(self, id):
		return self.getParsed(SnapshotItemIDs.OBJ_PICKUP, id)

	@property
	def AllObjPickup(self):
		return self.getAll(SnapshotItemIDs.OBJ_PICKUP)

	def getObjFlag(self, id):
		return self.getParsed(SnapshotItemIDs.OBJ_FLAG, id)

	@property
	def AllObjFlag(self):
		return self.getAll(SnapshotItemIDs.OBJ_FLAG)

	def getObjGameInfo(self, id):
		return self.getParsed(SnapshotItemIDs.OBJ_GAME_INFO, id)

	@property
	def AllObjGameInfo(self):
		return self.getAll(SnapshotItemIDs.OBJ_GAME_INFO)

	def getObjGameData(self, id):
		return self.getParsed(SnapshotItemIDs.OBJ_GAME_DATA, id)

	@property
	def AllObjGameData(self):
		return self.getAll(SnapshotItemIDs.OBJ_GAME_DATA)

	def getObjCharacterCore(self, player_id):
		return self.getParsed(SnapshotItemIDs.OBJ_CHARACTER_CORE, player_id)

	@property
	def AllObjCharacterCore(self):
		return self.getAll(SnapshotItemIDs.OBJ_CHARACTER_CORE)

	def getObjCharacter(self, player_id):
		return self.getParsed(SnapshotItemIDs.OBJ_CHARACTER, player_id)

	@property
	def AllObjCharacter(self):
		return self.getAll(SnapshotItemIDs.OBJ_CHARACTER)

	def getObjPlayerInfo(self, player_id):
		return self.getParsed(SnapshotItemIDs.OBJ_PLAYER_INFO, player_id)

	@property
	def AllObjPlayerInfo(self):
		return self.getAll(SnapshotItemIDs.OBJ_PLAYER_INFO)

	def getObjClientInfo(self, player_id):
		return self.getParsed(SnapshotItemIDs.OBJ_CLIENT_INFO, player_id)

	@property
	def AllObjClientInfo(self):
		return self.getAll(SnapshotItemIDs.OBJ_CLIENT_INFO)

	def getObjSpectatorInfo(self, player_id):
		return self.getParsed(SnapshotItemIDs.OBJ_SPECTATOR_INFO, player_id)

	@property
	def AllObjSpectatorInfo(self):
		return self.getAll(SnapshotItemIDs.OBJ_SPECTATOR_INFO)

	def getTypeId(self, name):
		lookup_result = self._client.rawSnapUnpacker.uuid_manager.LookupName(name)
		if lookup_result and 'type_id' in lookup_result:
			return lookup_result['type_id']
		return -1

	def getObjExMyOwnObject(self, id):
		return self.getParsed(self.getTypeId("my-own-object@heinrich5991.de"), id)

	@property
	def AllObjExMyOwnObject(self):
		return self.getAll(self.getTypeId("my-own-object@heinrich5991.de"))

	def getObjExDDNetCharacter(self, id):
		return self.getParsed(self.getTypeId("character@netobj.ddnet.tw"), id)

	@property
	def AllObjExDDNetCharacter(self):
		return self.getAll(self.getTypeId("character@netobj.ddnet.tw"))

	def getObjExGameInfo(self, id):
		return self.getParsed(self.getTypeId("gameinfo@netobj.ddnet.tw"), id)

	@property
	def AllObjExGameInfo(self):
		return self.getAll(self.getTypeId("gameinfo@netobj.ddnet.tw"))

	def getObjExDDNetProjectile(self, id):
		return self.getParsed(self.getTypeId("projectile@netobj.ddnet.tw"), id)

	@property
	def AllObjExDDNetProjectile(self):
		return self.getAll(self.getTypeId("projectile@netobj.ddnet.tw"))

	def getObjExLaser(self, id):
		return self.getParsed(self.getTypeId("laser@netobj.ddnet.tw"), id)

	@property
	def AllObjExLaser(self):
		return self.getAll(self.getTypeId("laser@netobj.ddnet.tw"))

	@property
	def OwnID(self):
		for parsed in self.AllObjPlayerInfo:
			if parsed['local']:
				return parsed['client_id']
		return None
