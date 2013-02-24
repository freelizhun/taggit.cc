import sys
from paste.cascade import Cascade
from ps_router import RouterApp;
from paste.urlparser import StaticURLParser

def make_app(mode):
    service_app = RouterApp(mode)

    service_app.add_route("/user/signup", 'UserApp', 'signup')
    service_app.add_route("/user/login", 'UserApp', 'login')
    service_app.add_route("/user/tagitem", 'UserApp', 'tag_item')
    service_app.add_route("/user/detagitem", 'UserApp', 'detag_item')
    service_app.add_route("/tag/addbyname", 'TagApp', 'add_by_name')
    service_app.add_route("/tag/getbyitem", 'TagApp', 'get_by_item')
    service_app.add_route("/tag/gettop10", 'TagApp', 'get_top10')
    service_app.add_route("/tag/searchbyprefix", 'TagApp', 'search_by_prefix')
    service_app.add_route("/paper/addbibtex", 'PaperApp', 'add_by_bibtex')
    service_app.add_route("/paper/getbyid", 'PaperApp', 'get_by_id')
    service_app.add_route("/paper/getbytag", 'PaperApp', 'get_by_tag')
    service_app.add_route("/paper/gettop10", 'PaperApp', 'get_top10')

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

    entry_app = make_app(options.mode)

    if options.mode == 'debug' or 'reset':
        options.port = 8002

    from paste import httpserver
    httpserver.serve(entry_app,host=options.host,port=options.port)

if __name__ == '__main__':
    main()
