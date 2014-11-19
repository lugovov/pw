import re
import urllib
import httplib
import os
import argparse
import xml.etree.ElementTree as Xml
from urlparse import urlparse


def request(url, param="", headers={}, method="GET"):
    if type(param) is dict:
        param = urllib.urlencode(param)

    uri = urlparse(url)
    conn = httplib.HTTPConnection(uri.netloc)
    conn.request(method, uri.path, param, headers)
    return conn.getresponse(), conn


def getCookies(responce):
    result = {}
    cookies = responce.getheader('set-cookie')
    if not cookies:  # cookies not found
        return result
    temp = re.split(",(?= \w+[\w\d]*=)", cookies)
    for cookie in temp:
        slices = re.split('=|; ', cookie)
        result.update({slices[0]: slices[1]})
    return result


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("login", help="GameCenter@Mail.ru login")
    parser.add_argument("password", help="GameCenter@Mail.ru password")
    parser.add_argument("-a","--account", help="GameCenter@Mail.ru account id")
    parser.add_argument("-s", "--server", help="login server address")
    return parser.parse_args()


def main():
	args = parseArgs()
	uagent='Downloader/4260'
	split = args.login.split("@")
	if len(split) < 2:
	    raise Exception("Bad email '{0}'".format(args.login))
	if not os.path.isfile('elementclient.exe'):
	    raise Exception("elementclient.exe not found")

	login = split[0]
	domain = split[1]
	password = args.password
	server = args.server or "178.22.90.37:29000"


	maildomains=['mail.ru','inbox.ru','bk.ru','list.ru']
	if domain in maildomains:
		params = {"Login": login, "Domain": domain, "Password": password}

		resp, conn = request(
			"http://win.mail.ru/cgi-bin/auth", params, method="POST")
		conn.close()

		cookies = getCookies(resp)
		if 'Mpop' not in cookies:
		    raise Exception(' '.join(["Authorization failed",login,domain,password]))

		mpop = cookies['Mpop']

		url = 'https://authdl.mail.ru/sz.php?hint=AutoLogin'
		params = '<?xml version="1.0" encoding="UTF-8"?>' + \
		         '<AutoLogin ProjectId="61" SubProjectId="0" ShardId="0" ' + \
		         'Mpop="%s"/>' % mpop
		headers = {'User-Agent': 'Downloader/4260'}
		resp, conn = request(url, params, headers, "POST")
		xml = resp.read()
		conn.close()
		root = Xml.fromstring(xml)

		uid2 = root.attrib['PersId']
		token = root.attrib['Key']

		url = 'https://authdl.mail.ru/sz.php?hint=PersList'
		params = '<?xml version="1.0" encoding="UTF-8"?>' + \
		         '<PersList ProjectId="61" SubProjectId="0" ShardId="0" ' + \
		         'Mpop="%s"/>' % mpop
		headers = {'User-Agent': 'Downloader/4260'}
		resp, conn = request(url, params, headers, "POST")
		xml = resp.read()
		conn.close()
	else:
		login = split[0]
		domain = split[1]
		password = args.password
		server = args.server or "178.22.90.37:29000"
		url = 'https://authdl.mail.ru/sz.php?hint=Auth'
		params = '<?xml version="1.0" encoding="UTF-8"?>' + \
		'<Auth ProjectId="61" SubProjectId="0" ShardId="0" Username="{0}" Password="{1}"/>'.format(args.login,args.password)
	   	headers = {'User-Agent': uagent}
	   	resp, conn = request(url, params, headers, "POST")
	   	xml = resp.read()
	   	print(xml)
	   	conn.close()
	   	root = Xml.fromstring(xml)
		PersId=root.attrib['PersId']
		url = 'https://authdl.mail.ru/sz.php?hint=AutoLogin'
		params = '<?xml version="1.0" encoding="UTF-8"?>' + \
 	         '<AutoLogin ProjectId="61" SubProjectId="0" ShardId="0" ' + \
   	         ' Username="{0}" Password="{1}"/>'.format(args.login,args.password)
		headers = {'User-Agent': uagent}
		resp, conn = request(url, params, headers, "POST")
		xml = resp.read()
		print(xml)
		conn.close()
		root = Xml.fromstring(xml)

		uid2 = root.attrib['PersId']
		token = root.attrib['Key']

		url = 'https://authdl.mail.ru/sz.php?hint=PersList'
		params = '<?xml version="1.0" encoding="UTF-8"?>' + \
	         '<PersList ProjectId="61" SubProjectId="0" ShardId="0" ' + \
	         ' Username="{0}" Password="{1}"/>'.format(args.login,args.password)
		headers = {'User-Agent': uagent}
		resp, conn = request(url, params, headers, "POST")
		xml = resp.read()
		print(xml)
		conn.close()
		
	root = Xml.fromstring(xml)
	allPers=root.findall('./Pers')
	if len(allPers)<= int(args.account or "0"):
	    raise Exception("Accounts in email too small")
	Pers = allPers[int(args.account or "0")]
	uid = Pers.attrib['Id']
	

	commandline = ' '.join(["start", "elementclient.exe", "game:cpw", "startbypatcher",
                            "user:" + uid,
                            "_user:" + uid2,
                            "token2:" + token])

	print "Starting client with", args.server or "default", "server"
	print commandline
	
	os.system(commandline)

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        print e
