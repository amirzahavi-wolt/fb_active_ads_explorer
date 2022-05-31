import streamlit as st
import pandas as pd
import requests
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adcreative import AdCreative
import datetime as dt

page_icon_address = 'https://icons-for-free.com/download-icon-assistant-131964752347025887_512.png'
st.set_page_config(page_title='Active FB Ads Assistant', layout = 'wide', page_icon=page_icon_address)

# Time window definitions definitions
tomorrow = (dt.datetime.today() + dt.timedelta(days=1)).strftime('%Y-%m-%d')
today = dt.datetime.today().strftime('%Y-%m-%d')

# Filters:
min_ad_spend = 0
campaign_name_contains = 'ISR_'
since = today
until = tomorrow
pagination_limit = 100


st.title('Active ads')
st.text("")
st.write('''This service retrieves the current active ads from the selected FB account. \nOnly ads that meet these conditions will be shown: \n1. Currently active \n2. Spent money in the defined timeframe
    \nChoose the relevant country, edit the timeframe (or keep the default) and click the "Get Ads!" button. \n Cheers!''')


selected_account = st.sidebar.radio(
     "Choose the FB account you want to get data for",
     ('Courier', 'W@W', 'Merchant','Retargeting','Recruitment','Brand','Smartly','UA'))

country_input = st.text_input("Country 3-digit code", 'ISR')
since_input = st.text_input("Since date YYYY-MM-DD", since)
until_input = st.text_input("Until date YYYY-MM-DD", until)



if st.button('Get Ads!'):
    # Authentication:
    fb_version = "v13.0"
    access_token = st.secrets["token"]
    FacebookAdsApi.init(access_token=access_token)

    # Preview params:
    scale_multiplier = 3

    # Selected account id: 
    selected_act_id = st.secrets[selected_account]

    URL = "https://graph.facebook.com/" + str(fb_version)+ "/act_"+ str(selected_act_id)+"/ads"

    PARAMS = {'fields':"campaign{name},name,effective_status,adcreatives{thumbnail_url}",
            "time_range":"{'since': '"+str(since_input)+"' ,'until': '"+str(until_input)+"'}",
            "level":"campaign",
            "limit": str(pagination_limit),
            "filtering":'[{field:"ad.spend",operator:"GREATER_THAN",value:'+str(min_ad_spend)+'},{field:"campaign.name",operator:"CONTAIN",value:"'+str(country_input+'_')+'"},{field:"effective_status",operator:"IN",value:["ACTIVE"]}]',
            "access_token":access_token
            }
    r = requests.get(url = URL, params = PARAMS)
    data = r.json()
    next_page = 'str'

    all_data_list_of_lists = []
    if data.get('data') == []:
        st.write("No ads meet the filter settings")
    else :
        while type(next_page) == str:
            page_data = data.get('data')
            # get column data
            for i in page_data:
                temp_ad_name = i.get('name')
                temp_ad_id = i.get('id')
                temp_campaign_name = i.get('campaign').get('name')
                temp_country = temp_campaign_name[0:3]
                temp_adcreative_data = page_data[0].get('adcreatives').get('data')[0]
                temp_adcreative_id = temp_adcreative_data.get('id')
                temp_image_url = temp_adcreative_data.get('thumbnail_url')
                # edit the temp_image_url in order to increase the thumbnail size:
                temp_h = int(temp_image_url.split("&h=")[1].split("&")[0])
                temp_w = int(temp_image_url.split("w=")[1].split("&h=")[0])
                # get the rescaled image using fb business SDK call:
                creative = AdCreative(temp_adcreative_id)
                fields = [AdCreative.Field.thumbnail_url]
                params = {
                    'thumbnail_width': temp_w * scale_multiplier,
                    'thumbnail_height': temp_h * scale_multiplier,
                }
                creative.api_get(fields=fields, params=params)
                temp_thumbnail_url = creative[AdCreative.Field.thumbnail_url]
                # moving on to body and title:
                temp_body = temp_adcreative_data.get('body')
                temp_title = temp_adcreative_data.get('title')
                if temp_body == None:
                    # This means that the ad has multiple options for body and title. The process below will retrieve all the options-
                    fields = [AdCreative.Field.asset_feed_spec]
                    creative.api_get(fields=fields)
                    asset_data = creative[AdCreative.Field.asset_feed_spec]._json
                    bodies = asset_data.get('bodies')
                    body_list = []
                    for body in bodies:
                        temp_body = body.get('text')
                        body_list.append(temp_body)
                    titles = asset_data.get('titles')
                    title_list = []
                    for title in titles:
                        temp_title = title.get('text')
                        title_list.append(temp_title)
                    temp_body = str(body_list).replace('[','').replace(']','').replace(',','\n')
                    temp_title = str(title_list).replace('[','').replace(']','').replace(',','\n')
                    
                all_data_list_of_lists.append([temp_ad_name,temp_campaign_name,temp_country,temp_thumbnail_url,temp_body,temp_title])
                        
                next_page = data.get('paging').get('next')
                if type(next_page) == str:
                    r = requests.get(url = next_page)
                    data = r.json()
                    print('next data page retrieved')
                                
        all_active_ads = pd.DataFrame(all_data_list_of_lists, columns =["ad_name",'campaign_name', 'country','thumbnail','body','title'])
        for index, row in all_active_ads.iterrows():
            thumbnail, ad_name, campaign_name, title, body = st.columns(5)

            with ad_name:
                st.text("ad name")
                st.text(all_active_ads.at[index,'ad_name'])

            with campaign_name:
                st.text("campaign name")
                st.text(all_active_ads.at[index,'campaign_name'])

            with thumbnail:
                st.text("creative")
                st.image(all_active_ads.at[index,'thumbnail'])

            with title:
                st.text("title")
                st.text(all_active_ads.at[index,'title'])
            
            with body:
                st.text("body")
                st.text(all_active_ads.at[index,'body'])

        
