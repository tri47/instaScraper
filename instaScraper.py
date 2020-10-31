import json, re, requests
import datetime
import time
import pandas as pd

'''
Code adapted from https://kaijento.github.io/2017/05/17/web-scraping-instagram.com/
with modifications to handle changes in Instagram request parameters. Specifically
the use of query hash, and to scrape specific post information: likes, date, captions, URL etc. 
'''
# Set three required identifiers for the scrapers, 
# see README for instructions to find these values
# Override the value if not using a params json file. i.e.

# UN-COMMENT:
# user = "instagram"
# user_id = "25025320"
# query_hash = "56a7068fea504063273cc2120ffd54f3"
# Instead of the "with" clause below

with open('params.JSON') as json_file:
    params = json.load(json_file)
    user = params['user']
    user_id = params['user_id']
    query_hash = params['query_hash']

MAX_PAGES = 3 # Number of extra infinite scroll loads to scrape (11 posts/page)

print("Scraping post info for user ", user_id)

captions, post_links, image_links, likes, post_dates =[], [], [], [], []
has_next_page = True

with requests.session() as s:
    s.headers['user-agent'] = 'Mozilla/5.0'
    end_cursor = '' 
    count = 0

    # Use has_bext_page while loop to scrape all posts
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
        df = pd.DataFrame(data_tuples)
df.to_csv(user + '_captions.csv')
print('Top entries')
print(df.head())
   