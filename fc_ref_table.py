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
    info = html.fromstring(r.content).xpath('//*[@id="overViewBox"]/div[1]/text()')

    for line in range(len(info)):
        info[line] = info[line].replace('\r', '').replace('\n', '')

    print('{}'.format(row.time))
    return info


def row_setup(prefix, friendly_names, event_type_ids):
    parsed_row = {}
    parsed_row['prefix'] = prefix
    parsed_row['event_type_ids'] = str(int(event_type_ids))
    parsed_row['friendly_name'] = [friendly_names]

    return parsed_row


def list_parse(event_list, new_event):
    lister = ''
    for elem in event_list.values:
        lister = lister + elem + ' '

    lister = lister + str(int(new_event)) + ' '
    return lister


def friendly_update(parsed_row, title):
    pref_len = len(parsed_row['prefix'])
    if title.count('(') > 1:
        title = title[title.find(')') + 2:]
    title = title[:title.find('(')]
    words = title.split(' ')
    words = ' '.join(words[-(pref_len + 1):-1])
    return parsed_row['friendly_name'] + [words, words + ' (' + parsed_row['prefix'] + ')']


def get_friendly(df):
    # you can just save it as a static list if that is its only use
    prefix_bank = pd.read_csv("known_prefixs.csv")
    prefix_bank = prefix_bank['prefixes'].values.tolist()

    new_df = pd.DataFrame(columns=['prefix', 'friendly_name', 'event_type_ids'])

    for index, row in df.iterrows():
        title = row['title']
        parsed_row = {}

        if '(' not in title:
            not_in_bank_flag = True
            for word in prefix_bank:
                if title.find(word) != -1:
                    not_in_bank_flag = False
                    parsed_row = new_df.loc[new_df['prefix'] == word].copy()
                    if parsed_row.empty:
                        parsed_row = row_setup(word, word, row['event_type_id'])
                    else:
                        parsed_row['event_type_ids'] = list_parse(parsed_row['event_type_ids'], row['event_type_id'])
            if not_in_bank_flag:
                pref = title
                if title not in prefix_bank:
                    prefix_bank.append(title)
                    parsed_row = row_setup(pref, pref, row['event_type_id'])
                else:
                    parsed_row = new_df.loc[new_df['prefix'] == pref].copy()
                    parsed_row['event_type_ids'] = list_parse(parsed_row['event_type_ids'], row['event_type_id'])
        else:
            can_skip = False
            for word in title.split(' '):
                if '(' in word:
                    w = word.replace('(', '').replace(')', '')
                    if w == 'Barrel':
                        w = 'Oil'
                    if w not in prefix_bank and can_skip == False:
                        prefix_bank.append(w)
                        parsed_row = row_setup(word.replace('(', '').replace(')', ''),
                                               word.replace('(', '').replace(')', ''), row['event_type_id'])
                        parsed_row['friendly_name'] = friendly_update(parsed_row, title)
                    else:
                        parsed_row = new_df.loc[new_df['prefix'] == w].copy()
                        parsed_row['event_type_ids'] = list_parse(parsed_row['event_type_ids'], row['event_type_id'])
                    can_skip = True

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
    info = html.fromstring(r.content).xpath('//*[@id="leftColumn"]/h1/text()')

    info = ''.join(info)

    info = info.replace('\r', '').replace('\n', '').replace('\t', '').replace('Core', '')
    # print(info)

    countires_list = pd.read_csv("countries.csv")
    countires_list = countires_list['country'].values.tolist()
    l = ['MoM', 'QoQ', 'YoY', '(MoM)', '(QoQ)', '(YoY)']

    for word in l:
        if info.find(word) != -1:
            info = info[:info.find(word) - 1]

    for word in countires_list:
        if info.find(word) != -1:
            info = info[info.find(word) + len(word) + 1:]

    # print('title: {}'.format(info))

    print('{}'.format(row['time']))
    return info


def get_url_parts(row):
    proper = row['event_name'].lower()
    event_id = str(int(row['event_type_id']))

    proper = proper.replace('/', ' ').replace('-', ' ')

    words = proper.split(' ')
    words_temp = proper.split(' ')

    for word in words_temp:
        if word.find('(') != -1:
            words.remove(word)
        if word.find('caixin') != -1:
            words = ['chinese'] + words

    words = '-'.join(words)

    return words + '-' + event_id


def no_parantasis(row):
    # TODO: this can be done with one line in regex and with no iterations
    proper = row['event_name']

    words = proper.split(' ')
    words_temp = proper.split(' ')

    for word in words_temp:
        if word.find('(') != -1:
            words.remove(word)

    words = ' '.join(words)
    return words


def pre_processing(df):
    df = df[df.impact != 'Holiday']
    # df= df[df.impact=='Low Volatility Expected']
    df = df.drop_duplicates(subset=['event_type_id'], keep='last')
    df['event_name'] = df.apply(no_parantasis, axis='columns')
    df['urls'] = df.apply(get_url_parts, axis='columns')
    print(len(df.index))
    df['title'] = df.apply(get_title, axis='columns')
    print('done pre_pocessing')
    return df


if __name__ == "__main__":
    # df= investing_scraper.get_events_year_range(2019,2020)
    # Tomer: I formatted all of the code to pep 8 you should read about it a little. (cntrl+alt+L)
    loader_fc = pd.read_csv("yearsTest2.csv")
    print(loader_fc.size)
    fc = pre_processing(loader_fc)
    # Tomer: why are you saving each part to a csv and not just the last output?
    # TODO: dont understand why you need these two lines you save fc only to load it again??
    fc.to_csv('FullTitles.csv', index=False)
    fc = pd.read_csv("FullTitles.csv")
    print('# of rows in FC: {}'.format(len(fc.index)))
    fc = get_friendly(fc)
    print('# of rows in FC after getting friendly names: {}'.format(len(fc.index)))
    fc.to_csv('tryingAll.csv', index=False)

    print('done!!')
