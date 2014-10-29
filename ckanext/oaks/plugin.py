import config

import pylons.config as CKAN_config
#from pylons import request

from beaker.middleware import SessionMiddleware

import platform

import os
import urllib2
import urllib
import json

import logging
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.uploader as uploader
import ckan.logic as logic

import ckan.lib.base as base

import re

#import refine.refine_oaks as refine_oaks
#import refine.refine_lib as refine_oaks

import csvutilities.oaks_csvclean as oaks_csvclean
import csvutilities.oaks_in2csv as oaks_convert

import inspect
from os.path import split
from dbf import Null

log = logging.getLogger(__name__)

class oaksPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm)
    p.implements(p.IResourceController,inherit=True)
    p.implements(p.IActions)
    p.implements(p.ITemplateHelpers)
    
    def __init__(self, *args, **kwargs):
        wsgi_app = SessionMiddleware(None, None)
        self.session = wsgi_app.session
        
    
    def update_config(self, config):
        log.debug('this is update_config calling')
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')    
        # Add the extension public directory so we can serve our own content
        tk.add_public_directory(config, 'templates/public')
#        tk.add_resource('fanstatic', 'oaks')
                
    def get_actions(self):
        return {
            'package_create': package_create_FN,
            'package_update': package_update_FN,
#            'resource_show': resource_show_FN,
            'activity_create': activity_create_FN
        }   

    def _modify_package_schema(self, schema):
        schema.update({
            'eurovoc_uri': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
            'eurovoc_concept': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')]        
        })
        return schema

    def create_package_schema(self):
        schema = super(oaksPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(oaksPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(oaksPlugin, self).show_package_schema()
        schema.update({
            'eurovoc_uri': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')],
            'eurovoc_concept': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')]        
        })
        return schema
    
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []  

        
    def get_helpers(self):
        return {'get_result_checked_csv': get_result_checked_csv,
                'get_dataset_type': dataset_type
                }
    
    def before_create(self, context, resource):
        log.info('this is before_create calling')
        print resource
        if ('url_type' in resource and resource['url_type'] == 'upload' and to_upper(resource['format']) == 'CSV'):
            log.info('uploaded file: ' + resource['url'])
    
        
    def after_create(self, context, resource):
        ''' After created resource: check CSV file '''
        log.info('this is after_create calling')
        self.session['csvclean'] = None
        self.session.save()
        if ('upload' in tk.request.params and tk.request.params['upload'] != '' and resource['url_type'] == 'upload' 
            and (to_upper(resource['format']) == 'CSV' or to_upper(resource['format']) == 'XLS' or to_upper(resource['format']) == 'XLSX')):
            log.info('uploaded file: ' + resource['url']+'----------\n')
            """ CSVKIT 
            """
            #print inspect.getmoduleinfo('/usr/lib/ckan/default/src/ckan/ckanext-oaks/ckanext/oaks/csvutilities/csvclean.py')
            slash = '/'
            if 'windows' in platform.system():
                slash = '\\'

            # build path to file uploaded
            basedir =  CKAN_config.get( 'ckan.storage_path' )
            site_url = CKAN_config.get('ckan.site_url')
            id_resource = resource['id']
            file_name = id_resource[6:len(id_resource)]
            inputfile = basedir+slash+'resources'+slash+id_resource[0:3]+slash+id_resource[3:6]+slash+file_name
            
            # Get the dataset id
            id_dataset = None
            url_uploaded_file = resource['url']
            p = re.compile(u'/dataset/(.+)/resource')
            re_res = re.search(p, url_uploaded_file)
            
            if (to_upper(resource['format']) == 'CSV'):
                            
                utility = oaks_csvclean.OAKSClean(inputfile)
                dryRun = True
                resultCleanCheck = utility.main(dryRun)
                
                if resultCleanCheck != None:
                    self.session['csvclean'] = resultCleanCheck
                    self.session.save()
                    if (re_res != None):
                        id_dataset = re_res.group(1)
                        #                redirect(h.url_for(controller='package', action='resource_read',id=id, resource_id=resource_id))
                        tk.redirect_to(controller='package', action='resource_read',id=id_dataset, resource_id=id_resource)
            elif (to_upper(resource['format']) == 'XLS' or to_upper(resource['format']) == 'XLSX'):
                args = None
                last_period = file_name.rfind('.')
                # extension = file_name[last_period + 1:]
                extension = resource['format'].lower()
                #file_name_no_extension = file_name[0:last_period]
                
                # check dir in which save converted file. If not exists need to create it
                dir_error = False
                output_dir = basedir+slash+'storage'+slash+'oaks'
                if not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                    except OSError:
                        if not os.path.isdir(path):
                            dir_error = True
                
                if not dir_error:
                    output_file = basedir+slash+'storage'+slash+'oaks'+slash+id_resource+'.csv'
                    #es.: output_file = /var/lib/ckan/default/storage/oaks/id_risorsa.csv
                    # corrispodente URL: http://ckan_URL/oaks/id_risorsa.csv
                    print 'convert: '+output_file
                    utility = oaks_convert.OAKSIn2CSV(inputfile, args, output_file, extension)
                    utility.main()
                    
                    if (re_res != None):
                        if os.path.isfile(output_file):
                                new_resource_url = site_url+slash+'oaks'+slash+id_resource+'.csv'
                                id_dataset = re_res.group(1)
                                data_dict = {}
                                data_dict['package_id'] = id_dataset
                                data_dict['url'] = new_resource_url
                                data_dict['format'] = 'csv'
                                data_dict['name'] = resource['name']
                                data_dict['description'] = resource['description']
                                
                                logic.action.create.resource_create(context, data_dict)
                                
                
                
            
                # INIZIO OpeRefine
    #            OR_server = refine_oaks.RefineServer()
    #            refineObj = refine_oaks.Refine(OR_server)
    #            project_file = None
    #            project_options = {}
    #            project_name = 'file_test_csv'
    #            project_url = resource['url']
    #            project_format = 'text/line-based/*sv'
    #            
    #            refineProject = refineObj.new_project(project_url=resource['url'],project_name='nome progetto',project_format= 'text/line-based/*sv' ,**project_options)
    #            refineProjects = refineObj.list_projects().items()
                #FINE OpenRefine

    def after_update(self, context, resource):
        ''' After updated resource: check CSV file '''
        log.info('this is after_update calling')
        #print inspect.getmembers(tk.request)
        self.session['csvclean'] = None
        self.session.save()
        if ('upload' in tk.request.params and tk.request.params['upload'] != '' and resource['url_type'] == 'upload' and to_upper(resource['format']) == 'CSV') :
            log.info('uploaded file: ' + resource['url']+'----------\n')
            """ CSVKIT 
            """
#            print inspect.getmembers(csvclean)
            #print inspect.getmoduleinfo('/usr/lib/ckan/default/src/ckan/ckanext-oaks/ckanext/oaks/csvutilities/csvclean.py')
            slash = '/'
            if 'windows' in platform.system():
                slash = '\\'

            # build path to file uploaded
            basedir =  CKAN_config.get( 'ckan.storage_path' )
            id_resource = resource['id']
            file_name = id_resource[6:len(id_resource)]
            inputfile = basedir+slash+'resources'+slash+id_resource[0:3]+slash+id_resource[3:6]+slash+file_name
            
            utility = oaks_csvclean.OAKSClean(inputfile)
            dryRun = True
            resultCleanCheck = utility.main(dryRun)
            print resultCleanCheck
#            print inspect.getmembers(request.session)

#            print inspect.getmembers(tk.request)

            self.session['csvclean'] = resultCleanCheck
            self.session.save()
            

            
#             self.session['csvclean'] = resultCleanCheck
#             print self.session
#             self.session.save()
    
    def resultCleanCheck(self):
        pass
    
def resource_show_FN(context, data_dict): 
    """Because of a bug of CKAN, the method gives back this error message:
            RuntimeError: maximum recursion depth exceeded
            
            We are not using this method.
            We use after_create instead.
            
            It seems fixed in version 2.2.1, 
            but we are using the latest (ver. 2.3 at the moment) 
            in which the fix was not included yet.
    """
    wsgi_app = SessionMiddleware(None, None)
    session = wsgi_app.session
    session['csvclean'] = None
    session.save()
    log.info('resource_show')

    return logic.get_action('resource_show')(context, data_dict)
    



        

def package_create_FN(context, data_dict):
    if ('eurovoc_checked' in data_dict):
        eurovoc_data = eurovoc_term(data_dict)
        if (len(eurovoc_data) > 0):
            data_dict['eurovoc_uri'] = eurovoc_data['eurovoc_uri']
            data_dict['eurovoc_concept'] = eurovoc_data['eurovoc_concept']

    return logic.action.create.package_create(context, data_dict)

def package_update_FN(context, data_dict):
#    print tk.request.params
#    print '-------'
    log.info('this is package_update_FN calling')
#    print data_dict

    if ('eurovoc_checked' in data_dict):
        log.info('before eurovoc_term calling')
        eurovoc_data = eurovoc_term(data_dict)
        if (len(eurovoc_data) > 0):
            data_dict['eurovoc_uri'] = eurovoc_data['eurovoc_uri']
            data_dict['eurovoc_concept'] = eurovoc_data['eurovoc_concept']
            

    return logic.action.update.package_update(context, data_dict)

def activity_create_FN(context, activity_dict, **kw):

    """Create a new activity stream activity.
        You must be a sysadmin to create new activities.
        Parameters
        * user_id (string) - the name or id of the user who carried out the activity, e.g. 'seanh'
        * object_id - the name or id of the object of the activity, e.g. 'my_dataset'
        * activity_type (string) - the type of the activity, this must be an activity type that CKAN
        knows how to render, e.g. 'new package', 'changed user', 'deleted group'
        etc.
        * data (dictionary) - any additional data about the activity
        Returns the newly created activity
        Return type dictionary"""

    log.info('activity_create_FN calling')
    return logic.action.create.activity_create(context, activity_dict, **kw)


def resource_create_FN(context, data_dict): 
    """Because of a bug of CKAN, the method gives back this error message:
            RuntimeError: maximum recursion depth exceeded
            
            We are not using this method.
            We use after_create instead.
            
            It seems fixed in version 2.2.1, 
            but we are using the latest (ver. 2.3 at the moment) 
            in which the fix was not included yet.
    """
    return logic.get_action('resource_create')(context, data_dict)


def eurovoc_term(data_dict):
    log.info('this is eurovoc_term calling 1')
    eurovoc = {}
    tags = data_dict['tags']
    tags_for_API = ''
    for singleTag in tags:
        if (singleTag['state'] == 'active'):
            print "The Current tag is:",
            print singleTag['name']
            tags_for_API += singleTag['name'] + ' '

    log.info('tutte le api: '+tags_for_API)
    server = config.semanticAPI['SERVER']+config.semanticAPI['PASS']+'/'+config.semanticAPI['EUROVOC_SEARCH']
    log.info('server: '+server)
    if (tags_for_API != ''):
        eurovoc_return = urlopen(server, tags_for_API)
        if (eurovoc_return != ''):
            eurovoc_data =  json.loads(eurovoc_return.read())
            eurovoc_category=eurovoc_data['categories'][0]['category']
            eurovoc['eurovoc_uri'] = 'http://eurovoc.europa.eu/'+eurovoc_category
            eurovoc['eurovoc_concept'] = eurovoc_data['categories'][0]['description'][0]
        else:
            eurovoc['eurovoc_uri'] = ''
            eurovoc['eurovoc_concept'] = ''

    log.info(eurovoc)
#    return data_dict['eurovoc_uri']
    return eurovoc
    

#************
# HELPERS
#************
def get_result_checked_csv(res):
    ''' return the result of csv checked'''
    wsgi_app = SessionMiddleware(None, None)
    session = wsgi_app.session
    csvclean = session['csvclean']
#    print session
    session['csvclean'] = None
    session.save()
#    log.info('checked helper')
#    return value.replace('\n','<br>\n')
    #return csvclean.replace('\n','<br />\n') 
    return ''
#     if (res != ''):
#         return res
    
def dataset_type():
    return 'ciccio'

def urlopen(server, data=None, params=None):
    """Open a API URL and with optional query params and GET data.

    data: GET data dict
    param: query params dict

    Returns urllib2.urlopen iterable."""
    data = urllib.quote_plus(data)
    log.info('calling urlopen')

    url = server +  data
    log.info('--- URL ----'+url)
    if data is None:
        return data
    if params:
        url += '?' + urllib.urlencode(params)
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        log.debug('HTTP %d "%s" for %s\n\t%s' % (e.code, e.msg, e.geturl()))
        response = ''
        #raise Exception('HTTP %d "%s" for %s\n\t%s' % (e.code, e.msg, e.geturl(), data))
    except urllib2.URLError as e:
        log.debug(urllib2.URLError(
            '%s for %s. No API service reachable/running; ENV set?' %
            (e.reason, server)))
        response = ''
        #raise urllib2.URLError(
        #    '%s for %s. No API service reachable/running; ENV set?' %
        #    (e.reason, self.server))
#    if response.info().get('Content-Encoding', None) == 'gzip':
        # Need a seekable filestream for gzip
#        gzip_fp = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
        # XXX Monkey patch response's filehandle. Better way?
#        urllib.addbase.__init__(response, gzip_fp)
#    log.info(response.read())
    return response

def urlopen_json(self, *args, **kwargs):
    """Open a Refine URL, optionally POST data, and return parsed JSON."""
    response = json.loads(self.urlopen(*args, **kwargs).read())
    if 'code' in response and response['code'] not in ('ok', 'pending'):
        error_message = ('server ' + response['code'] + ': ' +
                         response.get('message', response.get('stack', response)))
        raise Exception(error_message)
    return response

def to_upper(string):
    """ Converte la stringa in maiuscolo."""
    upper_case = ""
    for character in string:
        if 'a' <= character <= 'z':
            location = ord(character) - ord('a')
            new_ascii = location + ord('A')
            character = chr(new_ascii)
        upper_case = upper_case + character
    return upper_case