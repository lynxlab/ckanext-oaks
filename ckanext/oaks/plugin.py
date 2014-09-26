import config

import urllib2
import urllib
import json

import logging
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.uploader as uploader
import ckan.logic as logic

log = logging.getLogger(__name__)



class oaksPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm)
    p.implements(p.IResourceController,inherit=True)
    p.implements(p.IActions)
    p.implements(p.ITemplateHelpers)
    
    def update_config(self, config):
        log.debug('this is update_config calling')
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')    
        
    def get_actions(self):
        return {
            'package_create': package_create_FN,
            'package_update': package_update_FN,
#            'resource_create': resource_create_FN
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
        return {'get_dataset_type': dataset_type}
        
    def after_create(self, context, resource):
        log.info('this is after_create calling')
        print resource
        print '----'
        print context
    

def package_create_FN(context, data_dict):
#    print data_dict
    if ('eurovoc_checked' in data_dict):
        data_dict['eurovoc_uri'] = eurovoc_term(data_dict)
    return logic.action.create.package_create(context, data_dict)

def package_update_FN(context, data_dict):
#    print tk.request.params
#    print '-------'
    log.info('this is package_update_FN calling')
    print data_dict

    if ('eurovoc_checked' in data_dict):
        log.info('before eurovoc_term calling')
        eurovoc_data = eurovoc_term(data_dict)
        if (len(eurovoc_data) > 0):
            data_dict['eurovoc_uri'] = eurovoc_data['eurovoc_uri']
            data_dict['eurovoc_concept'] = eurovoc_data['eurovoc_concept']

    return logic.action.update.package_update(context, data_dict)

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
