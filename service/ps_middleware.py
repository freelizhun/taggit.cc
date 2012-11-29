from webob import Request, Response
from webob import exc

import json
#from simplejson import loads, dumps
import taggit_pb2 as taggit_pb 

OK = taggit_pb.JsonResponse.DESCRIPTOR.\
    enum_types_by_name['Status'].values_by_name['OK'].number
ERR = taggit_pb.JsonResponse.DESCRIPTOR.\
    enum_types_by_name['Status'].values_by_name['ERR'].number
UNO = taggit_pb.JsonResponse.DESCRIPTOR.\
    enum_types_by_name['Status'].values_by_name['UNKNOWN'].number

from ps_database import db_default

import protobuf_json

###############################################################################
# handler router
#   environ['_HANDLER'] must be set !
###############################################################################
class JsonApp(object):
    def __init__(self):
        self.dbo = db_default()
    # http -> webob, json -> dict
    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = Response(content_type="application/json")
        resp.dict = {'status':UNO}
        try:
            req.dict = json.loads(req.body)
            protobuf_json.json2pb(taggit_pb.JsonRequest(), req.dict) # DEBUG
            handler = getattr(self,environ['_HANDLER'])
            handler(req,resp) # handle !
            protobuf_json.json2pb(taggit_pb.JsonResponse(), resp.dict) # DEBUG
            resp.dict['status'] = OK
        except Exception, e:
            #print 'exception:', e
            resp.dict['message'] = str(e)
            resp.dict['status'] = ERR
        except:
            resp.dict['message'] = 'E_UNKNOWN'
            resp.dict['status'] = ERR

        resp.body = json.dumps(resp.dict)
        #print '**************', '\nREQ\n', req
        #print '\nRESP\n', resp, '\n***************\n'
        return resp(environ, start_response)

    def check_has_only_one_user(self,req,resp):
        try:
            if (len(req.dict['input']['users']) == 1):
                return True
            else:
                raise Exception('JsonApp', 'only allow one user')
        except:
            raise Exception('JsonApp', 'only allow one user')

    def check_has_only_one_item(self,req,resp):
        try:
            if (len(req.dict['input']['items']) == 1):
                return True
            else:
                raise Exception('JsonApp', 'allow one and only one item')
        except:
            raise Exception('JsonApp', 'allow one and only one item')

    def check_has_ge_one_item(self,req,resp):
        try:
            if (len(req.dict['input']['items']) >= 1):
                return True
            else:
                raise Exception('JsonApp', 'only allow one item')
        except:
            raise Exception('JsonApp', 'only allow one item')
        
###############################################################################
# /u/signup
###############################################################################
#   input: user[name]
#   action:
        # check if user name exist in db
        # if exist, raise exception
        # if not exist, generate a unique user id and add into db
#   output: 
        # OK: user[id]
        # ERR
#   ex:
#     req: {"input": {"users": [{"name": "sixin"}]}}
#     resp: 
# TODO once-verification code
###############################################################################
# /u/login
###############################################################################
#   input: user[name,passwd]
#   action:
        # check db
        # if exist (OK), return user id, cookie
        # if not exist (ERR), raise exception
#   output: 
        # OK: uesr[id,cookie]
        # ERR
# TODO password-cookie Auth
###############################################################################
# /u/profile
###############################################################################
###############################################################################
class UserApp(JsonApp):
    def signup(self,req,resp):
        assert(self.check_has_only_one_user(req,resp))
        user_dict = req.dict['input']['users'][0]
        print 'signup, user dict:', user_dict
        # TODO check user exist outside addUser?
        user_id = self.dbo.addUser(user_dict)
        resp.dict['output'] = {'users':[{'id':user_id}]}
        
    def login(self,req,resp):
        assert(self.check_has_only_one_user(req,resp))
        user_dict = req.dict['input']['users'][0]
        print 'login, user dict:', user_dict
        user_id, user_cookie = self.dbo.loginUser(user_dict)
        resp.dict['output'] = {'users':[{'id':user_id,\
                                         'cookie':user_cookie}]}

###############################################################################
# /i/addbibtex -> add_item_by_bibtex
###############################################################################
#   input: user id, bibtex text
#   action:
#       # auth user
#       # parse bibtex
#       # store into database
#   output: item list
#   ex:
#     req:  {"input": {"users": [{"id": "1"}], "items":[{"bibtex":"BIBTEX"}]}}
#     resp: 
#
###############################################################################
# /i/info
###############################################################################
# 
#
#
#
###############################################################################
# /i/addtag -> add_tag_to_item
##############################################################################
from zs.bibtex.parser import parse_string

class ItemApp(JsonApp):
    def add_item_by_bibtex(self,req,resp):
        assert(self.check_has_only_one_user(req,resp))
        user_dict = req.dict['input']['users'][0]
        user_id = user_dict['id']

        print 'add_item_by_bibtex, auth user:', user_dict
        assert(self.dbo.authUser(user_dict))

        assert(self.check_has_only_one_item(req,resp))
        item_dict = req.dict['input']['items'][0]

        bibtex = item_dict['bibtex'] # TODO check exist
        bibtex_dict = parse_string(bibtex)
        # print 'parsed bibtex\n', bibtex_dict

        item_list = self.dbo.addItemByBibtex(bibtex_dict, user_id)
        resp.dict['output'] = {'items':item_list}

    # offset, limit
    def get_item_by_tag(self,req,resp):
        pass

    def get_item_by_id(self,req,resp):
        assert(self.check_has_ge_one_item(req,resp))
        item_list = req.dict['input']['items']
        print 'get item by id, item_list:', item_list
        item_list = self.dbo.getItem(item_list)
        resp.dict['output'] = {'items':item_list}

###############################################################################
class TagApp(JsonApp):
    def add_tag_to_item(self,req,resp):
        pass



###############################################################################
# Factory
###############################################################################
import re
def make_middleware(name):
    if re.match(name,'UserApp'):
        return UserApp()
    elif re.match(name,'ItemApp'):
        return ItemApp()
    else:
        return None

