*Working as of November 2020*

**instaScraper.py**

Scraper to extract post information from an Instagram public page and output a CSV.  
Works as of November, 2020. The code deals with infinite scrolls using the new query_hash recently inplemented by Instagram. 
No authentification required. 

Please use with caution, respect people's intellectual properties etc.

**params.JSON**

Replace the values with the details of your target page. Follow the instructions to get the query_id and user_id in the blog post below. 
https://www.scatta.cc/2020/03/05/scraping-a-instagram-profile.html

Sample params.json file:  

    {
        "user": "yourpage",  
        "user_id": "uniqueid",  
        "query_hash": "ADD QUERY HASH HERE"}  


**lambdaHandler.py**

Serverless AWS Lambda version of the scraper. Requires an S3 bucket to store and retrieve report.

You don't need this if you only want to scrape to a flat file.

