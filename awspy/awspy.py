#########################################################################
# Copyright 2012 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################

import time
import urllib2
import httplib
import hmac
import hashlib
import base64

# the default versions need to be updated
# along with the new AWS products

versions = {
    "emr" : "2009-03-31",
    "ec2" : "2013-02-01",
    "sns" : "2010-03-31",
    "cfn" : "2010-05-15",
    "as" : "2010-08-01",
    "rds" : "2010-07-28",
    "sqs" : "2009-02-01",
    "ses" : "2010-12-01",
    "cw" : "2010-08-01",
    "elb" : "2011-04-05",
    "vpc" : "2010-11-15",
    "iam" : "2010-05-08",
    "sdb" : "2009-04-15",
    "r53" : "2012-12-12",
    "ebs" : "2010-12-01"}

# the newer products need to be added here

end_names = {
    "emr" : "elasticmapreduce",
    "ec2" : "ec2",
    "sns" : "sns",
    "cfn" : "cloudformation",
    "as" : "autoscaling",
    "rds" : "rds",
    "sqs" : "sqs",
    "ses" : "email",
    "cw" : "monitoring",
    "elb" : "elasticloadbalancing",
    "vpc" : "ec2",
    "iam" : "iam",
    "sdb" : "sdb",
    "r53" : "route53",
    "ebs" : "elasticbeanstalk"}


class AWSConn():
    """AWSConn - AWS connection class

        access_key - AWS access key
        secret_key - AWS secret key
        protocol - change to http if needed for private cloud
        endpoint - the endpoint for a private cloud, overrides region and product
        region - AWS region, ignored if endpoint is used
        product - AWS product abbreviation, ignored if endpoint is used
        api_version - overrides the default per product
        path - overrides the default path, e.g. "/services/Eucalyptus/"
        timeout - in seconds"""

    def __init__(self, access_key, secret_key, protocol="https", endpoint=None, region=None,
        product="ec2", api_version=None, path="/", timeout=10, debug=False):
        
        self.access_key = access_key
        self.secret_key = secret_key
        self.protocol = protocol
        self.path = path 
        self.timeout = timeout
        self.debug = debug
        self.product = product

        if not api_version:
            self.api_version = versions[product]
        else:
            self.api_version = api_version

        if self.debug:
            print("api version is %s" % (self.api_version))
        if not endpoint:
            self.endpoint = self.build_endpoint(product, region)
        else:
            self.endpoint = endpoint


    def build_endpoint(self, product, region):
        """build_endpoint - creates an endpoint based on an AWS product and region
            Do not use if the cloud is Eucalyptus or the OpenStack AWS endpoint

            product - the abbreviation for an AWS product
            region - the AWS region name"""

        end_name = end_names[product]

        # some aws products don't conform to the following, needs fixing up
        if not region or (product == "sdb" and region == "us-east-1") or product in ["iam", "r53"]:
            endpoint = "%s.amazonaws.com" % (end_name)
        else:
            endpoint = "%s.%s.amazonaws.com" % (end_name, region)
        return endpoint

        
    def _build_r53_request(self, action, action_params, request_type, data):

        baseurl = "%s://%s" % (self.protocol.lower(), self.endpoint)

        url = "%s/%s" % (baseurl, "date")
        response = urllib2.urlopen(url, None, self.timeout)
        timestamp = response.info().getheader("Date")
        if self.debug:
            print("Timestamp = %s" % (timestamp))

        url = "%s/%s/%s" % (baseurl, self.api_version, action)
        if self.debug:
            print("Url = %s" % (url))

        digest = hmac.new(self.secret_key, timestamp, hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        xauth = "AWS3-HTTPS AWSAccessKeyId=%s,Algorithm=HmacSHA256,Signature=%s" % (self.access_key, signature)

        req = urllib2.Request(url)
        req.get_method = lambda: request_type
        if data and not len(data):
            data = None
        elif data and len(data):
            length = str(len(data))
            req.add_header("Content-Length", length)
            
        req.add_data(data)

        req.add_header("X-Amzn-Authorization", xauth)
        req.add_header("x-amz-date", timestamp)
        req.add_header("Content-Type", "text/plain")
        req.add_header("Host", "route53.amazonaws.com")

        return req

    
    def _build_querystring_request(self, action, action_params):

        params = {}
        params["Timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        params["Action"] = action
        params["Version"] = self.api_version
        params["SignatureMethod"] = "HmacSHA256"
        params["SignatureVersion"] = "2"
        params["AWSAccessKeyId"] = self.access_key
        params_list = params.items() + action_params
        params_list.sort()

        if self.debug:
            print("Parameter List = %s" % (params_list))

        query_string = '&'.join(['%s=%s' % (urllib2.quote(k, safe=''),urllib2.quote(str(v), safe='-_~')) for (k,v) in params_list if v])

        string_to_sign = "GET\n%s\n%s\n%s" % (self.endpoint, self.path, query_string.encode("utf-8"))
        digest = hmac.new(self.secret_key, string_to_sign, hashlib.sha256).digest()
        signature = urllib2.quote(base64.b64encode(digest))

        url = "%s://%s%s?%s&Signature=%s" % (self.protocol.lower(), self.endpoint, self.path, query_string, signature)

        if self.debug:
            print("Url = %s" % (url))

        req = urllib2.Request(url)

        return req

    def aws_query(self, action, action_params=[], request_type="GET", data=None):
        """aws_query - queries the AWS compatible endpoint and returns the pure XML response
            throws an exception on error

            action - the AWS action, e.g. "DescribeInstances"
            action_params - a list of key, value pairs that correpond to the parameters
                of the action
            request_type - either GET, POST, DELETE, GET default
            data - POST or DELETE data"""

        # to do - some of the older and newer AWS products use different signing methods
        # this needs to be reflected in the code below

        if request_type not in ["GET", "POST", "DELETE"]:
            raise Exception("aws_query request type of %s unsupported. Must be one of GET, POST, DELETE" % (request_type))


        if self.product != "r53":
            req = self._build_querystring_request(action, action_params)
        else:
            req = self._build_r53_request(action, action_params, request_type, data)



        try:
            response = urllib2.urlopen(req, None,  self.timeout)
        except urllib2.HTTPError, e:
            raise Exception("HTTPError = %s, %s, %s" % (str(e.code), e.msg, e.read()))
        except urllib2.URLError, e:
            raise Exception("URLError = %s" % (str(e.reason)))
        except httplib.HTTPException, e:
            raise Exception("HTTPException")
        except Exception:
            import traceback
            raise Exception("generic exception: " + traceback.format_exc())


        r = response.read()
        return r

