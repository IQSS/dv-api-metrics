import sys
import argparse
import logging
import os
from datetime import datetime
from enum import StrEnum
import report as rp

class DVInstallation(StrEnum):
    HDV = 'hdv' # https://dataverse.harvard.edu
    DEMO = 'demo' # https://demo.dataverse.org

def main():
    """
    Get a collection's harvested dataset unique views. Includes its subcollections.

    Usage
    -----
    % python get_collection_harvest_dataset_views.py <collection> --installation <server>\
       --filename <filename>  --verbose
    """
    parser = argparse.ArgumentParser(
                    prog='get_collection_dataset_harvested_')
    parser.add_argument('collection', help='Name of collection, e.g., root, cafe')
    parser.add_argument('--installation', choices=['hdv','demo'], help='Dataverse installation to use, either hdv (default) or demo')
    parser.add_argument('--filename', help='Name of output file, otherwise default is chosen.')
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose logging output',
                        action='store_true')
    
    args = parser.parse_args()
    
    collection = args.collection
    if not collection:
        raise Exception('Collection name must be provided')
    
    installation = args.installation

    server_url = 'https://dataverse.harvard.edu'
    
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

    filename = args.filename
    if not filename:
        # set default filename
        tod = datetime.now()
        timestamp = tod.strftime('%Y_%m_%d_%H_%M')
        filename = f'harvested_datasets_unique_views_{timestamp}.tsv'
        logging.info(f'Using default output file: {filename}')       
       
    api_token = os.getenv('DATAVERSE_API_TOKEN')
    if not api_token:
        raise Exception('Environment variable: "DATAVERSE_API_TOKEN" is not set')

    report = rp.DataverseCollectionHarvestDatasetViewsUniqueReport(server_url, collection)
    df = report.generate(api_token)

    df.write_csv(filename, separator='\t')

    logging.info(f'Wrote dataset inventory to: {filename}')

if __name__ == "__main__":
    main()




