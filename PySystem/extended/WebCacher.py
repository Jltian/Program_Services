# -*- encoding: UTF-8 -*-
import json
import os
import cherrypy


@cherrypy.expose
class webSplitService(object):
    def __init__(self, folder_path: str):
        self.splitter = ContentSplit(data_path=folder_path)

    @cherrypy.tools.accept(media='text/plain')
    def GET(self, words, method, unable):
        unable_char_list = str(unable).split('|')
        unable_list = list()
        for char in unable_char_list:
            if char not in self.splitter.ustring_checker.language_base:
                print('warning: wrong unable char_type {0:s}'.format(char))
            else:
                unable_list.append(char)
        if int(method) == 0:
            cherrypy.session['my_string'] = json.dumps({'content': self.splitter.split(words)})
        elif int(method) == 1:
            cherrypy.session['my_string'] = json.dumps({'content': self.splitter.split_firm_name(words)})
        # elif int(method) == 9:
        #     self.splitter.add_blocked_company_keyword(words, force_add=False)
        # elif int(method) == 8:
        #     self.splitter.add_company_service_type(words, force_add=False)
        # elif int(method) == 7:
        #     self.splitter.add_company_type(words, force_add=False)
        else:
            print('Unknown method number {0:d}'.format(int(method)))
            cherrypy.session['my_string'] = json.dumps({'content': ''})
        return cherrypy.session['my_string']

if __name__ == '__main__':
    root = webSplitService(folder_path=os.path.join('xenSplittingService', 'data'))
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.quickstart(root, '/', conf)
