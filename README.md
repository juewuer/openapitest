# 使用修改
需要设置几个变量
1. access_key
1. secret_key
1. region
1. env_id
  这是一个dict，需要设置下列值的uuid
  - env_id['ImageId']['default']
  - env_id['SubnetId']['default']
  - env_id['SecurityGroupId']['default']

# 使用命令
```
创建命令:后面参数，第一个参数为创建的数目，第二个参数为创建的类型，第三个为数据盘的大小，第四个为可用区位置

# 在可用区A创建500台 I2.4B型主机，挂200G数据盘
python kec.py call create_inst 500 I2.4B 200 A

# 在可用区B创建500台 I1.4B型主机，挂200G数据盘
python kec.py call create_inst 500 I1.4B 200 B

删除命令
python kec.py call batch_inst destroy

获取虚机信息
python kec.py call batch_inst get
```
