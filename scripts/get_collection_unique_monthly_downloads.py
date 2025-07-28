import sys
import argparse
import logging
import os
from datetime import datetime
from enum import StrEnum
from report import DataverseCollectionDatasetUniqueDownloadsReport

class MetricsStrategy(StrEnum):
    DVM = 'dvm' # dataverse native metrics
    MDC = 'mdc' # make data count metrics

class FileOutputType(StrEnum):
    RECORDS = 'records' # one entry per metric
    TIME_SERIES = 'time_series' # one entry per dataset per month
    CUMULATIVE_TIME_SERIES = 'cumulative_time_series' # one entry per dataset per month, cumulatives
    ALL = 'all' # all three sets of metrics

class DVInstallation(StrEnum):
    HDV = 'hdv' # https://dataverse.harvard.edu
    DEMO = 'demo' # https://demo.dataverse.org

DEFAULT_FILE_STEM = 'dvmetrics'

def main():
    """
    Get monthly unique dataset download metrics for a named collection.
    Saves metrics to a tab-delimited file.

    When metrics=dvm, this Dataverse native API endpoint is used: 
        'api/info/metrics/uniquedownloads/monthly'

    Usage
    -----
    % python get_collection_metrics.py <installation> <collection> \
        --metrics [dvm | mdc] --filename <filename> --output [records|time_series] --verbose
    """
    parser = argparse.ArgumentParser(
                    prog='get_collection_unique_monthly_downloads')
    parser.add_argument('collection', help='Name of collection, e.g., root, cafe')
    parser.add_argument('--installation', choices=['hdv','demo'], help='Dataverse installation to use, either hdv (default) or demo')
    parser.add_argument('--metrics', choices=['dvm','mdc'], help='Type of metrics to collect. \
                        Either Dataverse metrics (default, dvm), or Make Data Count (mdc).')
    parser.add_argument('--filestem', help='Output file (e.g., my_file_stem -> my_file_stem_<metric>.tsv), otherwise default is chosen.')
    parser.add_argument('--output', choices=['records','time_series', 'cumulative_timeseries', 'all'], help='Type of data written to file. \
                        Either one record per metric (records), one record per dataset per month (time_series),\
                        cumulative monthly metrics, or all metrics')
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose logging output',
                        action='store_true')
    
    args = parser.parse_args()
    
    collection = args.collection
    if not collection:
        raise Exception('Collection name must be provided')
    
    installation = args.installation
    server_url = ''
    if not installation:
        server_url = 'https://dataverse.harvard.edu'
    elif installation == DVInstallation.HDV:
        server_url = 'https://dataverse.harvard.edu'
    else:
        server_url = 'https://demo.dataverse.org'
    
    verbose = args.verbose
    if verbose:
        logging.basicConfig(stream = sys.stdout,level = logging.DEBUG)
    else:
        logging.basicConfig(stream = sys.stdout,level = logging.ERROR)
    
    metrics = args.metrics
    if not metrics:
        # default to Dataverse api strategy
        metrics = MetricsStrategy.DVM
        logging.info(f'Using default metrics strategy: {metrics}')
    elif metrics == MetricsStrategy.MDC:
        raise Exception('Make Data Count metrics are not yet implemented.')

    output = args.output
    if not output:
        output = FileOutputType.ALL # set default output type
        logging.info(f'Using default file output type: {output}')

    filestem = args.filestem
    if not filestem:
        filestem = DEFAULT_FILE_STEM
        logging.info(f'Using default output filestem: {filestem}')

    api_token = os.getenv('DATAVERSE_API_TOKEN')
    if not api_token:
        raise Exception('Environment variable: "DATAVERSE_API_TOKEN" is not set')

    server = 'https://dataverse.harvard.edu'

    # create the report
    report = DataverseCollectionDatasetUniqueDownloadsReport(server, collection)
    df = report.generate(api_token)

    # check for presence of results
    if df.is_empty():
        logging.warning(f'Collection: {collection} has no local datasets. No dataset download metrics were collected.')        
        raise Exception('No dataset download metrics were collected.')
    
    # write selected report to file
    tod = datetime.now()
    timestamp = tod.strftime('%Y_%m_%d_%H_%M')

    output_df = None
    if output == FileOutputType.RECORDS:
        # write raw record data
        output_df = report.data
        records = f'{filestem}_{output}_{timestamp}.tsv'
        output_df.write_csv(records, separator='\t')
        logging.info(f'Wrote {output} metrics to: {records}.')
    elif output == FileOutputType.TIME_SERIES:
        # write metrics monthly time series
        output_df = report.monthly_metrics
        monthly = f'{filestem}_{output}_{timestamp}.tsv'
        output_df.write_csv(monthly, separator='\t')
        logging.info(f'Wrote {output} metrics to: {monthly}.')
    elif output == FileOutputType.CUMULATIVE_TIME_SERIES:
        
        output_df = report.cumulative_metrics
        cumulative = f'{filestem}_{output}_{timestamp}.tsv'
        output_df.write_csv(cumulative, separator='\t')
        logging.info(f'Wrote {output} metrics to: {cumulative}.')
    elif output == FileOutputType.ALL:
        tod = datetime.now()
        timestamp = tod.strftime('%Y_%m_%d_%H_%M')

        records_df = report.data
        records = f'{filestem}_records_{timestamp}.tsv'
        records_df.write_csv(records, separator='\t')

        monthly_df = report.monthly_metrics
        monthly = f'{filestem}_monthly_{timestamp}.tsv'
        monthly_df.write_csv(monthly, separator='\t')

        cumulative_df = report.cumulative_metrics
        cumulative = f'{filestem}_cumulative_{timestamp}.tsv'
        cumulative_df.write_csv(cumulative, separator='\t')

        logging.info(f'Wrote all metrics to: {filestem}_records_<output_type>_{timestamp}.tsv')

if __name__ == "__main__":
    main()




