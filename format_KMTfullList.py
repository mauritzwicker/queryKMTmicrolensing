'''
Format the KMT tables into a full KMT list with correct coordinates

author: Mauritz Wicker
email: mwicker@astrouw.edu.pl
date: 30.01.2025
'''

import pandas as pd
import os
from astropy.coordinates import SkyCoord
import astropy.units as u
from datetime import datetime

DIR_SAVETABLES = '/Users/mwicker/Documents/Other_Code/getKMTdata/kmt_EventTables'
FNS_DATATABLES_BASE = 'kmtEvents_'
YEAR_INIT = 2016
YEAR_FINAL = datetime.now().year
DIR_SAVEFULLTABLE = '/Users/mwicker/Documents/Other_Code/getKMTdata/'
FN_SAVEFULLTABLE = 'kmt_fullEvents.csv'
OVERWRITE_TABLES = True

def loadcombine_KMTtables(years_to_load):
    '''
    Load and combien the KMT tables for all the years
    '''
    kmtTables_loaded = {}
    for yr in years_to_load:
        fn_to_load = '{0}{1}.csv'.format(FNS_DATATABLES_BASE, yr)
        load_thisYear = os.path.join(DIR_SAVETABLES, fn_to_load)
        if not os.path.exists(load_thisYear):
            print('Trying to Load {0} -- Doesnt exist'.format(fn_to_load))
            loadData = False
        else:
            print('* Loading KMT-table for year {0} from {1}'.format(yr, fn_to_load))
            loadData = True

        # Get the Data
        if loadData:
            try:
                df_thisyear = pd.read_csv(load_thisYear)
                print('Successfully loaded KMT-table for {0}'.format(yr))
            except:
                df_thisyear = None
                print('Unable to load KMT-table for {0}'.format(yr))
        else:
            df_thisyear = None

        if df_thisyear is not None:
            kmtTables_loaded[yr] = df_thisyear
    # Combine into one df with new column 'table_year' from key of dict
    if len(kmtTables_loaded) == 0:
        kmtTables_loaded = None
    else:
        kmtEvents_combined = pd.concat([df.assign(table_year=year) for year, df in kmtTables_loaded.items()], ignore_index=True)
        print('\nFound {0} KMT-Events'.format(len(kmtEvents_combined)))
    return(kmtEvents_combined)

def format_KMTtable(df_kmt, ra_sexagesimal_id='RA', dec_sexagesimal_id='Dec', new_ra_deg_id='ra_deg', new_dec_deg_id='dec_deg'):
    '''
    Format the table so that we can use it easily for our Cross Matching with coordinates
    '''
    # convert RA and DEC to deg
    coords = SkyCoord(ra=df_kmt[ra_sexagesimal_id].values,
                   dec=df_kmt[dec_sexagesimal_id].values,
                   unit=(u.hourangle, u.deg))
    df_kmt[new_ra_deg_id] = coords.ra.deg
    df_kmt[new_dec_deg_id] = coords.dec.deg
    return(df_kmt)


def main():
    if not os.path.exists(DIR_SAVETABLES):
        print('Data Directory does not exist {0}'.format(DIR_SAVETABLES))
        return

    sv_FULLtable = os.path.join(DIR_SAVEFULLTABLE, FN_SAVEFULLTABLE)
    if (os.path.exists(sv_FULLtable) & (OVERWRITE_TABLES != True)):
        print('* Full KMT-table {0} exists -> continuing'.format(FN_SAVEFULLTABLE))
        loadData = False
    else:
        print('* Full KMT-table does not exists yes')
        loadData = True

    if loadData:
        years_to_load = range(YEAR_INIT, YEAR_FINAL+1)
        kmtEvent_df = loadcombine_KMTtables(years_to_load)
        if kmtEvent_df is not None:
            # Format the Events Dataframe
            kmtEvent_df_formatted = format_KMTtable(kmtEvent_df)
            if os.path.exists(sv_FULLtable):
                print('Full Table {0} exists'.format(FN_SAVEFULLTABLE))
                if OVERWRITE_TABLES:
                    print('Saving Table {0}'.format(FN_SAVEFULLTABLE))
                    kmtEvent_df_formatted.to_csv(sv_FULLtable, index=False)
            else:
                print('Saving Table {0}'.format(FN_SAVEFULLTABLE))
                kmtEvent_df_formatted.to_csv(sv_FULLtable, index=False)
        else:
            print('Full Table is NONE -> cannot save')
    return


if __name__ == '__main__':
    main()