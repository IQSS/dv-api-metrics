from abc import ABC, abstractmethod
import polars as pl
from polars import DataFrame
import requests
import copy
import apiquery as api

class MetricsReportBaseClass(ABC):
    """
    Abstract metrics report base class

    Puplic properties
    ----------
    - name : str
    - description : strt
    - data : DataFrame

    Public Methods
    -------
    - Property setters/getters
    - generate
    - export
    """
    """
    Class properties and setter/getters
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """report name"""
        return ''

    @name.setter
    def name(self, name : str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return ''

    @property
    @abstractmethod
    def description(self) -> str:
        """report description"""
        pass

    @description.setter
    def description(self, description : str):
        """set report description"""
        pass

    @description.getter
    def description(self) -> str:
        """get report description"""
        return ''

    @property
    @abstractmethod
    def data(self) -> DataFrame:
        """report data"""

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        pass

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return DataFrame()

    """
    Class methods
    """
    @abstractmethod
    def generate(self, api_token : str) -> DataFrame:
        """generate the report"""
        return self.data

    @abstractmethod
    def export(self, file_format : str):
        """export the result"""
        pass

class DataverseMetricsReportBaseClass(MetricsReportBaseClass):
    """
    Concrete base class for Dataverse metrics reports

    Puplic properties
    ----------
    - name : str
    - description : str
    - server_url : str
    - data : DataFrame

    Private Methods
    ---------------

    Public Methods
    -------
    - Property setters/getters
    - generate
    """
    def __init__(self, server_url : str):
        self._name = ''
        self._description = ''
        self._server_url = server_url

    """
    Class properties and setters/getters
    """
    @property
    def name(self) -> str:
        """report name"""
        return self._name

    @name.setter
    def name(self, name : str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return self._name

    @property
    def description(self) -> str:
        """report description"""
        return self._description

    @description.setter
    def description(self, description : str):
        """set report description"""
        pass

    @description.getter
    def description(self) -> str:
        """get report description"""
        return ''

    @property
    def data(self) -> DataFrame:
        """report data"""
        return DataFrame()

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        self._raw_data = kwargs.get('data', None)

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return DataFrame()

    """
    Private class methods
    """
    def _get_collection_metadata(self, collection : str, api_token : str) -> dict:
        """
        Get a collection's metadata

        Return
        ------
        dict
            {'alias':collection_alias, 
            'name':collection_name, 
            'description':collection_description}
        """
        if not collection or not api_token:
            return {}

        query = api.DataverseViewCollection(self._server_url, id=collection)
        result = query.execute(api_token)

        if not result.get('status_code') == requests.codes.ok:
            return {}

        record = result['data']
        return {
            'alias':collection,
            'name':record.get('name', None),
            'description':record.get('description', None)
        }

    def _get_subcollections(self, collection : str, api_token : str) -> dict:
        """
        Get collection's subcollections

        Return
        ------
        dict (keyed on collection alias)
        """
        if not collection or not api_token:
            return {}

        subcollections = {}
        collection_tree_query = api.DataverseCollectionTreeHierarchy(self._server_url)
        collection_tree_query.parameters = {'parentAlias':collection}
        results = collection_tree_query.execute(api_token)

        if not results.get('status_code') == requests.codes.ok:
            return {}

        # there are no subcollections
        if not results['data'].get('children'):
            return {}

        kids = results['data']['children']

        # get subcollections
        for kid in kids:
            alias = kid['alias']
            subcollections[alias] = self._get_collection_metadata(alias, api_token)

        return subcollections

    def _get_collection_datasets(self, collection : str, api_token : str) -> dict:
        """
        Get collection's datasets

        Return
        ------
        dict (dataset info, keyed on dataset pid of form: "doi:authority/identifier")
        """
        if not collection or not api_token:
            return {}

        query = api.DataverseShowCollectionContents(self._server_url)
        query.parameters = {'id':collection}
        results = query.execute(api_token)

        if not results.get('status_code') == requests.codes.ok:
            return {}

        datasets = {}
        for result in results['data']:
            if result['type'] and result['type'] == 'dataset':
                result['parent_alias'] = collection
                id = 'doi:' + result['authority'] + '/' + result['identifier']
                datasets[id] = result

        return datasets

    def _get_dataset_details(self, collection : str, pid : str, api_token : str) -> dict:
        """
        Get details about a dataset
        """
        if not pid or not collection or not api_token:
            return {}

        query = api.DataverseDatasetDetails(self._server_url)
        query.parameters = {
            'persistentId':pid
        }
        result = query.execute(api_token)

        if not result.get('status_code') == requests.codes.ok:
            return {}

        data = result['data']
        fields = data['metadataBlocks']['citation']['fields']

        details = {}
        details['parent_alias'] = collection
        for field in fields:
            if field['typeName'] == 'title':
                details['title'] = field.get('value', '')
            if field['typeName'] == 'dsDescription':
                value = field['value']
                details['description'] = value[0]['dsDescriptionValue']['value']
            details['publication_date'] = data.get('publicationDate', '')
            details['version_number'] = data.get('versionNumber', 'DRAFT')
            details['minor_version_number'] = data.get('versionMinorNumber', 'DRAFT')
        details['num_files'] = len(data['files'])

        return details

    def _is_local(self, pid : str) -> bool:
        """
        Is dataset local (or harvested)

        Parameters
        ----------
        pid : str 

        Return
        ------
        bool
        """
        if not pid: 
            return False
        hdv_authority = '10.7910'
        if not hdv_authority in pid:
            return False
        return True

    def _get_monthly_counts(self, cumulative_df : DataFrame, index : list) -> DataFrame:
        """
        Given a cumulative count dataset, calculate individual monthly counts
        """
        columns = cumulative_df.columns
        months = []
        for col in columns:
            if col not in index:
                months.append(col)
        months.sort()

        # dataset subsets
        index_columns_df = cumulative_df.select(index)
        month_columns_df = cumulative_df.select(months)
        month_columns_df = month_columns_df.fill_null(0)

        # create dict of series
        # (keyed on month, e.g., 2025-07)
        month_series = {}
        for month in months:
            month_series[month] = []

        dates = month_columns_df.columns
        for row in month_columns_df.iter_rows(named=True):
            # name of prev col, e.g., 2024-07
            previous_date = None
            for date in dates:
                current_value = row[date]
                if not previous_date:
                    month_series[date].append(current_value)
                else: 
                    previous_value = row[previous_date]
                    month_series[date].append(current_value - previous_value)
                previous_date = date

        df = pl.from_dict(month_series)
        monthly_df = pl.concat([index_columns_df, df], how='horizontal')

        return monthly_df

    """
    Public class methods
    """

    def generate(self, api_token : str) -> DataFrame:
        """generate the report"""
        return DataFrame()

    def export(self, file_format : str):
        """export the result"""
        pass

class DataverseCollectionDatasetUniqueDownloadsReport(DataverseMetricsReportBaseClass):
    """
    Report for cumulative and monthly collection downloads.

    Uses the following endpoints:
    - api/info/metrics/uniquedownloads
    - api/dataverses/{$collection}/contents
    - api/datasets/:persistentId/?persistentId={$id}
    - 

    Parameters
    ----------
    server : str
        Url for server to query (e.g., https://demo.dataverse.org)
    collection : str
        Name of collection metrics to retrieve
    """
    def __init__(self, server : str, collection : str):
        self._name = 'Dataverse Cumulative and Monthy Collection Unique Downloads Report'
        self._description = 'TBD'
        self._server_url = server

        # parameters
        self.collection = collection

        # datasets
        self._raw_data = DataFrame()
        self._cumulative_df = DataFrame()
        self._monthly_df = DataFrame()

    @property
    def name(self) -> str:
        """report name"""
        return self._name

    @name.setter
    def name(self, name : str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return self._name

    @property
    def description(self) -> str:
        """report description"""
        return self._description

    @description.setter
    def description(self, description : str):
        """set report description"""
        pass

    @description.getter
    def description(self):
        """get report description"""
        return self._description

    @property
    def data(self) -> DataFrame:
        """report data"""
        return self._raw_data

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        pass

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return self._raw_data

    @property
    def cumulative_metrics(self):
        """get cumulative metrics"""
        return self._cumulative_df

    @property
    def monthly_metrics(self):
        """get monthly metrics"""
        return self._monthly_df

    def _get_downloads(self, api_token : str) -> dict:
        query = api.DataverseUniqueDownloadsMonthly(self._server_url)
        query.parameters = {'parentAlias':self.collection}
        metrics = query.execute(api_token)
        return metrics

    def _remove_harvested_datasets(self, datasets : dict) -> dict:
        """
        Remove any harvested datasets from an input dictionary
        """
        if not datasets:
            return {}

        local_datasets = copy.deepcopy(datasets)
        for dataset in datasets:
            if not self._is_local(dataset):
                del local_datasets[dataset]
        return local_datasets

    def _process_results(self, collections : dict, datasets : dict, downloads : list) -> list:
        """
        Combine each dataset's collection, details, and download information
        """
        if not collections or not datasets or not downloads:
            return []

        results = []
        for dataset in downloads:
            pid = dataset['pid']
            if datasets.get(pid):
                dataset_details = datasets[pid]
                title = dataset_details['title']
                description = dataset_details['description']
                pub_date = dataset_details['publication_date']
                version = dataset_details['version_number']
                minor_version_number = dataset_details['minor_version_number']
                num_files = dataset_details['num_files']
                alias = dataset_details['parent_alias']
                collection_details = collections[alias]
                collection_name = collection_details['name']
                collection_description = collection_details['description']
                result = dataset | {'title':title,
                                    'description':description,
                                    'collection_name':collection_name, 
                                    'parent_alias':alias,
                                    'publication_date':pub_date,
                                    'version_number':version,
                                    'minor_version_number':minor_version_number,
                                    'num_files':num_files,
                                    'collection_description':collection_description}
                results.append(result)
        return results

    def generate(self, api_token : str) -> DataFrame:
        """generate the report"""
        # dict of current collection & subcollections metadata
        all_collections = {}

        # get top-level collection metadata
        # this collection may contain datasets as well as subcollections
        all_collections[self.collection] = self._get_collection_metadata(self.collection, api_token)

        # get top-level collection's subcollections
        subcollections = self._get_subcollections(self.collection, api_token)

        # add subcollections to all collections
        all_collections = all_collections | subcollections

        # get datasets for all collections
        all_collection_datasets = {}
        for collection in all_collections.keys():
            alias = all_collections[collection]['alias']
            datasets = self._get_collection_datasets(alias, api_token)
            all_collection_datasets = all_collection_datasets | datasets

        # remove harvested datasets
        all_collection_datasets = self._remove_harvested_datasets(all_collection_datasets)

        # get all dataset details
        all_datasets_details = {}
        for dataset in all_collection_datasets:
            alias = all_collection_datasets[dataset]['parent_alias']
            all_datasets_details[dataset] = self._get_dataset_details(alias, dataset, api_token)


        # get cumulative unique downloads
        results = self._get_downloads(api_token)
        downloads = results.get('data', [])

        # process results to create one table
        processed_datasets = self._process_results(all_collections, all_datasets_details, downloads)

        # handle empty results
        if not processed_datasets:
            return self._raw_data

        # create dataframe from processed results
        df = pl.from_dicts(processed_datasets)
        df = df.fill_null(0)
        self._raw_data = df.clone() # cache raw data

        # calculate cumulative and monthly reports
        index = ['pid','title', 
                     'description','parent_alias',
                     'publication_date', 'version_number',
                     'minor_version_number','num_files',
                    'collection_description']
        pivot_table = df.pivot('date', index=index, values='count')
        pivot_table = pivot_table.fill_null(0)
        self._cumulative_df = pivot_table

        # calculate monthlies
        monthly_df = self._get_monthly_counts(pivot_table, index)
        monthly_df = monthly_df.fill_null(0) # set months with None values to 0
        self._monthly_df = monthly_df

        # return the raw data
        return self._raw_data

    def export(self, file_format : str):
        """export the result"""
        pass

class DataverseCollectionMonthlyDownloadsReport(DataverseMetricsReportBaseClass):
    """
    Report for cumulative and monthly collection downloads

    Enpoints:
    - api/info/metrics/downloads/monthly
    - TBD

    Parameters
    ----------
    server : str
        Url for server to query (e.g., https://demo.dataverse.org)
    collection : str
        Name of collection metrics to retrieve
    """
    def __init__(self, server : str, collection : str):
        self._name = 'Dataverse Cumulative and Monthly Collection Downloads Report'
        self._description = 'TBD'
        self._server_url = server

        # parameters
        self.collection = collection

        # datasets
        self._raw_data = DataFrame()
        self._cumulative_df = DataFrame()
        self._monthly_df = DataFrame()

    @property
    def name(self) -> str:
        """report name"""
        return self._name

    @name.setter
    def name(self, name : str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return self._name

    @property
    def description(self) -> str:
        """report description"""
        return self._description

    @description.setter
    def description(self, description : str):
        """set report description"""
        pass

    @description.getter
    def description(self):
        """get report description"""
        return self._description

    @property
    def data(self) -> DataFrame:
        """report data"""
        return self._raw_data

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        pass

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return self._raw_data

    @property
    def cumulative_metrics(self):
        """get cumulative metrics"""
        return self._cumulative_df

    @property
    def monthly_metrics(self):
        """get monthly metrics"""
        return self._monthly_df

    def _get_collection_downloads(self, collection : str, api_token : str) -> list:
        """
        Get monthly collection downloads
        """
        downloads = []
        query = api.DataverseCollectionDownloadsMonthly(self._server_url, parentAlias=collection)
        result = query.execute(api_token)
        if not result['status_code'] == requests.codes.ok:
            return []
        for entry in result['data']:
            downloads.append({'count':entry['count'],
                              'date':entry['date'],
                              'collection':collection})
        return downloads

    def generate(self, api_token : str) -> DataFrame:
        """generate the report"""

        # dict of current collection & subcollections metadata
        all_collections = {}

        # get top-level collection metadata
        # this collection may contain datasets as well as subcollections
        all_collections[self.collection] = self._get_collection_metadata(self.collection, api_token)

        # get top-level collection's subcollections
        subcollections = self._get_subcollections(self.collection, api_token)

        # add subcollections to all collections
        all_collections = all_collections | subcollections

        downloads = []
        for collection in all_collections.keys():
            counts = self._get_collection_downloads(collection, api_token)
            downloads = downloads + counts

        if not downloads:
            return self._raw_data 

        all_collection_downloads = []
        for download in downloads:
            alias = download['collection']
            coll_info = all_collections[alias]
            coll_info = coll_info | download
            all_collection_downloads.append(coll_info)

        # create dataframe from downloads
        df = pl.from_dicts(all_collection_downloads)
        df = df.fill_null(0)
        self._raw_data = df.clone() # cache raw data

        # calculate cumulative and monthly reports
        index = ['alias',
                 'name', 
                 'description']
        pivot_table = df.pivot('date', index=index, values='count')
        pivot_table = pivot_table.fill_null(0)
        self._cumulative_df = pivot_table

        # calculate monthlies
        monthly_df = self._get_monthly_counts(pivot_table, index)
        monthly_df = monthly_df.fill_null(0) # set months with None values to 0
        self._monthly_df = monthly_df

        # return the raw data
        return self._raw_data

    def export(self, file_format : str):
        """export the result"""
        pass


class DataverseCollectionMonthlyDatasetsReport(DataverseMetricsReportBaseClass):
    """
    Report for cumulative and monthly collection downloads

    Enpoints:
    - api/info/metrics/datasets/monthly
    - TBD

    Parameters
    ----------
    server : str
        Url for server to query (e.g., https://demo.dataverse.org)
    collection : str
        Name of collection metrics to retrieve
    """

    def __init__(self, server: str, collection: str):
        self._name = 'Dataverse Cumulative and Monthly Collection Datasets Report'
        self._description = 'TBD'
        self._server_url = server

        # parameters
        self.collection = collection

        # datasets
        self._raw_data = DataFrame()
        self._cumulative_df = DataFrame()
        self._monthly_df = DataFrame()

    @property
    def name(self) -> str:
        """report name"""
        return self._name

    @name.setter
    def name(self, name: str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return self._name

    @property
    def description(self) -> str:
        """report description"""
        return self._description

    @description.setter
    def description(self, description: str):
        """set report description"""
        pass

    @description.getter
    def description(self):
        """get report description"""
        return self._description

    @property
    def data(self) -> DataFrame:
        """report data"""
        return self._raw_data

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        pass

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return self._raw_data

    @property
    def cumulative_metrics(self):
        """get cumulative metrics"""
        return self._cumulative_df

    @property
    def monthly_metrics(self):
        """get monthly metrics"""
        return self._monthly_df

    def _get_collection_datasets(self, collection: str, api_token: str) -> list:
        """
        Get monthly collection datasets
        """
        datasets = []
        query = api.DataverseDatasetsMonthly(self._server_url, parentAlias=collection)
        result = query.execute(api_token)
        if not result['status_code'] == requests.codes.ok:
            return []
        for entry in result['data']:
            datasets.append({'count': entry['count'],
                              'date': entry['date'],
                              'collection': collection})
        return datasets

    def generate(self, api_token: str) -> DataFrame:
        """generate the report"""

        # dict of current collection & subcollections metadata
        all_collections = {}

        # get top-level collection metadata
        # this collection may contain datasets as well as subcollections
        all_collections[self.collection] = self._get_collection_metadata(self.collection, api_token)

        # get top-level collection's subcollections
        subcollections = self._get_subcollections(self.collection, api_token)

        # add subcollections to all collections
        all_collections = all_collections | subcollections

        datasets = []
        for collection in all_collections.keys():
            counts = self._get_collection_datasets(collection, api_token)
            datasets = datasets + counts

        if not datasets:
            return self._raw_data

        all_collection_datasets = []
        for dataset in datasets:
            alias = dataset['collection']
            coll_info = all_collections[alias]
            coll_info = coll_info | dataset
            all_collection_datasets.append(coll_info)

        # create dataframe from downloads
        df = pl.from_dicts(all_collection_datasets)
        df = df.fill_null(0)
        self._raw_data = df.clone()  # cache raw data

        # calculate cumulative and monthly reports
        index = ['alias',
                 'name',
                 'description']
        pivot_table = df.pivot('date', index=index, values='count')
        pivot_table = pivot_table.fill_null(0)
        self._cumulative_df = pivot_table

        # calculate monthlies
        monthly_df = self._get_monthly_counts(pivot_table, index)
        monthly_df = monthly_df.fill_null(0)  # set months with None values to 0
        self._monthly_df = monthly_df

        # return the raw data
        return self._raw_data

    def export(self, file_format: str):
        """export the result"""
        pass


class DataverseCollectionDatasetInventoryReport(DataverseMetricsReportBaseClass):
    """
    Report producing an inventory of all datasets for a collection
    and its subcollections

    Endpoints
    ---------
    -

    Parameters
    ----------
    server : str
        Url for server to query (e.g., https://demo.dataverse.org)
    collection : str
        Name of collection metrics to retrieve
    """
    def __init__(self, server : str, collection : str):
        self._name = 'Dataverse Collection Dataset Inventory Report'
        self._description = 'TBD'
        self._server_url = server

        # parameters
        self.collection = collection

        # datasets
        self._raw_data = DataFrame()

    @property
    def name(self) -> str:
        """report name"""
        return self._name

    @name.setter
    def name(self, name : str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return self._name

    @property
    def description(self) -> str:
        """report description"""
        return self._description

    @description.setter
    def description(self, description : str):
        """set report description"""
        pass

    @description.getter
    def description(self):
        """get report description"""
        return self._description

    @property
    def data(self) -> DataFrame:
        """report data"""
        return self._raw_data

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        pass

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return self._raw_data

    def generate(self, api_token : str) -> DataFrame:
        """generate the report"""

        # dict of current collection & subcollections metadata
        all_collections = {}

        # get top-level collection metadata
        # this collection may contain datasets as well as subcollections
        metadata = self._get_collection_metadata(self.collection, api_token)
        all_collections[self.collection] = metadata

        # get top-level collection's subcollections
        subcollections = self._get_subcollections(self.collection, api_token)

        # add subcollections to all collections
        all_collections = all_collections | subcollections

        # get datasets for all collections
        all_collection_datasets = {}

        for collection in all_collections.keys():
            if all_collections[collection]:
                alias = all_collections[collection]['alias']
                datasets = self._get_collection_datasets(alias, api_token)
                all_collection_datasets = all_collection_datasets | datasets

        # get all dataset details
        for dataset in all_collection_datasets.keys():
            if dataset:
                alias = all_collection_datasets[dataset]['parent_alias']
                details = self._get_dataset_details(alias, dataset, api_token)
                all_collection_datasets[dataset].update(details)

        # if no datasets were collected
        if not all_collection_datasets:
            return DataFrame()

        # create dataframe from downloads
        df = pl.from_dicts(list(all_collection_datasets.values()), 
                           schema_overrides={'version_number':pl.String,
                                             'minor_version_number':pl.String})
        df = df.fill_null(0)
        self._raw_data = df.clone() # cache raw data

        # return the raw data
        return self._raw_data

    def export(self, file_format : str):
        """export the result"""
        pass

class DataverseCollectionHarvestDatasetViewsUniqueReport(DataverseMetricsReportBaseClass):
    """
    Report for cumulative and monthly collection downloads.

    Uses the following endpoints:
    - api/info/metrics/uniquedownloads
    - api/dataverses/{$collection}/contents
    - api/datasets/:persistentId/?persistentId={$id}
    -

    Parameters
    ----------
    server : str
        Url for server to query (e.g., https://demo.dataverse.org)
    collection : str
        Name of collection metrics to retrieve
    """

    def __init__(self, server: str, collection: str):
        self._name = 'Dataverse Cumulative and Monthy Collection Unique Downloads Report'
        self._description = 'TBD'
        self._server_url = server

        # parameters
        self.collection = collection

        # datasets
        self._raw_data = DataFrame()

    @property
    def name(self) -> str:
        """report name"""
        return self._name

    @name.setter
    def name(self, name: str):
        """set report name"""
        pass

    @name.getter
    def name(self):
        """get report name"""
        return self._name

    @property
    def description(self) -> str:
        """report description"""
        return self._description

    @description.setter
    def description(self, description: str):
        """set report description"""
        pass

    @description.getter
    def description(self):
        """get report description"""
        return self._description

    @property
    def data(self) -> DataFrame:
        """report data"""
        return self._raw_data

    @data.setter
    def data(self, **kwargs):
        """set report data"""
        pass

    @data.getter
    def data(self) -> DataFrame:
        """get report data"""
        return self._raw_data

    def _remove_local_datasets(self, datasets: dict) -> dict:
        """
        Remove any harvested datasets from an input dictionary
        """
        if not datasets:
            return {}

        harvested_datasets = copy.deepcopy(datasets)
        for dataset in datasets:
            if self._is_local(dataset):
                del harvested_datasets[dataset]
        return harvested_datasets

    def _process_results(self,  views: dict) -> list:
        """
        Combine each dataset's collection, details, and download information
        """
        if not views:
            return []

        results = []
        for pid, dataset_details in views.items():
            views_unique = dataset_details.get('viewsUnique', 0)
            result = {'persistentId': pid,
                                'unique_views': views_unique}
            results.append(result)
        return results

    def generate(self, api_token: str) -> DataFrame:
        """generate the report"""
        # dict of current collection & subcollections metadata
        all_collections = {}

        # get top-level collection metadata
        # this collection may contain datasets as well as subcollections
        all_collections[self.collection] = self._get_collection_metadata(self.collection, api_token)

        # get top-level collection's subcollections
        subcollections = self._get_subcollections(self.collection, api_token)

        # add subcollections to all collections
        all_collections = all_collections | subcollections

        # get datasets for all collections
        all_collection_datasets = {}
        for collection in all_collections.keys():
            alias = all_collections[collection]['alias']
            datasets = self._get_collection_datasets(alias, api_token)
            all_collection_datasets = all_collection_datasets | datasets

        # remove local datasets, leaving only harvested datasets
        all_collection_datasets = self._remove_local_datasets(all_collection_datasets)

        all_views = {}
        views = []
        for dataset in all_collection_datasets:
            unique_views = api.DataverseMDCUniqueViews(self._server_url, persistentId=dataset)
            result = unique_views.execute(api_token)
            all_views[dataset] = result['data']
            views.append(result['data'])

        # process results to create one table
        processed_datasets = self._process_results(all_views)

        # handle empty results
        if not processed_datasets:
            return self._raw_data

        # create dataframe from processed results
        df = pl.from_dicts(processed_datasets)
        df = df.fill_null(0)
        self._raw_data = df.clone()  # cache raw data


        # return the raw data
        return self._raw_data
