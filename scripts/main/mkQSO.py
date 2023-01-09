#standard python
import sys
import os
import shutil
import unittest
from datetime import datetime
import json
import numpy as np
import healpy as hp
import fitsio
import glob
import argparse
from astropy.table import Table,join,unique,vstack
from matplotlib import pyplot as plt
from desitarget.io import read_targets_in_tiles
from desitarget.mtl import inflate_ledger
from desimodel.footprint import is_point_in_desi
import desimodel.footprint as foot
from desitarget import targetmask

#import logging
#logging.getLogger().setLevel(logging.ERROR)


#sys.path.append('../py') #this requires running from LSS/bin, *something* must allow linking without this but is not present in code yet

#from this package
#try:
import LSS.main.cattools as ct
import LSS.common_tools as common
from LSS.globals import main
from LSS.qso_cat_utils import qso_catalog_maker,build_qso_catalog_from_healpix,build_qso_catalog_from_tiles

if os.environ['NERSC_HOST'] == 'cori':
    scratch = 'CSCRATCH'
elif os.environ['NERSC_HOST'] == 'perlmutter':
    scratch = 'PSCRATCH'
else:
    print('NERSC_HOST is not cori or permutter but is '+os.environ['NERSC_HOST'])
    sys.exit('NERSC_HOST not known (code only works on NERSC), not proceeding') 

parser = argparse.ArgumentParser()
parser.add_argument("--basedir", help="base directory for output, default is SCRATCH",default=scratch)
parser.add_argument("--version", help="catalog version; use 'test' unless you know what you are doing!",default='test')
parser.add_argument("--survey", help="e.g., main (for all), DA02, any future DA",default='main')
parser.add_argument("--verspec",help="version for redshifts",default='himalayas')




args = parser.parse_args()
print(args)

basedir = args.basedir
version = args.version
specrel = args.verspec


qsodir = basedir +'/'+args.survey+'/QSO/'+specrel
if not os.path.exists(basedir +'/'+args.survey+'/QSO/'):
    os.mkdir(basedir +'/'+args.survey+'/QSO/')

if not os.path.exists(qsodir):
    os.mkdir(qsodir)
    print('made '+qsodir)

#required columns for importing from zcatalogs, add any as needed
columns = ['TARGETID','ZWARN','ZERR','SPECTYPE']

surpipe = 'main'
if args.survey == 'SV3':
    surpipe = 'sv3'

reldir = '/global/cfs/cdirs/desi/spectro/redux/'+specrel


#make the per tile version; only used for LSS
build_qso_catalog_from_tiles( release=args.verspec, dir_output=qsodir, npool=20, tiles_to_use=None, qsoversion=args.version)
#load the dark time healpix zcatalog, to be used for getting extra columns
zcat = Table(fitsio.read(reldir+'/zcatalog/zpix-'+surpipe+'-dark.fits',columns=columns))
#make the dark time QSO target only QSO catalog
build_qso_catalog_from_healpix( release=args.verspec, survey=surpipe, program='dark', dir_output=qsodir, npool=20, keep_qso_targets=True, keep_all=False,qsoversion=args.version)
#load what was written out and get extra columns
qsofn = qsodir+'QSO_cat_'+specrel+'_'+surpipe+'_dark_healpix_only_qso_targets_v'+args.version+'.fits'
qf = fitsio.read(qsofn)
qcols = list(qf.dtype.names)
kc = ['TARGETID']
for col in columns:
    if col not in qcols:
        kc.append(col)
zcat.keep_columns(kc)
qf = join(qf,zcat,keys=['TARGETID'])
common.write_LSS(qf,qsofn,extname='QSOCAT')
#make the dark time any target type QSO catalog
build_qso_catalog_from_healpix( release=args.verspec, survey=surpipe, program='dark', dir_output=qsodir, npool=20, keep_qso_targets=False, keep_all=False,qsoversion=args.version)
#load what was written out and get extra columns
qsofn = qsodir+'QSO_cat_'+specrel+'_'+surpipe+'_dark_healpix_v'+args.version+'.fits'
qf = fitsio.read(qsofn)
qf = join(qf,zcat,keys=['TARGETID'])
common.write_LSS(qf,qsofn,extname='QSOCAT')
#make the bright time any target type QSO catalog
build_qso_catalog_from_healpix( release=args.verspec, survey=surpipe, program='bright', dir_output=qsodir, npool=20, keep_qso_targets=False, keep_all=False,qsoversion=args.version)
#load the bright time healpix zcatalog, to be used for getting extra columns
zcat = Table(fitsio.read(reldir+'/zcatalog/zpix-'+surpipe+'-bright.fits',columns=columns))
zcat.keep_columns(kc)
#load bright time QSO cat and get extra columns
qsofn = qsodir+'QSO_cat_'+specrel+'_'+surpipe+'_bright_healpix_v'+args.version+'.fits'
qf = fitsio.read(qsofn)
qf = join(qf,zcat,keys=['TARGETID'])
common.write_LSS(qf,qsofn,extname='QSOCAT')


