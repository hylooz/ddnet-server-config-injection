import hashlib

def createTwMD5Hash(name: str) -> bytes:
	"""
	Generates a custom MD5 hash used in Teeworlds/DDNet.
	https://github.com/ddnet/ddnet/blob/6d9284adc1e0be4b5348447d857eae575e06e654/src/engine/shared/uuid_manager.cpp#L26
	"""
	seed = bytes([0xe0, 0x5d, 0xda, 0xaa, 0xc4, 0xe6, 0x4c, 0xfb, 0xb6, 0x42, 0x5d, 0x48, 0xe8, 0x0c, 0x00, 0x29])
	hasher = hashlib.md5()
	hasher.update(seed)
	hasher.update(name.encode('utf-8'))
	hash_bytes = bytearray(hasher.digest())  # Convert to bytearray for modification
	hash_bytes[6] &= 0x0f
	hash_bytes[6] |= 0x30
	hash_bytes[8] &= 0x3f
	hash_bytes[8] |= 0x80
	return bytes(hash_bytes)  # Convert back to bytes

class UUIDManager:
	def __init__(self, pOffset = 65536, pSnapshot = False):
		self.uuids = []
		self.offset = pOffset
		self.snapshot = pSnapshot

	def LookupUUID(self, hash_value):
		"""
		Looks up a UUID by its hash.
		"""
		for uuid_data in self.uuids:
			if uuid_data['hash'] == hash_value:
				return uuid_data
		return None

	def LookupName(self, name):
		"""
		Looks up a UUID by its name.
		"""
		for uuid_data in self.uuids:
			if uuid_data['name'] == name:
				return uuid_data
		return None

	def LookupType(self, ID):
		"""
		Looks up a UUID by its type ID.
		"""
		if not self.snapshot:
			if 0 <= ID - self.offset < len(self.uuids):
				return self.uuids[ID - self.offset]
			else:
				return None
		else:
			for uuid_data in self.uuids:
				if uuid_data['type_id'] == ID:
					return uuid_data
			return None

	def RegisterName(self, name: str, type_id = None):
		"""
		Registers a new UUID with the given name and type ID.
		If type_id is not provided, it defaults to offset - current number of UUIDs.
		"""
		if type_id is None:
			type_id = self.offset - len(self.uuids)
		self.uuids.append({
			'name': name,
			'hash': createTwMD5Hash(name),
			'type_id': type_id
		})
