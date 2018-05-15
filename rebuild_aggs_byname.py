import sys
import time
import json
import requests
from uritemplate import expand
from test.test_set import cube

__author__ = 'joe, radek'


AGG_BATCH_REBUILD_ENDPOINT = '/aggregate-batch/orgId/{orgId}/envId/{envId}/{projectId}?cubeId={cubeId}'
AGG_BATCH_STATUS_ENDPOINT = '/aggregate-batch/orgId/{orgId}/envId/{envId}'
ATSCALE_AUTH_ENDPOINT = '/{orgId}/auth'

def base_url(config):
    return ('https' if config.get('useHttps') else 'http') + '://' + config['hostName'] + ':' + str(config['port'])

def base_url_auth(config):
    return ('https' if config.get('useHttps') else 'http') + '://' + config['designConfig']['hostName'] + ':' + str(config['designConfig']['port'])

def get_config(file_path):
    with open(file_path) as file:
        return json.load(file)

def getOrgId(orgName, sec):
    orgId = None
    url = base_url_auth(config) + '/api/1.0/orgs'
    r = requests.get(url, headers = {'Authorization': 'Bearer ' + sec}, verify=False)
    print 'Return: ' + r.text
    if r.status_code != 200:
        print 'Get origid failed: ' + str(r.status_code)
        return orgId
    o_json = r.json()
    for e in o_json['response']:
        print e
        if e['name'] == orgName:
            orgId = e['id']
            break
        
    return orgId

def rebuild_aggs(config):
    urlAuth = base_url_auth(config) + '/' + config['designConfig']['defaultOrgId'] + '/auth'
    ar = requests.get(urlAuth, auth=(config['designConfig']['userName'],config['designConfig']['password']))
     
    if ar.status_code != 200:
        print 'Authenticate failed with Error:  Call was not successful for unknown reason, status code == ' + str(ar.status_code) + ' and plain text response was: ' + ar.text
        return False

    orgId = getOrgId(config['defaultOrgName'], ar.text)
    if orgId == None:
        print 'Orgid not found for orgName: ' + config['defaultOrgName']
        return False
    
    print 'GOT orgId: ' + str(orgId);

    projectId = None
    cubeId = None
    
    url = base_url(config) + '/projects/orgId/' + orgId + '/envId/' + config['defaultEnvId'] + '?includeCubes=true'
    r = requests.get(url, headers = {'Authorization': 'Bearer ' + ar.text})

    if r.status_code != 200:
        print 'Call was not successful for unknown reason, status code == ' + str(r.status_code) + ' and plain text response was: ' + r.text
        return False
    
    print r.text
    
    o_json = r.json()
    for e in o_json['response']['projects']:
        if e['name'] == config['projectName']:
            projectId = e['id']
            for cube in e['cubes']:
                if cube['name'] == config['cubeName']:
                    cubeId = cube['id']
                    break
    
    if projectId == None:
        print 'projectId not found for projectsName: ' + config['projectName']
        return False
    if cubeId == None:
        print 'cubeId not found for cubeName: ' + config['cubeName']
        return False
        
    print "Project is: " + projectId
    print "Cube is: " + cubeId
                    
    url = base_url(config) + '/aggregate-batch/orgId/' + config['defaultOrgId'] + '/envId/' + config['defaultEnvId'] + '/' + config['projectId'] + '?cubeId=' + config['cubeId']

    print 'Sending rebuild aggs POST request to: ' + url

    r = requests.post(url, headers = {'Authorization': 'Bearer ' + ar.text})
    
    print 'Response (plain text ): ' + r.text

    if r.status_code == 500:
        print 'Internal server error response (status code == 500), usually this means a batch is already running'
        return False
    if r.status_code != 200:
        print 'Error:  Call was not successful for unknown reason, status code == ' + str(r.status_code) + ' and plain text response was ' + r.text
        return False

    r_json = r.json()
    batch_response = r_json['batch']
    batch_response_id = batch_response['id']

    print 'Batch status: ' + batch_response['status']
    print 'Batch id: ' + batch_response_id

    status_url = base_url(config) + '/aggregate-batch/orgId/' + config['defaultOrgId'] + '/envId/' + config['defaultEnvId']

    if config['waitForCompletion']:
        done = False
        status = ''
        while not done:
            r = requests.get(status_url, headers={'Authorization': 'Bearer ' + ar.text})
            
            print 'status_url : ' + status_url
            print 'Response (again status_url ): ' + r.text
 
            r_json = r.json()

            batch = None
            for e in r_json['response']['batches']:
             if config['projectId'] == r_json['response']['batches'][0]['projectId'] and config['cubeId'] == r_json['response']['batches'][0]['cubeId']:
                if config['projectId'] == e['projectId'] and config['cubeId'] == e['cubeId']:
                    batch = e['batch']
                    break

            if batch['id'] != batch_response_id:
                print 'Batch id==' + batch['id'] + 'on most recent batch status query response does not match batch id==' + batch_response_id + ' from batch rebuild response called by this action.  Is another process triggering batch rebuild?'

            status = batch['status']
            progress = batch['progressPercentage']
            print 'Progress percentage: ' + str(progress)
            print 'Status: ' +  status
            if not (status == 'new' or status == 'inprogress'):
                done = True
            else:
                time.sleep(config['pollingPeriodSeconds'])

        if not status == 'done':
            print 'Final batch status was: ' + status
            return False

    return True


if __name__ == '__main__':
    config = get_config(sys.argv[1])
    if not rebuild_aggs(config):
        sys.exit(1)