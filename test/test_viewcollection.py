import os
from apiquery import DataverseViewCollection

class  TestDataverseViewCollection:

    def test_succeed(self):

        api_token = os.getenv('DATAVERSE_API_TOKEN')
        server = os.getenv('DV_SERVER')
        collection = os.getenv('DV_COLLECTION')

        if not api_token:
            raise Exception('Environment variable: "DATAVERSE_API_TOKEN" is not set')
        
        if not server: 
            raise Exception('Environment variable: "DV_SERVER" is not set')
        
        if not collection: 
            raise Exception('Environment variable: "DV_COLLECTION" is not set')

        query = DataverseViewCollection(server, id=collection)
        
        results = query.execute(api_token)

        status_code = results.get('status_code')
        data = results.get('data', [])

        result = True if data and status_code == 200 else False

        assert result == True