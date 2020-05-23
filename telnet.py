#Auteur --> aiglematth

#Imports
from socket import *

#Exceptions
class TelnetError(Exception):
	"""
	Erreur de base de Telnet
	"""
	def __init__(self):
		"""
		Constructeur
		"""
		Exception.__init__(self)

	def __str__(self):
		"""
		On surcharge cette méthode pour que str(monException) renvoie un prompt cool
		"""
		return "Telnet error"

class TelnetConnectionError(TelnetError):
	"""
	On est pas connecté
	"""
	def __init__(self):
		"""
		Constructeur
		"""
		TelnetError.__init__(self)

	def __str__(self):
		"""
		On surcharge cette méthode pour que str(monException) renvoie un prompt cool
		"""
		return "Telnet connection is not established"

class TelnetBadUserPasswd(Exception):
	"""
	On a pas pu se connecter
	"""
	def __init__(self):
		"""
		Constructeur
		"""
		TelnetError.__init__(self)

	def __str__(self):
		"""
		On surcharge cette méthode pour que str(monException) renvoie un prompt cool
		"""
		return "Telnet login or password is False"


#Classes
class TelnetCodes():
	"""
	--- IMPORTANT ---
	Pour changer le comportement
	--- --------- ---
	On rassemble les codes dans une seule classe...
	Par défaut, on va répondre à la négative à toutes les demandes
	du serveur, SAUF pour un WILL ECHo où on répondra DO ECHO. Pour
	changer le comportement par défaut, il suffit de surcharger la
	méthode goodMess avec vos options.
	la méthode
	"""
	def __init__(self):
		"""
		Constructeur
		"""
		#Codes de base
		self.IAC       = "\xff"

		#Codes opérations
		self.SE        = "\xf0"
		self.NOP       = "\xf1"
		self.DATA_MARK = "\xf2"
		self.BREAK     = "\xf3"
		self.IP        = "\xf4"
		self.AO        = "\xf5"
		self.AYT       = "\xf6"
		self.EC        = "\xf7"
		self.EL        = "\xf8"
		self.GA        = "\xf9"
		self.SB        = "\xfa"
		self.WILL      = "\xfb"
		self.WONT      = "\xfc"
		self.DO        = "\xfd"
		self.DONT      = "\xfe"

		#Codes options
		self.BIN_TRANS   = "\x00"
		self.ECHO 	     = "\x01"
		self.RECO	     = "\x02"
		self.SUPP_GOAHED = "\x03"
		self.MESS_SIZE	 = "\x04"
		self.STATUS      = "\x05"
		self.TIMING_MARK = "\x06"
		self.REM_CONTROL = "\x07"
		self.LINE_WIDTH  = "\x08"
		self.PAGE_SIZE   = "\x09"
		self.CAR_RET_POS = "\x0a"
		self.H_TAB_STOP  = "\x0b"
		self.H_TAB_DISP  = "\x0c"
		self.FORM_DISP   = "\x0d"
		self.V_TAB_STOP  = "\x0e"
		self.V_TAB_DISP  = "\x0f"
		self.LINE_DISP   = "\x10"
		self.EXT_ASCII   = "\x11"
		self.LOGOUT      = "\x12"
		self.BYTE_MACRO  = "\x13"
		self.ENTRY_TERM  = "\x14"
		self.SUPDUP      = "\x15"
		self.SUPDUP_OUT  = "\x16"
		self.SEND_LOC    = "\x17"
		self.TERM_TYPE   = "\x18"
		self.END_RECORD  = "\x19"
		self.TACAS_USER  = "\x1a"
		self.OUT_MARK    = "\x1b"
		self.TERM_LOC    = "\x1c"
		self.TELN_3070   = "\x1d"
		self.X3_PAD      = "\x1e"
		self.WINDOW_SIZE = "\x1f"
		self.TERM_SPEED  = "\x20"
		self.REM_FLOW    = "\x21"
		self.LINEMODE    = "\x22"
		self.X_DISP_LOC  = "\x23"
		self.EXTEND_OPT  = "\xff"

		#Codes formattage
		self.NULL	   = "\x00"
		self.BELL      = "\x07"
		self.BS        = "\x08"
		self.HT        = "\x09"
		self.LF		   = "\x0a"
		self.VT        = "\x0b"
		self.FF        = "\x0c"
		self.CR        = "\x0d"

		#Codes dont j'ai besoin par défaut
		self.DONT_ECHO = self.create(self.DONT, self.ECHO)
		self.DO_ECHO   = self.create(self.DO, self.ECHO)

		# NOTE #
		# Vous pouvez rajouter vos variables en héritant de cette classe
		# #### #

		self.mess   = None
		self.toSend = []

	def create(self, *codes):
		"""
		On va créer un code correct en mettant l'IAC au début
		:param *codes: Les codes à mettre à la suite
		:return: 	   Le code correct
		"""
		correct = self.IAC

		for code in codes:
			correct += code

		return correct

	def inverser(self):
		"""
		Permet de répondre à la négative à toutes les options proosées par le serveur
		"""
		messFinal = ""

		for byte in self.mess:
			if byte == self.DO.encode("latin-1"):
				messFinal += self.WONT
			elif byte == self.WILL.encode("latin-1"):
				messFinal += self.DONT
			elif byte == self.DONT.encode("latin-1"):
				messFinal += self.WONT
			elif byte == self.WONT.encode("latin-1"):
				messFinal += self.DONT
			else:
				messFinal += chr(byte)

		self.mess = messFinal

	def allowEcho(self):
		"""
		Transforme le DON'T ECHO en DO ECHO. Obligé de faire ceci car le serveur VEUT faire de l'echo...
		"""
		self.mess = self.mess.replace(self.DONT_ECHO, self.DO_ECHO)	

	def goodMess(self, mess):
		"""
		--- A SURCHARGER POUR CHANGER LE COMPORTEMENT ---
		Si vous avez des informations à envoyer, les mettre dans self.toSend
		en chaine de chars (strings)
		Transforme mess en l'inverse, tout en acceptant l'echo
		:param mess: Le mess en bytes
		:return:	 Un mess valide
		"""
		self.mess = mess

		self.inverser()
		self.allowEcho()

		return self.mess

class Telnet():
	"""
	Classe principale, permet d'établir une connection avec la cible
	"""
	def __init__(self, host, port=23, user="", passwd="", parse=TelnetCodes):
		"""
		Constructeur
		:param host:   La machine à cibler
		:param port:   Le port cible
		:param user:   Le nom d'utilisateur
		:param passwd: Le mot de passe
		:param parse:  La classe (ou une fille) TelnetCodes, elle décrit les options utilisées
		"""
		#Attributs
		self.sockTupl = (self.host, self.port) = (host, port)
		self.user     = user
		self.passwd   = passwd

		#Notre nécessaire ^^
		self.buffSize  = 1024
		self.timeout   = 0.5
		self.encode    = "latin-1"
		self.eol       = "\r\n"
		self.parse     = parse()
		self.sock      = None
		self.prompt    = None
		self.isConnect = False

	def recv(self):
		"""
		Permet de se simplifier la vie car cette méthode retourne :
			- self.sock.recv(self.buffSize)
		:return: self.sock.recv(self.buffSize)
		"""
		return self.sock.recv(self.buffSize)

	def recvPrompt(self):
		"""
		On tente d'établir ce qu'est le prompt, pour ce faire, on envoi
		une commande vide, et on strip le résultat
		:return: Potentiellement un prompt valide
		"""
		return self.send("").strip()

	def vide(self):
		"""
		Vide le buffer de reception
		"""
		self.sock.settimeout(self.timeout)

		try:
			while True:
				self.recv()
		except timeout:
			self.sock.settimeout(None)
			return None

	def send(self, mess, vide=True, result=True):
		"""
		Permet d'envoyer proprement un message
		:param mess:   Le message
		:param vide:   Est ce qu'on vide explicitement le buffer...
		:param result: On retourne en resultat le contenu du buffer
		:return      La réponse au message
		"""
		if vide == True:
			self.vide()

		self.sock.send(mess.encode(self.encode) + self.eol.encode(self.encode))

		if result != True:
			return None

		result = ""

		self.sock.settimeout(self.timeout)
		try:
			while True:
				result += self.recv().decode()
		except timeout:
			self.sock.settimeout(None)
			return result

	def sendCommande(self, commande, checkPrompt=False):
		"""
		Envoi un commande et tente de ne récup que le resultat
		:param commande:    La commande à envoyer
		:param checkPrompt: Si ce param est à true, on va envoyer une requete pour avoir le prompt du shell...attention, perte de temps !
		:return:         Un résultat
		"""
		if checkPrompt == True:
			self.prompt = self.recvPrompt()
		result      = self.send(commande, vide=False)
		result      = result.replace(self.prompt, "")
		result      = result.replace(commande, "")
		result      = result.strip()
		return result

	def connect(self):
		"""
		Permet de se connecter en Telnet
		"""
		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.connect(self.sockTupl)

		#Negociations
		for req in self.parse.toSend:
			self.sock.send(req.encode(self.encode))

		while True:
			neg = self.recv()
			if self.parse.IAC.encode(self.encode) not in neg:
				break
			reponse = self.parse.goodMess(neg)
			self.sock.send(reponse.encode(self.encode))

		#Envoi du login/mdp
		self.send(self.user)
		end = self.send(self.passwd)
		neg = neg.decode()

		#On vérifie qu'on a passé l'épreuve du MDP^^
		if neg in end or end in neg:
			raise TelnetBadUserPasswd

		self.prompt    = self.recvPrompt()
		self.isConnect = True

	def interractive(self):
		"""
		On ouvre un ptit client telnet
		"""
		if self.isConnect != True:
			raise TelnetConnectionError

		try:
			print(self.recvPrompt(), end="")
			while True:
				commande = input()
				if commande in ["exit", "quit"]:
					self.close()
					break
				print(self.send(commande, vide=False), end="")
		except KeyboardInterrupt:
			return None

	def close(self):
		"""
		Clos la connection
		"""
		self.send("exit", vide=False, result=False)
		self.sock.close()

	def __enter__(self):
		"""
		On fais en sorte que notre objet soit utilsable dans un with
		"""
		return self

	def __exit__(self, *args):
		"""
		Même commentaire que pour enter
		"""
		self.close()


if __name__ == "__main__":
	with Telnet("192.168.1.28", user="ytb", passwd="ytb") as t:
		t.connect()
		t.interractive()
		#print(t.send("ls -all /"))
		#print(t.sendCommande("cat /etc/passwd"))