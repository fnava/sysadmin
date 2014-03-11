# -*- coding: utf-8 -*-
import csv     
import subprocess,re
import base64
import sys

# This must be a CSV file with containing at least the labeled columns: 
#    login, Extension, Numero
# login will be used as key to search by sAMAccountname in AD
# Extension / Numero will be the value inserted in AD user register
# within facsimileTelefphoneNumber field
agendacsv = "agenda.csv"

with open(agendacsv,"r") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        header = reader.next()
        hdict = {}
        for t in enumerate(header):
            hdict[t[1]]=t[0]            
        agenda = {}
        for row in reader:
            login = row[hdict ["login"]]
            agenda[login] = {}
            for k in ["Extension","Numero"]:
                agenda[login][k] = row[hdict[k]]

if len(sys.argv)==4:
    domain_controller = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
else:
    print "Usage: %s Domain-Controller AD-User Password" % sys.argv[0]
    sys.exit(1)

ldapsearch = "/usr/bin/ldapsearch -x -h %s \
-D %s -w %s \
-b dc=s21sec,dc=int \
-o ldif-wrap=no " % (domain_controller, user, password)

ldapmodify = "/usr/bin/ldapmodify -x -h %s \
-D %s -w %s" % (domain_controller, user, password)

for login,data in agenda.items():
    cmd = ldapsearch + ' (sAMAccountname=%s) dn' % login
    cmd = ldapsearch + ' (sAMAccountname=%s) dn' % login
    p = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE)
    out, err = p.communicate()    
    res = re.search('^dn(:+) (.*)', out, re.MULTILINE)
    #print login, res.groups()
    if res.groups()[0] == ":":
        dn = res.groups()[1]
    # If DN has special characters (e.g. latin1) then is encoded in base64
    # LDIF format specifies that the field value is prepended by two colons (::)
    # instead of one colon (:) for only ascii values
    elif res.groups()[0] == "::":
        dn = base64.b64decode(res.groups()[1])
    else: 
        print res.groups()
        dn = None

    if dn is not None:
        print dn
        telephone = data["Numero"][1:4]+" "+data["Numero"][4:7]+" "+data["Numero"][7:10]+" / "+data["Extension"]
        template = """
dn: %s
changetype: modify
replace: facsimileTelephoneNumber
facsimileTelephoneNumber: %s
""" % (dn , telephone)
        cmd = ldapmodify
#        p = subprocess.Popen("/bin/cat", shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p = subprocess.Popen(cmd.split(), shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = p.communicate(input=template)
        print out
    else:
        print None
