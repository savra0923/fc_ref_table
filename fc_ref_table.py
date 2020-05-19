import pandas as pd
import requests
import numpy as np
from lxml import etree, html

def get_dis(row):
    if (row['impact'] == 'Holiday'):
        return ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    url = 'https://www.investing.com/economic-calendar/{}'.format(row.urls)

    r = requests.get(url, headers=headers)
    info=html.fromstring(r.content).xpath('//*[@id="overViewBox"]/div[1]/text()')

    for line in range(len(info)):
        info[line]=info[line].replace('\r','').replace('\n','')

    print('{}'.format(row.time))
    return info

def get_friendly(df):
    prefix_bank=pd.read_csv("known_prefixs.csv")
    prefix_bank= prefix_bank['prefixes'].values.tolist()
    countires_list=pd.read_csv("countries.csv")
    countires_list=countires_list['country'].values.tolist()

    parsed_data = []
    new_df=pd.DataFrame(columns=['prefix', 'friendly_name', 'event_type_ids'])

    for index, row in df.iterrows():
        title = row['title']
        #print(title)
        parsed_row = {}

        if '(' not in title:
            not_in_bank_flag=True
            for word in prefix_bank:
                if title.find(word) != -1:
                    not_in_bank_flag=False
                    parsed_row = new_df.loc[new_df['prefix'] == word].copy()
                    if parsed_row.empty:
                        parsed_row = {}
                        parsed_row['prefix'] = word
                        parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                        parsed_row['friendly_name'] = [word]
                    else:
                        lister = ''
                        for elem in parsed_row['event_type_ids'].values:
                            lister = lister + elem + ' '

                        lister = lister + str(int(row['event_type_id'])) + ' '
                        parsed_row.loc[parsed_row.prefix == parsed_row['prefix'], 'event_type_ids'] = lister
            if not_in_bank_flag:
                for word in countires_list:
                    if title.find(word) != -1:
                        title=title[title.find(word)+len(word)+1:]

                print('title: {}'.format(title))
                if(title.find('MoM') != -1 or title.find('QoQ') != -1 or title.find('YoY') != -1):
                    print('mew_title: {}'.format(title))

                pref = title
                if title not in prefix_bank:
                    prefix_bank.append(title)
                    parsed_row['prefix'] = pref
                    parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                    parsed_row['friendly_name'] = [pref]
                else:
                    parsed_row = new_df.loc[new_df['prefix'] == pref].copy()
                    parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                    lister = ''
                    for elem in parsed_row['event_type_ids'].values:
                        lister = lister + elem + ' '

                    lister = lister + str(int(row['event_type_id'])) + ' '
                    parsed_row.loc[parsed_row.prefix == parsed_row['prefix'], 'event_type_ids'] = lister
                    parsed_row['friendly_name'] = [pref]

        elif '(' in title:
            for word in title.split(' '):
                if '(' in word:
                    w= word.replace('(', '').replace(')', '')
                    if w not in prefix_bank:
                        prefix_bank.append(w)
                        parsed_row['prefix']= word.replace('(', '').replace(')', '')
                        parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                        parsed_row['friendly_name'] = [word.replace('(', '').replace(')', '')]

                        pref_len = len(parsed_row['prefix'])
                        if title.count('(') > 1:
                            title = title[title.find(')')+2:]
                        title=title[:title.find('(')]
                        print('title: {}'.format(title))
                        words = title.split(' ')
                        words = ' '.join(words[-(pref_len+1):-1])
                        parsed_row['friendly_name'] = parsed_row['friendly_name'] + [words, words + ' (' + parsed_row['prefix'] + ')']
                    else:
                        parsed_row=new_df.loc[new_df['prefix']==w].copy()
                        lister=''
                        for elem in parsed_row['event_type_ids'].values:
                            lister= lister +elem+' '

                        lister = lister + str(int(row['event_type_id']))+' '
                        parsed_row.loc[parsed_row.prefix == parsed_row['prefix'], 'event_type_ids'] = lister
        else:
            print('title: {}'.format(title))
            for word in countires_list:
                if title.find(word) != -1:
                    print(word)

            pref = title.split(' ', 1)[1]
            if title not in prefix_bank:
                prefix_bank.append(title)
                parsed_row['prefix'] = pref
                parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                parsed_row['friendly_name'] = [pref]
            else:
                parsed_row = new_df.loc[new_df['prefix'] == pref].copy()
                parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                lister = ''
                for elem in parsed_row['event_type_ids'].values:
                    lister = lister + elem + ' '

                lister = lister + str(int(row['event_type_id'])) + ' '
                parsed_row.loc[parsed_row.prefix == parsed_row['prefix'], 'event_type_ids'] = lister
                parsed_row['friendly_name'] = [pref]

        new_df = new_df.append(parsed_row, ignore_index=True)
        new_df = new_df.drop_duplicates(subset=['prefix'], keep='last')

    print(new_df)

    return new_df

def get_title(row):
    if (row['impact'] == 'Holiday'):
        return ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    url = 'https://www.investing.com/economic-calendar/{}'.format(row.urls)

    r = requests.get(url, headers=headers)
    info=html.fromstring(r.content).xpath('//*[@id="leftColumn"]/h1/text()')

    info=''.join(info)

    info=info.replace('\r','').replace('\n','').replace('\t','')
    print('{}'.format(row['time']))
    return info

def get_url_parts(row):
    proper=row['event_name'].lower()
    event_id= str(int(row['event_type_id']))

    proper=proper.replace('/', ' ')

    words = proper.split(' ')
    words_temp= proper.split(' ')

    for word in words_temp:
        if word.find('(') != -1:
            words.remove(word)
        if word.find('caixin') != -1:
            words=['chinese']+ words

    words= '-'.join(words)

    return words+'-'+event_id

def no_parantasis(row):
    proper = row['event_name']

    words = proper.split(' ')
    words_temp = proper.split(' ')

    for word in words_temp:
        if word.find('(') != -1:
            words.remove(word)

    words = ' '.join(words)
    return words

def pre_processing(df):
    months=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep','Dec'] # i don't need it

    df= df[df.impact!='Holiday']
    df= df.drop_duplicates(subset=['event_type_id'], keep='last')
    df['event_name'] = df.apply(no_parantasis, axis='columns')
    df['urls'] = df.apply(get_url_parts, axis='columns')
    df['title'] = df.apply(get_title, axis='columns')
    print('done pre_pocessing')
    return df

if __name__ == "__main__":

    #df= investing_scraper.get_events_year_range(2019,2020)

    #loader_fc = pd.read_csv("yearsHighV.csv")
    #print(loader_fc.size)
    #fc= pre_processing(loader_fc)
    #fc.to_csv('FullTitles.csv', index=False)
    fc=pd.read_csv("FullTitles.csv")
    print(fc.size)
    fc=get_friendly(fc)
    fc.to_csv('trying.csv', index=False)

    print('done!!')