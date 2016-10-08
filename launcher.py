import re
import urllib
import httplib
import os
import subprocess
import argparse
import getpass
import xml.etree.ElementTree as Xml
from urlparse import urlparse
from sys import platform as _platform
uagent='Downloader/12340'

def request(url, param="", headers={}, method="GET"):
    if type(param) is dict:
        param = urllib.urlencode(param)
    uri = urlparse(url)
    headers['host']=uri.netloc;
    headers['content-length']=len(param);
    headers['accept']='*/*';
    headers['content-type']='application/x-www-form-urlencoded';
    headers['user-agent']=uagent;

    conn = httplib.HTTPConnection(uri.netloc)
    conn.putrequest(method, uri.path, 1,1,)
    for hdr, value in headers.iteritems():
	conn.putheader(hdr, value)
    conn.endheaders(param)
    return conn.getresponse(), conn


def getCookies(responce):
    result = {}
    cookies = responce.getheader('set-cookie')
    if not cookies:  # cookies not found
        return result
    temp = re.split(",(?= \w+[\w\d]*=)", cookies)
    for cookie in temp:
        slices = re.split('=|; ', cookie)
        result.update({slices[0].strip(): slices[1]})
    return result


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("login", nargs='?', default="", help="email")
    parser.add_argument("password", nargs='?', default="", help="password")
    parser.add_argument("-a","--account", help="account number from 0 (if your mulptiple accounts in email)")
    return parser.parse_args()

def auth(fulllogin,password,account = 0):
    split = fulllogin.split("@")
    if len(split) < 2:
        raise Exception("Bad email '{0}'".format(fulllogin))
    login = split[0]
    domain = split[1]


    maildomains=['mail.ru','inbox.ru','bk.ru','list.ru','mail.ua']
    if domain in maildomains:
	params = {"Login": login, "Domain": domain, "Password": password}

	resp, conn = request(
	    "https://auth.mail.ru/cgi-bin/auth", params, method="POST")
	conn.close()

	cookies = getCookies(resp)
	print resp.getheaders()
	print cookies
	print resp.read()
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
	host='authdl.mail.ru';
	url = 'https://{0}/sz.php?hint=Auth'.format(host)
	begin='ProjectId="61" SubProjectId="0" ShardId="0" UserId="1" UserId2="2" '
	end=' FirstLink="0"'
	params = '<?xml version="1.0" encoding="UTF-8"?>' + \
	'<Auth {2}Username="{0}" Password="{1}"{3}/>'.format(fulllogin,password,begin,end)
        headers = {}

        resp, conn = request(url, params, headers, "POST")
        xml = resp.read()
        conn.close()
        root = Xml.fromstring(xml)
	PersId=root.attrib['PersId']
	url = 'https://{0}/sz.php?hint=AutoLogin'.format(host)
	params = '<?xml version="1.0" encoding="UTF-8"?><AutoLogin {2}Username="{0}" Password="{1}"{3}/>'.format(fulllogin,password,begin,end)

	resp, conn = request(url, params, headers, "POST")
	xml = resp.read()
	conn.close()
	root = Xml.fromstring(xml)

	uid2 = root.attrib['PersId']
	token = root.attrib['Key']

	url = 'https://{0}/sz.php?hint=PersList'.format(host)
	params = '<?xml version="1.0" encoding="UTF-8"?>' + \
             '<PersList {2}Username="{0}" Password="{1}"/>'.format(fulllogin,password,begin,end)
	resp, conn = request(url, params, headers, "POST")
	xml = resp.read()
	conn.close()
    root = Xml.fromstring(xml)
    allPers=root.findall('./Pers')
    if len(allPers)<= int(account or "0"):
        raise Exception("Accounts in email too small")
    Pers = allPers[int(account or "0")]
    uid = Pers.attrib['Id']

    result={"uid":uid, "uid2":uid2, "token":token}
    return result

def main():
    args = parseArgs()
    while args.login == '' or args.password == '':
	print 'Few important arguments is missing. Specify e-mail and password'
	args.login = raw_input('e-mail:')
	args.password = getpass.getpass('password:')
    if not os.path.isfile('elementclient.exe'):
        raise Exception("elementclient.exe not found")

    authdata=auth(args.login,args.password, args.account)
#    print authdata
    if _platform == "linux" or _platform == "linux2":
	startcmd="wine"
    else:
	startcmd="start"
    command=[startcmd, "elementclient.exe", "console:1", "startbypatcher",
                            "user:" + authdata['uid'],
                            "_user:" + authdata['uid2'],
                            "token2:" + authdata['token']]

    print "Starting elementclient.exe"
    subprocess.Popen(command)

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        print e
