import time
import random

###############################################################################
# primitives
###############################################################################
class db_taggit:
    # Singleton
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(db_taggit, self).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    # API
    # return new user id
    def addUser(self, user_dict): pass
    # return new tag id
    def addTag (self, tag_dict, user_id): pass
    # return new item id
    def addItem(self, item_dict, user_id): pass
    def addItemByBibtex(self, bibtex_dict, user_id): pass
    # return OK/ERR?
    def tagItem(self, user_id, tag_id, item_id): pass

ITEM_DB_MAP = {
    '__bibtex':'bibtex',
    '_type':'type',
    'author':'author',
    'year':'year',
    'url':'url'
}

###############################################################################
# cassandra
###############################################################################
import pycassa
from pycassa.pool import ConnectionPool
from pycassa import NotFoundException
from pycassa.columnfamily import ColumnFamily

class db_cassandra(db_taggit):
    def __init__(self, hosts):
        self.pool = ConnectionPool('taggit', hosts)
        self.cf_user = pycassa.ColumnFamily(self.pool, 'User')
        self.cf_user_name2id = pycassa.ColumnFamily(self.pool, 'Uname2id')
        self.cf_item = pycassa.ColumnFamily(self.pool, 'Item')
        self.cf_user_add_item = pycassa.ColumnFamily(self.pool, 'UIAdd')
        self.cf_item_added_user = pycassa.ColumnFamily(self.pool, 'IUAdded')

    def __del__(self):
        self.pool = None

    # signup
    def addUser(self, user_dict):
        user_name = user_dict['name']
        try:
            ret = self.cf_user_name2id.get(user_name)
            print 'ERR user exist:', ret
            raise Exception('addUser', 'E_USER_ALREADY_EXIST')
        except NotFoundException:
            # TODO in batch (transaction)
            print 'OK to addUser:', user_name
            user_id = self.genKeyId(self.cf_user)
            print 'generated user id:', user_id

            print 'add into user_name2id:', {'user_id':user_id}
            self.cf_user_name2id.insert(user_name,{'user_id':user_id})

            print 'add into user:', user_dict
            self.cf_user.insert(user_id,user_dict)

            return user_id        
    
    # get user profile by user id
    # TODO combined use with searchUser
    def getUser(self, user_dict):
        user_id = user_dict['id']
        try:
            ret = self.cf_user.get(user_id)
            print 'OK user found:', ret
            return ret['name']
        except NotFoundException:
            raise Exception('getUser', 'E_USER_NOT_FOUND')

    # login 
    # input: user[name]
    # return user[id,cookie]
    def loginUser(self, user_dict):
        user_name = user_dict['name']
        try:
            # TODO cookie
            ret = self.cf_user_name2id.get(user_name)
            print 'OK user login:', ret
            return ret['user_id'], user_name
        except NotFoundException:
            raise Exception('loginUser', 'E_USER_NOT_FOUND')
    
    # auth 
    # input: user[id]
    # return True if ok, otherwise raise exception 
    def authUser(self, user_dict):
        # TODO, passwd, cookie (loginUser)
        # right now only check user id
        user_id = user_dict['id']
        try:
            ret = self.cf_user.get(user_id)
            print 'OK user auth:', ret
            return True
        except:
            raise Exception('authUser', 'E_USER_AUTH')

    # assume user authed
    # return item_id
    def addItem(self, item_dict, user_id):
        # TODO check item exists? ..
        # TODO in BATCH (transaction)
        try:
            print 'OK to addItem'
            item_id = self.genKeyId(self.cf_item)
            print 'generated item id:', item_id

            # print 'add into item:', item_dict
            self.cf_item.insert(item_id,item_dict)

            print 'user item add relation:', user_id, ',', item_id
            self.cf_user_add_item.insert(user_id,{item_id:''})
            self.cf_item_added_user.insert(item_id,{user_id:''})

            return item_id
        except Exception, e:
            raise Exception('addItem', 'E_ADD_ITEM')

    # return item_list
    def addItemByBibtex(self, bibtex_dict, user_id):
        item_list = []
        for key in bibtex_dict:
            # print '\nitem', key, '\nbibtex:\n', bibtex_dict[key]['__bibtex']
            item_dict = {}
            for field in ITEM_DB_MAP:
                try:
                    if (bibtex_dict[key][field]):
                        item_dict[ITEM_DB_MAP[field]] =\
                            bibtex_dict[key][field]
                except KeyError:
                    #print 'skipping field:', field
                    pass

            # print 'add item_dict:', item_dict
            item_id = self.addItem(item_dict,user_id)
            item_dict['id'] = item_id

            for field in ITEM_DB_MAP:
                try:
                    if field.startswith('__'):
                        #print 'removing field:', ITEM_DB_MAP[field]
                        del(item_dict[ITEM_DB_MAP[field]])
                except KeyError:
                    pass

            item_list.append(item_dict)
        return item_list

    # get item dict (full info) by item id
    def getItem(self, item_list):
        item_list_ = []
        for item_dict in item_list:
            item_id = item_dict['id']
            try:
                item_dict_ = dict(self.cf_item.get(item_id))
                item_dict_['id'] = item_id
                print 'OK item found:', item_dict_
                item_list_.append(item_dict_)
            except NotFoundException:
                raise Exception('getItem', 'E_ITEM_NOT_FOUND')
        return item_list_

    # generate id (unique key) for ColumnFamily cf
    def genKeyId(self,cf):
        while 1:
            gid = long(time.mktime(time.gmtime()))*1000000\
                + random.randint(1,1000000) # mms
            try:
                cf.get(gid)
            except NotFoundException:
                cf.insert(gid,{}) # get slot
                return gid
            except: 
                raise Exception('genKeyId', 'E_UNKNOWN')

            sleep(0.005)


###############################################################################
# Factory
###############################################################################
def db_default():
    return db_cassandra(['128.122.47.240:9160'])

