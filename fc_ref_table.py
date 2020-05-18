import pandas as pd
import requests
import numpy as np
from lxml import etree, html

def effect_on_asset(row):
    split_str = row['description'][-1]

    for word in split_str.split(' '):
        if '/bullish' in word:
            if 'positive' in word:
                return row['currency']+' Positive'
            else:
                return row['currency']+' Negative'

def is_high_positive(row):
    split_str = row['description'][-1]

    for word in split_str.split(' '):
        if '/bullish' in word:
            if 'positive' in word:
                return True
            else:
                return False

def get_relation(row):
    return row['currency']+' - Strong'

def get_friendly(row):
    friendly_list=[]
    capitals=''
    parse_str=row['description'][0].replace('The ','').replace('\r','').replace('\n','')

    if parse_str.count(')') > 1:
        parse_str = parse_str[(parse_str.find(')')+2):]
    if parse_str.count(',') > 1:
        parse_str = parse_str[:(parse_str.find(',')+1)]
    if parse_str.count('.') > 1:
        parse_str = parse_str[:(parse_str.find('.')+1)]

    for word in parse_str.split(' '):
        if word.isupper() and len(word) >= 3 and word.find('.') == -1 and word not in friendly_list:
            friendly_list = friendly_list + [parse_str[:(parse_str.find(word)+len(word))]]
            friendly_list = friendly_list + [parse_str[:(parse_str.find(word)-1)]]
            friendly_list = friendly_list + [word.replace('(','').replace(')','')]

    friendly_list=list(dict.fromkeys(friendly_list))

    for word in parse_str.split():
        if word[0].isupper() and len(word) >= 3 and word.find('.') == -1:
            capitals=capitals+' '+word

    capitals=capitals[1:]

    if capitals not in friendly_list and capitals.find(',') == -1:
        friendly_list=[capitals]

    if len(friendly_list) > 3:
        friendly_list=friendly_list[3:]

    print('{}'.format(row.time))
    return friendly_list

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

def get_friendly_two(df):
    prefix_bank=[]
    parsed_data = []
    #new_df = pd.DataFrame()
    new_df=pd.DataFrame(columns=['prefix', 'friendly_name', 'event_type_ids'])
    #new_df=new_df.append(old_df, ignore_index=True)

    for index, row in df.iterrows():
        title = row['title']
        print(title)
        parsed_row = {}

        if not title:
            continue

        if '(' not in title:
            pref=title.split(' ', 1)[1]
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
        else:
            for word in title.split(' '):
                if '(' in word:
                    w= word.replace('(', '').replace(')', '')
                    if w not in prefix_bank:
                        prefix_bank.append(w)
                        parsed_row['prefix']= word.replace('(', '').replace(')', '')
                        parsed_row['event_type_ids'] = str(int(row['event_type_id']))
                        parsed_row['friendly_name'] = [word.replace('(', '').replace(')', '')]

                        pref_len = len(parsed_row['prefix'])
                        title=title[:title.find('(')]
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

        new_df = new_df.append(parsed_row, ignore_index=True)
        new_df = new_df.drop_duplicates(subset=['prefix'], keep='last')
        #print(new_df)
        new_df.to_csv('fuckIt.csv', index=False)

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
    print(info)
    print('{}'.format(row.time))
    return info

def get_url_parts(row):

    if(row['impact']=='Holiday'):
        return ''

    proper=row['event_name'].lower()
    event_id= str(int(row['event_type_id']))

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

if __name__ == "__main__":

    strx= "Core CPI (MoM) (Apr)"

    #df= investing_scraper.get_events_year_range(2019,2020)
    #df= investing_scraper.tryhard()
    #print(df.head())
    #df= df.to_csv('yearsTest2.csv', index=False)

    #loader_fc = pd.read_csv("yearsHighV.csv")
    loader_fc = pd.read_csv("yearsTest2.csv")
    print(loader_fc.size)
    fc= loader_fc[loader_fc.impact!="Holiday"]
    fc= fc.drop_duplicates(subset=['event_type_id'], keep='last')
    print(fc.size)

    fc['event_name'] = fc.apply(no_parantasis, axis='columns')
    #print(fc.size)
    #fc.to_csv('tryingNoP.csv', index=False)
    fc['urls'] = fc.apply(get_url_parts, axis='columns')
    #print(fc.size)

    #fc.to_csv('trying.csv', index=False)

    # create the driver object.
    #fc['description']= fc.apply(get_dis, axis='columns')
    fc['title'] = fc.apply(get_title, axis='columns')
    print(fc.size)
    fc.to_csv('FullTitles.csv', index=False)
    #fc= pd.read_csv('trying.csv')
    #new_fc=get_friendly_two(fc)



    #fc['relation_to_asset'] = fc.apply(get_relation, axis='columns')
    #fc['is_high_positive'] = fc.apply(is_high_positive, axis='columns')
    #fc['effect'] = fc.apply(effect_on_asset, axis='columns')
    #fc['description']= fc.apply(getDescription, args=[driver], axis='columns')

    #print(new_fc)
    #new_fc.to_csv('tableTest.csv', index=False)
    #fc.to_csv('trying.csv', index=False)

    print('done!!')