from abc import ABC, abstractmethod
import requests

class APIQueryBaseClass(ABC):
    """
    Abstract APIQuery base class
    Support for REST APIs, e.g., Dataverse, DataCite
    """
    @property
    @abstractmethod
    def server_url(self) -> str:
        """
        API query server url
        """
        return ''

    @server_url.setter
    def server_url(self, url : str):
        """
        Set server url

        Parameters
        ----------
        url : str
        """
        pass

    @server_url.getter
    def server_url(self) -> str:
        """
        Get server url

        Return
        ------
        str
        """
        return ''
    
    @property
    @abstractmethod 
    def endpoint(self) -> str:
        """
        API endpoint string
        """
        return ''

    @endpoint.getter
    def endpoint(self) -> str:
        """
        Get API endpoint string

        Return
        ------
        str
        """
        return ''
    
    @property
    @abstractmethod
    def parameters(self):
        """
        API parameters
        """
        return {}

    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameters
        ----------
        dict
        """
        pass

    @parameters.getter
    def parameters(self) -> dict:
        """
        Get API parameters

        Return
        ------
        dict
        """
        return {}

    @abstractmethod
    def validate_parameters(self) -> bool:
        """
        Validate parameters and their values

        Return
        ------
        bool
        """
        pass
    
    @abstractmethod
    def execute(self, api_token : str) -> dict:
        """
        Execute API query and return the result

        Return
        ------
        dict
            {'status_code':code, 'data':data, 'reason':reason}
        """
        return {}

class DataverseMetricsAPIQuery(APIQueryBaseClass):
    """
    Base class for all Dataverse metrics subclasses

    Parameter
    ---------
    server : str
        Url for API server. e.g., https://demo.dataverse.org
    """
    def __init__(self, server : str):
        self._server_url = server
        self._parameters = {}

    @property
    def server_url(self) -> str:
        """
        API query server url
        """
        return self._server_url

    @server_url.setter
    def server_url(self, url : str):
        """
        Set server url

        Parameters
        ----------
        url : str
        """
        self._server_url = url

    @server_url.getter
    def server_url(self) -> str:
        """
        Get server url

        Return
        ------
        str
        """
        return self._server_url

    @property
    def parameters(self):
        """
        API parameters
        """
        return self._parameters

    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameters
        ----------
        dict

        Return
        ------
        None
        """
        for key, value in params.items():
            self._parameters[key] = value

    def validate_parameters(self) -> bool:
        """
        Validate parameters and their values

        Return
        ------
        bool
        """
        values = self._parameters.values()
        if None in values:
            return False
        return True
    
    def execute(self, api_token: str) -> dict:
        """
        Execute API query

        Return
        ------
        dict 
            {'status_code':code, 'data':data, 'reason':reason}
        """
        return {}

class DataverseUniqueDownloadsMonthly(DataverseMetricsAPIQuery):
    """
    Monthly cumulative timeseries of unique user counts for 
    datasets in the collection scope.

    Endpoint: /api/info/metrics/uniquedownloads

    See: https://guides.dataverse.org/en/latest/api/metrics.html
    """
    def __init__(self, server : str, **kwargs):
        super().__init__(server)
        self._parameters = {
            'parentAlias': kwargs.get('parentAlias', None),
        }

    @property
    def endpoint(self) -> str:
        return 'api/info/metrics/uniquedownloads/monthly'

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.getter
    def parameters(self):
        """
        Get API parameters

        Return
        ------
        dict        
        """
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Execute query

        Return
        ------
        dict
            {'status_code': code, 'data':[data], 'reason':reason}
        """
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        request_url = f'{self.server_url}/{self.endpoint}'
        payload = self._parameters

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }


class DataverseDatasetsMonthly(DataverseMetricsAPIQuery):
    """
    Monthly cumulative timeseries of unique user counts for
    datasets in the collection scope.

    Endpoint: /api/info/metrics/datasets/monthly

    See: https://guides.dataverse.org/en/latest/api/metrics.html
    """

    def __init__(self, server: str, **kwargs):
        super().__init__(server)
        self._parameters = {
            'parentAlias': kwargs.get('parentAlias', None),
        }

    @property
    def endpoint(self) -> str:
        return 'api/info/metrics/datasets/monthly'

    @property
    def parameters(self):
        return self._parameters

    @parameters.getter
    def parameters(self):
        """
        Get API parameters

        Return
        ------
        dict
        """
        return self._parameters

    @parameters.setter
    def parameters(self, params: dict):
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Execute query

        Return
        ------
        dict
            {'status_code': code, 'data':[data], 'reason':reason}
        """
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        request_url = f'{self.server_url}/{self.endpoint}'
        payload = self._parameters

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code': r.status_code,
                'reason': r.reason,
                'data': []
            }

        return {
            'status_code': r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }


class DataverseDatasetDetails(DataverseMetricsAPIQuery):
    """
    Get detailed information about a dataset given its 
    persistent identifier
    """
    def __init__(self, server : str, **kwargs):
        super().__init__(server)
        self._parameters = {
            'persistentId': kwargs.get('persistentId', None)
        }

    @property
    def endpoint(self) -> str:
        #return 'api/datasets/:persistentId'
        return 'api/datasets/:persistentId/versions/:latest-published'
    
    @endpoint.setter
    def endpoint(self, endpoint : str):
        """
        Set API endpoint string

        Parameter
        ---------
        endpoint : str
        """
        pass    

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Execute API query

        Return
        ------
        dict 
            {'status_code':code, 'data':data, 'reason':reason}
            data fields:
                UNF, citationDate, createTime, datasetId
                datasetPersistentId, deaccessionLink, fileAccessRequest
                files, id, lastUpdateTime, latestVersionPublishedState,
                license, metadataBlocks, publicationDate, releaseTime
                storageIdentifier, versionMinorNumber, versionNumber
                versionState
        """
        if not self.validate_parameters():
            raise Exception('Invalid parameter values')
        
        pid = self._parameters['persistentId']

        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        request_url = f'{self.server_url}/{self.endpoint}'
        payload = self._parameters

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }

class DataverseCollectionTreeHierarchy(DataverseMetricsAPIQuery):
    """
    Get the (nested) tree hierarchy for a collection
    """
    def __init__(self, server : str, **kwargs):
        super().__init__(server)
        self._parameters = {
            'parentAlias': kwargs.get('parentAlias', None)
        }

    @property
    def endpoint(self) -> str:
        return 'api/info/metrics/tree'
    
    @endpoint.setter
    def endpoint(self, endpoint : str):
        """
        Endpoint string
        """
        pass

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Execute API query

        Return
        ------
        dict 
            {'status_code':code, 'data':data, 'reason':reason}
            data fields:
                alias, depth, id, name, ownerId
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')
        
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        request_url = f'{self.server_url}/{self.endpoint}'
        payload = self._parameters

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }
        
class DataverseShowCollectionContents(DataverseMetricsAPIQuery):
    """
    Get the contents of a collection (non-nesting)
    """
    def __init__(self, server, **kwargs):
        super().__init__(server)
        self._parameters = {
            'id': kwargs.get('id', None)
        }

    @property
    def endpoint(self) -> str:
        return f'api/dataverses'

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Execute API query

        Return
        ------
        dict 
            {'status_code':code, 'data':data, 'reason':reason}
            data fields:
                collections: id, title, type
                datasets: authority, datasetType, id, identifier
                persistentUrl, protocol, publicationDate, publisher
                separator, storageIdentifier, type
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')
        
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        id = self._parameters['id']
        request_url = f'{self.server_url}/{self.endpoint}/{id}/contents'

        r = requests.get(request_url, headers=headers)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }
        
class DataverseViewCollection(DataverseMetricsAPIQuery):
    """
    View a collection's metadata
    """
    def __init__(self, server, **kwargs):
        super().__init__(server)
        self._parameters = {
            'id': kwargs.get('id', None)
        }

    @property
    def endpoint(self) -> str:
        return f'api/dataverses'

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Query api

        Return
        ------
        dict: 
            {'status_code': code, 'data':{data}}
            data fields:
                affiliation, alias, creationDate, dataverseContacts, 
                dataverseType, description, effectiveRequiresFilesToPublish
                id, inputLevels, isFacetRoot, isMetadataBlockRoot
                name, ownerId, permissionRoot
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')
        
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        id = self._parameters['id']
        request_url = f'{self.server_url}/{self.endpoint}/{id}'

        r = requests.get(request_url, headers=headers)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }
    
class DataverseDatasetSearch(DataverseMetricsAPIQuery):
    """
    Retrieve dataset metadata from the Search API
    """
    def __init__(self, server, **kwargs):
        super().__init__(server)
        self._parameters = {
            'persistentId': kwargs.get('persistentId', None)
        }

    @property
    def endpoint(self) -> str:
        return f'api/search?q='

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Query api

        Return
        ------
        dict: 
            {'status_code': code, 'data':{data}}
            data fields:
                count_in_response, items
                items ->
                    authors, citation, citationHTML, contacts, createdAt
                    description, fileCount, global_id, identifier_of_dataverse
                    image_url, keywords, majorVersion, minorVersion, name
                    name_of_dataverse, publicationStatuses, publications,
                    published_at, publisher, storageIdentifier, subjects
                    type, updatedAt, url, versionId, versionState
                q, spelling_alternatives, start, total_count
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')
        
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        pid = self._parameters['persistentId']
        request_url = f'{self.server_url}/{self.endpoint}"{pid}"'

        r = requests.get(request_url, headers=headers)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }
    
class DataverseCollectionDownloadsMonthly(DataverseMetricsAPIQuery):
    """
    Retrieve cumulative monthly downloads

    Endpoint: api/info/metrics/downloads/monthly
    """
    def __init__(self, server, **kwargs):
        super().__init__(server)
        self._parameters = {
            'parentAlias': kwargs.get('parentAlias', None)
        }

    @property
    def endpoint(self) -> str:
        return f'api/info/metrics/downloads/monthly'

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Query api

        Return
        ------
        dict: 
            {'status_code': code, 'data':{data}}
            data fields:
                count, date
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')
        
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        payload = self._parameters
        request_url = f'{self.server_url}/{self.endpoint}'

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': []
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }
    
class DataverseMDCUniqueViews(DataverseMetricsAPIQuery):
    """
    Retrieve Make Data Count unique dataset views

    See: https://guides.dataverse.org/en/latest/api/native-api.html#retrieving-unique-views-for-a-dataset

    Endpoint: api/datasets/:persistentId/makeDataCount/viewsUnique?persistentId=$PERSISTENT_ID
    """
    def __init__(self, server, **kwargs):
        super().__init__(server)
        self._parameters = {
            'persistentId': kwargs.get('persistentId', None)
        }

    @property
    def endpoint(self) -> str:
        return f'api/datasets/:persistentId/makeDataCount/viewsUnique'

    @property
    def parameters(self):
        return self._parameters
    
    @parameters.setter
    def parameters(self, params : dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Query api

        Return
        ------
        dict: 
            {'status_code': code, 'data':{data}}
            data fields:
                count, date
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')
        
        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        payload = self._parameters
        request_url = f'{self.server_url}/{self.endpoint}'

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code':r.status_code,
                'reason': r.reason,
                'data': {}
            }
        
        return {
            'status_code':r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }

class DataverseDatasetsHarvestedMonthly(DataverseMetricsAPIQuery):
    """
    Retrieve Make Data Count unique dataset views

    See: https://guides.dataverse.org/en/latest/api/native-api.html#retrieving-unique-views-for-a-dataset

    Endpoint: api/info/metrics/makeDataCount/viewsUnique/?parentAlias=:parentAlias&datalocation=remote
    """

    def __init__(self, server, **kwargs):
        super().__init__(server)
        self._parameters = {
            'parentAlias': kwargs.get('parentAlias', None)
      }

    @property
    def endpoint(self) -> str:
        return f'api/info/metrics/datasets/?parentAlias=:parentAlias&dataLocation=remote'

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, params: dict):
        """
        Set API parameters

        Parameter
        ---------
        params : dict
        """
        for key in params.keys():
            if not key in self._parameters.keys():
                raise Exception(f'Invalid parameter: {key}')
            self._parameters[key] = params[key]

    def execute(self, api_token: str) -> dict:
        """
        Query api

        Return
        ------
        dict:
            {'status_code': code, 'data':{data}}
            data fields:
                count, date
        """
        if not self.validate_parameters():
            raise Exception(f'Invalid parameter value in: {self._parameters}')

        headers = {}
        headers['Accept'] = 'application/json'
        headers['X-Dataverse-key'] = api_token

        payload = self._parameters
        request_url = f'{self.server_url}/{self.endpoint}'

        r = requests.get(request_url, headers=headers, params=payload)

        if not r.status_code == requests.codes.ok:
            return {
                'status_code': r.status_code,
                'reason': r.reason,
                'data': {}
            }

        return {
            'status_code': r.status_code,
            'reason': r.reason,
            'data': r.json()['data']
        }
