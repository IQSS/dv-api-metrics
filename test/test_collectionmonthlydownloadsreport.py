import os
from report import DataverseCollectionMonthlyDownloadsReport

class  TestMonthlyDownloadsReport:

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
        
        report = DataverseCollectionMonthlyDownloadsReport(server, collection)
        df = report.generate(api_token)

        raw_len = len(df)
        cumulative_len = len(report._cumulative_df)
        monthly_len = len(report._monthly_df)

        result = True if raw_len > 0 and cumulative_len > 0 and monthly_len > 0 else False
        assert result == True