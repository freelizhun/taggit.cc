from webob import Request, Response
from webob import exc

import json
import taggit_pb2 as taggit_pb 
from ps_database import db_factory
import protobuf_json

###############################################################################
# PRE-REQUEST: handler router, environ['_HANDLER'] must be set !
###############################################################################
class JsonApp(object):
    def __init__(self,mode):
        self.dbo = db_factory(mode)
        self.mode = mode

    # http -> webob, json -> dict
    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = Response(content_type="application/json")
        resp.dict = {}
        try:
            req.dict = json.loads(req.body)
            if self.mode == "debug":
                protobuf_json.json2pb(taggit_pb.JsonRequest(), req.dict)
            handler = getattr(self,environ['_HANDLER'])
            handler(req,resp) # handle !
            if self.mode == "debug":
                protobuf_json.json2pb(taggit_pb.JsonResponse(), resp.dict)
            #resp.dict['status'] = OK
        except Exception, e:
            print 'exception:', e
            #resp.dict['message'] = str(e)
            #resp.dict['status'] = ERR
        except:
            #resp.dict['message'] = 'E_UNKNOWN'
            #resp.dict['status'] = ERR
            pass

        resp.body = json.dumps(resp.dict)
        #print '**************', '\nREQ\n', req
        #print '\nRESP\n', resp, '\n***************\n'
        return resp(environ, start_response)

'''
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
'''
        
###############################################################################
# /user/signup
###############################################################################
#   input: user[name]
#   action:
        # check if user name exist in db
        # if exist, return user id -1  
        # if not exist, add into db, return the unique user id
#   output: 
        # user[id]
#   ex:
#     req: {"input": {"users": [{"name": "sixin"}]}}
#     resp: {"output":{"users":[{"id":1}]}}
# TODO once-verification code
###############################################################################
# /user/login
###############################################################################
#   input: user[name]
#   action:
        # check db
        # if exist, return user id
        # if not exist, return user id -1
#   output: 
        # uesr[id]
#   ex:
#     
# TODO password-cookie Auth
###############################################################################
# TODO /user/profile
###############################################################################
class UserApp(JsonApp):
    def signup(self,req,resp):
        #assert(self.check_has_only_one_user(req,resp))
        print req
        user_dict = req.dict['input']['users'][0]
        print '(I) userapp, signup:', user_dict
        user_id = self.dbo.addUser(user_dict['name'])
        resp.dict['output'] = {'users':[{'id':user_id}]}
        
    def login(self,req,resp):
        #assert(self.check_has_only_one_user(req,resp))
        user_dict = req.dict['input']['users'][0]
        print '(I) userapp, login:', user_dict
        user_id = self.dbo.loginUser(user_dict['name'])
        resp.dict['output'] = {'users':[{'id':user_id}]}

###############################################################################
# /paper/addbibtex -> add_paper_by_bibtex
###############################################################################
#   input: bibtex string
#   action:
#       # parse bibtex
#       # store into database
#   output: paper list
#   ex:
#     req: {"input": {"users": [{"id": "1"}], "papers":[{"bibtex":"BIBTEX"}]}}
#     resp: 
# TODO
#       # auth user
###############################################################################
from zs.bibtex.parser import parse_string
class PaperApp(JsonApp):
    def add_by_bibtex(self,req,resp):
        # user_dict = req.dict['input']['users'][0]
        # user_id = user_dict['id']  # TODO check exist
        # print 'add_item_by_bibtex, auth user:', user_dict
        # assert(self.dbo.authUser(user_dict))
        # assert(self.check_has_only_one_item(req,resp))
        paper_dict = req.dict['input']['papers'][0] # assume one bibtex
        # print '(I) paperapp, add_by_bibtex:', paper_dict
        bibtex = paper_dict['bibtex']
        bibtex_dict = parse_string(bibtex)
        print '(I) paperapp, add_by_bibtex\n', bibtex_dict
        paper_list = self.dbo.addPapersByBibtex(bibtex_dict)
        resp.dict['output'] = {'papers':paper_list}

###############################################################################
# /i/info
###############################################################################
###############################################################################
# /i/addtag -> add_tag_to_item
##############################################################################
'''
from zs.bibtex.parser import parse_string

class ItemApp(JsonApp):
    # offset, limit
    def get_item_by_tag(self,req,resp):
        pass

    def get_item_by_id(self,req,resp):
        assert(self.check_has_ge_one_item(req,resp))
        item_list = req.dict['input']['items']
        print 'get item by id, item_list:', item_list
        item_list = self.dbo.getItem(item_list)
        resp.dict['output'] = {'items':item_list}
'''

###############################################################################
class TagApp(JsonApp):
    def add_tag_to_item(self,req,resp):
        pass


###############################################################################
# Factory
###############################################################################
import re
def middleware_factory(name,mode):
    if re.match(name,'UserApp'):
        return UserApp(mode)
    elif re.match(name,'PaperApp'):
        return PaperApp(mode)
    else:
        return None
