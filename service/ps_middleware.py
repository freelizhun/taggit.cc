from webob import Request, Response
from webob import exc
import json
import protobuf_json
import taggit_pb2 as taggit_pb 
from ps_database import db_factory

###############################################################################
# PRE-REQUEST: handler router, environ['_HANDLER'] must be set !
###############################################################################
class JsonApp:
    # singleton
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(JsonApp, self).__new__(
                                cls, *args, **kwargs)
        return cls._instance
    
    # conn db, set mode
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
        except Exception, e:
            print '(E) JsonApp call:', e
        except:
            pass

        resp.body = json.dumps(resp.dict)
        return resp(environ, start_response)
        
###############################################################################
# /user/signup
###############################################################################
#   input: user name
#   action:
        # check if user name exist in db
        # if exist, return user id -1  
        # if not exist, add into db, return (unique) user id
#   output: 
        # user id
#   ex:
#     req: {"input": {"users": [{"name": "sixin"}]}}
#     resp: {"output":{"users":[{"id":1}]}}
# TODO once-verification code
###############################################################################
# /user/login
###############################################################################
#   input: user name
#   action:
        # if exist, return user id
        # if not exist, return user id -1
#   output: 
        # uesr id
#   ex:
#     req: {"input": {"users": [{"name": "sixin"}]}}
#     resp: {"output":{"users":[{"id":1}]}}
# TODO password-cookie Auth
###############################################################################
# TODO /user/profile
###############################################################################
class UserApp(JsonApp):
    def signup(self,req,resp):
        #assert(self.check_has_only_one_user(req,resp))
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

    def tag_item(self,req,resp):
        uti_dict = req.dict['input']['utis'][0]
        print '(I) userapp, tagitem:', uti_dict
        uti_id = self.dbo.tagItem(\
            uti_dict['user_id'], uti_dict['tag_id'], uti_dict['item_id'])
        resp.dict['output'] = {'utis':[{'id':uti_id}]}

    def detag_item(self,req,resp):
        uti_dict = req.dict['input']['utis'][0]
        print '(I) userapp, detagitem:', uti_dict
        uti_id = self.dbo.detagItem(\
            uti_dict['user_id'], uti_dict['tag_id'], uti_dict['item_id'])
        resp.dict['output'] = {'utis':[{'id':uti_id}]}

###############################################################################
# /paper/addbibtex -> add_paper_by_bibtex
###############################################################################
#   input: bibtex string
#   action:
#       # parse bibtex
#       # store each into database
#   output: paper list
#   ex:
#     req: {"input": {"users": [{"id": "1"}], "papers":[{"bibtex":"BIBTEX"}]}}
#     resp: {"output":{"papers":[{"id":3},{"id":4}]}}
# TODO
#       # auth user
###############################################################################
from zs.bibtex.parser import parse_string
class PaperApp(JsonApp):
    def add_by_bibtex(self,req,resp):
        # assert(self.check_has_only_one_item(req,resp))
        paper_dict = req.dict['input']['papers'][0] # assume one bibtex
        bibtex = paper_dict['bibtex']
        bibtex_dict = parse_string(bibtex)
        print '(I) paperapp, add_by_bibtex\n', bibtex_dict
        paper_list = self.dbo.addPapersByBibtex(bibtex_dict)
        resp.dict['output'] = {'papers':paper_list}

    def get_by_id(self,req,resp):
        paper_list = req.dict['input']['papers']
        print '(I) paperapp, get_by_id:', paper_list
        paper_ids = [x['id'] for x in paper_list]
        paper_list2 = self.dbo.getPapersById(paper_ids)
        resp.dict['output'] = {'papers':paper_list2}

    def get_by_tag(self,req,resp):
        tag_dict = req.dict['input']['tags'][0]
        print '(I) paperapp, get_by_tag:', tag_dict
        paper_list = self.dbo.getPapersByTagId(tag_dict['id'])
        resp.dict['output'] = {'papers':paper_list}

    def get_top10(self,req,resp):
        print '(I) paperapp, get_top10:'
        paper_list = self.dbo.getPapersTop10()
        resp.dict['output'] = {'papers':paper_list}

###############################################################################
class TagApp(JsonApp):
    # similar to user signup
    def add_by_name(self,req,resp):
        tag_dict = req.dict['input']['tags'][0]
        print '(I) tagapp, add_by_name:', tag_dict
        tag_id = self.dbo.addTag(tag_dict['name'])
        resp.dict['output'] = {'tags':[{'id':tag_id}]}

    # get tags of one item
    def get_by_item(self,req,resp):
        item_dict = req.dict['input']['items'][0]
        print '(I) tagapp, get_by_item:', item_dict
        tag_list = self.dbo.getTagsByItemId(item_dict['id'])
        resp.dict['output'] = {'tags':tag_list}

    # get top 10 tags
    def get_top10(self,req,resp):
        print '(I) tagapp, get_top10'
        tag_list = self.dbo.getTagsTop10()
        resp.dict['output'] = {'tags':tag_list}

    def search_by_prefix(self,req,resp):
        prefix = req.dict['input']['query']
        if 'query_offset' in req.dict['input'].keys():
            offset = req.dict['input']['query_offset']
        else:
            offset = 0
        if 'query_size' in req.dict['input'].keys():
            size = req.dict['input']['query_size']
        else:
            size = 0
        print '(I) tagapp, search_by_prefix:', prefix, offset, size
        tag_list = self.dbo.searchTagsByPrefix(prefix,offset,size)
        resp.dict['output'] = {'tags':tag_list}

###############################################################################
# Factory
###############################################################################
import re
def middleware_factory(name,mode):
    if re.match(name,'UserApp'):
        return UserApp(mode)
    elif re.match(name,'PaperApp'):
        return PaperApp(mode)
    elif re.match(name,'TagApp'):
        return TagApp(mode)
    else:
        return None
