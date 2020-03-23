'''
Instagram scraper to extract post information
Contain functions to be deployed to AWS Lambda service.
Contain methods to connect to S3 Bucket to store and retrieve summary report
'''
import json, re, requests
import datetime
import time
from io import StringIO
import pandas as pd
import boto3


import os

from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


USER = 'ID'
USER_ID = 'ID'
QUERY_HASH = 'ID'
SENDER = "gmail.com"
RECIPIENT = "gmail.com"
AWS_REGION = "ap-southeast-2"


client = boto3.client(
    'ses',
    region_name=AWS_REGION,
)

def save_file_to_s3(bucket, file_name, data):
    csv_buffer = StringIO()
    s3 = boto3.resource('s3')
    data.to_csv(csv_buffer)
    obj = s3.Object(bucket, file_name)
    obj.put(Body=csv_buffer.getvalue())

def scrape_instagram():
    user = USER
    user_id = USER_ID
    query_hash = QUERY_HASH

    MAX_PAGES = 1 # Number of extra infinite scroll loads to scrape (11 posts/page)
    print("Scraping post info for user ", user)

    captions, post_links, image_links, likes, post_dates =[], [], [], [], []
    has_next_page = True
    with requests.session() as s:
        s.headers['user-agent'] = 'Mozilla/5.0'
        end_cursor = '' 
        count = 0

        # Use has_next_page while loop to scrape all posts
        while count < MAX_PAGES: 
        #while has_next_page: #for count in range(1, 4):
            print('PAGE: ', count)
            if count == 1: # The profile page
                profile = 'https://www.instagram.com/' + user
            else: # subsequent infinite scroll requests
                profile = 'https://www.instagram.com/graphql/query/?query_hash=' + query_hash +'&variables={"id":"' + user_id + '","first":12,"after":"' +  end_cursor + '"}'
            r = s.get(profile)
            time.sleep(2)

            if count == 1: # Profile page
                data = re.search(
                    r'window._sharedData = (\{.+?});</script>', r.text).group(1)
                data = json.loads(data)
                data_point = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']
            else: # subsequent infinite scroll requests
                data = json.loads(r.text)['data']
                data_point = data['user']['edge_owner_to_timeline_media']

            # Extract data and find the end cursor for the current page
            end_cursor = data_point['page_info']['end_cursor']
            has_next_page = data_point['page_info']['has_next_page']
            for link in data_point['edges']:
                post_link = 'https://www.instagram.com'+'/p/'+link['node']['shortcode']+'/'
                caption = link['node']['edge_media_to_caption']['edges'][0]['node']['text']
                like = link['node']['edge_media_preview_like']['count']
                post_time = link['node']['taken_at_timestamp']
                image_link = link['node']['display_url']
                post_time = datetime.datetime.fromtimestamp(post_time).strftime('%Y-%m-%d %a %H:%M')
                captions.append(caption)
                likes.append(like)
                post_dates.append(post_time)
                image_links.append(image_link)
                post_links.append(post_link)
            count += 1
                
            captions.pop()
            likes.pop()
            post_dates.pop()
            image_links.pop()
            post_links.pop()

            data_tuples = list(zip(captions, likes, post_dates, post_links ) )
            df = pd.DataFrame(data_tuples, columns = ['caption', 'likes', 'date','link' ] )
    saved_data = df.to_csv(index=False)
    print('Top entries')
    print(df.head())
    return df

def handle(event, context):
    data = scrape_instagram()
    df = data
    file_name = "instaposts.csv"
    # save newest version to s3 bucket
    save_file_to_s3('instareports', file_name, data)

    # Set up html body of the email to contain a table of the report
    htmlBody = """
        <!DOCTYPE html>
        <html>
        <body>
            <p>Hi, your lastest post report ,</p>
        <table border="1px solid black">
          <tr>
            <th>Caption</th>
            <th>Likes</th>
            <th>Date</th>
          </tr>
        """
    for i in range(0, df.shape[0]): 
            new_row = """
            <tr>
                <td> {} </td>
                <td> {} </td>
                <td> {} </td>
            </tr>
            """.format(df.loc[i,'caption'], df.loc[i,'likes'], df.loc[i,'date'] )

            htmlBody += new_row
    
    end_html = "</table> </body>  </html>"
    htmlBody += end_html
    SUBJECT = "Latest Instagram posts summary"
    BODY_TEXT = ""
    BODY_HTML = htmlBody
    # The character encoding for the email.
    CHARSET = "utf-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    msg['Subject'] = SUBJECT 
    msg['From'] = SENDER 
    msg['To'] = RECIPIENT
    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')
    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    s3 = boto3.resource('s3')
    obj = s3.Object('instareports', "instaposts.csv")
    obj = obj.get()['Body'].read().decode('utf-8') 
    att = MIMEApplication(obj)
    att.add_header('Content-Disposition','attachment',filename="instaposts.csv")
    msg.attach(msg_body)
    # Add the attachment to the parent container.
    msg.attach(att)
    try:
        #Provide the contents of the email.
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=[
                RECIPIENT
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
          # ConfigurationSetName=CONFIGURATION_SET
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

if __name__ == '__main__':
    print('running')
    handle('dummy','dummy')

   