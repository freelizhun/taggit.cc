#import time
#import random
#import sqlite3
import psycopg2
import sys
import datetime
import time

BIBTEX_PAPER_MAP = {
    'title':'title',
    'author':'author',
    'year':'year',
    'url':'url',
    '__bibtex':'bibtex',
}

###############################################################################
# DB
###############################################################################
class db_taggit:
    # Singleton
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(db_taggit, self).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self,sqlhost):
        self.sql2 = None
        try:
            self.sql2 = psycopg2.connect(host=sqlhost, port='5432', \
                          database='test', user='taggit', password='taggit')
        except psycopg2.DatabaseError, e:
            print '(F) db_taggit init: %s' % e
            sys.exit()

    def __del__(self):
        if self.sql2:
            self.sql2.close()

    def reset(self):
        try:
            cur = self.sql2.cursor()

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
                  "author VARCHAR(127), year VARCHAR(4), url VARCHAR(127), "+\
                  "lastmod timestamp, bibtex VARCHAR(8191), "+\
                  "FOREIGN KEY(id) REFERENCES items(id))")
            cur.execute(
                "CREATE TABLE utis(" +\
                    "user_id INTEGER, tag_id INTEGER, item_id INTEGER, "+\
                    "FOREIGN KEY(user_id) REFERENCES users(id), "+\
                    "FOREIGN KEY(tag_id) REFERENCES tags(id), "+\
                    "FOREIGN KEY(item_id) REFERENCES items(id))")
            cur.execute("CREATE INDEX index_un ON users (name)")
            cur.execute("CREATE INDEX index_tn ON tags (name)")
            
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

    def commit3(self, sql, data):
        try:
            cur = self.sql2.cursor()
            cur.executemany(sql, data)
            self.sql2.commit()
            #rows = cur.fetchmany()
        except psycopg2.DatabaseError, e:
            self.sql2.rollback()
            print '(E) db_taggit commit3: %s' % e
        finally:
            cur.close()
        #return rows

    def add0(self, sql, data):
        rows = self.execute2(sql, data)
        assert(len(rows)==1)
        return rows[0][0] # id

    def add1(self, sql):
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
    # output: user id or -1 (if user exist)
    def addUser(self, name): 
        if not self.existUser(name):
            sql = 'INSERT INTO users(name) VALUES('+\
                "'" + name + "'" + ') RETURNING id;'
            return self.add1(sql)
        return -1

    def existUser(self, name):
        sql = 'SELECT id from users where name = '+\
            "'" + name + "'" + ';'
        return self.exist(sql)
    
    # user login
    # input: user name
    # output: user id or -1 (if user not exist)
    def loginUser(self, name):
        user_id = -1
        sql = 'SELECT id from users where name = '+\
            "'" + name + "'" + ';'
        rows = self.execute1(sql)
        if len(rows) > 0:
            id = rows[0][0]
        return id

    # similar to existItem
    def existItem(self, name):
        sql = 'SELECT id from items where name = '+\
            "'" + name + "'" + ';'
        return self.exist(sql)

    # similar to addUser
    def addItem(self, name):
        if not self.existItem(name):
            sql = 'INSERT INTO items(name) VALUES('+\
                "'" + name + "'" + ') RETURNING id;'
            return self.add1(sql)
        return -1
    
    def addPapersByBibtex(self, bibtex_dict):
        paper_list = []
        sql = """INSERT INTO papers(id,title,author,year,url,lastmod,bibtex) VALUES (%(id)s, %(title)s, %(author)s, %(year)s, %(url)s,%(lastmod)s, %(bibtex)s)  RETURNING id;"""
        for key in bibtex_dict:
            paper_dict = {}
            paper_dict['id'] = self.addItem(key)
            paper_dict['lastmod'] = datetime.datetime.utcnow().strftime(\
                "%a, %d %b %Y %H:%M:%S +0000")
            if (paper_dict['id'] != -1):
                for field in BIBTEX_PAPER_MAP:                    
                    paper_dict[BIBTEX_PAPER_MAP[field]] = ''
                    try:
                        if (bibtex_dict[key][field]):
                            paper_dict[BIBTEX_PAPER_MAP[field]] =\
                                bibtex_dict[key][field]
                    except KeyError, e:
                        pass
                paper_id = self.add0(sql,paper_dict)
                paper_list.append({'id':paper_id})
            else:
                paper_list.append({'id':-1})

        self.commit0() # TODO rollback -> -1
        return paper_list


###############################################################################
# Factory
###############################################################################
def db_factory(mode):
    dbo = db_taggit('taggit.cc')
    if mode == "reset":
        dbo.reset()
    return dbo
