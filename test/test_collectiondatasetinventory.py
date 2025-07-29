import os
from report import DataverseCollectionDatasetInventoryReport

class  TestInventoryReport:

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
        
        report = DataverseCollectionDatasetInventoryReport(server, collection)
        df = report.generate(api_token)

        assert len(df) > 1 == True