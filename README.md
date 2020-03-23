FILE: instaScraper.py..
Scraper to extract post information from an Instagram public page and output a CSV.  
Works as of March, 2020. The code deals with infinite scrolls using the new query_hash recently inplemented by Instagram. 

No authentification required. Use with caution, respect others' IP...

Sample params.json file:  

{
    "user": "yourpage",  
    "user_id": "uniqueid",  
    "query_hash": "ADD QUERY HASH HERE"  
}  

Instructions on how to obtain query_id and user_id for an instagram account:  
TO BE ADDED


FILE: lambdaHandler.py  
Serverless AWS Lambda version of the scraper. Requires an S3 bucket to store and retrieve report.  
DETAILS TO BE ADDED  

