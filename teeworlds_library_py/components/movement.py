class NetObj_PlayerInput:
	def __init__(self):
		self.m_Direction = 0
		self.m_TargetX = 0
		self.m_TargetY = 0
		self.m_Jump = 0
		self.m_Fire = 0
		self.m_Hook = 0
		self.m_PlayerFlags = 1
		self.m_WantedWeapon = 1
		self.m_NextWeapon = 0
		self.m_PrevWeapon = 0

class Movement:
	input = None
	def __init__(self):
		self.input = NetObj_PlayerInput()

	def RunLeft(self):
		self.input.m_Direction = -1;

	def RunRight(self):
		self.input.m_Direction = 1;

	def RunStop(self):
		self.input.m_Direction = 0;

	def Jump(self, state = True):
		self.input.m_Jump = int(state)

	def Fire(self):
		self.input.m_Fire += 1

	def Hook(self, state = True):
		self.input.m_Hook = int(state)

	def NextWeapon(self):
		self.input.m_NextWeapon = 1;
		self.WantedWeapon(0);

	def PrevWeapon(self):
		self.input.m_PrevWeapon = 1;
		self.WantedWeapon(0);

	def WantedWeapon(self, weapon):
		self.input.m_WantedWeapon = weapon;

	def SetAim(self, x, y):
		self.input.m_TargetX = x;
		self.input.m_TargetY = y;

	def Flag(self, toggle, num):
		if toggle:
			self.input.m_PlayerFlags |= num;
		else:
			self.input.m_PlayerFlags &= ~num;

	def FlagPlaying(self, toggle = True):
		self.Flag(toggle, 1);

	def FlagInMenu(self, toggle = True):
		self.Flag(toggle, 2);

	def FlagChatting(self, toggle = True):
		self.Flag(toggle, 4);

	def FlagScoreboard(self, toggle = True):
		self.Flag(toggle, 8);

	def FlagHookline(self, toggle = True):
		self.Flag(toggle, 16);

	def Reset(self):
		self.input.m_Direction = 0;
		self.input.m_Jump = 0;
		self.input.m_Fire = 0;
		self.input.m_Hook = 0;
		self.input.m_PlayerFlags = 0;
		self.input.m_NextWeapon = 0;
		self.input.m_PrevWeapon = 0;
