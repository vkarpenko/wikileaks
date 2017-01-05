import sys
import urllib2  
import commands 
import struct
from binascii import unhexlify, crc32

# usage, python script.py address
addr = str(sys.argv[1])

def txdecode(transaction):

    data = urllib2.urlopen("https://blockchain.info/rawtx/"+transaction+"?show_adv=true")
    dataout = b''
    atoutput = False
    inchunk = False
    inoutput = False
    index = -1
    unspents = []

    for line in data:
        if 'relayed_by' in line:
            inoutput = True

        if 'spent' in line and inoutput:
            index += 1
            if 'false' in line:
                inchunk = True
            else:
                inchunk = False
        
        if inchunk and 'script' in line and inoutput:
            unspents.append(index)

    indexat = 0
    data = urllib2.urlopen("https://blockchain.info/tx/"+transaction+"?show_adv=true")
    for line in data:
            if 'Output Scripts' in line:
                atoutput = True

            if '</table>' in line:
                atoutput = False

            if atoutput:
                if ' <br/>' in line:
                    chunks = line.split(' ')

                    for c in chunks:
                        if 'O' not in c and '\n' not in c and '>' not in c and '<' not in c:
                            if indexat in unspents:
                                dataout += unhexlify(c.encode('utf8'))
                    indexat += 1

    #length = struct.unpack('<L', dataout[0:4])[0]
    #checksum = struct.unpack('<L', dataout[4:8])[0]
    #dataout = dataout[8:8+length]
    return dataout

print 'Reading '+addr+"'s transactions..."
offset = 0
startatpage = 0 #17
offset = startatpage*50
data = urllib2.urlopen("https://blockchain.info/address/"+addr+"?offset="+str(offset)+"&filter=0") 

pagecalc = offset/50
if pagecalc == 0:
    pagecalc = 1

page = pagecalc
files = 0
keep_reading = True
tx_list = []
f = open('dataout/'+addr+"new_tx_list.txt", 'w')

while (keep_reading):
    tx_exist = False

    if keep_reading:
        print 'Page', page, '...'
        data = urllib2.urlopen("https://blockchain.info/address/"+addr+"?offset="+str(offset)+"&filter=0") 
    for line in data:
        chunks = line.split('><')
        if 'hash-link' in line:
            tx_exist = True
            ll = chunks[4].split(' ')
            #print 'll', len(ll)
            if len(ll) == 1:
                continue
            #print ll
            #print 'll2', len(ll[2])
            lll = ll[2][10:10+64]

            date1 = ll[4].split('>')[1]
            date2 = ll[5].split('<')[0]
            print date1, date2

            print lll
            tx_list.append(lll)
            f.write(str(lll)+'\n')
            
            decoded_data = txdecode(str(lll))
            if decoded_data != None:
                fd = open('dataout/'+str(lll),"wb")
                fd.write(decoded_data)
                fd.close()
                status, output = commands.getstatusoutput("dataout/trid dataout/"+str(lll))
                if 'Unknown!' not in output or 'ASCII' in output:
                    ff = open('dataout/'+addr+"new_file_tx_list.txt", 'a')
                    files += 1
                    outputlines = output.split('\n')
                    if 'ASCII' in output:
                        print '** file seems to be plain text/ASCII'
                        ff.write(str(lll)+' ASCII '+date1+' '+date2+'\n')
                    else:
                        for i in range(6,len(outputlines)):
                            print outputlines[i]
                        ff.write(str(lll)+' '+outputlines[6]+' '+date1+' '+date2+'\n')
                    ff.close()

    page += 1
    offset += 50
    if tx_exist == False:
        keep_reading = False

print len(tx_list), 'transactions found'
print files, 'file headers found'
print 'List saved in file', addr+"_tx_list.txt"
print 'Txs with file headers saved in', addr+"_file_tx_list.txt"
f.close()
