# http://docs.webob.org/en/latest/jsonrpc-example.html
# import traceback
import sys
from paste.cascade import Cascade
from ps_router import RouterApp;
from paste.urlparser import StaticURLParser

def make_app():
    service_app = RouterApp()

    service_app.add_route("/u/signup", 'UserApp', 'signup')
    service_app.add_route("/u/login", 'UserApp', 'login')
    service_app.add_route("/i/addbibtex", 'ItemApp', 'add_item_by_bibtex')
    service_app.add_route("/i/getbytag", 'ItemApp', 'get_item_by_tag')
    service_app.add_route("/i/info", 'ItemApp', 'get_item_by_id')
    service_app.add_route("/taggit", 'TagApp', 'add_tag_to_item')
#    router.add_route("/search", SearchApp);
    static_app = StaticURLParser('../www/')
    cascade_app = [service_app,static_app]

    return Cascade(cascade_app)

def main():
    import optparse
    parser = optparse.OptionParser(
        usage="%prog [OPTIONS] MODULE:EXPRESSION")
    parser.add_option(
        '-P', '--port', default='8080',
        help='Port to serve on (default 8080)')
    parser.add_option(
        '-H', '--host', default='0.0.0.0',
        help='Host to serve on (default localhost; 0.0.0.0 to make public)')
    parser.add_option(
        '-M', '--mode', default='debug',
        help='debug or prod mode')
    options, args_ = parser.parse_args()

    # options.mode
    entry_app = make_app()
    from paste import httpserver
    httpserver.serve(entry_app,host=options.host,port=options.port)

if __name__ == '__main__':
    main()
