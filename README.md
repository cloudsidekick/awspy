# awspy

## Description

A simple python client for AWS compatible web services. This library is compatible with
AWS, Eucalyptus and the OpenStack AWS endpoint. 

It is called simple because it provides a non-abstracted interface to AWS. It simply 
builds the query string based on the actions and parameters you provide and returns
the pure XML from the cloud endpoint.

## Repository and Download

https://github.com/cloudsidekick/awspy

To download _the latest_ source:

```
curl -Lk --output awspy.tar.gz https://github.com/cloudsidekick/awspy/tarball/master
```

or clone in git:

```
git clone git://github.com/cloudsidekick/awspy.git
```

## Bug and Feature Requests

https://github.com/cloudsidekick/awspy/issues

## Requirements

Python 2.6+ 

## Installation

```
python setup.py install
```

## Example

# AWS

```
import awspy

access_key = "SJFKDSJLKGLKDSF"
secret_key = "SFLKJSLKGLKGLKDSFSJFJSLFDSLFJ"

# cloud formation, non-default region
cfn = AWSConn(access_key, secret_key, region="us-west-1", product="cfn")
result = cfn.aws_query("DescribeStacks")
print result

# ec2, default region, with parameters
ec2 = AWSConn(access_key, secret_key, product="ec2")
result = ec2.aws_query("DescribeInstances", [("InstRRReId.1","i-81ce9afd")] )
print result
```

# Eucalyptus

```
import awspy

access_key = "SDKJLKJFGKLJLGJ"
secret_key = "LKKJDLSFDSFLKDSFLKDJLSLFDSLFJ"

euca = AWSConn(access_key, secret_key, endpoint="123.123.123.123", path="/services/Eucalyptus/", api_version="2011-01-01")
result = euca.aws_query("DescribeInstances")
print result

```



