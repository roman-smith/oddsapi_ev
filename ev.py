# IMORTS
import pandas
import numpy
import requests
import json
import datetime
import dateutil.parser
import pytz
from typing import Optional, Union

# ATTENTION!
# PULLING ALL ODDS FROM ONE MARKET (us, eu, etc.) TAKES ~150-350 API REQUESTS

# Main function
# Takes an Odds API key or filename as well as a variety of optional parameters to calculate expected value (EV) percentage(s) and filter and sort the betting odds of upcoming sporting events
def data(api_key: Optional[str]=None, sports: Optional[list[str]]=None, regions: Optional[list[str]]=['us', 'eu', 'uk', 'au'], markets: Optional[list[str]]=['h2h', 'spreads', 'totals'], ev_type: Optional[str]='both', recommended: Optional[bool]=False, days_from_now: Optional[Union[int, float]]=None, books: Optional[list[str]]=None, min_odds: Optional[Union[int, float]]=None, max_odds: Optional[Union[int, float]]=None, max_width: Optional[Union[int, float]]=None, max_vig_pct: Optional[Union[int, float]]=None, min_ev_pct: Optional[Union[int, float]]=None, min_num_books: Optional[Union[int, float]]=None, pref_ev_filter: Optional[str]='both', sortby: Optional[str]='default', ascending: Optional[bool]=False, pref_ev_sort: Optional[str]='avg', expanded: Optional[bool]=False, filename: Optional[str]=None) -> pandas.DataFrame:

    # Returns a list of sports from the API
    def get_sports(api_key):
        sports_response = requests.get(
            'https://api.the-odds-api.com/v4/sports', 
            params={
                'api_key': api_key
            }
        )


        if sports_response.status_code != 200:
            print(f'Failed to get sports: status_code {sports_response.status_code}, response body {sports_response.text}')
            return

        else:
            sports_list = [sport['key'] for sport in sports_response.json() if not sport['has_outrights']]

        return sports_list

    # Pulls data from the API into a JSON object
    def api_to_json(api_key, sports=None, regions=['us', 'eu', 'uk', 'au'], markets=['h2h', 'spreads', 'totals']):
        if sports is None:
            sports = get_sports(api_key=api_key)
        regions_string = ','.join(regions)
        markets_string = ','.join(markets)

        all_odds_json = []

        for sport in sports:
            
            odds_response = requests.get(
                f'https://api.the-odds-api.com/v4/sports/{sport}/odds',
                params={
                    'api_key': api_key,
                    'regions': regions_string,
                    'markets': markets_string,
                    'oddsFormat': 'american',
                    'dateFormat': 'iso',
                }
            )

            if odds_response.status_code != 200:
                print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

            else:
                odds_json = odds_response.json()
                all_odds_json.extend(odds_json)

                # Check the usage quota
                print('Remaining requests', odds_response.headers['x-requests-remaining'])
                print('Used requests', odds_response.headers['x-requests-used'])

        return odds_json

    # Reads data from a JSON file into a JSON object
    def file_to_json(filename):
        odds_json = json.load(open(filename))

        return odds_json

    # Converts the JSON object to a Dataframe
    def json_to_df(odds_json):
        # Put the json in a dataframe
        df_ori = pandas.DataFrame(odds_json)

        return df_ori

    # Takes API parameters and returns the resulting Dataframe
    def api_to_df(api_key, sports=None, regions=['us', 'eu', 'uk', 'au'], markets=['h2h', 'spreads', 'totals']):
        json_data = api_to_json(api_key=api_key, sports=sports, regions=regions, markets=markets)
        df_data = json_to_df(json_data)
        return df_data

    # Reads data from a JSON file and converts it to a Dataframe
    def file_to_df(filename):
        json_data = file_to_json(filename)
        df_data = json_to_df(json_data)
        return df_data

    # Unpacks a Dataframe that was derived from JSON into it's most robust, redundant form
    def unpacked_data(df_ori):
        # Unpack each of the bookmakers the 'bookmakers' column into its own row
        # Make new dataframe of bookmakers where each bookmaker has its own column
        df_bookmakers = pandas.DataFrame(list(df_ori['bookmakers']))

        # Concactenate df and df2 together
        df = pandas.concat([df_ori, df_bookmakers], axis=1, join='inner')

        # Unpivot the table using the melt() function (take the bookmaker columns and combine them into multiple rows in the same single column)
        df = pandas.melt(df, id_vars=df_ori.columns, value_name='bookmaker')
        df.drop(columns=['variable', 'bookmakers'], inplace=True)
        df.sort_values(['commence_time', 'id'], inplace=True)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Now, unpack the json in the bookmaker column
        df_ori = df
        df_bookmakers = pandas.DataFrame(list(df_ori['bookmaker']))
        df = pandas.concat([df_ori, df_bookmakers], axis=1, join='inner')
        df.drop(columns=['bookmaker'], inplace=True)
        df.rename(columns={'key' : 'book_key', 'title' : 'book_title'}, inplace=True)

        # Now, do the same unpacking, concat, and melting with the markets column
        df_ori = df
        df_markets = pandas.DataFrame(list(df_ori['markets']))
        df = pandas.concat([df_ori, df_markets], axis=1, join='inner')

        df = pandas.melt(df, id_vars=df_ori.columns, value_name='market')
        df.drop(columns=['variable', 'markets'], inplace=True)
        df.sort_values(['commence_time', 'id', 'book_key'], inplace=True)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Unpack the json in market column
        df_ori = df
        df_market = pandas.DataFrame(list(df_ori['market']))
        df = pandas.concat([df_ori, df_market], axis=1, join='inner')
        df.drop(columns=['market'], inplace=True)
        df.rename(columns={'key' : 'market'}, inplace=True)

        # Delete all lay markets
        df = df.loc[~df['market'].isin(['h2h_lay', 'outright_lay'])]
        df.reset_index(drop=True, inplace=True)

        # Unpack the 'outcomes' column
        df_ori = df
        df_outcomes = pandas.DataFrame(list(df_ori['outcomes']))
        df = pandas.concat([df_ori, df_outcomes], axis=1, join='inner')

        # Melt the resulting columns
        df = pandas.melt(df, id_vars=df_ori.columns, value_name='outcome')
        df.drop(columns=['outcomes', 'variable'], inplace=True)
        df.sort_values(['commence_time', 'id', 'book_key', 'market'], inplace=True)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Unpack outcome column
        df_ori = df
        df_outcome = pandas.DataFrame(list(df_ori['outcome']))
        df = pandas.concat([df_ori, df_outcome], axis=1, join='inner')
        df.drop(columns=['outcome'], inplace=True)
        df.rename(columns={'name' : 'position', 'price' : 'line'}, inplace=True)

        return df

    # Expands an unpacked Dataframe by calculating additional columns
    def processed_data(df):
        # Calculate the number of possible outcomes for the market
        df['num_outcomes'] = df.groupby(by=['id', 'book_key', 'market'])['line'].transform('count')
        # Calculate the market width only for markets with 2 outcomes
        df['above_below'] = numpy.where(df['num_outcomes'] != 2, numpy.nan, numpy.where(df['line'] > 0, df['line'] - 100, df['line'] + 100))
        df['width'] = numpy.where(df['num_outcomes'] != 2, numpy.nan, (-1)*(df.groupby(by=['id', 'book_key', 'market'])['above_below'].transform('sum')))

        # Calculate the number of books that carry each market
        key_fields = ['id', 'sport_key', 'sport_title', 'commence_time', 'home_team', 'away_team', 'market', 'position', 'point']
        df['num_books'] = df.groupby(by=key_fields, dropna=False)['book_key'].transform('count')

        # Calculate the implied win dec, fair implied win dec, fair line, amount to win from the real line, amount to win from the fair line, and vig pct
        df['vig_win_dec'] = numpy.where(df['line'] > 0, 100/(df['line'] + 100), abs(df['line'])/(abs(df['line']) + 100))
        df['fair_win_dec'] = df['vig_win_dec']/df.groupby(by=['id', 'book_key', 'market'])['vig_win_dec'].transform('sum')
        df['fair_line'] = numpy.where(df['fair_win_dec'] < 0.5, (100/df['fair_win_dec']) - 100, ((df['fair_win_dec']*100)/(1-df['fair_win_dec']))*(-1))
        df['amount_to_win_line'] = numpy.where(df['line'] > 0, df['line'], (100/abs(df['line']))*100)
        df['amount_to_win_fair'] = numpy.where(df['fair_line'] > 0, df['fair_line'], (100/abs(df['fair_line']))*100)
        # Vig pct to be used for multi-outcome games where market width cannot be calculated
        df['vig_dec'] = df.groupby(by=['id', 'book_key', 'market'])['vig_win_dec'].transform('sum') - df.groupby(by=['id', 'book_key', 'market'])['fair_win_dec'].transform('sum')
        df['vig_pct'] = df['vig_dec'] * 100

        return df

    # Takes API parameters and returns a fully unpacked and processed Dataframe
    def api_to_processed_df(api_key, sports=None, regions=['us', 'eu', 'uk', 'au'], markets=['h2h', 'spreads', 'totals']):
        raw_df = api_to_df(api_key=api_key, sports=sports, regions=regions, markets=markets)
        unpacked_df = unpacked_data(raw_df)
        processed_df = processed_data(unpacked_df)
        return processed_df

    # Reads data from a JSON file and converts it to a fully unpacked and processed Dataframe
    def file_to_processed_df(filename):
        raw_df = file_to_df(filename)
        unpacked_df = unpacked_data(raw_df)
        processed_df = processed_data(unpacked_df)
        return processed_df

    # Groups and aggregates a processed Dataframe to find the average odds of each position of each market of each game
    def av_odds(df):
        key_fields = ['id', 'sport_key', 'sport_title', 'commence_time', 'home_team', 'away_team', 'market', 'position', 'point']

        # Aggregate by mean
        df = df.groupby(key_fields, dropna=False).mean()
        df.sort_values(['commence_time', 'id', 'market'], inplace=True)
        return df

    # Extracts the pinnacle odds from processed odds (function will return an empty df if eu odds are not part of input df)
    def extract_pinnacle(odds):
        pinnacle_odds = odds.loc[odds['book_key'] == 'pinnacle']
        pinnacle_odds.reset_index(drop=True, inplace=True)
        return pinnacle_odds

    # Calculates the expected value with regard to the average odds, takes just book_odds as parameter as average odds are calculated directly from book odds
    def avg_ev(book_odds):
        # Calculate average odds
        average_odds = av_odds(book_odds)

        # Key fields for merging
        key_fields = ['id', 'sport_key', 'sport_title', 'commence_time', 'home_team', 'away_team', 'market', 'position', 'point', 'num_outcomes', 'num_books']

        # Merge book odds with the average odds
        avg_merge = book_odds.merge(average_odds, how='inner', on=key_fields, suffixes=['_book', '_avg'], validate='m:1')

        # Calculate ev data
        avg_merge['ev_pct_avg'] = (avg_merge['fair_win_dec_avg'] * avg_merge['amount_to_win_line_book']) - ((1 - avg_merge['fair_win_dec_avg']) * 100)
        avg_merge['kelly_dec_avg'] = avg_merge['fair_win_dec_avg'] - ((1 - avg_merge['fair_win_dec_avg']) / (avg_merge['amount_to_win_line_book'] / 100))
        avg_merge['kelly_pct_avg'] = avg_merge['kelly_dec_avg'] * 100

        return avg_merge

    # Calculates the expected value with regard to pinnacle odds, takes both book odds and pinnacle odds as parameters as book_odds may not necessarily have pinnacle odds within it
    def pinnacle_ev(book_odds, pinnacle_odds):
        # Key fields for merging
        key_fields = ['id', 'sport_key', 'sport_title', 'commence_time', 'home_team', 'away_team', 'market', 'position', 'point', 'num_outcomes']
        
        # Fields that are not keys but should not be duplicated when merging Pinnacle
        drop_fields = ['book_key', 'book_title', 'num_books']
        
        # Merge book odds with the pinnacle odds
        pinnacle_merge = book_odds.merge(pinnacle_odds.drop(columns=drop_fields), how='inner', on=key_fields, suffixes=['_book','_pinnacle'], validate='m:1')

        # Calculate ev data
        pinnacle_merge['ev_pct_pinnacle'] = (pinnacle_merge['fair_win_dec_pinnacle'] * pinnacle_merge['amount_to_win_line_book']) - ((1 - pinnacle_merge['fair_win_dec_pinnacle']) * 100)
        pinnacle_merge['kelly_dec_pinnacle'] = pinnacle_merge['fair_win_dec_pinnacle'] - ((1 - pinnacle_merge['fair_win_dec_pinnacle']) / (pinnacle_merge['amount_to_win_line_book'] / 100))
        pinnacle_merge['kelly_pct_pinnacle'] = pinnacle_merge['kelly_dec_pinnacle'] * 100

        return pinnacle_merge

    # Merge the avg ev and pinnacle ev dataframes into one
    def merge_ev(avg_merge, pinnacle_merge):
        # Key fields for merging
        key_fields = ['id', 'sport_key', 'sport_title', 'commence_time', 'home_team', 'away_team', 'book_key', 'book_title', 'market', 'position', 'line_book', 'point', 'num_outcomes', 'above_below_book', 'width_book', 'vig_win_dec_book', 'fair_win_dec_book', 'fair_line_book', 'amount_to_win_line_book', 'amount_to_win_fair_book', 'vig_dec_book', 'vig_pct_book']

        # Merge the dataframes (left merge because there are more averages than pinnacle odds and we don't want to lose those)
        final_merge = avg_merge.merge(pinnacle_merge.drop(columns=['num_books']), how='left', on=key_fields, suffixes=['_avg', '_pinnacle'])

        return final_merge

    # Takes API parameters and the desired type of expected value and returns a complete Dataframe with ev fields
    def api_to_ev(api_key, sports=None, regions=['us', 'eu', 'uk', 'au'], markets=['h2h', 'spreads', 'totals'], ev_type='both'):
        book_odds = api_to_processed_df(api_key=api_key, sports=sports, regions=regions, markets=markets)

        if ev_type == 'avg':
            ev = avg_ev(book_odds=book_odds)
        elif ev_type == 'pinnacle':
            if 'eu' not in regions:
                eu_odds = api_to_processed_df(api_key=api_key, sports=sports, regions=['eu'], markets=markets)
                pinnacle_odds = extract_pinnacle(eu_odds)
                ev = pinnacle_ev(book_odds=book_odds, pinnacle_odds=pinnacle_odds)
            else:
                pinnacle_odds = extract_pinnacle(book_odds)
                ev = pinnacle_ev(book_odds=book_odds, pinnacle_odds=pinnacle_odds)
        else: # assumed to be 'both'
            average = avg_ev(book_odds=book_odds)
            if 'eu' not in regions:
                eu_odds = api_to_processed_df(api_key=api_key, sports=sports, regions=['eu'], markets=markets)
                pinnacle_odds = extract_pinnacle(eu_odds)
                pinnacle = pinnacle_ev(book_odds=book_odds, pinnacle_odds=pinnacle_odds)
            else:
                pinnacle_odds = extract_pinnacle(book_odds)
                pinnacle = pinnacle_ev(book_odds=book_odds, pinnacle_odds=pinnacle_odds)
            ev = merge_ev(avg_merge=average, pinnacle_merge=pinnacle)

        return ev

    # Reads data from a JSON file and returns a complete Dataframe with ev fields (if ev_type 'pinnacle' is selected and file does not contain eu odds, df will be empty)
    def file_to_ev(filename, ev_type='both'): 
        book_odds = file_to_processed_df(filename)
        if ev_type == 'avg':
            ev = avg_ev(book_odds=book_odds)
        elif ev_type == 'pinnacle':
            pinnacle_odds = extract_pinnacle(book_odds)
            ev = pinnacle_ev(book_odds=book_odds, pinnacle_odds=pinnacle_odds)
        else: # assumed to be 'both'
            average = avg_ev(book_odds=book_odds)
            pinnacle_odds = extract_pinnacle(book_odds)
            pinnacle = pinnacle_ev(book_odds=book_odds, pinnacle_odds=pinnacle_odds)
            ev = merge_ev(avg_merge=average, pinnacle_merge=pinnacle)

        return ev

    # Filters a Dataframe of ev odds based on several optional parameters
    def filter_ev(odds, pref_ev_filter, sports=None, markets=None, days_from_now=None, books=None, min_odds=None, max_odds=None, max_width=None, max_vig_pct=None, min_ev_pct=None, min_num_books=None):
        if sports is not None:
            odds = odds.loc[odds['sport_key'].isin(sports)]
        if markets is not None:
            odds = odds.loc[odds['market'].isin(markets)]
        if days_from_now is not None:
            date = pytz.UTC.localize(datetime.datetime.now())+datetime.timedelta(days=days_from_now)
            odds = odds.loc[odds['commence_time'].apply(lambda t: dateutil.parser.isoparse(t)) <=  date]
        if books is not None:
            odds = odds.loc[odds['book_key'].isin(books)]
        if min_odds is not None:
            odds = odds.loc[odds['line_book'] >= min_odds]
        if max_odds is not None:
            odds = odds.loc[odds['line_book'] <= max_odds]
        if max_width is not None:
            odds = odds.loc[odds['num_outcomes'] == 2]
            if pref_ev_filter == 'both' or pref_ev_filter == 'avg':
                odds = odds.loc[odds['width_avg'] <= max_width]
            if pref_ev_filter == 'both' or pref_ev_filter == 'pinnacle':
                odds = odds.loc[odds['width_pinnacle'] <= max_width]
        if max_vig_pct is not None:
            if pref_ev_filter == 'both' or pref_ev_filter == 'avg':
                odds = odds.loc[odds['vig_pct_avg'] <= max_vig_pct]
            if pref_ev_filter == 'both' or pref_ev_filter == 'pinnacle':
                odds = odds.loc[odds['vig_pct_pinnacle'] <= max_vig_pct]
        if min_ev_pct is not None:
            if pref_ev_filter == 'both' or pref_ev_filter == 'avg':
                odds = odds.loc[odds['ev_pct_avg'] >= min_ev_pct]
            if pref_ev_filter == 'both' or pref_ev_filter == 'pinnacle':
                odds = odds.loc[odds['ev_pct_pinnacle'] >= min_ev_pct]
        if min_num_books is not None:
            odds = odds.loc[odds['num_books'] >= min_num_books]

        odds.reset_index(drop=True, inplace=True)

        return odds

    # Sorts a Dataframe of ev odds by a field
    def sort_ev(odds, sortby, ascending, pref_ev_sort='avg'):
        if sortby == 'commence_time':
            odds.sort_values(['commence_time'], ascending=ascending, inplace=True)
        elif sortby == 'line':
            odds.sort_values(['line_book'], ascending=ascending, inplace=True)
        elif sortby == 'width':
            if pref_ev_sort == 'avg':
                odds.sort_values(['width_avg'], ascending=ascending, inplace=True)
            if pref_ev_sort == 'pinnacle':
                odds.sort_values(['width_pinnacle'], ascending=ascending, inplace=True)
        elif sortby == 'ev_pct':
            if pref_ev_sort == 'avg':
                odds.sort_values(['ev_pct_avg'], ascending=ascending, inplace=True)
            if pref_ev_sort == 'pinnacle':
                odds.sort_values(['ev_pct_pinnacle'], ascending=ascending, inplace=True)
        if sortby == 'kelly_pct':
            if pref_ev_sort == 'avg':
                odds.sort_values(['kelly_pct_avg'], ascending=ascending, inplace=True)
            if pref_ev_sort == 'pinnacle':
                odds.sort_values(['kelly_pct_pinnacle'], ascending=ascending, inplace=True)

        if sortby == 'default':
            odds.sort_values(['commence_time', 'id', 'book_key', 'market'], inplace=True)

        odds.reset_index(drop=True, inplace=True)
        
        return odds

    # Simplify the dataframe into a more easily consumable format
    def cleanup_ev(odds, ev_type):
        fields_keep = ['sport_title', 'commence_time', 'home_team', 'away_team', 'book_title', 'market', 'position', 'line_book', 'point', 'num_books']

        if ev_type == 'both' or ev_type == 'avg':
            add_fields = ['fair_line_avg', 'width_avg', 'vig_pct_avg', 'ev_pct_avg', 'kelly_pct_avg']
            fields_keep.extend(add_fields)
        if ev_type == 'both' or ev_type == 'pinnacle':
            add_fields = ['fair_line_pinnacle', 'width_pinnacle', 'vig_pct_pinnacle', 'ev_pct_pinnacle', 'kelly_pct_pinnacle']
            fields_keep.extend(add_fields)


        odds = odds[fields_keep]
        odds = odds.round(2)
        return odds


    ########################################################################################################################################
    # 
    # BEGIN data() main code body
    # 
    ########################################################################################################################################

    # Check inputs for api call and/or filename
    if api_key is None and filename is None:
        raise SystemExit("Error: API key or filename must be specified\n")

    if sports is None:
        if filename is None and api_key is not None:
            sports = get_sports(api_key=api_key)
    elif sports is not None and (type(sports) != list or len(sports) == 0):
        raise TypeError("parameter 'sports' must be a list of valid sport IDs or None value. Refer to documentation for information on valid sport IDs\n")

    if type(regions) != list or len(regions) == 0:
        raise TypeError("parameter 'regions' must be a list of valid regions. Refer to documentation for information on valid regions\n")

    region_list = ['us', 'eu', 'uk', 'au']
    for region in regions:
        if region not in region_list:
            raise SystemExit("Error: one or more regions are invalid. Refer to documentation for information on valid regions\n")
    
    if type(markets) != list or len(markets) == 0:
        raise TypeError("parameter 'markets' must be a list of valid markets. Refer to documentation for information on valid markets\n")
        
    market_list = ['h2h', 'spreads', 'totals']
    for market in markets:
        if market not in market_list:
            raise SystemExit("Error: one or more markets are invalid. Refer to documentation for information on valid markets\n")

    ev_types = ['avg', 'pinnacle', 'both']
    if ev_type not in ev_types:
        raise SystemExit("Error: ev_type must be one of: 'avg', 'pinnacle', 'both' or be left blank")
    
    # Get ev data frame
    if filename is not None:
        df = file_to_ev(filename=filename, ev_type=ev_type)
    else:
        df = api_to_ev(api_key=api_key, sports=sports, regions=regions, markets=markets, ev_type=ev_type)

    # If recommended is on, reassign everything to values to give recommended bets (except books because a user should still be able to customize which books are displayed)
    if type(recommended) != bool:
        print("parameter 'recommended' must be a boolean. Default value is false")
        recommended = False
    if recommended:
        days_from_now = 2
        min_odds = -200
        max_odds = 200
        max_width = 45
        min_ev_pct = 1
        min_num_books = 4
        pref_ev_filter = 'both'
        sortby = 'ev_pct'
        ascending = False
        pref_ev_sort = 'avg'
        expanded = False

    # Check inputs for filter
    if days_from_now is not None and (type(days_from_now) != int or days_from_now < 0):
        if type(days_from_now) == float:
            days_from_now = int(days_from_now)
        else:
            print("parameter 'days_from_now' must be an integer >= 0. Filter parameter ignored")
            days_from_now = None

    if books is not None:
        if type(books) != list:
            print("parameter 'books' must be a list of valid book keys. Refer to documentation for information on valid books. Filter parameter ignored")
            books = None
        else:
            book_list = df['book_key'].unique().tolist()
            for book in list(books):
                if book not in book_list:
                    books.remove(book)
                    print(f'{book} is not a valid book. Data filtered by other specified books')
            if len(books) == 0:
                books = None

    if min_odds is not None and type(min_odds) != int and type(min_odds) != float:
        print("parameter 'min_odds' must be an integer or float. Filter parameter ignored")
        min_odds = None

    if max_odds is not None and type(max_odds) != int and type(max_odds) != float:
        print("parameter 'max_odds' must be an integer or float. Filter parameter ignored")
        max_odds = None

    if max_width is not None and type(max_width) != int and type(max_width) != float:
        print("parameter 'max_width' must be an integer or float. Filter parameter ignored")
        max_width = None

    if max_vig_pct is not None and type(max_vig_pct) != int and type(max_vig_pct) != float:
        print("parameter 'max_vig_pct' must be an integer or float. Filter parameter ignored")
        max_vig_pct = None

    if min_ev_pct is not None and type(min_ev_pct) != int and type(min_ev_pct) != float:
        print("parameter 'min_ev_pct' must be an integer or float. Filter parameter ignored")
        min_ev_pct = None

    if min_num_books is not None and type(min_num_books) != int and type(min_num_books) != float: 
        print("parameter 'min_num_books' must be an integer or float. Filter parameter ignored")
        min_num_books = None

    if pref_ev_filter not in ev_types:
        print("parameter 'pref_ev_filter' must be one of: 'avg', 'pinnacle', 'both' or be left blank. Value defaults to 'both'")
        pref_ev_filter = 'both'
    elif pref_ev_filter == 'avg' and ev_type == 'pinnacle':
        print("parameter 'pref_ev_filter' cannot be 'avg' when parameter 'ev_type' is 'pinnacle'. Value defaults to 'pinnacle'")
        pref_ev_filter = 'pinnacle'
    elif pref_ev_filter == 'pinnacle' and 'ev_type' == 'avg':
        print("parameter 'pref_ev_filter' cannot be 'pinnacle' when parameter 'ev_type' is 'avg'. Value defaults to 'avg'")
        pref_ev_filter = 'avg'

    if ev_type == 'both':
        if pref_ev_filter is None:
            pref_ev_filter = 'both'
    else:
        pref_ev_filter = ev_type

    # Filter the df
    df = filter_ev(df, pref_ev_filter, sports=sports, markets=markets, days_from_now=days_from_now, books=books, min_odds=min_odds, max_odds=max_odds, max_width=max_width, max_vig_pct=max_vig_pct, min_ev_pct=min_ev_pct, min_num_books=min_num_books)

    # Check inputs for sorting
    sort_options = ['commence_time', 'line', 'width', 'ev_pct', 'kelly_pct', 'default']
    if type(sortby) != str and sortby not in sort_options:
        print("parameter 'sortby' invalid. Refer to documentation for valid 'sortby' values. Filter parameter ignored")
        sortby = 'default'

    if ascending is not None and type(ascending) != bool:
        print("parameter 'ascending' must be a boolean. Default value used")
        ascending = False

    if pref_ev_sort is not None and (pref_ev_sort not in ev_types or pref_ev_sort == 'both'):
        print("parameter 'pref_ev_sort' must be 'avg' or 'pinnacle' or be left blank. Value defaults to 'avg'")
        pref_ev_sort = 'avg'
    elif pref_ev_sort == 'avg' and ev_type == 'pinnacle':
        print("parameter 'pref_ev_sort' cannot be 'avg' when parameter 'ev_type' is 'pinnacle'. Value defaults to 'pinnacle'")
        pref_ev_sort = 'pinnacle'
    elif pref_ev_sort == 'pinnacle' and 'ev_type' == 'avg':
        print("parameter 'pref_ev_sort' cannot be 'pinnacle' when parameter 'ev_type' is 'avg'. Value defaults to 'avg'")
        pref_ev_sort = 'avg'
    
    # Sort the df
    df = sort_ev(df, sortby=sortby, ascending=ascending, pref_ev_sort=pref_ev_sort)

    # If expanded is false, simplify the df
    if type(expanded) != bool:
        print("parameter 'expanded' must be a boolean. Value defaults to false.")
    if not expanded:
        df = cleanup_ev(df, ev_type=ev_type)

    return df