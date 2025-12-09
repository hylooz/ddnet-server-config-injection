# packer
class MsgPacker:
	def __init__(self, msg, sys, flag):
		self.result = bytearray([2 * msg + (1 if sys else 0)])
		self.sys = sys
		self.flag = flag

	def AddString(self, s):
		self.result.extend(s.encode('utf-8'))
		self.result.append(0x00)

	def AddBuffer(self, buffer):
		self.result.extend(buffer)

	def AddInt(self, i):
		result = []
		pDst = (i >> 25) & 0x40
		i = i ^ (i >> 31)
		pDst |= i & 0x3f
		i >>= 6
		if i:
			pDst |= 0x80
			result.append(pDst)
			while True:
				pDst = i & 0x7f
				i >>= 7
				pDst |= (int(i != 0)) << 7
				result.append(pDst)
				if not i:
					break
		else:
			result.append(pDst)

		self.result.extend(result)

	@property
	def size(self) -> int:
		return len(self.result)

	@property
	def buffer(self) -> bytes:
		return bytes(self.result)

def unpackInt(pSrc) -> tuple[int, bytes]:
	if not pSrc:
		return 0, b""
	src_index = 0
	sign = (pSrc[src_index] >> 6) & 1
	result = (pSrc[src_index] & 0b00111111)
	while src_index < len(pSrc) and src_index <= 4:
		if (pSrc[src_index] & 0b10000000) == 0:
			break
		src_index += 1
		if src_index < len(pSrc):
			result |= ((pSrc[src_index] & 0b01111111)) << (6 + 7 * (src_index - 1))
		else:
			break
	result ^= -sign
	return result, pSrc[src_index + 1:] if src_index + 1 <= len(pSrc) else b""

def unpackString(pSrc) -> tuple[str, bytes]:
	null_index = pSrc.index(0)
	result = pSrc[:null_index].decode('utf-8')
	remaining = pSrc[null_index + 1:]
	return result, remaining

# unpacker
class MsgUnpacker:
	def __init__(self, data):
		self.remaining = data

	def unpackInt(self) -> int:
		result, self.remaining = unpackInt(self.remaining)
		return result

	def unpackString(self) -> str:
		result, self.remaining = unpackString(self.remaining)
		return result

	def unpackRaw(self, size) -> bytes:
		unpacked = self.remaining[:size]
		self.remaining = self.remaining[size:]
		return unpacked
