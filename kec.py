#!/usr/bin/env python
# encoding=utf8

import json
import sys
import time
import getopt
import random
import datetime
# in the Authorization header.
import sys, os, base64, datetime, hashlib, hmac
import requests # pip install requests
from urllib import urlencode
import traceback

reload(sys)
sys.path.append("..")
sys.path.append("../..")
sys.setdefaultencoding('utf-8')


program_version= '1.0.1H'

g_RunInstances_Max=50
g_Batch_Max=50

service = 'kec'
#region = 'cn-shanghai-3'
#region = 'cn-beijing-6'
region = 'cn-shanghai-2'
host = '%s.%s.api.ksyun.com' % (service, region)
endpoint = 'http://%s/' % host
access_key =''
secret_key = ''

env_id ={}

env_id = {
	'ImageId':{
		'centos7':'d3410864-1cf1-418f-9afe-c70aa3fa9cd4',
		'default':'d3410864-1cf1-418f-9afe-c70aa3fa9cd4',
	},
	'SubnetId': {
		'A': '7d534941-e8d6-4402-8736-8aee21a88229',
		'B': '2d889188-abe5-411a-9d1c-8bbd91003072',
		'default': '7d534941-e8d6-4402-8736-8aee21a88229',
	},
	'SecurityGroupId': {
		'default': '155c57ac-8369-4d64-afe4-31f7775c0e0a',
	},
}	
	
version='2016-03-04'

if(not access_key or not secret_key):
	print 'access_key or secret_key is blank, please set first'
	sys.exit()

def my_exit(msg=""):
	print "\n",'='*80,"\nprogram died for %s\n"%msg, '='*80
	sys.exit()

logfilename = time.strftime('kec-test-%Y-%m-%d.log', time.localtime(time.time()))
flog = open(logfilename, 'a+')


class AwsRequest(object):
	'''
	__init__ method
	'''

	def __init__(self, service, host, region, endpoint, access_key, secret_key):
		self.method = 'GET'
		self.service = service
		self.host = host
		self.region = region
		self.endpoint = endpoint

		if access_key is None or secret_key is None:
			print 'No access key is available.'
			sys.exit()
		self.access_key = access_key
		self.secret_key = secret_key

	def __str__(self):
		return '%s,%s' % (self.host, self.service)

	@staticmethod
	def sign(key, msg):
		return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

	@staticmethod
	def getSignatureKey(key, dateStamp, regionName, serviceName):
		kDate = AwsRequest.sign(('AWS4' + key).encode('utf-8'), dateStamp)
		kRegion = AwsRequest.sign(kDate, regionName)
		kService = AwsRequest.sign(kRegion, serviceName)
		kSigning = AwsRequest.sign(kService, 'aws4_request')
		return kSigning

	def getHeaderse(self, request_parameters):
		# Create a date for headers and the credential string
		t = datetime.datetime.utcnow()
		amzdate = t.strftime('%Y%m%dT%H%M%SZ')
		datestamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope

		# ************* TASK 1: CREATE A CANONICAL REQUEST *************
		# http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

		# Step 1 is to define the verb (GET, POST, etc.)--already done.

		# Step 2: Create canonical URI--the part of the URI from domain to query
		# string (use '/' if no path)
		canonical_uri = '/'

		# Step 3: Create the canonical query string. In this example (a GET request),
		# request parameters are in the query string. Query string values must
		# be URL-encoded (space=%20). The parameters must be sorted by name.
		# For this example, the query string is pre-formatted in the request_parameters variable.
		request_parameters = sorted(request_parameters.items(), key=lambda d: d[0])
		canonical_querystring = urlencode(request_parameters)

		# Step 4: Create the canonical headers and signed headers. Header names
		# must be trimmed and lowercase, and sorted in code point order from
		# low to high. Note that there is a trailing \n.
		canonical_headers = 'host:' + self.host + '\n' + 'x-amz-date:' + amzdate + '\n'

		# Step 5: Create the list of signed headers. This lists the headers
		# in the canonical_headers list, delimited with ";" and in alpha order.
		# Note: The request can include any headers; canonical_headers and
		# signed_headers lists those that you want to be included in the
		# hash of the request. "Host" and "x-amz-date" are always required.
		signed_headers = 'host;x-amz-date'

		# Step 6: Create payload hash (hash of the request body content). For GET
		# requests, the payload is an empty string ("").
		payload_hash = hashlib.sha256('').hexdigest()

		# Step 7: Combine elements to create create canonical request
		canonical_request = self.method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

		# ************* TASK 2: CREATE THE STRING TO SIGN*************
		# Match the algorithm to the hashing algorithm you use, either SHA-1 or
		# SHA-256 (recommended)
		algorithm = 'AWS4-HMAC-SHA256'
		credential_scope = datestamp + '/' + self.region + '/' + self.service + '/' + 'aws4_request'
		string_to_sign = algorithm + '\n' + amzdate + '\n' + credential_scope + '\n' + hashlib.sha256(
			canonical_request).hexdigest()

		# ************* TASK 3: CALCULATE THE SIGNATURE *************
		# Create the signing key using the function defined above.
		signing_key = AwsRequest.getSignatureKey(self.secret_key, datestamp, self.region, self.service)

		# Sign the string_to_sign using the signing_key
		signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

		# ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
		# The signing information can be either in a query string value or in
		# a header named Authorization. This code shows how to use a header.
		# Create authorization header and add to request headers
		authorization_header = algorithm + ' ' + 'Credential=' + self.access_key + '/' + credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

		# The request can include any headers, but MUST include "host", "x-amz-date",
		# and (for this scenario) "Authorization". "host" and "x-amz-date" must
		# be included in the canonical_headers and signed_headers, as noted
		# earlier. Order here is not significant.
		# Python note: The 'host' header is added automatically by the Python 'requests' library.
		headers = {'x-amz-date': amzdate, 'Authorization': authorization_header, "Accept": "application/json"}
		# ************* SEND THE REQUEST *************
		request_url = self.endpoint + '?' + canonical_querystring
		return request_url, headers

	def sendRequest(self, request_parameters):
		request_url, headers = self.getHeaderse(request_parameters)
		# print 'Request URL = ' + request_url
		try:
			rep = requests.get(request_url, headers=headers, timeout=10)
		# print 'Response code: %d\n' % rep.status_code
		except Exception, e:
			print "headers: %s" % headers
			traceback.print_exc()
		return rep, headers


def get_kec_data(param):
	request_parameters = param
	re = AwsRequest(service, host, region, endpoint, access_key, secret_key)
	res, headers = re.sendRequest(request_parameters)
	#print ('In get_kec_data: ',res, json.dumps(jret, sort_keys=True, indent=4).encode('utf-8'))
	return res.status_code, res.text


def get_desc_inst():
	request_parameters = {
		"Action": "DescribeInstances",
		'Version': version,
		'MaxResults':1000
	}
	ret, value = get_kec_data(request_parameters)
	return ret, value


def batch_inst(op='get',*kecs):
	if(op=='create'):
		create_inst(*kecs)
		return
	elif(op == 'get' or op == 'show'):
		show_desc_inst()
		return

	ret,data=get_desc_inst()
	jret = json.loads(data)
	#print jret
	print 'Total vms: %d'%jret['InstanceCount']
	kecs = []
	for instance in jret['InstancesSet']:
		kec=KecInst(instance)
		kecs.append(kec)

	#print 'get toatal: ', len(kecs)
	while (len(kecs) > 0):
		if(len(kecs)> g_Batch_Max):
			cr = g_Batch_Max
		else:
			cr = len(kecs)
		batch_op_inst(op, *kecs[0:cr])
		del kecs[0:cr]


def show_desc_inst():
	ret,data=get_desc_inst()
	jret = json.loads(data)
	print 'Total vms: %d'%jret['InstanceCount']
	for instance in jret['InstancesSet']:
		kec=KecInst(instance)
		print kec


class KecObj(object):
	def __init__(self, data, create=0):
		super(KecObj, self).__init__()
		self.id = ''
		self.data = data

	def __str__(self):
		return self.id

	def show_detail(self):
		print json.dumps(self.data, sort_keys=True, indent=4)

def get_kec_action(op):
	op_dict = {
		'start':'StartInstances',
		'stop': 'StopInstances',
		'reboot': 'RebootInstances',
		'destroy': 'TerminateInstances',
		'get':'DescribeInstances',
		'show':'DescribeInstances',
	}
	return op_dict.get(op, '')


def batch_op_inst(op, *kecs):
	request_parameters = {
		'Version': version,
	}

	request_parameters['Action']=get_kec_action(op)
	id_start=1
	if(len(kecs) == 0):
		return
	for kec in kecs:
		#print 'kec: ', kec
		if(isinstance(kec, str)):
			kecid=kec
		else:
			kecid=kec.id
		request_parameters['InstanceId.%d'%id_start] = kecid
		id_start+=1
	print '-'*80
	print(request_parameters)
	print '-' * 80
	ret, value = get_kec_data(request_parameters)
	print ("bengin to get  ", request_parameters)
	print(ret, value)
	if(ret != 200):
		print  ret, value;


g_starttime = ''
def create_inst(count=1, type='I1.1A',disk=10,az='A'):
	global g_starttime
	totalcount = int(count)
	disk=int(disk)
	count = totalcount
	g_starttime = datetime.datetime.now()
	print '[%s]: Begin create %d VMs' % (g_starttime.strftime('%Y-%m-%d %H:%M:%S'), totalcount)
	flog.write('\n[%s]: Begin create %d VMs\n' % (g_starttime.strftime('%Y-%m-%d %H:%M:%S'), totalcount))
	flog.write('region:%s, count: %d, type: %s, disk:%d\n'%(region, count, type, disk))
	while (count > 0):
		if(count> g_RunInstances_Max):
			cr = g_RunInstances_Max
			rec = 0
		else:
			cr = count
			rec = 1
		create_inst_one(cr,type,disk,rec,remain=count,az=az)
		count = count - cr

def create_inst_one(count=1, type='I1.1A',disk=10, record=1,remain=0,az='A'):
	request_parameters = {
		"Action": "RunInstances",
		'Version': version,
		'InstanceType':type,
		"ImageId": '',
		'DataDiskGb':disk,
		'MaxCount': count,
		'MinCount': count,
		'SubnetId': '',
		'InstancePassword': 'Ksyun123',
		'ChargeType':'Daily',
		'PurchaseTime':'',
		'SecurityGroupId':'',
	}
	for param in ['ImageId','SubnetId','SecurityGroupId']:
		request_parameters[param]=env_id[param]['default']
	if(env_id['SubnetId'].get(az)):
		request_parameters['SubnetId'] = env_id['SubnetId'].get(az)
	starttime = datetime.datetime.now()

	#nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	print '[%s]: start create %d/%d VMs'%(starttime.strftime('%Y-%m-%d %H:%M:%S'), count,remain)
	ret, value = get_kec_data(request_parameters)
	#print ("bengin to create:\n",request_parameters,"\n",ret, value)
	if(ret != 200):
		print request_parameters
		print ret, value
	if(record):
		request_parameters = {
			"Action": "DescribeInstances",
			'Version': version,
			'MaxResults': 1000
		}
		total_vms=0
		notready = 1
		while(notready !=0 ):
			ret, data = get_kec_data(request_parameters)
			endtime = datetime.datetime.now()
			if(ret != 200):
				continue
			jret = json.loads(data)
			if(not total_vms):
				total_vms = jret['InstanceCount']

			notready=0
			for instance in jret['InstancesSet']:
				if(instance['InstanceState']['Name']!='active'):
					notready=notready+1


			print '[%s]: total: %d, not ready %d'%(endtime.strftime('%Y-%m-%d %H:%M:%S'), total_vms, notready)
			flog.write("%d\t%d\n"%((endtime - g_starttime).seconds, notready))
			if(notready == 0):
				print
				print '%d seconds used'%((endtime - g_starttime).seconds)
				flog.write("\n")
				flog.write(json.dumps(jret, sort_keys=True, indent=4,ensure_ascii=False))
				flog.write("\n\n")
			time.sleep(1)



	return ret, value


class KecInst(KecObj):
	def __init__(self, data=None):
		super(KecInst, self).__init__(data)
		if(not data):
			return
		try:
			self.id = self.data.get('InstanceId', None)
			self.name = self.data.get('InstanceName', None)
			self.ip = self.data.get('PrivateIpAddress', None)
			self.type = self.data.get('InstanceType',None)
			istate = self.data.get('InstanceState','')
			self.state = istate.get('Name')
			self.az = self.data.get('AvailabilityZoneName')

		except Exception, e:
			print '> str(Exception):\t', str(Exception)
			print '> str(e):\t\t', str(e)
			print '> repr(e):\t', repr(e)
			print '> e.message:\t', e.message
			print '> traceback.print_exc():',traceback.print_exc()
			print '> traceback.format_exc():\n%s' % traceback.format_exc()
			print( '> Error in %s:%s  %s ' % (self.id, self.ip, self.name))
			my_exit("<Error in class %s, func %s>" % (self.__class__.__name__, sys._getframe().f_code.co_name))



	def __str__(self):
		return 'Id:%s\tName:%-17s\tIp:%-15s\tState:%s\tType:%s' % (self.id,self.name, self.ip, self.state, self.type)

	def show(self):
		print 'Name: %s:\n\tIp:%s\n\tState:%s\n\tType:%s' % (self.name, self.ip, self.state, self.type)

	def checkip(self,cidr):
		if(not self.ip):
			return 0
		if(self.ip[0:len(cidr)] == cidr):
			return 1
		return 0

	def stop_inst(self):
		request_parameters = {
			"Action": "StopInstances",
			'Version': version,
			'InstanceId.1': self.id,
		}
		ret, value = get_kec_data(request_parameters)
		print '\t',self.ip,': ',self.state,': ', ret,value;

	def start_inst(self):
		request_parameters = {
			"Action": "StartInstances",
			'Version': version,
			'InstanceId.1': self.id,
		}
		ret, value = get_kec_data(request_parameters)
		print '\t', self.ip,': ',self.state,': ', ret,value;

	def reboot_inst(self):
		request_parameters = {
			"Action": "RebootInstances",
			'Version': version,
			'InstanceId.1': self.id,
		}
		ret, value = get_kec_data(request_parameters)
		print '\t',self.ip,': ',self.state,': ', ret,value;

def print_help_msg():
	print U'''
创建命令:后面三个参数，第一个参数为创建的数目，第二个参数为创建的类型，第三个为数据盘的大小
python kec.py call create_inst 50 I2.4B 200 A

删除命令
python kec.py call batch_inst destroy

获取虚机信息
python kec.py call batch_inst get

'''
if __name__ == "__main__":
	argv = list(sys.argv[1:])
	datas = []
	op=None
	try:
		while (len(argv) > 0):
			opts, args = getopt.getopt(argv, "hi:I:p:d:c:", ["help", "output="])
			for cmd, arg in opts:
				if cmd in ("-h", "--help"):
					print_help_msg()
					sys.exit()
				elif cmd in ("-v", "--version"):
					print("%s version %s" % sys.argv[0], program_version)
				elif cmd in ("-d", "--data"):
					datas.append(arg)
			if (len(args)):
				datas.append(args[0])
			argv = args[1:]
	except getopt.GetoptError:
		print("argv error,please input")
		sys.exit()
	lend = len(datas)
	if (lend > 0):
		op = datas[0]
	if (lend > 1):
		p1 = datas[1]

	if(op == 'call'):
			# call 只能调用一个函数，后面的做参数，run只接受无参数的函数，依次执行
			func = getattr(sys.modules[__name__], datas[1])
			func(*datas[2:])
	elif(op == 'run'):
		for func in datas[1:]:
			func = getattr(sys.modules[__name__], func)
			func()
	else:
		print 'parameter error, use -h to find more help'



	flog.close()
	pass