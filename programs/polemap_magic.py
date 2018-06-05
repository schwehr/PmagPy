#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-
# define some variables

from __future__ import division
from __future__ import print_function
from builtins import input
from past.utils import old_div
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.new_builder as nb


def main():
    """
    NAME
        polemap_magic.py

    DESCRIPTION
        makes a map of paleomagnetic poles and a95/dp,dm for pole  in a locations table

    SYNTAX
        polemap_magic.py [command line options]

    OPTIONS
        -h prints help and quits
        -eye  ELAT ELON [specify eyeball location], default is 90., 0.
        -f FILE location format file, [default is locations.txt]
        -res [c,l,i,h] specify resolution (crude, low, intermediate, high]
        -etp plot the etopo20 topographpy data (requires high resolution data set)
        -prj PROJ,  specify one of the following:
             ortho = orthographic
             lcc = lambert conformal
             moll = molweide
             merc = mercator
        -sym SYM SIZE: choose a symbol and size, examples:
            ro 5 : small red circles
            bs 10 : intermediate blue squares
            g^ 20 : large green triangles
        -ell  plot dp/dm or a95 ellipses
        -rev RSYM RSIZE : flip reverse poles to normal antipode
        -S:  plot antipodes of all poles
        -age : plot the ages next to the poles
        -crd [g,t] : choose coordinate system, default is to plot all location poles
        -fmt [pdf, png, eps...] specify output format, default is pdf
        -sav  save and quit
    DEFAULTS
        FILE: locations.txt
        res:  c
        prj: ortho
        ELAT,ELON = 0,0
        SYM SIZE: ro 8
        RSYM RSIZE: g^ 8

    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", ".")
    # plot: default is 0, if -sav in sys.argv should be 1
    plot = pmag.get_flag_arg_from_sys("-sav", true=1, false=0)
    fmt = pmag.get_named_arg_from_sys("-fmt", "pdf")
    res = pmag.get_named_arg_from_sys("-res", "c")
    proj = pmag.get_named_arg_from_sys("-prj", "ortho")
    anti = pmag.get_flag_arg_from_sys("-S", true=1, false=0)
    fancy = pmag.get_flag_arg_from_sys("-etp", true=1, false=0)
    ell = pmag.get_flag_arg_from_sys("-ell", true=1, false=0)
    ages = pmag.get_flag_arg_from_sys("-age", true=1, false=0)
    if '-rev' in sys.argv:
        flip = 1
        ind = sys.argv.index('-rev')
        rsym = (sys.argv[ind + 1])
        rsize = int(sys.argv[ind + 2])
    else:
        flip, rsym, rsize = 0, "g^", 8
    if '-sym' in sys.argv:
        ind = sys.argv.index('-sym')
        sym = (sys.argv[ind + 1])
        size = int(sys.argv[ind + 2])
    else:
        sym, size = 'ro', 8
    if '-eye' in sys.argv:
        ind = sys.argv.index('-eye')
        lat_0 = float(sys.argv[ind + 1])
        lon_0 = float(sys.argv[ind + 2])
    else:
        lat_0, lon_0 = 90., 0.
    crd = pmag.get_named_arg_from_sys("-crd", "")
    coord_dict = {'g': 0, 't': 100}
    coord = coord_dict[crd] if crd else ""
    results_file = pmag.get_named_arg_from_sys("-f", "locations.txt")

    con = nb.Contribution(dir_path, single_file=results_file)
    if not list(con.tables.keys()):
        print("-W - Couldn't read in data")
        return

    FIG = {'map': 1}
    pmagplotlib.plot_init(FIG['map'], 6, 6)
    # read in location file
    lats, lons = [], []
    Pars = []
    dates, rlats, rlons = [], [], []

    pole_container = con.tables['locations']
    pole_df = pole_container.df
    # use individual results
    if 'result_type' in pole_df.columns:
        pole_df = pole_df[pole_df['result_type'] == 'a']
    if 'pole_lat' not in pole_df.columns or 'pole_lon' not in pole_df.columns:
        print("-W- pole_lat and pole_lon are required columns to run polemap_magic.py")
        return
    # use records with pole_lat and pole_lon
    cond1, cond2 = pole_df['pole_lat'].notnull(), pole_df['pole_lon'].notnull()
    Results = pole_df[cond1 & cond2]
    # use tilt correction
    if coord and 'dir_tilt_correction' in Results.columns:
        Results = Results[Results['dir_tilt_correction'] == coord]
    # get location name and average ages
    locations = ":".join(Results['location'].unique())
    if 'age' not in Results.columns and 'age_low' in Results.columns and 'age_high' in Results.columns:
        Results['age']=Results['age_low']+0.5*(Results['age_high']-Results['age_low'])
    if 'age' in Results.columns and ages == 1:
        dates = Results['age'].unique()

    # go through rows and extract data
    for ind, row in Results.iterrows():
        lat, lon = float(row['pole_lat']), float(row['pole_lon'])
        if anti == 1:
            lats.append(-lat)
            lon = lon + 180.
            if lon > 360:
                lon = lon - 360.
            lons.append(lon)
        elif flip == 0:
            lats.append(lat)
            lons.append(lon)
        elif flip == 1:
            if lat < 0:
                rlats.append(-lat)
                lon = lon + 180.
                if lon > 360:
                    lon = lon - 360
                rlons.append(lon)
            else:
                lats.append(lat)
                lons.append(lon)

        ppars = []
        ppars.append(lon)
        ppars.append(lat)
        ell1, ell2 = "", ""
        if 'pole_dm' in list(row.keys()) and row['pole_dm']:
            ell1 = float(row['pole_dm'])
        if 'pole_dp' in list(row.keys()) and row['pole_dp']:
            ell2 = float(row['pole_dp'])
        if 'pole_alpha95' in list(row.keys()) and row['pole_alpha95']:
            ell1, ell2 = float(row['pole_alpha95']), float(row['pole_alpha95'])
        if ell1 and ell2:
            ppars = []
            ppars.append(lons[-1])
            ppars.append(lats[-1])
            ppars.append(ell1)
            ppars.append(lons[-1])
            isign = old_div(abs(lats[-1]), lats[-1])
            ppars.append(lats[-1] - isign * 90.)
            ppars.append(ell2)
            ppars.append(lons[-1] + 90.)
            ppars.append(0.)
            Pars.append(ppars)

    locations = locations.strip(':')
    Opts = {'latmin': -90, 'latmax': 90, 'lonmin': 0., 'lonmax': 360.,
            'lat_0': lat_0, 'lon_0': lon_0, 'proj': proj, 'sym': 'bs',
            'symsize': 3, 'pltgrid': 0, 'res': res, 'boundinglat': 0.}
    Opts['details'] = {'coasts': 1, 'rivers': 0, 'states': 0,
                       'countries': 0, 'ocean': 1, 'fancy': fancy}
    # make the base map with a blue triangle at the pole
    pmagplotlib.plotMAP(FIG['map'], [90.], [0.], Opts)
    Opts['pltgrid'] = -1
    Opts['sym'] = sym
    Opts['symsize'] = size
    if len(dates) > 0:
        Opts['names'] = dates
    if len(lats) > 0:
        # add the lats and lons of the poles
        pmagplotlib.plotMAP(FIG['map'], lats, lons, Opts)
    Opts['names'] = []
    if len(rlats) > 0:
        Opts['sym'] = rsym
        Opts['symsize'] = rsize
        # add the lats and lons of the poles
        pmagplotlib.plotMAP(FIG['map'], rlats, rlons, Opts)
    if plot == 0:
        pmagplotlib.drawFIGS(FIG)
    if ell == 1:  # add ellipses if desired.
        Opts['details'] = {'coasts': 0, 'rivers': 0, 'states': 0,
                           'countries': 0, 'ocean': 0, 'fancy': fancy}
        Opts['pltgrid'] = -1  # turn off meridian replotting
        Opts['symsize'] = 2
        Opts['sym'] = 'g-'
        for ppars in Pars:
            if ppars[2] != 0:
                PTS = pmagplotlib.plotELL(FIG['map'], ppars, 'g.', 0, 0)
                elats, elons = [], []
                for pt in PTS:
                    elons.append(pt[0])
                    elats.append(pt[1])
                # make the base map with a blue triangle at the pole
                pmagplotlib.plotMAP(FIG['map'], elats, elons, Opts)
                if plot == 0:
                    pmagplotlib.drawFIGS(FIG)
    files = {}
    for key in list(FIG.keys()):
        if pmagplotlib.isServer:  # use server plot naming convention
            files[key] = 'LO:_' + locations+ '_POLE_map.' + fmt
        else:  # use more readable naming convention
            files[key] = '{}_POLE_map.{}'.format(locations, fmt)

    if pmagplotlib.isServer:
        black = '#000000'
        purple = '#800080'
        titles = {}
        titles['eq'] = 'LO:_' + locations + '_POLE_map'
        FIG = pmagplotlib.addBorders(FIG, titles, black, purple)
        pmagplotlib.saveP(FIG, files)
    elif plot == 0:
        pmagplotlib.drawFIGS(FIG)
        ans = input(" S[a]ve to save plot, Return to quit:  ")
        if ans == "a":
            pmagplotlib.saveP(FIG, files)
        else:
            print("Good bye")
            sys.exit()
    else:
        pmagplotlib.saveP(FIG, files)


if __name__ == "__main__":
    main()