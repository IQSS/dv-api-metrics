import os
from apiquery import DataverseDatasetSearch

class  TestSearchDataset:

    def test_succeed(self):

        api_token = os.getenv('DATAVERSE_API_TOKEN')
        server = os.getenv('DV_SERVER')
        dataset_id = os.getenv('DV_DATASET_ID') # e.g, doi:10.7910/DVN/9STGWE

        if not api_token:
            raise Exception('Environment variable: "DATAVERSE_API_TOKEN" is not set')
        
        if not server: 
            raise Exception('Environment variable: "DV_SERVER" is not set')
        
        if not dataset_id: 
            raise Exception('Environment variable: "DV_DATASET_ID" is not set')

        query = DataverseDatasetSearch(server, persistentId=dataset_id)
        
        results = query.execute(api_token)

        status_code = results.get('status_code')
        data = results.get('data', {})

        result = True if data and status_code == 200 else False

        assert result == True