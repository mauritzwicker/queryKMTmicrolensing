'''
For an event we have X-matched, load the KMT results and plot

author: Mauritz Wicker
email: mwicker@astrouw.edu.pl
date: 30.01.2025
'''

import pandas as pd
import os
import numpy as np
import json
import matplotlib.pyplot as plt

DIR_SAVEFULLTABLE = '/Users/mwicker/Documents/Other_Code/queryKMTmicrolensing/'
FN_SAVEFULLTABLE = 'kmt_fullEvents.csv'

PTH_SAVETEMPFILES = './tempData'
PTH_SAVEPROCESSEDFILES = './processedData'
PTH_SAVEXMATCHEDFILES = './xmatchedData'


def main(eventName_inp='test_MW', ra_inp=67.0, dec_inp=76.0, pltInfo=True):
    xmatch_thisevent = os.path.join(PTH_SAVEXMATCHEDFILES, eventName_inp)
    if os.path.exists(xmatch_thisevent):
        print('X-Match exists for {0}\n'.format(eventName_inp))
        diff_x_matches = [fn for fn in os.listdir(xmatch_thisevent) if fn.endswith('.json')] # could be more than one Xmatch, shouldn't but could
        for xmatch in diff_x_matches:
            with open(os.path.join(xmatch_thisevent, xmatch), "r") as f:
                crossMatch = json.load(f)
            print('* Found a X-Match between {0} : {1}'.format(crossMatch['Name'], crossMatch['KMT_Name']))
            procData_path = crossMatch['pth_Processed_data']
            data_fns = [fn for fn in os.listdir(procData_path) if fn.endswith('.csv')]

            fig, ax = plt.subplots(figsize=(10, 7))
            for fn in data_fns:
                dfNow = pd.read_csv(os.path.join(procData_path, fn))
                print(' - {0} ({1})'.format(fn, len(dfNow)))
                # ax.scatter(dfNow['MJD'], dfNow['Magnitude'], label=dfNow['Facility'][0], s=1)
                ax.errorbar(dfNow['MJD'], dfNow['Magnitude'], yerr=dfNow['Error'], label=dfNow['Facility'][0], ms=0.5, fmt=' ', capsize=1.0, lw=0.4)
            ax.legend(loc='upper right')
            ax.set_xlabel('Time [MJD]')
            ax.set_ylabel('Magnitude')
            ax.set_title('{0} : {1}'.format(crossMatch['Name'], crossMatch['KMT_Name']))
            ax.invert_yaxis()
            # Add text box
            if pltInfo:
                keys_to_show = [ 'Name', 'ra_input', 'dec_input', 'KMT_Name', 'KMT_year',
                 'kmt_data_status', 'kmt_public_release_date',
                 'KMT_id', 'kmt_fieldStarID', 'kmt_t0', 'kmt_u0',
                 'kmt_tE', 'kmt_Isource', 'kmt_Ibase', 'kmt_A_I' ]
                lines = []
                for k in keys_to_show:
                    v = crossMatch.get(k, "N/A")
                    if isinstance(v, float):
                        lines.append(f"{k}: {v:.3f}")
                    else:
                        lines.append(f"{k}: {v}")
                textstr = "\n".join(lines)
                ax.text(
                    0.02, 0.98, textstr,
                    transform=ax.transAxes,
                    fontsize=10,
                    verticalalignment='top',
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
                )
            fig.tight_layout()
            plt.show()
    else:
        print('X-Match does NOT exists for {0}'.format(eventName_inp))

    return

if __name__ == '__main__':
    name_usr = 'Gaia17bcu' # KMT-2017-BLG-2573
    ra_usr = 266.54918
    dec_usr = -25.62171
    main(eventName_inp=name_usr, ra_inp=ra_usr, dec_inp=dec_usr)