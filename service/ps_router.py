#!/usr/bin/env python
from webob import Request, Response
from webob import exc

from routes import Mapper
from ps_middleware import make_middleware

class RouterApp:
    """ Route request to the matching wsgiapp. """
    def __init__(self):
        self.map = Mapper()
        self.__routing_table = {}; # Maps path to app.

    # POST/JSON 
    # WebOb (No need?)
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
        if mid not in self.__routing_table:
            self.__routing_table[mid] = make_middleware(mid); # SINGELTON?
        self.map.connect(pat,middleware=mid,handler=han)
