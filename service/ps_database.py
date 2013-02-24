import psycopg2
import datetime, time, sys

BIBTEX_PAPER_MAP = {
    'title':'title',
    'author':'author',
    'year':'year',
    'url':'url',
    '__bibtex':'bibtex',
}

ID_NOT_EXIST = -1

###############################################################################
# DB
###############################################################################
class db_taggit:

    # singleton
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(db_taggit, self).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    # conn
    def __init__(self,sqlhost):
        self.sql2 = None
        try:
            self.sql2 = psycopg2.connect(host=sqlhost, port='5432', \
                          database='test', user='taggit', password='taggit')
        except psycopg2.DatabaseError, e:
            print '(F) db_taggit init: %s' % e
            sys.exit()

    # de-conn
    def __del__(self):
        if self.sql2:
            self.sql2.close()

    def reset(self):
        try:
            cur = self.sql2.cursor()

            cur.execute("DROP INDEX IF EXISTS index_si")
            cur.execute("DROP INDEX IF EXISTS index_st")
            cur.execute("DROP INDEX IF EXISTS index_su")
            cur.execute("DROP INDEX IF EXISTS index_pi")
            cur.execute("DROP INDEX IF EXISTS index_tn")
            cur.execute("DROP INDEX IF EXISTS index_un")
            cur.execute("DROP TABLE IF EXISTS utis")
            cur.execute("DROP TABLE IF EXISTS papers")
            cur.execute("DROP TABLE IF EXISTS items")
            cur.execute("DROP TABLE IF EXISTS tags")
            cur.execute("DROP TABLE IF EXISTS users")

            cur.execute(
                "CREATE TABLE users(id serial PRIMARY KEY, name VARCHAR(15))")
            cur.execute(
                "CREATE TABLE tags(id serial PRIMARY KEY, name VARCHAR(15))")
            cur.execute(
                "CREATE TABLE items(id serial PRIMARY KEY, name VARCHAR(127))")
            cur.execute(
                "CREATE TABLE papers(id INT, title VARCHAR(127), "+\
                  "author VARCHAR(127), year VARCHAR(63), url VARCHAR(127), "+\
                  "lastmod timestamp, bibtex VARCHAR(8191), "+\
                  "FOREIGN KEY(id) REFERENCES items(id))")
            cur.execute(
                "CREATE TABLE utis(id serial PRIMARY KEY, " +\
                    "user_id INTEGER, tag_id INTEGER, item_id INTEGER, "+\
                    "FOREIGN KEY(user_id) REFERENCES users(id), "+\
                    "FOREIGN KEY(tag_id) REFERENCES tags(id), "+\
                    "FOREIGN KEY(item_id) REFERENCES items(id))")
            cur.execute("CREATE INDEX index_un ON users (name)")
            cur.execute("CREATE INDEX index_tn ON tags (name)")
            cur.execute("CREATE INDEX index_pi ON papers (id)")
            cur.execute("CREATE INDEX index_su ON utis (user_id)")
            cur.execute("CREATE INDEX index_st ON utis (tag_id)")
            cur.execute("CREATE INDEX index_si ON utis (item_id)")
            
            self.sql2.commit()

        except psycopg2.DatabaseError, e:
            self.sql2.rollback()
            print '(E) db_taggit reset: %s' % e
        finally:
            cur.close()

    def execute1(self, sql):
        try:
            cur = self.sql2.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        except psycopg2.DatabaseError, e:
            print '(E) db_taggit execute1: %s' % e
        finally:
            cur.close()
        return rows        

    def execute2(self, sql, data):
        try:
            cur = self.sql2.cursor()
            cur.execute(sql, data)
            rows = cur.fetchall()
        except psycopg2.DatabaseError, e:
            print '(E) db_taggit execute2: %s' % e
        finally:
            cur.close()
        return rows

    def commit1(self, sql):
        try:
            cur = self.sql2.cursor()
            cur.execute(sql)
            self.sql2.commit()
            rows = cur.fetchall()
        except psycopg2.DatabaseError, e:
            self.sql2.rollback()
            print '(E) db_taggit commit1: %s' % e
        finally:
            cur.close()
        return rows

    def commit0(self):
        try:
            self.sql2.commit()
        except psycopg2.DatabaseError, e:
            self.sql2.rollback()
            print '(E) db_taggit commit0: %s' % e

    def add2e(self, sql, data):
        rows = self.execute2(sql, data)
        assert(len(rows)==1)
        return rows[0][0] # id

    def add1c(self, sql):
        rows = self.commit1(sql)
        assert(len(rows)==1)
        return rows[0][0] # id

    def exist(self, sql):
        rows = self.execute1(sql)
        if len(rows) > 0:
            return True
        else:
            return False

    # add new user
    # input: user name
    # output: user id or ID_NOT_EXIST (if user exist)
    def addUser(self, name): 
        if not self.existUser(name):
            sql = 'INSERT INTO users(name) VALUES('+\
                "'" + name + "'" + ') RETURNING id;'
            return self.add1c(sql)
        return ID_NOT_EXIST

    def existUser(self, name):
        sql = 'SELECT id from users where name = '+\
            "'" + name + "'" + ';'
        return self.exist(sql)
    
    # user login
    # input: user name
    # output: user id or ID_NOT_EXIST (if user not exist)
    def loginUser(self, name):
        id = ID_NOT_EXIST
        sql = 'SELECT id from users where name = '+\
            "'" + name + "'" + ';'
        rows = self.execute1(sql)
        if len(rows) > 0:
            id = rows[0][0]
        return id

    # similar to existUser
    def existItem(self, name):
        sql = 'SELECT id from items where name = '+\
            "'" + name + "'" + ';'
        return self.exist(sql)

    # similar to addUser
    def addItem(self, name):
        if not self.existItem(name):
            sql = 'INSERT INTO items(name) VALUES('+\
                "'" + name + "'" + ') RETURNING id;'
            return self.add1c(sql)
        else:
            return ID_NOT_EXIST
    
    def addPapersByBibtex(self, bibtex_dict):
        paper_list = []
        sql = """INSERT INTO papers(id,title,author,year,url,lastmod,bibtex) VALUES (%(id)s, %(title)s, %(author)s, %(year)s, %(url)s,%(lastmod)s, %(bibtex)s)  RETURNING id;"""
        for key in bibtex_dict:
            paper_dict = {}
            paper_dict['id'] = self.addItem(key)
            paper_dict['lastmod'] = datetime.datetime.utcnow().strftime(\
                "%a, %d %b %Y %H:%M:%S +0000")
            if (paper_dict['id'] != ID_NOT_EXIST):
                for field in BIBTEX_PAPER_MAP:                    
                    paper_dict[BIBTEX_PAPER_MAP[field]] = ''
                    try:
                        if (bibtex_dict[key][field]):
                            paper_dict[BIBTEX_PAPER_MAP[field]] =\
                                bibtex_dict[key][field]
                    except KeyError, e:
                        pass
                paper_id = self.add2e(sql,paper_dict)
                paper_list.append({'id':paper_id})
            else:
                paper_list.append({'id':ID_NOT_EXIST})

        self.commit0() # assume ok, TODO rollback -> id:ID_NOT_EXIST
        return paper_list
    
    # get paper by id
    # input: list of_ids
    # output: list of (existing) paper dicts
    def getPapersById(self, paper_ids):
        sql = "SELECT id,title,author,year,url,lastmod " +\
            "FROM papers WHERE id IN %s;"
        data = [tuple(paper_ids)]
        rows = self.execute2(sql,data)
        paper_list = []
        for x in rows:
            paper_dict = {}
            paper_dict["id"] = x[0]
            paper_dict["title"] = x[1]
            paper_dict["author"] = x[2]
            paper_dict["year"] = x[3]
            paper_dict["url"] = x[4]
            paper_dict["lastmod"] = x[5].strftime("%a, %d %b %Y %H:%M:%S +0000")
            paper_list.append(paper_dict)
        return paper_list

    def getPapersTop10(self):
        sql = "SELECT id FROM papers ORDER BY lastmod DESC LIMIT 10;"
        rows = self.execute1(sql)
        return self.getPapersById(rows)

    # similar to addUser
    # return tag id
    def addTag(self, name):
        if not self.existTag(name):
            sql = 'INSERT INTO tags(name) VALUES('+\
                "'" + name + "'" + ') RETURNING id;'
            return self.add1c(sql)
        return ID_NOT_EXIST

    # similar to existItem
    def existTag(self, name):
        sql = 'SELECT id from tags where name = '+\
            "'" + name + "'" + ';'
        return self.exist(sql)

    # input: tag id list
    def getTagsById(self, tag_ids):
        sql = "SELECT id,name FROM tags WHERE id IN %s;"
        data = [tuple(tag_ids)]
        rows = self.execute2(sql,data)
        tag_list = []
        for x in rows:
            tag_dict = {}
            tag_dict["id"] = x[0]
            tag_dict["name"] = x[1]
            tag_list.append(tag_dict)
        return tag_list

    def getTagsTop10(self):
        sql = "SELECT id FROM tags LIMIT 10;"
        rows = self.execute1(sql)
        return self.getTagsById(rows)

    def getUTI(self, user_id, tag_id, item_id):
        sql = 'SELECT id from utis where'+\
            ' user_id = '+ str(user_id) +\
            ' and tag_id = ' + str(tag_id) +\
            ' and item_id = ' + str(item_id) + ';'
        rows = self.execute1(sql)
        if len(rows) > 0:
            return rows[0][0]
        else:
            return ID_NOT_EXIST
    
    def existUTI(self, user_id, tag_id, item_id):
        sql = 'SELECT id from utis where'+\
            ' user_id = '+ str(user_id) +\
            ' and tag_id = ' + str(tag_id) +\
            ' and item_id = ' + str(item_id) + ';'
        return self.exist(sql)

    # similar to addItem
    # return uti id
    def tagItem(self, user_id, tag_id, item_id):
        if not self.existUTI(user_id, tag_id, item_id):
            sql = 'INSERT INTO utis(user_id, tag_id, item_id) VALUES('+\
                str(user_id) + "," + str(tag_id) + "," + str(item_id) +\
                ') RETURNING id;'
            return self.add1c(sql)
        else:
            return ID_NOT_EXIST

    # drop that uti relation
    # return uti id
    def detagItem(self, user_id, tag_id, item_id):
        uti_id = self.getUTI(user_id, tag_id, item_id)
        if uti_id != ID_NOT_EXIST:
            sql = 'DELETE FROM utis WHERE id = '+ str(uti_id) +\
                 ' RETURNING id;'
            rows = self.commit1(sql)
            assert(uti_id == rows[0][0])
        return uti_id

    # return tag list
    def getTagsByItemId(self, item_id):
        sql = 'SELECT tag_id FROM utis WHERE item_id = '+ str(item_id) + ';'
        rows = self.execute1(sql)
        if len(rows)>0:
            return self.getTagsById(rows)
        else:
            return []

    # return item list
    def getPapersByTagId(self, tag_id):
        sql = 'SELECT item_id FROM utis WHERE tag_id = '+ str(tag_id) + ';'
        rows = self.execute1(sql)
        if len(rows)>0:
            return self.getPapersById(rows)
        else:
            return []

    # return tag list
    def searchTagsByPrefix(self, prefix, offset, size):
        # ilike: case insensitive
        sql = 'SELECT id FROM tags WHERE name ilike ' + "'" + prefix + "%'" +\
            ' LIMIT ' + str(size) + ' OFFSET ' + str(offset) + ';' 
        rows = self.execute1(sql)
        if len(rows)>0:
            return self.getTagsById(rows)
        else:
            return []

###############################################################################
# Factory
###############################################################################
def db_factory(mode):
    dbo = db_taggit('taggit.cc')
    if mode == "reset":
        dbo.reset()
    return dbo
