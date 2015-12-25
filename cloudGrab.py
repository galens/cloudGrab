#!/usr/bin/python

# cloudGrab by:   Galen Senogles
# created: 		  03/01/2010
# latest updated: 12/24/2015
#
# version 0.2
#

import urllib,urllib2, re, sys, time, getopt, os, os.path, fnmatch, json
from urlparse import urlparse
from urllib2 import Request, urlopen, URLError
from htmlentitydefs import name2codepoint as n2cp
from mimetypes import guess_extension

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
	global user_agent
	
	user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0';

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
			print "                                needs both method (-m) and key (-k) parameter"
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
			print "     "+sys.argv[0]+" -s -m artist -k dogoftears -o \"/home/user/music/rips/\""
			print "  Rip a single track only:"
			print "     "+sys.argv[0]+" -d -u \"https://soundcloud.com/dogoftears/spiral70a-mastered-by-sean-price-mlc\" -o \"/home/user/music/rips/\""
			print "  Rip a single track and specify id3 info:"
			print "     "+sys.argv[0]+" -d -u \"https://soundcloud.com/dogoftears/spiral70a-mastered-by-sean-price-mlc\" -o \"/home/user/music/rips/\" -a \"the Dog of Tears\" -g \"rusted fucktech\""
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
		directRip(url)
		sys.exit()
	if spiderf & methodf & keyf:
		print "Spidering: "+method+" "+key
		spiderSc(method,key)
		sys.exit()

def returnPage(yaurl, song=False):
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
	urllib2.install_opener(opener) 
	req = urllib2.Request(yaurl)
	req.add_header('User-Agent', user_agent)

	try:
		if song:
			print 'Downloading file.'
			CHUNK = 16 * 1024
			try:
				response = urllib2.urlopen(yaurl)
			except urllib2.HTTPError, err:
				if err.code == 404:
					print "Page not found error, exiting!"
					exit()
				elif err.code == 401:
					# this occurs when you attempt to download a song when you are not allowed to
					# which shouldn't occur except soundcloud has bugs(?) and incorrectly said the song was downloadable
					return 'unauthorized'
				elif err.code == 403:
					print "Access denied error, exiting!"
					exit()
				else:
					print "Something happened! Error code", err.code
			except urllib2.URLError, err:
				print "Some other error happened:", err.reason
				exit()
			extension = guess_extension(response.info()['Content-Type'])
			file_path = (song+extension)
			with open(file_path.strip(), 'wb') as f:
				while True:
					chunk = response.read(CHUNK)
					if not chunk: break
					f.write(chunk)
		else:
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
	req.add_header('User-Agent',user_agent)
	try:
		resp = urllib2.urlopen(req)
	except urllib2.URLError, e:
		return False
	else:
		return True
		
def returnList(offset=0):	
	full_url = 'https://api-v2.soundcloud.com/stream/users/%s?client_id=%s&limit=10000&offset=0&linked_partitioning=1&app_version=%s' % (user_vars['user_id'], user_vars['client_id'], user_vars['app_version']) 
	#print full_url
	
	return returnPage(full_url)
	
def loop_maintenance(dl, rt):
	dl += 1
	rt += 1
	if(rt == 10):
		time.sleep(5)
		rt = 0
		
	return [dl, rt]

def spiderSc(yamethod, yakey):
	# check which method was used
	songs_downloaded = 0
	rotations = 0
	
	if yamethod == "artist":
		urlFull = "http://soundcloud.com/"+yakey
		print urlFull
		site_content  = returnPage(urlFull)

		if (site_content == None) | (site_content == False):
			print "The sound cloud url of: http://soundcloud.com/"+yakey+" appears to be invalid.\nPlease check the url and try again"
			sys.exit()
			
		set_user_vars(site_content)

		list_content = clean_output(returnList())
		parsed_list  = json.loads(list_content, strict=False)
		for i in parsed_list['collection']:
			if 'track' in i:
				print 'ripping: ' + i['track']['permalink_url']
				ret_main = loop_maintenance(songs_downloaded, rotations)
				rotations = ret_main[1]
				songs_downloaded = ret_main[0]
				directRip(i['track']['permalink_url'])
			elif 'playlist' in i:
				for j in i['playlist']['tracks']:
					if 'permalink_url' in j:
						print 'ripping: ' + j['permalink_url']
						ret_main = loop_maintenance(songs_downloaded, rotations)
						rotations = ret_main[1]
						songs_downloaded = ret_main[0]
						
		print '%s songs downloaded!' % (songs_downloaded)
	else:
		print "Alternate spider methods have not been implemented, use artist only for now"
		
def clean_output(dirty):
	dirty = dirty.replace("\u0026","&")
	dirty = dirty.replace("amp;","")
	return decode_htmlentities(removeNonAscii(dirty))
	
def set_user_vars(site_content, app_js_check=None):
	global user_vars
	global app_js
	 
	user_vars = {}	
	site_content = clean_output(site_content)
		
	username	 = re.findall("username\":\".{1,100}\",\"verified", site_content)
	username	 = username[0].split(':')
	username 	 = username[1][1:-11]
	username	 = username.replace("'", '')
	username	 = username.replace('"', '')
	username	 = username.replace('\\', '')
	username	 = username.replace('/', '')
	username	 = username.replace('?', '')
	username	 = username.replace(':', '')
	username	 = username.replace('*', '')
	username	 = username.replace('<', '')
	username	 = username.replace('>', '')
	username	 = username.replace('|', '')

	if app_js_check == None:
		site_app_js  = re.findall("src.{1,20}cdn.com\/assets\/app.{1,20}\.js", site_content)
		site_app_js  = site_app_js[0].replace('src="', '')
		app_js 		 = returnPage(site_app_js)
		app_js		 = clean_output(app_js)

	app_version  = re.findall("sc_version.{1,30}\"", site_content)
	app_version	 = app_version[0].replace('sc_version = "', '')
	app_version	 = app_version.replace('"', '')

	client_id	 = re.findall("client_id:\".{1,50}\"", app_js)
	client_id	 = client_id[0].replace('client_id:"', '')
	client_id	 = client_id.replace('"', '')
	
	try:	
		user_id		 = re.findall("soundcloud://users:.{1,15}\"", site_content)
		user_id		 = user_id[0].split(':')
		user_id		 = user_id[2][:-1]
		user_vars['user_id'] = user_id
	except:
		pass
				
	user_vars['username'] = username
	user_vars['site_app_js'] = site_app_js
	user_vars['app_version'] = app_version
	user_vars['client_id'] = client_id	
	#print user_vars
		
def set_track_vars(site_content, no_download=False):
	global track_vars
	
	track_vars  = {}
	site_content = clean_output(site_content)
	
	downloadable = re.findall("downloadable\":(false|true),\"", site_content)
	if 'true' in downloadable:
		download_url = re.findall("\"download_url\":\".{1,200},\"duration\":", site_content)
		download_url = download_url[0][16:-13]
	else:
		download_url = False	
			
	title		 = re.findall("title\":\".{1,100}\",\"uri\":\"", site_content)
	title		 = title[0][8:-9]
	title		 = title.replace("'", '')
	title		 = title.replace('"', '')
	title		 = title.replace("\\", '')
	title		 = title.replace("/", '')
	title		 = title.replace("?", '')
	title		 = title.replace(":", '')
	title		 = title.replace("*", '')
	title		 = title.replace("<", '')
	title		 = title.replace(">", '')
	title		 = title.replace("|", '')

	api_number	 = re.findall("sounds:.{1,20}\"", site_content)
	api_number	 = api_number[-1].replace('sounds:','')
	api_number	 = api_number.replace('"','')

	song_url	 = 'https://api.soundcloud.com/i1/tracks/%s/streams?client_id=%s&app_version=%s' % (api_number, user_vars['client_id'], user_vars['app_version'])

	source_url 	 = returnPage(song_url)
	source_url 	 = clean_output(source_url)
		
	if (download_url) and (no_download == False):
		source_url = '%s?client_id=%s' % (download_url, user_vars['client_id'])
	else: 
		parsed  = json.loads(source_url)
		source_url = parsed['http_mp3_128_url']

	track_vars['download_url'] = download_url
	track_vars['title'] = title
	track_vars['api_number'] = api_number
	track_vars['song_url'] = song_url
	track_vars['source_url'] = source_url
	
def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result
	
def directRip(yaurl):
	count = 0
	while(count < 3):
		site_content = returnPage(yaurl)
		if (site_content != None) | (site_content != False):
			break
		else:
			count += 1
			
	set_user_vars(site_content)
	set_track_vars(site_content)
	
	# create subdirectory
	subdir = out+user_vars['username']
	if subdir[len(subdir)-1:len(subdir)] != "/":
		subdir += "/"
	if not os.path.exists(subdir):
		print "Creating subdirectory: "+user_vars['username']
		os.makedirs(subdir)

	if not os.path.exists(subdir):
		print "Failed to create subdirectory, saving file to: "+out
		fileout = out
	else:
		fileout = subdir

	# rip song
	file_name = '%s%s' % (fileout, track_vars['title'])
	#print file_name
		
	if find(track_vars['title'] + '*', fileout):
		print "File %s already exists! Skipping." % (track_vars['title'])
	else:
		response = returnPage(track_vars['source_url'], file_name)
		if response == 'unauthorized':
			set_track_vars(site_content, True)
			returnPage(track_vars['source_url'], file_name)
			
		#returnPage('https://api.soundcloud.com/tracks/216493786/download?client_id=02gUJC0hH2ct1EGOcYXQIzRFU91c72Ea', file_name)

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
