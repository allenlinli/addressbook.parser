import sys
import time
import re
import shelve
import codecs
import socket
import urllib2
from json import dumps
from retry_decorator import retry
from org_info_parser import OrgInformation

data_URL = 'http://oid.nat.gov.tw/infobox1/showdata.jsp'
time_str = time.strftime("%Y%m%dT%H%M%S", time.localtime())

def save_to_json(file_name, data):
    """ Save data to json format, this will use file_name to save
    """
    with codecs.open(file_name, 'w', 'utf-8') as f:
        f.write(dumps(data, ensure_ascii = False, indent=4))

def collect_showdata_param(data):
    """ find request param in showdata
    this will find special param, like "javascript:showdata(<PARAM>)"
    """
    param_pat = re.compile(r'showdata\(\'(?P<PARAM>\S*)\'\)')

    for match in re.finditer(param_pat, data):
        return match.group('PARAM')

@retry((urllib2.URLError,socket.timeout))
def showdata(data_URL, param):
    """ request show_data on data_URL with param
    """
    request = urllib2.Request(data_URL, param)
    response = urllib2.urlopen(request)
    return response.read().decode('big5')

def walk(d, output, level):
    for i in d.keys():
        param = collect_showdata_param(eval(i)[1])
        if __debug__:
            print '\t'*level + "%s" % (param)

        data = showdata(data_URL, param)

        if __debug__:
            print data

        output.append(data)
        walk(d[i], output, level+1)

def main(f):
    oid = shelve.open(f)['oid']
    raw_data_list = []

    walk(oid, raw_data_list, 0)

    org_info = OrgInformation()
    for raw_data in raw_data_list:
        org_info.parse_data(raw_data)

    # Get org_info data iter
    data = []
    for info in org_info.get_info_iter():
        data.append(info)

    save_to_json(file_name = "raw_data/oid.nat.gov.tw_%s.json" %(time_str),
                 data = data)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: ./%s <oid_shelve file>" % (sys.argv[0])
        sys.exit(-1)

    main(sys.argv[1])
