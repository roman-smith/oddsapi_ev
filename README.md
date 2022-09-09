# **Expected Value Odds Calculator**
#### Authored by Roman Smith
#### Powered by [The Odds API](https://the-odds-api.com/)  

<br>

## **Install**
    pip install oddsapi_ev

<br>

## **Imported Packages**
    pandas
    numpy
    requests
    json
    datetime
    dateutil.parser
    pytz
    typing

<br>

## **Overview**
The module gets upcoming sports betting odds from [The Odds API](https://the-odds-api.com/) and calculates the expected value (ev) of that bet with regard to either or both of two standards of "true odds". For more information on ev betting, [see this informative post](https://oddsjam.com/betting-education/positive-expected-value-betting).

<br>

## **`ev.py`**
This is the only module in the package. It contains the funciton `data()`.

<br>

## **`data()`**
This is the only function in the module `ev.py`.

**Parameters:** see **`data()` parameters** section

**Returns:** pandas DataFrame

### **THE USER MUST HAVE AN API KEY FOR [The Odds API](https://the-odds-api.com/) TO PULL DATA!**

<br>

## **`data()` parameters**

Each parameter is optional and each has a default value. However, either **api_key** or **filename** must be passed.

<br>

### Data Import
#### The following parameters are used for retrieving the raw data used in the function. Data can either be pulled from the API or uploaded from a JSON file.

**api_key (`str`)**:

A valid Odds API key

**filename (`str`):**

The name of a JSON file containing data in the same format as the Odds API

EITHER **api_key** OR **filename** MUST BE PASSED (**api_key** IS RECOMMENDED) OTHERWISE THE FUNCTION WILL EXIT!**

<br>

### API Call Parameters

The following parameters are passed to the API call to specify which types of odds are pulled and ***affect the number of requests you are charged against your quota***. When uploading a file instead of calling the API, all of the following except `regions` will be used to filter the file data. If bad input is given for any of the API parameters, the function will exit.

**sports (`list[str]`):**

A list of sports to be included[as defined by The Odds API](https://the-odds-api.com/sports-odds-data/sports-apis.html)

**regions (`list[str]`):**

A list of sports book regions to be included. Must be a subset of: `['us', 'eu', 'uk', 'au']`

**markets (`list[str]`):**

A list of betting markets to be included. Must be a subset of `['h2h', 'spreads', 'totals']`. For more info [see here](https://the-odds-api.com/sports-odds-data/betting-markets.html)

<br>

### Expected Value Type

This parameter identifies which type of expected value to use. There are 2 ways to determine the fair odds of a position and thus 2 ways to determine the expected value of a bet.

*Average:* determines the fair odds of a position as the average of all of the odds for that position across all sports books with the sports books' edge removed.

*Pinnacle:* determines the fair odds of a position to be the odds offered by sharp sports book Pinnacle with the sports book's edge removed.

If bad input is given, the function will exit.

**ev_type (`str`):**

The method(s) of calculating expected value to be used. Must be one of the following: **'avg'**, **'pinnacle'**, or **'both'**

<br>

### Filter Values
These parameters are used to filter the odds. If bad input is given, the function continue but will not filter the odds based on that value.

**recommended (`bool`):**

If recommended is True, all filter values will be overriden with recommended values to find the most profitable bets.

**days_from_now (`int` or `float`):**

The maximum number of days into the future to return odds

**books (`list[str]`):**

A list of sports books to be included in the odds. [See here](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html#us-bookmakers) for valid sports books keys.

**min_odds (`int` or `float`):**

The minimum odds line (in American format) of the returned odds.

**min_odds (`int` or `float`):**

The maximum odds line (in American format) of the returned odds.

If **min_odds** > **max_odds**, the function will return an empty DataFrame

**max_width (`int` or `float`):**

The maximum width of the returned odds. (See **Calculated DataFrame Fields** for more information on width)

**max_vig_pct (`int` or `float`):**

The maximum 'vig' or 'edge' in the sports book's odds

**min_ev_pct (`int` or `float`):**

The minimum expected value percentage of the odds

**min_num_books (`int` or `float`):**

The minimum number of sports books offering each line

**pref_ev_filter (`str`):**

The preferred method of ev calculation to filter values on. Must be one of the following: **'avg'**, **'pinnacle'**, or **'both'**.

Note: the **ev_type** and **pref_ev_filter** cannot contradict each other (e.g. if **'avg'** is the **ev_type**, **'pinnacle'** cannot be the **pref_ev_filter**. In that scenario, **pref_ev_filter** will default to **ev_type**).

<br>

### Sort Values
These parameters are used to sort the DataFrame

**sortby (`str`):**

The value to sort the DataFrame on.

Must be one of the following: **'commence_time'**, **'line'**, **'width'**, **'ev_pct'**, **'kelly_pct'**, or **'default'**.

**'default'** sorts the DataFrame according to a default combination of fields.

**ascending (`bool`):**

Sort the chosen value in ascending order when True, and descending order when False

**pref_ev_sort (`str`):**

The preferred method of ev calculation to sort values on. Must be either **'avg'** or **'pinnacle'** (NOT **'both'**).

Note: the **ev_type** and **pref_ev_sort** cannot contradict each other (e.g. if **'avg'** is the **ev_type**, **'pinnacle'** cannot be the **pref_ev_sort**. In that scenario, **pref_ev_sort** will default to **ev_type**).

<br>

### Expanded
This parameter controls wether the returned DataFrame will include all data fields or only the essential fields. Defaults to False.

**expanded (`bool`):**

If expanded is True, extra fields will be included in the returned DataFrame. Many of these fields are intermediate fields in calculating more significant fields.

If expanded is False, the DataFrame returns only the most significant fields.

Defaults to False if unspecified.

<br>

## **Examples of data() calls**
    from oddsapi_ev import ev

    # get all of the most profitable bets
    odds1 = ev.data(api_key=YOURKEY, recommended=True)

    # get all odds from DraftKings, sorted by ev percentage with respect to the average odds
    odds2 = ev.data(api_key=YOURKEY, regions=['us'], ev_type='avg', books=['draftkings'], sortby='ev_pct', ascending=False, pref_ev_sort='avg')

    # get all head to head odds at eu book makers for UEFA champions league games with maximum odds of +110 and the ev calculated with respect to Pinnacle odds
    odds3 = ev.data(api_key=YOURKEY, sports=['soccer_uefa_champs_league'], regions=['eu'], markets=['h2h'], ev_type='pinnacle', min_odds=110, pref_ev_filter='pinnacle') 

<br>

## **Calculated DataFrame Fields**

The following is a description of the additional fields calculated by `data()` (not including expanded fields) that do not exist in the Odds API data.

**num_books:**

The number of sports books that have odds posted for the given position. This is significant for calculations done with average values as the higher the number of books contributing to the average, the more reliable it is

**fair_line:**

This is what the odds of a given position would be if the 'vig' or 'edge' that sports books build in to their odds to guarentee profit were removed

They indicate what the actual chances of the outcome are according to the sports book

**width:**

The combined number of points the odds for both sides of a market are below the fair odds (+100/-100)

For example, if two sides of a market were +105 and -125, the width would be 20 as -125 is 25 below and +105 is 5 above so the net number would be 20.

[Read more here](https://oddsjam.com/betting-education/market-width)

**vig_pct:**

The percent difference between the implied winning percentage of a given set of odds at a sports book with 'vig' or 'edge' built in and the winning perctentage of those same set of odds at the same sports book with the vig taken out to find the fair winning percentage. It is a measure of how unfair the odds are.

**ev_pct:**

The expected value (ev) percentage is the percent difference between the implied winning percentage of a given position at some sports book before the vig is removed and the implied winning percentage of the same position at a more accurate sports book (like Pinnacle) or average of multiple sports books after the vig removed.

More simply it represents the difference between the odds you bet and what the true chance at winning a bet has.

Most bets will have negative ev percentages. The few with positive percentages are the profitable bets.

[Read more here](https://oddsjam.com/betting-education/positive-expected-value-betting)

**kelly_pct:**

The statistically optimal percentage of your bankroll to bet based on the ev percentage and the overall probability of winning.