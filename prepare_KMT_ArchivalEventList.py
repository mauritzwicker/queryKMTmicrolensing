'''
Prepare the KMT lists for X-matching with BHTOM-coordinates to download data.
"https://kmtnet.kasi.re.kr/ulens/event/YEAR/listpage.dat"

auther: Mauritz Wicker
date: 30.01.2025
'''

import pandas as pd
import re
import requests
import os

DIR_SAVETABLES = '/Users/mwicker/Documents/Other_Code/queryKMTmicrolensing/kmt_EventTables'
YEAR_INIT = 2016
YEAR_FINAL = 2025
OVERWRITE_TABLES = False

RA_RE  = re.compile(r"^\d{2}:\d{2}:\d{2}(\.\d+)?$")
DEC_RE = re.compile(r"^[+-]?\d{2}:\d{2}:\d{2}(\.\d+)?$")
COLS = [
    "Event", "FieldStarID", "RA", "Dec",
    "t_0", "t_E", "u_0", "Isource", "Ibase", "Icat", "Ctype", "A_I",
    "Related_event"
]

def load_kmt_listpage(url):
    text = requests.get(url, timeout=30).text

    rows = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if len(parts) < 6:
            continue

        event = parts[0]
        fieldstar = parts[1]  # e.g. SAO02K0103.022072 (Field.StarID)

        # Find RA and Dec by pattern (this is the key to handling the inconsistency)
        ra_idx = next((i for i, tok in enumerate(parts) if RA_RE.match(tok)), None)
        if ra_idx is None or ra_idx + 1 >= len(parts):
            raise ValueError(f"Line {line_no}: can't find RA/Dec in: {line}")

        ra = parts[ra_idx]
        dec = parts[ra_idx + 1]
        if not DEC_RE.match(dec):
            raise ValueError(f"Line {line_no}: token after RA isn't Dec in: {line}")

        # After Dec: numeric block then optional related-event ids
        tail = parts[ra_idx + 2:]

        # Expected numeric fields after Dec:
        # t_0, t_E, u_0, Isource, Ibase, Icat, Ctype, A_I  -> 8 tokens
        numeric = tail[:8]
        related = " ".join(tail[8:]) if len(tail) > 8 else None

        # Pad numeric if short
        numeric += [None] * (8 - len(numeric))

        rows.append([event, fieldstar, ra, dec] + numeric + [related])

    df = pd.DataFrame(rows, columns=COLS)

    # Convert numeric columns
    num_cols = ["t_0", "t_E", "u_0", "Isource", "Ibase", "Icat", "Ctype", "A_I"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")

    return(df)

def main():
    base_url = 'https://kmtnet.kasi.re.kr/ulens/event/'
    base_fn = 'listpage.dat'

    if not os.path.exists(DIR_SAVETABLES):
        print('Making Directory to save tables: {0}'.format(DIR_SAVETABLES))
        os.makedirs(DIR_SAVETABLES)

    years_to_load = range(YEAR_INIT, YEAR_FINAL+1)
    print(years_to_load)
    for yr in years_to_load:
        url = '{0}{1}/{2}'.format(base_url, yr, base_fn)
        fn_save = 'kmtEvents_{0}.csv'.format(yr)
        sv_thisYear = os.path.join(DIR_SAVETABLES, fn_save)

        if (os.path.exists(sv_thisYear) & (OVERWRITE_TABLES != True)):
            print('* Table KMT-table for year {0} exists -> continuing'.format(yr))
            loadData = False
            saveYr = False
        else:
            print('* Loading KMT-table for year {0} from {1}'.format(yr, url))
            loadData = True
            saveYr = True
        
        # Get the Data
        if loadData:
            try:
                df_thisyear = load_kmt_listpage(url)
                print('Successfully loaded KMT-table for {0}'.format(yr))
            except:
                df_thisyear = None
                print('Unable to load KMT-table for {0}'.format(yr))
                saveYr = False

        # Save the Data
        if saveYr:
            if os.path.exists(sv_thisYear):
                print('Table {0} exists'.format(fn_save))
                if OVERWRITE_TABLES:
                    print('Saving Table {0}'.format(fn_save))
                    df_thisyear.to_csv(sv_thisYear, index=False)
            else:
                print('Saving Table {0}'.format(fn_save))
                df_thisyear.to_csv(sv_thisYear, index=False)
    
    return


if __name__ == '__main__':
    main()