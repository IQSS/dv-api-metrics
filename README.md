# cafe-metrics
Python code to collect metrics from datasets in CAFE collections

## Objectives
- Track collection change over time. Collection change could include tracking unique depositors and datasets created. 
- Track dataset engagement over time. Dataset engagement could include tracking dataset and file download counts, as well as dataset citations (where possible). 

## Desired Metrics
- Number of datasets created per month
- Number of collections per month
- Number of dataset downloads per month
- Dataset keyword frequency per month
- Number of (unique) depositors per month
- Number of file downloads per month per dataset

## Additional Metrics
- Number of harvested dataset engagements (Note: not available via APIs)

## Desired Formats
Open questions:
- Are reports preferred to raw data outputs?
    - Raw data (e.g., outputs from API queries)
    - Reports (e.g., summaries of API query output)
## Technical Limitations
- Metrics will be collected using existing Dataverse Metrics API endpoints or Native API endpoints.