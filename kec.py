#!/usr/bin/env python
# encoding=utf8

import json
import sys
import time
import getopt
import random
import datetime

reload(sys)
sys.path.append("..")
sys.path.append("../..")
sys.setdefaultencoding('utf-8')


from lib.user_server import *
program_version= '1.0.0H'

g_RunInstances_Max=2
g_Batch_Max=2

service = 'kec'
#region = 'cn-shanghai-3'
#region = 'cn-beijing-6'
region = 'cn-shanghai-2'
host = '%s.%s.api.ksyun.com' % (service, region)
endpoint = 'http://%s/' % host
access_key =''
secret_key = ''

version='2016-03-04'

if(not access_key or not secret_key):
	print 'access_key or secret_key is blank, please set first'
	sys.exit()

def my_exit(msg=""):
	print "\n",'='*80,"\nprogram died for %s\n"%msg, '='*80
	sys.exit()

logfilename = time.strftime('kec-test-%Y-%m-%d.log', time.localtime(time.time()))
flog = open(logfilename, 'a+')

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

env_id ={}

if(region == 'cn-shanghai-3'):
	env_id = {
		'ImageId':{
			'default':'b2e78146-58f1-4298-9397-ebf942246a2b',
		},
		'SubnetId': {
			'default': '9d66690a-9f64-470c-847d-7d208af20566',
		},
		'SecurityGroupId': {
			'default': '62394380-7099-4141-bc19-dfeb1de37bf4',
		},
	}
elif(region == 'cn-beijing-6'):
	env_id = {
		'ImageId':{
			'centos7':'d3410864-1cf1-418f-9afe-c70aa3fa9cd4',
			'default':'d3410864-1cf1-418f-9afe-c70aa3fa9cd4',
		},
		'SubnetId': {
			'default': 'b0594c84-3cde-42be-8f64-8dbfc85ba694',
		},
		'SecurityGroupId': {
			'default': 'ed708421-6fb1-44ce-b805-3af8e561414c',
		},
	}
elif(region == 'cn-shanghai-2'):
	env_id = {
		'ImageId':{
			'centos7':'d3410864-1cf1-418f-9afe-c70aa3fa9cd4',
			'default':'d3410864-1cf1-418f-9afe-c70aa3fa9cd4',
		},
		'SubnetId': {
			'net1': '7d534941-e8d6-4402-8736-8aee21a88229',
			'default': '7d534941-e8d6-4402-8736-8aee21a88229',
		},
		'SecurityGroupId': {
			'default': '155c57ac-8369-4d64-afe4-31f7775c0e0a',
		},
	}

g_starttime = ''
def create_inst(count=1, type='I1.1A',disk=10):
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
		create_inst_one(cr,type,disk,rec,remain=count)
		count = count - cr

def create_inst_one(count=1, type='I1.1A',disk=10, record=1,remain=0):
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
python kec.py call create_inst 50 I2.4B 200

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