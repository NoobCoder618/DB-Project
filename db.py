'''to implement:
	
	get id
	add column
	update row
	add multiple rows (use extend()?)
	move row/column
	link tables to db
	list tables in db
	rework connection auth to allow close/reconnect
	encrypt data/session auth
	load file only if auth
	db pack/unpack? (write everything to a single encrypted file when not logged in)
 '''

from datetime import datetime
from os import makedirs, path, remove
from random import randint
from atexit import register

now = datetime.now()
fnow = datetime.strftime(now, '%b %d, %Y %H:%M:%S')

def createdb(dbname, login, pw):
	makedirs(dbname, exist_ok=True)
	# create password file
	with open(f'{dbname}/auth.txt', 'w') as authfile:
		authfile.write(f'{login}{pw}')
	# file to store table names
	with open(f'{dbname}/{dbname}.txt', 'w') as dbfile:
		dbfile.write('')
	
def createsid():
	return str(randint(1, 10000))
	
def checkauth(db, sid):
	if path.exists(f'{db}/sid.ses'):
		sesfile = open(f'{db}/sid.ses')
		if sesfile.read() == sid:
			return True
	else:
		return False
		
def connect():
	pass

class dbaccess:
	
	def __init__(self, dbname):
		self.dbname = dbname
		login = input('Enter username: ')
		pw = input('Enter password: ')
		if path.exists(f'{dbname}/auth.txt'):
			authfile = open(f'{dbname}/auth.txt', 'r')
			if authfile.read() == login + pw:
				msg = f'Connected to {dbname}'
				# create session file to prove auth
				self.sid = createsid()
				with open(f'{dbname}/sid.ses', 'w') as sess:
					sess.write(self.sid)
				# db file for table names
				with open(f'{dbname}/{dbname}.txt', 'r') as dbfile:
					self.dbtables = dbfile.read()
			else:
				msg = 'User or pw incorrect'
				authfile.close()
		else:
			msg = 'Database not found'
		print(msg)
		
	def newtable(self, name, *headers):
		newtable = table(
			name,
			*headers,
			db=self.dbname,
			auth=checkauth(self.dbname, self.sid),
			sid=self.sid
			)
		self.dbtables += name + '\n'
		self.save()
		return newtable
		
	def save(self):
		with open(f'{self.dbname}/{self.dbname}.txt', 'w') as dbfile:
			dbfile.write(self.dbtables)
	
	def addtable(self):
		pass
		
	def close(self):
		if path.exists(f'{self.dbname}/sid.ses'):
			remove(f'{self.dbname}/sid.ses')
		print(f'Connection to {self.dbname} closed')
	
	# read table from file
	def loadtable(self, location):
		filename = path.basename(location).rsplit('.', 1)
		openfile = open(location, 'r')
		csv = openfile.read()
		listdata = [i.split(',') for i in csv.split('\n')]
		openfile.close()
		loaded = table(filename[0], fromfile=True, auth=self.auth)
		loaded.data = []
		loaded.tablefile = location
		loaded.lastid = listdata[len(listdata)-1][0]
		for i in listdata:
			loaded.data.append(i)
		return loaded


class table():
	
	def __init__(self, name, *headers, fromfile=False, db='', auth=False, sid=''):
		#self.sid = sid
		if auth:
			# init class attributes
			self.data = [[]]
			self.name = name
			self.sid = sid
			self.lastid = 0
			self.cx, self.cy = 0, 0
			self.logfile = f'{db}/logs/{name}_log.txt'
			if not fromfile:
				# create files
				self.dblink = db
				makedirs(f'{db}/table', exist_ok=True)
				self.tablefile = f'{db}/table/{name}.csv'
				makedirs(f'{db}/logs', exist_ok=True)
				# create table columns
				self.data = [['id']]
				msg = f'Table \'{name}\' created with headers: id, '
				for i in headers:
					self.data[0].append(i)
					msg += f'{i}, '
				if len(headers) != len(set(headers)):
					msg += '\nDUPLICATE HEADERS ENTERED!\n'
				self.save()
			else:
				msg = f'Loaded from file'
			self.log(msg)
		else:
			print('Access denied')
	
	def numCols(self):
		return len(self.data[0])
		
	def numRows(self):
		return len(self.data)
		
	def log(self, msg):
		openlog = open(self.logfile, 'a')
		st = f'{fnow} - {msg}\n'
		openlog.write(st)
		openlog.close()
		
	def addrow(self, *coldata):
		if checkauth(self.dblink, self.sid):
			self.data.append([self.lastid])
			self.lastid += 1
			diff = len(self.data[0]) - len(coldata) - 1
			if diff > 0:
			# not all columns entered
				for i in coldata:
					self.data[self.lastid].append(i)
				for j in range(diff):
					self.data[self.lastid].append('')
				msg = f'Row added with id {self.lastid-1}, not all columns entered'
			# too many columns entered
			elif diff < 0:
				msg = 'Didn\'t add row: too many items entered'
			else:
				for i in coldata:
					self.data[self.lastid].append(i)
					msg = f'Row added with ID {self.lastid-1}'
			self.log(msg)
			return msg
		else:
			print('Access denied')
		
	def delrow(self, id):
		if checkauth(self.dblink, self.sid):
			for y in range(len(self.data)):
				if y == id:
					self.data.remove(self.data[y+1])
					msg = f'Row with ID {id} deleted'
					break
				elif y == len(self.data) - 1 and y != id:
					msg = 'ID not found from delrow()'
			self.log(msg)
			return msg
		else:
			print('Access denied')
	
	# write to file
	def save(self, newfile=''):
		if checkauth(self.dblink, self.sid):
			x, y = 0, 0
			csv = ''		
			while y < len(self.data):
				while x < len(self.data[y]):
					# store item iter in temp string
					csv += str(self.data[y][x])
					# end of row
					if x == (len(self.data[y])-1):
						if y == (len(self.data)-1):
							break # last row, don't add newline
						else:
							csv += '\n'
					else:
						csv += ','
					x += 1 # next column
				y += 1 # next row
				x = 0   # start back at column 0
			if newfile == '':
				opentable = open(self.tablefile, 'w')
			else:
				opentable = open(f'{self.dblink}/table/{newfile}', 'w')
			opentable.write(csv)
			opentable.close()
		else:
			print('Access denied')
	
	def getcellfc(self, x, y):
		# get cell data from x, y coordinates
		# ignoring headers
		if checkauth(self.dblink, self.sid):
			return self.data[y+1][x]
		else:
			print('Access denied')
	
	def getcell(self, header, id):
		if checkauth(self.dblink, self.sid):
			self.getcoord(header, id, func='getcell()')
			return self.data[self.cy][self.cx]
		else:
			print('Access denied')
		
	def updatecell(self, header, id, content):
		if checkauth(self.dblink, self.sid):
			self.getcoord(header, id, func='updatecell()')
			self.data[self.cy][self.cx] = content
			self.log(f'Record updated at {self.cx}, {self.cy}')
		else:
			print('Access denied')
		
	def getcoord(self, header, id, func='getcoord()'):
		if checkauth(self.dblink, self.sid):
			x, y = 0, 0
			# find column from header
			while x < len(self.data[0]):
				if self.data[0][x] == header:
					# found column, now find row from id
					while y < len(self.data):
						if self.data[y][0] == id:
							self.cx, self.cy = x, y
							ret = self.cx, self.cy
							break # found cell
						else:
							# couldn't find row
							ret = 'ID not found from {func}'
							self.log(ret)
						y += 1 # search next row
					break # found row, end search
				else:
					# couldn't find column
					ret = 'Column not found from {func}'
					self.log(ret)
				x += 1 # search next column
			return ret
		else:
			print('Access denied')
		
	def getrow(self, id):
		if checkauth(self.dblink, self.sid):
			y = 1 # ignore headers
			# search for row from id
			while y < len(self.data):
				if self.data[y][0] == id:
					ret = self.data[y]
					break # found it
				else:
					# didn't find it
					ret = 'ID not found from getrow()'
					self.log(ret)
				y += 1
			return ret
		else:
			print('Access denied')
	
	def print(self):
		if checkauth(self.dblink, self.sid):
			print(self.data)
		else:
			print('Access denied')
	
	def display(self, ret=False): # no wrapping for now
		if checkauth(self.dblink, self.sid):
			disp = f'{self.name}\n'
			# get longest string in each column
			# to get width of cells
			w = -1
			wlist = []
			x, y = 0, 0
			while x < len(self.data[y]): # iterate columns 2nd
				while y < len(self.data): # iterate rows 1st
					if len(str(self.data[y][x])) > w:
						w = len(str(self.data[y][x]))
					y += 1
				wlist.append(w) # write to temp list
				w = -1 # reset width check
				y = 0 # back to row 1
				x += 1 # next column
			# now create the display
			x = 0
			hpad = 1
			#vpad = 0
			#define the horizontal lines
			def hline():
				line = ''
				for i in range(len(wlist)):
					line += '+'
					for n in range(wlist[i]+hpad*2):
						line += '—'
				line += '+\n'
				return line
			#top border
			disp += hline()
			#header cells
			while x < len(self.data[0]):
				disp += f'| {str(self.data[0][x]).center(wlist[x])} '
				x += 1
			disp += '|\n'
			#rows
			x, y = 0, 1
			while y < len(self.data):
				#top border for each row
				disp += hline()
				#cell data
				while x < len(self.data[y]):
					disp += f'| {str(self.data[y][x]).ljust(wlist[x])} '
					x += 1
				disp += '|\n'
				x = 0
				y += 1
			#bottom border
			disp += hline()
			
			# draw it up babyyyyyy
			if ret:
				return disp
			else:
				print(disp)
		else:
			print('Access denied')
