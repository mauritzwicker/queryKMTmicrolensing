'''
Run X-Match of an Source (cordinates) with KMT-Microlensing Catalogues

author: Mauritz Wicker
email: mwicker@astrouw.edu.pl
date: 30.01.2025
'''
import os
import prepare_KMT_AlertsEventList
import prepare_KMT_ArchivalEventList
import format_KMTfullList
import xMatch_KMTcoords
import loadview_KMTdata

QUERY_NEW_ALERTS = True # Whether to query again the table for the current year or not

def main():
    # Check if KMT list exists
    if QUERY_NEW_ALERTS:
        print('Creating the KMT list of Events')
        prepare_KMT_AlertsEventList.main()
        format_KMTfullList.main()
    elif not os.path.exists('./kmt_fullEvents.csv'):
        print('Creating the KMT list of Events')
        prepare_KMT_AlertsEventList.main()
        prepare_KMT_ArchivalEventList.main()
        format_KMTfullList.main()
    else:
        print('KMT list of Events exists and not Querying current alerts')

    # Source
    obj_Name = 'Gaia17bcu' # KMT-2017-BLG-2573
    obj_ra = 266.54918 # deg
    obj_dec = -25.62171 # deg
    
    # X-Match with the source 
    xMatch_KMTcoords.main(obj_Name, obj_ra, obj_dec)

    # Plot the results
    loadview_KMTdata.main(obj_Name, obj_ra, obj_dec, pltInfo=True)

    return


if __name__ == '__main__':
    main()