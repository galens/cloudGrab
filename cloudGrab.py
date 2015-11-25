#!/usr/bin/python

# cloudGrab by: Galen
# 03/01/2010
#
# known bugs: 
#  - saves file as mp3 no matter what; need to implement proper mime/type checking to fix
#  - jul 2013 - i dont think this works anymore and needs to be rewritten with new urls

import urllib,urllib2, re, sys, time, getopt, os, os.path
from urlparse import urlparse
from urllib2 import Request, urlopen, URLError
from htmlentitydefs import name2codepoint as n2cp

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hdsu:m:k:o:a:b:g:",["help","direct","spider","url=","method=","key=","out=","artist=","album=","genre="])
	except getopt.GetoptError, err:
		print str(err)
		sys.exit()
	
	global out
	global artist
	global album
	global genre
	global retries

	direct = False
	spider = False
	url    = False
	method = False
	key    = False
	out    = False
	artist = False
	album  = False
	genre  = False

	directf = False
	spiderf = False
	urlf    = False
	methodf = False
	keyf    = False
	outf    = False

	retries = 5

	if not sys.argv[1:]:
		print sys.argv[0]+" -h or --help for help"
		sys.exit()
	for o, a in opts:
		if o in ("-h", "--help"):
			print " ### cloudGrab - the soundcloud spider - by: galen ### \n"
			print "Usage: "+sys.argv[0]+" [options]"
			print "---- Modes ----"
			print "   -d  --direct                 rip a song directly"
			print "                                needs url (-u) parameter only"
			print "   -s  --spider                 spider through soundcloud"
			print "                                needs both type (-t) and key (-k) parameter"
			print "---- Variables ----"
			print "   -u  --url=<soundcloud url>   url to test"
			print "                                needed in direct mode (-d)"
			print "   -m  --method=artist          spider method"
			print "                                needed in spider mode (-s)"
			print "                                artist is currently the only mode available"
			print "   -k  --key=<artist name>      name from soundcloud url"
			print "                                needed in spider mode (-s)"
			print "   -o  --out=/home/user/downloads/cloudGrab/rips/"
			print "                                directory to output rips to"
			print "---- Optional Variables ----"
			print "   -a  --artist=<artist name>   manually enter artist"
			print "                                id3 tag for all ripped mp3s"
			print "   -b  --album=<album name>     manually enter album"
			print "                                id3 tag for all ripped mp3s"
			print "   -g  --genre=<genre name>     manually enter genre"
			print "                                id3 tag for all ripped mp3s"
			print "---- Examples ----"
			print "  Spider an entire artists collection:"
			print "     "+sys.argv[0]+" -s -m artist -k the-andychrist -o \"/home/user/music/rips/\""
			print "  Rip a single track only:"
			print "     "+sys.argv[0]+" -d -u \"http://soundcloud.com/the-andychrist/the-andychrist-clouds-are-floating-lakes\" -o \"/home/user/music/rips/\""
			print "  Rip a single track and specify id3 info:"
			print "     "+sys.argv[0]+" -d -u \"http://soundcloud.com/the-andychrist/the-andychrist-clouds-are-floating-lakes\" -o \"/home/user/music/rips/\" -a \"the andychrist\" -g \"goa\""
			sys.exit()
		elif o in ("-d", "--direct"):
			direct = a
			directf = True
		elif o in ("-s", "--spider"):
			spider = a
			spiderf = True
		elif o in ("-u", "--url"):
			url = a
			urlf = True
		elif o in ("-m", "--method"):
			method = a
			methodf = True
		elif o in ("-k", "--key"):
			key = a
			keyf = True
		elif o in ("-o", "--out"):
			out = a
			outf = True
		elif o in ("-a", "--artist"):
			artist = a.title()
		elif o in ("-b", "--album"):
			album = a.title()
		elif o in ("-g", "--genre"):
			genre = a.title()
		else:
			assert False, "unhandled option"

	if (directf == False) & (spiderf == False):
		print "You must provide at least one mode!"
		sys.exit()
	if directf & spiderf:
		print "Direct download and spider mode can not be used simultaneously!"
		sys.exit() 
	if directf & (urlf == False):
		print "You must include the url option and a url when directly ripping a song"
		sys.exit()
	if spiderf & (methodf == False ) | spiderf & ( keyf == False):
		print "You must include both the method, and the keyword when spidering"
		sys.exit()
	if outf == False:
		print "Please provide a directory to output file(s) to with the -o option"
		sys.exit()
	else:
		if out[len(out)-1:len(out)] != "/":
			out += "/"
	if os.path.isdir(out) == False:
		print "Directory: "+out+" does not exist....attempting to create"
		os.makedirs(out)
		if os.path.isdir(out) == False:
			print "Could not create "+out+ " - Please create this directory and try again"
			sys.exit()
	if directf & urlf:
		print "Ripping: "+url
		directRip(url,retries)
		sys.exit()
	if spiderf & methodf & keyf:
		print "Spidering: "+method+" "+key
		spiderSc(method,key)
		sys.exit()

def returnPage(yaurl):
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
	urllib2.install_opener(opener) 
	req = urllib2.Request(yaurl)
	req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0')

	try:
		response = opener.open(req).read()
	except URLError, e:
		if hasattr(e, 'reason'):
			print 'We failed to reach a server.'
			print 'Reason: ', e.reason
		elif hasattr(e, 'code'):
			print 'The server couldn\'t fulfill the request.'
			print 'Error code: ', e.code
	else:
		return response

def remoteFileExist(yaurl):
	req = urllib2.Request(yaurl)
	req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0')
	try:
		resp = urllib2.urlopen(req)
	except urllib2.URLError, e:
		return False
	else:
		return True

def spiderSc(yamethod,yakey):
	# check which method was used
	if yamethod == "artist":
		yastack = []
		urlFull = "http://soundcloud.com/"+yakey
		pgTest  = returnPage(urlFull)

		if (pgTest == None) | (pgTest == False):
			print "The sound cloud url of: http://soundcloud.com/"+yakey+" appears to be invalid.\nPlease check the url and try again"
			sys.exit()

		# find number of pages
		pages = re.findall("page=\w{1,5}",pgTest)
		
		if not pages:
			# only one page of song links
			pgurl     = urlFull+"/tracks?page=1"
			retTracks = returnPage(pgurl)
			rawurl    = re.findall("\},\"uri\":\".{1,500}\",\"duration",retTracks)
				
			# iterate tracks on a page
			for j in rawurl:
				rawSong = j[9:-11]
				full    = "http://soundcloud.com"+rawSong
				directRip(full,retries)
		else:
			# multiple pages of song links
			for pg in pages:
				tmp = pg.split('=')
				yastack.append(tmp[1])

			# highest page
			maxpg = max(yastack)
			cnt   = 0

			# iterate pages
			for i in range(1,int(maxpg)+1):
				cnt += 1
				strCnt    = str(cnt)
				pgurl     = urlFull+"/tracks?page="+strCnt
				retTracks = returnPage(pgurl)
				rawurl    = re.findall("\},\"uri\":\".{1,500}\",\"duration",retTracks)
				
				# iterate tracks on a page
				for j in rawurl:
					rawSong = j[9:-11]
					full    = "http://soundcloud.com"+rawSong
					directRip(full,retries)
	else:
		print "Alternate spider methods have not been implemented, use artist only for now"

def directRip(yaurl,maxretries):
	raw = returnPage(yaurl)
	if (raw != None) | (raw != False):
		raw = raw.replace("\u0026","&")
		raw = raw.replace("amp;","")
		raw = removeNonAscii(raw)
		raw = decode_htmlentities(raw)

		rawid = re.findall("\"uid\":\"\w{12}\",\"user\"",raw)
		uid   = re.findall("\w{12}",rawid[0])

		rawfold = re.findall("\"permalink\":\".{1,200}\"\},\"uri",raw)
		rawfold = rawfold[0].replace("\"permalink\":\"","")
		folder  = rawfold[:-7]
		folder  = folder.replace("-"," ")
		folder  = folder.title()

		rawtitle = re.findall("\"title\":\".{1,200}\",\"commentable",raw)
		rawtitle = rawtitle[0].replace("\"title\":\"","")
		title    = rawtitle.replace("\",\"commentable","")
		title    = title.replace("/","-")

		# create subdirectory
		subdir = out+folder
		if subdir[len(subdir)-1:len(subdir)] != "/":
			subdir += "/"
		if not os.path.exists(subdir):
			print "Creating subdirectory: "+folder
			os.makedirs(subdir)

		if not os.path.exists(subdir):
			print "Failed to create subdirectory, saving file to: "+out
			fileout = out
		else:
			fileout = subdir

		# rip song
		ripurl = "http://media.soundcloud.com/stream/"+uid[0]
		file_name = fileout+title+".mp3"

		if os.path.exists(file_name):
			print "File "+title+" already exists! Skipping."
		else:
			pgExist = remoteFileExist(ripurl)		
			if pgExist == False:
				for i in range(1,retries+1):
					pgExist = remoteFileExist(ripurl)
					if pgExist != False:
						break
			if pgExist == False:
				print "There was a problem downloading "+title+" ... Skipping."
			else:
				u = urllib2.urlopen(ripurl)
				f = open(file_name, 'wb')
				meta = u.info()
				file_size = int(meta.getheaders("Content-Length")[0])
				print "Downloading: %s Bytes: %s" % (file_name, file_size)

				file_size_dl = 0
				block_sz = 1024
				while True:
					buffer = u.read(block_sz)
					if not buffer:
						break

					file_size_dl += block_sz
					f.write(buffer)
					status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
					status = status + chr(8)*(len(status)+1)
					print status,
				f.close()

				if title.count('-'):
					arTitle = title.split('-')
					yaartist = arTitle[0].strip(' ')
					yatitle  = arTitle[1].strip(' ')
				else:
					yaartist = folder.strip(' ')
					yatitle  = title.strip(' ')

				if artist != False:
					yaartist = artist
				
				if album != False:
					tagMp3(file_name,'ALBUM',album)

				if genre != False:
					tagMp3(file_name,'GENRE',genre)

				yacomment = "galen's cloudGrab"

				print "Writing ID3 tags to file: "+title
				tagMp3(file_name,'ARTIST',yaartist)	
				tagMp3(file_name,'TITLE',yatitle)
				tagMp3(file_name,'COMMENT',yacomment)
	else:
		if maxretries == 0:
			print "There was an unexpected error with: "+yaurl+" ...skipping"
		else:
			maxretries -= 1
			directRip(yaurl,maxretries)

def tagMp3(filename,idtag,idvalue):
	id3info = ID3(filename)
	id3info[idtag] = idvalue

def showTag(filename):
	id3info = ID3(filename)
	return id3info

# https://github.com/sku/python-twitter-ircbot/blob/321d94e0e40d0acc92f5bf57d126b57369da70de/html_decode.py 
def decode_htmlentities(string):

    def substitute_entity(match):
        ent = match.group(3)
        if match.group(1) == "#":
            # decoding by number
            if match.group(2) == '':
                # number is in decimal
                return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x'+ent, 16))
        else:
            # they were using a name
            cp = n2cp.get(ent)
            if cp: return unichr(cp)
            else: return match.group()
    
    entity_re = re.compile(r'&(#?)(x?)(\w+);')
    return entity_re.subn(substitute_entity, string)[0]

# http://stackoverflow.com/questions/1342000/how-to-make-the-python-interpreter-correctly-handle-non-ascii-characters-in-stri
def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)
	
if __name__ == "__main__":
	main()
