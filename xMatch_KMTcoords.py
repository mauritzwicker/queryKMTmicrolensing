'''
Cross-Match the coordinates of a source with the KMT lists

author: Mauritz Wicker
email: mwicker@astrouw.edu.pl
date: 30.01.2025
'''

import pandas as pd
import os
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import requests
import tarfile
import json
import math
import shutil

DIR_SAVEFULLTABLE = '/Users/mwicker/Documents/Other_Code/getKMTdata/'
FN_SAVEFULLTABLE = 'kmt_fullEvents.csv'
MAX_SEP = 1.0 # arcsec
OVERWRITE_TABLES = False
RELOAD_DATA_IF_EXISTS = False
DELETE_TEMP_TARGZ = True
DELETE_TEMP_DATA = False

KMT_MAPPING = {'KMTC': 'CTIO', 'KMTA': 'SSO', 'KMTS': 'SAAO'}
# C = CTIO
# A = SSO
# S = SAAO

PTH_SAVETEMPFILES = './tempData'
PTH_SAVEPROCESSEDFILES = './processedData'
PTH_SAVEXMATCHEDFILES = './xmatchedData'

def find_nearest(ra, dec, df, max_sep_arcsec):
    '''
    Find the KMT for given coordinates
    '''
    target = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    catalog = SkyCoord(ra=df['ra_deg'].values*u.deg,
                        dec=df['dec_deg'].values*u.deg)
    idx, sep2d, _ = target.match_to_catalog_sky(catalog)
    if sep2d < max_sep_arcsec * u.arcsec:
        return df.iloc[int(idx)], sep2d.arcsec
    else:
        return None, None

def getSave_kmt_data(url, dir_temp_save, nmXmatchSv):
    '''
    Pull the KMT data from the url and save in temporary directory
    '''
    print('Extracting KMT data from {0}'.format(url))
    r = requests.get(url)
    # tempSave_fn = 'all_pysis_{0}.tar.gz'.format(nmXmatch)
    temp_targz = os.path.join(PTH_SAVETEMPFILES, nmXmatchSv)
    with open(temp_targz,"wb") as f:
        f.write(r.content)
    with tarfile.open(temp_targz) as tar:
        tar.extractall(dir_temp_save)
    return

def extract_kmt_data(dir_temp_save):
    '''
    Extract the individual tables from the downloaded data with .pysis ending
    '''
    loaded_KMT_data = {}
    for fn_i in [fn for fn in os.listdir(dir_temp_save) if fn.endswith('.pysis')]:
        # Read the first non-empty comment line as header
        data_this_file = os.path.join(dir_temp_save, fn_i)
        with open(data_this_file) as f:
            for line in f:
                if line.startswith("#"):
                    header = line[1:].strip().split()
                    break
        df = pd.read_csv(data_this_file,comment="#",delim_whitespace=True,names=header)
        loaded_KMT_data[fn_i] = df
    return(loaded_KMT_data)

def format_extracted_data(data_df):
    '''
    For the kmt data we extracted, format it (ie only I-band and which telescope)
    '''
    finalBHTOMdata = {}
    for ky, data in data_df.items():
        obsLocation = KMT_MAPPING[ky[:4]]
        obsTelescope = ky.split('_')[0]
        obsFilter = 'KMT(' + ky.split('_')[1][0] + ')'
        obsFacility = obsLocation + '_' + obsTelescope
        print(obsLocation, obsTelescope, obsFilter, len(data))
        if obsFilter == 'KMT(I)':
            data['HJD'] += 2450000
            data['MJD'] = data['HJD'] - 2400000.5
            data['Magnitude'] = data['mag']
            data['Error'] = data['mag_err']
            data['Facility'] = obsFacility
            data['Filter'] = obsFilter
            data['Observer'] = 'KMT'
            data_for_BHTOM = data[['MJD', 'Magnitude', 'Error', 'Facility', 'Filter', 'Observer']]
            data_for_BHTOM = data_for_BHTOM[data_for_BHTOM['Error'] > 0]
            data_for_BHTOM.sort_values('MJD').reset_index(drop=True)
            if len(data_for_BHTOM) != 0:
                finalBHTOMdata[obsFacility] = data_for_BHTOM
    
    if len(finalBHTOMdata) != 0:
        return(finalBHTOMdata)
    else:
        return(None)

def safe_float(x):
    try:
        if x is None:
            return None
        x = float(x)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except (ValueError, TypeError):
        return None


def main(eventName_inp='test_MW', ra_inp=67.0, dec_inp=76.0):
    saved_FULLtable = os.path.join(DIR_SAVEFULLTABLE, FN_SAVEFULLTABLE)

    if not os.path.exists(PTH_SAVETEMPFILES):
        print('Making Folder to save temporarily Data')
        os.makedirs(PTH_SAVETEMPFILES)
    if os.path.exists(PTH_SAVEPROCESSEDFILES):
        print('Path for processed files exists')
    if not os.path.exists(PTH_SAVEPROCESSEDFILES):
        print('Making Folder to save processed Data')
        os.makedirs(PTH_SAVEPROCESSEDFILES)
    if not os.path.exists(PTH_SAVEXMATCHEDFILES):
        print('Making Folder to save XMatch info')
        os.makedirs(PTH_SAVEXMATCHEDFILES)

    if not os.path.exists(saved_FULLtable):
        print('Full Table does not exist {0}'.format(saved_FULLtable))
        return
    else:
        df_KMT = pd.read_csv(saved_FULLtable)

    assert df_KMT is not None

    # Include a check that the coordinate input is okay
    # *** ra_inp
    assert ra_inp is not None
    assert type(ra_inp) == float
    # *** dec_inp
    assert dec_inp is not None
    assert type(dec_inp) == float
    # ***

    # X-Match
    row, sep = find_nearest(ra_inp, dec_inp, df_KMT, max_sep_arcsec=MAX_SEP)
    if row is None:
        print('No Match')
    else:
        print('Found a Match for ({0:.3f}, {1:.3f}) with {2}'.format(ra_inp, dec_inp, row['Event']))
        sep_sv = sep[0] if isinstance(sep, np.ndarray) else sep
        print('Separation: {0:.3e} arcsec'.format(sep_sv))
        # Now Load the data for this event from KMT
        yrEvent = row['table_year']
        kmtName = row['Event']
        kmtID = kmtName.split('-')[0][0] + kmtName.split('-')[2][0] + kmtName.split('-')[1][-2:] + kmtName.split('-')[-1]
        url = 'https://kmtnet.kasi.re.kr/ulens/event/{0}/view.php?event={1}'.format(yrEvent, kmtName)
        url_tar = 'https://kmtnet.kasi.re.kr/ulens/event/{0}/data/{1}/pysis/pysis.tar.gz'.format(yrEvent, kmtID)
        tempSave_fn = 'all_pysis_{0}.tar.gz'.format(kmtName)

        pthSaveTempData_thisEvent = os.path.join(PTH_SAVETEMPFILES, kmtName) # where to save temporary files
        pthSaveProcessedData_thisEvent = os.path.join(PTH_SAVEPROCESSEDFILES, kmtName) # where to save final files
        pthSaveXmatchData_thisEvent = os.path.join(PTH_SAVEXMATCHEDFILES, eventName_inp)
        if not os.path.exists(pthSaveXmatchData_thisEvent):
            os.makedirs(pthSaveXmatchData_thisEvent)
        
        kmt_t0   = safe_float(row['t_0'])
        kmt_u0   = safe_float(row['u_0'])
        kmt_tE   = safe_float(row['t_E'])
        kmt_fsID = row['FieldStarID']
        kmt_Is   = safe_float(row['Isource'])
        kmt_Ib   = safe_float(row['Ibase'])
        kmt_AI   = safe_float(row['A_I'])

        # Save the Cross Match Data
        crossMatch = {'Name': eventName_inp, 'ra_input': float(ra_inp), 'dec_input': float(dec_inp),
                      'KMT_Name': kmtName, 'KMT_year': int(yrEvent), 'KMT_id': kmtID,
                      'KMT_url': url, 'KMT_urldata': url_tar,
                      'pth_Temp_data': pthSaveTempData_thisEvent,
                      'pth_Processed_data': pthSaveProcessedData_thisEvent,
                      'separation_arcsec': float(sep_sv),
                      'kmt_fieldStarID': kmt_fsID, 
                      'kmt_t0': kmt_t0,
                      'kmt_u0': kmt_u0,
                      'kmt_tE': kmt_tE,
                      'kmt_Isource': kmt_Is,
                      'kmt_Ibase': kmt_Ib,
                      'kmt_A_I': kmt_AI,
                      }
        if crossMatch is not None:
            print('Saving Cross Match Result for {0} / {1}'.format(eventName_inp, kmtName))
            fn_saveXmatchData = 'xmatch_{0}_with_{1}.json'.format(eventName_inp, kmtName)
            pth_saveXmatchData = os.path.join(pthSaveXmatchData_thisEvent, fn_saveXmatchData)
            if ((os.path.exists(pth_saveXmatchData)) & (OVERWRITE_TABLES != True)):
                print('Dont overwrite: not saving {0}'.format(fn_saveXmatchData))
            else:
                with open(pth_saveXmatchData, "w") as f:
                    json.dump(crossMatch, f, indent=4)
                print('Successfully saved {0}'.format(fn_saveXmatchData))
        
        # Get, Format, Save Individual Telescope Data
        if not os.path.exists(pthSaveTempData_thisEvent):
            getSave_kmt_data(url_tar, pthSaveTempData_thisEvent, tempSave_fn)
        elif RELOAD_DATA_IF_EXISTS:
            getSave_kmt_data(url_tar, pthSaveTempData_thisEvent, tempSave_fn)
        else:
            print('Temporary files exist -> dont reload')

        unformatted_kmt_data = extract_kmt_data(pthSaveTempData_thisEvent)
        kmt_data = format_extracted_data(unformatted_kmt_data)
        if not os.path.exists(pthSaveProcessedData_thisEvent):
            os.makedirs(pthSaveProcessedData_thisEvent)

        # savedFiles = []
        if kmt_data is not None:
            print('Saving BHTOM data for {0}'.format(kmtName))
            for nmData, df_BHTOM in kmt_data.items():
                print('Saving {0}'.format(nmData))
                fn_saveData = 'data_{0}_{1}.csv'.format(kmtName, nmData)
                pth_saveData = os.path.join(pthSaveProcessedData_thisEvent, fn_saveData)
                # savedFiles.append(fn_saveData)
                if ((os.path.exists(pth_saveData)) & (OVERWRITE_TABLES != True)):
                    print('Final Table for {0} Exists -> dont overwrite'.format(fn_saveData))
                else:
                    df_BHTOM.to_csv(pth_saveData, index=False)
                    print('Successfully saved {0}'.format(nmData))

        # Delete the tar.gz temporary file
        temp_targz = os.path.join(PTH_SAVETEMPFILES, tempSave_fn)
        if DELETE_TEMP_TARGZ:
            print('Deleting temporary {0} file'.format(tempSave_fn))
            if os.path.exists(temp_targz):
                os.remove(temp_targz)
        # Delete all temporary files
        if DELETE_TEMP_DATA:
            print('Deleting ALL temporary data files')
            if os.path.exists(pthSaveTempData_thisEvent):
                shutil.rmtree(pthSaveTempData_thisEvent)
    return

if __name__ == '__main__':
    name_usr = 'Gaia17bcu' # KMT-2017-BLG-2573
    ra_usr = 266.54918
    dec_usr = -25.62171
    main(eventName_inp=name_usr, ra_inp=ra_usr, dec_inp=dec_usr)