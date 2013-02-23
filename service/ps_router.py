#!/usr/bin/env python
from webob import Request, Response
from webob import exc

from routes import Mapper
from ps_middleware import middleware_factory

class RouterApp:
    """ Route request to the matching wsgiapp. """
    def __init__(self,mode):
        self.map = Mapper()
        self.__routing_table = {}; # Maps path to app.
        self.mode = mode

    # HTTP POST json 
    # -> webob (maybe no need?)
    def __call__(self, environ, start_response):
        req = Request(environ);
#        print 'env:\n', environ
#        print 'route:\n', req.path_qs
#        print 'match:\n', self.map.match(req.path_qs)
        match = self.map.match(req.path_qs)
        if match:
            m = match['middleware']
            h = match['handler']
            o = self.__routing_table[m]
            if o is not None:
                environ['_HANDLER'] = h
                return o(environ, start_response)

        err = exc.HTTPNotFound('NO SERVICE FOUND')
        return err(environ, start_response)

    def add_route(self, pat, mid, han):
        if mid not in self.__routing_table: # SINGELTON
            self.__routing_table[mid] = \
                middleware_factory(mid,self.mode); 
        self.map.connect(pat,middleware=mid,handler=han)
