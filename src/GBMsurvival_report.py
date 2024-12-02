#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import nibabel as nib
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi
import fpdf
from fpdf import FPDF
import time
import seaborn as sns
sns.set_theme(color_codes=True)
from sklearn.linear_model import LinearRegression
from lifelines import KaplanMeierFitter

import matplotlib as mpl
mpl.use('agg')

DESCRIPTION='''
Output pdf report for GBM Survival prediction, respond 22 model
'''

#default values:
modeldir_default='src/data'


def buildArgsParser():
    p = argparse.ArgumentParser(description=DESCRIPTION)
    p.add_argument('-n',action='store',metavar='ename',dest='ename',
                    type=str, required=True, 
                    help='Experiment Name passed from IPP user'
                    )
    p.add_argument('-a',action='store',metavar='flag_noTC',dest='flag_noTC',
                    type=int, required=True, 
                    help=''
                    )
    p.add_argument('-t',action='store',metavar='t1',dest='t1',
                    type=str, required=True, 
                    help='Path to input t1 image filename'
                    )
    p.add_argument('-c',action='store',metavar='t1ce',dest='t1ce',
                    type=str, required=True, 
                    help='Path to input t1ce image filename'
                    )
    p.add_argument('-w',action='store',metavar='t2',dest='t2',
                    type=str, required=True, 
                    help='Path to input t2 image filename'
                    )
    p.add_argument('-f',action='store',metavar='flair',dest='flair',
                    type=str, required=True, 
                    help='Path to input flair image filename'
                    )
    p.add_argument('-m',action='store',metavar='mask',dest='mask',
                    type=str, required=False, 
                    help='Path to input mask image filename'
                    )
    p.add_argument('-s',action='store',metavar='seg',dest='seg',
                    type=str, required=True, 
                    help='Path to input seg image filename'
                    )
    p.add_argument('--segtype',action='store',metavar='segtype',dest='segtype',
                    type=int, required=True, 
                    help='Segm type for reference: 0-user; 1-DeepMedic; 2-FeTS'
                    )
    p.add_argument('--tcinatlas',action='store',metavar='seg_tcinatlas',dest='seg_tcinatlas',
                    type=str, required=False, 
                    help='Path to input TC binary seg in Jacob space'
                    ) 
    p.add_argument('-e',action='store',metavar='fecsv',dest='fecsv',
                    type=str, required=False, 
                    help='Path to input features csv'
                    )
    p.add_argument('-r',action='store',metavar='resultcsv',dest='resultcsv',
                    type=str, required=False, 
                    help='Path to input SPI and Subtype csv'
                    )
    p.add_argument('--modeldir',action='store',metavar='modeldir',dest='modeldir',
                    type=str, required=False, default=modeldir_default,
                    help='Path to output dir (must exist)'
                    )
    p.add_argument('-o',action='store',metavar='outdir',dest='outdir',
                    type=str, required=True, 
                    help='Path to output dir (must exist)'
                    )
    return p


def main(argv):

    parser = buildArgsParser()
    args = parser.parse_args()
    

    
    usemask=1
    ## check for input and output files: 
    if args.mask is None:
        usemask=0        


    ename=args.ename
    flag_noTC=args.flag_noTC
    t1=args.t1    
    t1ce=args.t1ce
    t2=args.t2
    flair=args.flair  
    mask=args.mask  
    seg=args.seg 
    segtype=args.segtype
    seg_tcinatlas=args.seg_tcinatlas
    fecsv=args.fecsv
    resultcsv=args.resultcsv
    # festats_respond=args.festats_respond
    # kmcurve=args.kmcurve
    outdir=args.outdir
    modeldir=args.modeldir
    print(modeldir)
    
    
    print("\nInput info:")
    print("user description:",ename)
    print("flag_noTC (1-noTC):",flag_noTC)
    print("t1:",t1)
    print("t1ce:",t1ce)    
    print("t2:",t2)    
    print("flair:",flair)    
    print("mask:",mask)    
    print("seg:",seg)      
    print("segtype:",segtype)      
    print("seg_tcinatlas:",seg_tcinatlas)      
    print("fe:",fecsv)    
    print("spi:",resultcsv)    
    print("modeldir:",modeldir)  
    print("outdir:",outdir)    

            
    festats_respond=modeldir+'/Features_2293_stats.csv'
    kmcurve=modeldir+'/KMv5.png'
    spi_sur=modeldir+'/SPI_SUR.csv'

    osmatlas1=modeldir+'/Atlas_Sur_NatMed.nii.gz'
    #default:
    hasflagged=0;

    
    for f in [t1,t1ce,t2,flair,seg,festats_respond,kmcurve,osmatlas1]:
        if not os.path.isfile(f):
            print("\nError: Input file (%s) not found"%f)
            exit()

    if flag_noTC==0: 
        for f in [fecsv,resultcsv,seg_tcinatlas]:
            if not os.path.isfile(f):
                print("\nError: Input file (%s) not found"%f)
                exit()
            
    if not os.path.isdir(outdir):
        print("\nError: Output dir (%s) not found"%outdir)
        exit()
        
    #make snapshots
    modlist=['t1','t1ce','t2','flair']
    imglist=[]
    
    imglist.append(nib.load(t1).get_fdata())
    imglist.append(nib.load(t1ce).get_fdata())
    imglist.append(nib.load(t2).get_fdata())
    imglist.append(nib.load(flair).get_fdata())
    
    if usemask==1:
        imgmask=nib.load(mask).get_fdata()
    imgseg=nib.load(seg).get_fdata()
    if flag_noTC==0: 
        imgseg_tcinatlas=nib.load(seg_tcinatlas).get_fdata()
    
    imgatlas=nib.load(ocmatlas1).get_fdata()
    imgatlas_iqar=imgatlas[:,:,:,3]
    
    # get slice of largest tumor core
    # make binary TC mask (if no TC, use WT)
    if  flag_noTC==0:
        imgseg_tc=imgseg.copy()
        imgseg_tc[imgseg_tc==2]=0
        imgseg_tc[imgseg_tc>0]=1
    else:
        imgseg_tc=imgseg.copy()
        imgseg_tc[imgseg_tc==2]=0 #exclude edema
        imgseg_tc[imgseg_tc>0]=1
        
    dimx=imgseg.shape[0]
    dimy=imgseg.shape[1]
    dimz=imgseg.shape[2]
    
    xx=0; volmax=0;
    for i in range (0,dimx):
        vol=np.sum(imgseg_tc[i,:,:])
        if vol>volmax: 
            xx=i
            volmax=vol
    yy=0; volmax=0;
    for i in range (0,dimy):
        vol=np.sum(imgseg_tc[:,i,:])
        if vol>volmax: 
            yy=i
            volmax=vol         
    zz=0; volmax=0;
    for i in range (0,dimz):
        vol=np.sum(imgseg_tc[:,:,i])
        if vol>volmax: 
            zz=i
            volmax=vol    
    
    if usemask==1: 
        maskslicez=imgmask[:,:,zz].copy()
        maskslicex=imgmask[xx,:,:].copy()
        maskslicey=imgmask[:,yy,:].copy()

    segslicez=imgseg[:,:,zz].copy()    
    segslicex=imgseg[xx,:,:].copy()
    segslicey=imgseg[:,yy,:].copy()
    
    
    ##get slice of largest TC in jacob space

    if flag_noTC==0:
        dimxj=imgseg_tcinatlas.shape[0]
        dimyj=imgseg_tcinatlas.shape[1]
        dimzj=imgseg_tcinatlas.shape[2]
        
        xxj=0; volmax=0;
        for i in range (0,dimxj):
            vol=np.sum(imgseg_tcinatlas[i,:,:])
            if vol>volmax: 
                xxj=i
                volmax=vol
                yyj=0; volmax=0;
        for i in range (0,dimyj):
            vol=np.sum(imgseg_tcinatlas[:,i,:])
            if vol>volmax: 
                yyj=i
                volmax=vol         
                zzj=0; volmax=0;
        for i in range (0,dimzj):
            vol=np.sum(imgseg_tcinatlas[:,:,i])
            if vol>volmax: 
                zzj=i
                volmax=vol    

        segslicezj=imgseg_tcinatlas[:,:,zzj].copy()    
        segslicexj=imgseg_tcinatlas[xxj,:,:].copy()
        segsliceyj=imgseg_tcinatlas[:,yyj,:].copy()    
    
    
    
    palette = np.array([[  0,   0,   0],   # black
                    [255,   0,   0],   # red
                    [  0, 255,   0],   # green
                    [  0,   0, 255],   # blue
                    [255, 255, 0]])  # yellow
    
    
    for i in range (0,4):
        mod=modlist[i]
        imgmod=imglist[i]

        # save images with brain mask
        if usemask == 1: 
            plt.figure(figsize=(dimx/100,dimy/100),dpi=100,frameon=False)
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.imshow(imgmod[:,:,zz].T,cmap='gray')
            plt.imshow(palette[maskslicez.T.astype(np.int16)],alpha=0.4,cmap='brg',interpolation='none')
            plt.text(dimx/2,dimy-7,"P",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(dimx/2,7,"A",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(7,dimy/2,"R",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(dimx-7,dimy/2,"L",ha='center',va='center',c='orange',fontsize='x-small')
            plt.plot([0,dimx],[yy,yy],c='white',alpha=0.5,linewidth=0.5)
            plt.plot([xx,xx],[0,dimy],c='white',alpha=0.5,linewidth=0.5)
            plt.savefig('%s/%s_mask_ax.png'%(outdir,mod),dpi=100,bbox_inches='tight',pad_inches=0)
            plt.close()
        
            plt.figure(figsize=(dimy/100,dimz/100),dpi=100,frameon=False)
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.imshow(imgmod[xx,:,:].T,cmap='gray',origin='lower')
            plt.imshow(palette[maskslicex.T.astype(np.int16)],origin='lower',alpha=0.4,cmap='brg',interpolation='none')
            plt.text(dimy/2,dimz-7,"S",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(dimy/2,7,"I",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(7,dimz/2,"A",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(dimy-7,dimz/2,"P",ha='center',va='center',c='orange',fontsize='x-small')
            plt.plot([yy,yy],[0,dimz],c='white',alpha=0.5,linewidth=0.5)
            plt.plot([0,dimy],[zz,zz],c='white',alpha=0.5,linewidth=0.5)
            plt.savefig('%s/%s_mask_sag.png'%(outdir,mod),dpi=100,bbox_inches='tight',pad_inches=0)
            plt.close()
        
    
            plt.figure(figsize=(dimx/100,dimz/100),dpi=100,frameon=False)
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.imshow(imgmod[:,yy,:].T,origin='lower',cmap='gray')
            plt.imshow(palette[maskslicey.T.astype(np.int16)],origin='lower',alpha=0.4,cmap='brg',interpolation='none')
            plt.text(dimx/2,dimz-7,"S",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(dimx/2,7,"I",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(7,dimz/2,"R",ha='center',va='center',c='orange',fontsize='x-small')
            plt.text(dimx-7,dimz/2,"L",ha='center',va='center',c='orange',fontsize='x-small')
            plt.plot([xx,xx],[0,dimz],c='white',alpha=0.5,linewidth=0.5)
            plt.plot([0,dimx],[zz,zz],c='white',alpha=0.5,linewidth=0.5)
            plt.savefig('%s/%s_mask_cor.png'%(outdir,mod),dpi=100,bbox_inches='tight',pad_inches=0)    
            plt.close()
    
        #save images with tumor segm
        plt.figure(figsize=(dimx/100,dimy/100),dpi=100,frameon=False)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
            hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.imshow(imgmod[:,:,zz].T,cmap='gray')
        plt.imshow(palette[segslicez.T.astype(np.int16)],alpha=0.4,cmap='brg',interpolation='none')
        plt.text(dimx/2,dimy-7,"P",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(dimx/2,7,"A",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(7,dimy/2,"L",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(dimx-7,dimy/2,"R",ha='center',va='center',c='orange',fontsize='x-small')
        plt.plot([0,dimx],[yy,yy],c='white',alpha=0.5,linewidth=0.5)
        plt.plot([xx,xx],[0,dimy],c='white',alpha=0.5,linewidth=0.5)
        plt.savefig('%s/%s_seg_ax.png'%(outdir,mod),dpi=100,bbox_inches='tight',pad_inches=0)
        plt.close()
        
    
        plt.figure(figsize=(dimy/100,dimz/100),dpi=100,frameon=False)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
            hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.imshow(imgmod[xx,:,:].T,cmap='gray',origin='lower')
        plt.imshow(palette[segslicex.T.astype(np.int16)],origin='lower',alpha=0.4,cmap='brg',interpolation='none')
        plt.text(dimy/2,dimz-7,"S",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(dimy/2,7,"I",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(7,dimz/2,"P",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(dimy-7,dimz/2,"A",ha='center',va='center',c='orange',fontsize='x-small')
        plt.plot([yy,yy],[0,dimz],c='white',alpha=0.5,linewidth=0.5)
        plt.plot([0,dimy],[zz,zz],c='white',alpha=0.5,linewidth=0.5)
        plt.savefig('%s/%s_seg_sag.png'%(outdir,mod),dpi=100,bbox_inches='tight',pad_inches=0)
        plt.close()
    

        plt.figure(figsize=(dimx/100,dimz/100),dpi=100,frameon=False)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
            hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.imshow(imgmod[:,yy,:].T,origin='lower',cmap='gray')
        plt.imshow(palette[segslicey.T.astype(np.int16)],origin='lower',alpha=0.4,cmap='brg',interpolation='none')
        plt.text(dimx/2,dimz-7,"S",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(dimx/2,7,"I",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(7,dimz/2,"L",ha='center',va='center',c='orange',fontsize='x-small')
        plt.text(dimx-7,dimz/2,"R",ha='center',va='center',c='orange',fontsize='x-small')
        plt.plot([xx,xx],[0,dimz],c='white',alpha=0.5,linewidth=0.5)
        plt.plot([0,dimx],[zz,zz],c='white',alpha=0.5,linewidth=0.5)
        plt.savefig('%s/%s_seg_cor.png'%(outdir,mod),dpi=100,bbox_inches='tight',pad_inches=0)    
        plt.close()
        
    
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    
    ### atlas slice
    if flag_noTC==0:
        plt.figure(figsize=(dimxj/100,dimyj/100),dpi=100,frameon=False)
        plt.gca().set_axis_off()
        plt.gcf().set_facecolor("red")
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                            hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.imshow(imgatlas_iqar[:,:,zzj].T,cmap='YlGnBu') #'gray')#
        plt.text(dimxj/2,dimyj-7,"P",ha='center',va='center',fontsize='x-small')
        plt.text(dimxj/2,7,"A",ha='center',va='center',fontsize='x-small')
        plt.text(7,dimyj/2,"R",ha='center',va='center',fontsize='x-small')
        plt.text(dimxj-7,dimyj/2,"L",ha='center',va='center',fontsize='x-small')
        plt.plot([0,dimxj],[yyj,yyj],c='black',alpha=0.5,linewidth=0.5)
        plt.plot([xxj,xxj],[0,dimyj],c='black',alpha=0.5,linewidth=0.5)
        plt.savefig('%s/iqar_ax.png'%(outdir),dpi=100,bbox_inches='tight',pad_inches=0)
        plt.close()   

        plt.figure(figsize=(dimyj/100,dimzj/100),dpi=100,frameon=False)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                            hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.imshow(imgatlas_iqar[xxj,:,:].T,cmap='YlGnBu',origin='lower',aspect=1.6)
        plt.text(dimyj/2,dimzj-7,"S",ha='center',va='center',fontsize='x-small')
        plt.text(dimyj/2,7,"I",ha='center',va='center',fontsize='x-small')
        plt.text(7,dimzj/2,"A",ha='center',va='center',fontsize='x-small')
        plt.text(dimyj-7,dimzj/2,"P",ha='center',va='center',fontsize='x-small')
        plt.plot([yyj,yyj],[0,dimzj],c='black',alpha=0.5,linewidth=0.5)
        plt.plot([0,dimyj],[zzj,zzj],c='black',alpha=0.5,linewidth=0.5)
        plt.savefig('%s/iqar_sag.png'%(outdir),dpi=100,bbox_inches='tight',pad_inches=0)
        plt.close()


        plt.figure(figsize=(dimxj/100,dimzj/100),dpi=100,frameon=False)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                            hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.imshow(imgatlas_iqar[:,yyj,:].T,origin='lower',cmap='YlGnBu',aspect=1.6)
        plt.colorbar(fraction=0.04)
        plt.text(dimxj/2,dimzj-7,"S",ha='center',va='center',fontsize='x-small')
        plt.text(dimxj/2,7,"I",ha='center',va='center',fontsize='x-small')
        plt.text(7,dimz/2,"R",ha='center',va='center',fontsize='x-small')
        plt.text(dimx-7,dimz/2,"L",ha='center',va='center',fontsize='x-small')
        plt.plot([xxj,xxj],[0,dimzj],c='black',alpha=0.5,linewidth=0.5)
        plt.plot([0,dimxj],[zzj,zzj],c='black',alpha=0.5,linewidth=0.5)
        plt.savefig('%s/iqar_cor.png'%(outdir),dpi=100,bbox_inches='tight',pad_inches=0)    
        plt.close()
        

    if flag_noTC==0:
        dffe=pd.read_csv(festats_respond)
        dftmp=pd.read_csv(fecsv,index_col=False)
        dffe['Feature value']=dftmp.values[0]
        dffe['Flag']=[" " for i in range (0,len(dffe))]
        dffe.loc[dffe['Feature value']>dffe['ReSPOND.max'],'Flag']="H"
        dffe.loc[dffe['Feature value']<dffe['ReSPOND.min'],'Flag']="L"    
        
        dffe_styled=dffe.style.set_table_styles([dict(selector="th",props=[('max-width', '300px')])])
        #dfi.export(dffe_styled,'%s/features_table.png'%outdir,table_conversion = 'matplotlib')
        dfi.export(dffe_styled,'%s/features_table.png'%outdir)
        
        ### get list of Flag L and H
        dffe_flag=dffe[dffe.Flag!=" "][['Feature name','Flag']]
        if len(dffe_flag) > 0:
            hasflagged=1
            dffe_styled=dffe_flag.style.set_table_styles([dict(selector="th",props=[('max-width', '300px')])])
            #dfi.export(dffe_styled,'%s/features_table_flag.png'%outdir,table_conversion = 'matplotlib')
            dfi.export(dffe_styled,'%s/features_table_flag.png'%outdir)    
    
        dfstage=pd.read_csv(resultcsv,index_col=False)    
        stage=dfstage['stage'][0]
        spi=dfstage['SPI'][0]

    
    ############ make personalized survival figures

    spi_table = pd.read_csv(spi_sur)
    spi_vect = np.array(spi_table.iloc[:,0]).reshape(-1,1)
    sur_vect = np.array(spi_table.iloc[:,1]).reshape(-1,1)
    mdl = LinearRegression().fit(spi_vect, sur_vect)
    # mdl.predict(np.array(spi).reshape(-1,1))
    spi_diff = abs(spi_vect - spi)
    nearest_index = np.where(spi_diff == min(spi_diff)[0])
    nearest_index = nearest_index[0][0]

    if nearest_index < 50:
        nearest_index = 50
    elif nearest_index > 1911:
        nearest_index = 1911

    sur_sub = spi_table.iloc[nearest_index - 50: nearest_index + 50, 1]
    kmf = KaplanMeierFitter()
    kmf.fit(sur_sub)

    ci = kmf.confidence_interval_survival_function_
    ts = ci.index
    low, high = np.transpose(ci.values)
    plt.fill_between(ts, low, high, color='gray', alpha=0.3)
    kmf.survival_function_.plot(ax=plt.gca())
    plt.ylabel('Survival probability')
    plt.xlabel('Time (days)')
    plt.legend(["95% confidence interval",'Patient-specific survival function'])
    KM_patient = '%s/KM_patient.png'%(outdir)
    plt.savefig(KM_patient,dpi=100,bbox_inches='tight',pad_inches=0)    
    plt.close()

    sub_df = pd.DataFrame({'Survival':sur_sub, 'Cohort': 'Patient-specific'})
    respond_df = pd.DataFrame({'Survival':spi_table.iloc[:,1], 'Cohort': 'ReSPOND population'})
    all_df = respond_df.append(sub_df)

    sns.violinplot(x="Cohort", y="Survival", data=all_df)
    # sns.stripplot(x="cohort", y="Survival", data=all_df, jitter=True)
    plt.ylabel('Survival (days)')
    plt.xlabel('')
    violins_patient = '%s/violins_patient.png'%(outdir)
    plt.savefig(violins_patient, dpi=100,bbox_inches='tight', pad_inches=0)    
    plt.close()



    ######### func for report
    def create_title(title, pdf):
        
        # Add main title
        pdf.set_font('Helvetica', 'b', 16)  
        pdf.ln(1)
        pdf.write(8, title)
        pdf.ln(10)
        
        # Add date of report
        pdf.set_font('Helvetica', '', 14)
        pdf.set_text_color(r=128,g=128,b=128) #grey
        pdf.write(4, 'Case ID: %s   '%ename)
        # today = time.strftime("%m/%d/%Y")
        # pdf.write(4, f'{today}')
        pdf.ln(10)
    
    def write_to_pdf(pdf, words):        
        # Set text colour, font size, and font type
        pdf.set_text_color(r=0,g=0,b=0)
        pdf.set_font('Helvetica', '', 12)
        pdf.write(5, words)

    def write_title_pdf(pdf, words):        
        # Set text colour, font size, and font type
        pdf.set_text_color(r=0,g=0,b=0)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.write(5, words)

    def write_bold_pdf(pdf, words):        
        # Set text colour, font size, and font type
        pdf.set_text_color(r=0,g=0,b=0)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.write(5, words)

    class PDF(FPDF):
        def footer(self):
            today = time.strftime("%m/%d/%Y")
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, 'Page ' + str(self.page_no()) + '  - CBICA IPP output, ' + str(today), 0, 0, 'C')
            
    # Global Variables
    TITLE = "Novel ML-based Prognostic Subgrouping of Glioblastoma:\nReSPOND 2022 model"
    #WIDTH = 210
    #HEIGHT = 297
    
    WIDTH = 216
    HEIGHT = 279
        
    
    ##########################################
    # Create PDF
    #pdf = PDF() # A4 (210 by 297 mm)
    pdf = PDF('P','mm','Letter') # Letter portrait
    
    # Page1
    pdf.add_page()
    create_title(TITLE, pdf)
    
    # write_to_pdf(pdf,'Input parameters:\n' )
    # for line in '{}/../input_log.txt'.format(outdir):
    #     write_to_pdf(pdf, line)
    #     pdf.ln(1)

    write_title_pdf(pdf,'This report includes the following:\n' )
    pdf.ln(1)
    write_to_pdf(pdf,'1. ML results and flagged features\n')
    pdf.ln(1)
    pdf.write(5,'2. Snapshots of the preprocessed images with brain mask. Users should review these images to approve the quality of the preprocessing.\n')
    pdf.ln(1)
    pdf.write(5,'3. Snapshots of the preprocessed images with tumor segmentation. Users should review these images to approve the quality of the segmentation.\n')
    pdf.ln(1)
    pdf.write(5,'4. Overall Survival Map (OSM) atlas\n')
    pdf.ln(1)
    pdf.write(5,'5. Extracted feature values along with value ranges from the ReSPOND cohort. Users should proceed with caution if the values are flagged to be lower or higher \n')

    pdf.ln(5)
    write_title_pdf(pdf,'Disclaimers:\n' )
    pdf.ln(1)
    write_to_pdf(pdf,'1. This software has been designed for research purposes only and has neither been reviewed nor approved for clinical use by the Food and Drug Administration (FDA) or by any other federal/state agency.\n')
    pdf.ln(1)
    pdf.write(5,'2. This code (excluding dependent libraries) is governed by the license provided in https://www.med.upenn.edu/sbia/software-agreement.html unless otherwise specified.\n')
    pdf.ln(1)
    # pdf.write(5,'3. This paper is currently under review by \x1B[3mNature Medicine\x1B[0m (reference number: NMED-A124673)\n')
    pdf.write(5,'3. This paper is currently under review by')
    pdf.set_font('Helvetica', 'I', 12) 
    pdf.write(5, ' Nature Medicine ')
    pdf.set_font('Helvetica', '', 12)
    pdf.write(5, '(reference number: NMED-A124673)\n')

    # Page2
    pdf.add_page()  
    # pdf.line(10,95,WIDTH-10,95)
    pdf.ln(10)
    write_title_pdf(pdf, "1. ML results and flagged features\n")
    pdf.ln(5)

    pdf.set_text_color(r=0,g=0,b=0)
    pdf.set_font('Helvetica', 'B', 12)
    if flag_noTC==0:
        if stage == 1: pdf.write(5, "Subgroup: I\n")
        elif stage == 2: pdf.write(5, "Subgroup: II\n")
        else: pdf.write(5, "Subgroup: III\n")    
    #    pdf.write(5, "ReSPOND Survival Prediction Index (SPI): %.2f\n"%spi)
        pdf.write(5, " ")
    else:
        write_to_pdf(pdf,"Subgroup: Not Available. Because our model uses features related to the Tumor Core (TC), we cannot apply our model when the TC is too small. Please check preprocessing and tumor segmentation. \n")
    #    pdf.write(5,"Stage: Not Available as tumor core (TC) volume was too small to extract features.\n")
    #    pdf.write(5,"Please check preprocessing and segmentation.\n")
                  
    pdf.ln(2)
    # write_to_pdf(pdf, "The figures below show the survival distribution for the subgroups I,II,III from the ReSPOND 2022 cohort (n=2293). The left panel shows the Kaplan-Meier survival curves. The right panel shows boxplots of the subgroups versus patient survival. On each box, the central line indicates the median, and the bottom and top edges indicate the 25th and 75th percentiles, respectively. The whiskers extend to the most extreme data points not considered outliers. Please refer to the publication for more details [\x1B[3mNature Medicine\x1B[0m reference number: NMED-A124673].")
    write_to_pdf(pdf, "The figures below show the survival distribution for the subgroups I,II,III from the ReSPOND 2022 cohort (n=2293). The left panel shows the Kaplan-Meier survival curves. The right panel shows boxplots of the subgroups versus patient survival. On each box, the central line indicates the median, and the bottom and top edges indicate the 25th and 75th percentiles, respectively. The whiskers extend to the most extreme data points not considered outliers. Please refer to the publication for more details [")
    pdf.set_font('Helvetica', 'I', 12) 
    pdf.write(5, 'Nature Medicine ')
    pdf.set_font('Helvetica', '', 12)
    pdf.write(5, 'reference number: NMED-A124673]\n')
    pdf.ln(5)
    pdf.image(kmcurve, 10, None, WIDTH-70)    

    pdf.ln(5)
    write_bold_pdf(pdf,"Features outside of the ReSPOND range:\n")
    write_to_pdf(pdf,"If any features are listed here, this indicates that these feautres were outside of the typical range we've seen in the ReSPOND cohort. Users should proceed with caution if this is the case.\n")
    if hasflagged == 1:
        pdf.image("%s/features_table_flag.png"%outdir,10,240,w=35)
    elif flag_noTC == 1:
        pdf.ln(2)
        pdf.write(5,"Not Applicable")
    else:
        pdf.ln(2)
        pdf.write(5,"None")    

    pdf.ln(10)
    write_bold_pdf(pdf,"Personalized survival estimate:\n")
    write_to_pdf(pdf,"The figures below show the survival distribution for a patient-matched subset of the ReSPOND cohort. The subset is made up of 100 patients with the nearest SPI values to the user-provided patient. The left panel shows the Kaplan-Meier survival curve with 95% confidence interval. The right panel shows violin plots of patient survival for the overall ReSPOND cohort and patient-matched subset. On each box, the central point indicates the median, and the bottom and top edges indicate the 25th and 75th percentiles, respectively. The whiskers extend to the most extreme data points not considered outliers. \n")
    pdf.ln(5)
    y_fig = FPDF.get_y(pdf)
    pdf.image(KM_patient, 10, y_fig, (WIDTH-70)/2)
    pdf.image(violins_patient, ((WIDTH-70)/2)+20, y_fig, (WIDTH-70)/2) 

    # Page3
    pdf.add_page()    
    write_bold_pdf(pdf, "2. Preprocessed images and brain mask (shown in red). All 3D images can be found in the Results folder for further evaluation.\n")

    #same size for mask and segm
    imgwidth=(HEIGHT-50)/4
    x1=10
    x2=x1+imgwidth+10
    x3=x2+imgwidth+10
    y1=30
    y2=y1+imgwidth+5
    y3=y2+imgwidth+5
    y4=y3+imgwidth+5

    if usemask == 0:
        pdf.ln(10)
        write_to_pdf(pdf,"skipped because skull-stripped images were provided as input\n")
    
    else:
        
        pdf.ln(5)
        write_to_pdf(pdf, "T1\n")
        pdf.image("%s/t1_mask_ax.png"%outdir,x1,y1,imgwidth)
        pdf.image("%s/t1_mask_sag.png"%outdir,x2,y1,imgwidth)
        pdf.image("%s/t1_mask_cor.png"%outdir,x3,y1,imgwidth)
        pdf.ln(57.25)
        pdf.write(5, "T1CE\n")
        pdf.image("%s/t1ce_mask_ax.png"%outdir,x1,y2,imgwidth)
        pdf.image("%s/t1ce_mask_sag.png"%outdir,x2,y2,imgwidth)
        pdf.image("%s/t1ce_mask_cor.png"%outdir,x3,y2,imgwidth)    
        pdf.ln(57.25)
        pdf.write(5, "T2\n")
    
        pdf.image("%s/t2_mask_ax.png"%outdir,x1,y3,imgwidth)
        pdf.image("%s/t2_mask_sag.png"%outdir,x2,y3,imgwidth)
        pdf.image("%s/t2_mask_cor.png"%outdir,x3,y3,imgwidth)
        pdf.ln(57.25)
        pdf.write(5, "FLAIR\n")
        pdf.image("%s/flair_mask_ax.png"%outdir,x1,y4,imgwidth)
        pdf.image("%s/flair_mask_sag.png"%outdir,x2,y4,imgwidth)
        pdf.image("%s/flair_mask_cor.png"%outdir,x3,y4,imgwidth)
    
    # Page4
    pdf.add_page()


    if segtype==0:
        segoption="USER"
    elif segtype==1:
        segoption="DeepMedic[3]"
    else:
        segoption="FeTS[4]"
        
    
    write_bold_pdf(pdf, "3. Tumor segmentation. Snapshot of the largest TC volume slice is shown. Labels follow the BraTS convention, enhancing tumor (ET; Yellow), peritumoral edematous/infiltrated tissue (ED; Green), and necrotic and non-enhancing tumor core (NC; Red). SegmOption=%s\n"%(segoption))
    
    # Add images 
    #pdf.ln(2)
    write_to_pdf(pdf, "T1\n")
    pdf.image("%s/t1_seg_ax.png"%outdir,x1,y1,imgwidth)
    pdf.image("%s/t1_seg_sag.png"%outdir,x2,y1,imgwidth)
    pdf.image("%s/t1_seg_cor.png"%outdir,x3,y1,imgwidth)
    pdf.ln(57.25)
    pdf.write(5, "T1CE\n")
    pdf.image("%s/t1ce_seg_ax.png"%outdir,x1,y2,imgwidth)
    pdf.image("%s/t1ce_seg_sag.png"%outdir,x2,y2,imgwidth)
    pdf.image("%s/t1ce_seg_cor.png"%outdir,x3,y2,imgwidth)    
    pdf.ln(57.25)
    pdf.write(5, "T2\n")

    pdf.image("%s/t2_seg_ax.png"%outdir,x1,y3,imgwidth)
    pdf.image("%s/t2_seg_sag.png"%outdir,x2,y3,imgwidth)
    pdf.image("%s/t2_seg_cor.png"%outdir,x3,y3,imgwidth)
    pdf.ln(57.25)
    pdf.write(5, "FLAIR\n")
    pdf.image("%s/flair_seg_ax.png"%outdir,x1,y4,imgwidth)
    pdf.image("%s/flair_seg_sag.png"%outdir,x2,y4,imgwidth)
    pdf.image("%s/flair_seg_cor.png"%outdir,x3,y4,imgwidth)


    
    # Add Page for atlas and feature. Skip if no TC

    if flag_noTC==0:
        # Page5
        pdf.add_page()    
        write_bold_pdf(pdf, "4.Overall Survival Map (OSM) atlas. The crosshair shows the slices at the largest TC volume.\n")
        # Add images 
        pdf.ln(10)
        # write_to_pdf(pdf, "IQAR atlas\n")
        pdf.image("%s/iqar_ax.png"%outdir,x1,y1,imgwidth-4)
        pdf.image("%s/iqar_sag.png"%outdir,x2-3,y1,imgwidth-4)
        pdf.image("%s/iqar_cor.png"%outdir,x3-6,y1,imgwidth+15)
        pdf.ln(57.25)
        # pdf.write(5, "OSM atlas\n")
        # pdf.image("%s/ssd_ax.png"%outdir,x1,y2,imgwidth-4)
        # pdf.image("%s/ssd_sag.png"%outdir,x2-3,y2,imgwidth-4)
        # pdf.image("%s/ssd_cor.png"%outdir,x3-6,y2,imgwidth+15)    

        # Page6
        pdf.add_page()
        write_bold_pdf(pdf, "5. Radiomic Features")
        pdf.ln(1)
        # Add table
        pdf.image("%s/features_table.png"%outdir,10,20,w=130)
        pdf.ln(220)
    else:
        pdf.add_page()    

    pdf.add_page() 
    write_bold_pdf(pdf, "References\n")
    pdf.set_font('Helvetica', '', 10)
    pdf.write(4,"[1] (Prognostic Subgrouping) Akbari et al. Novel AI-based Prognostic Subgrouping of Glioblastoma: A Multi-center Study, Nat Med, NMED-A124673\n")
    pdf.write(4,"[2] (Preprocessing Pipeline) Davatzikos et al. Cancer imaging phenomics toolkit: quantitative imaging analytics for precision diagnostics and predictive modeling of clinical outcome, J Med Imaging, 5(1):011018, 2018\n")
    pdf.write(4,"[3] (Brain mask) Thakur et al. Brain Extraction on MRI Scans in Presence of Diffuse Glioma: Multi-institutional Performance Evaluation of Deep Learning Methods and Robust Modality-Agnostic Training, Neuroimage. 2020 Oct 15;220:117081.\n")
    pdf.write(4,"[4] (DeepMedic) Kamnitsas et al. Efficient Multi-Scale 3D CNN with Fully Connected CRF for Accurate Brain Lesion Segmentation. Medical Image Analysis, 2016.\n")
    pdf.write(4,"[5] (FeTS) Pati et al. The federated tumor segmentation (FeTS) tool: an open-source solution to further solid tumor research. 2022 Phys. Med. Biol. in press.\n")
    
    # Generate the PDF
    pdf.output("%s/report.pdf"%outdir, 'F')


    print ("Finished\n")

if __name__ == '__main__':
    main(sys.argv[1:])    
    
    
    
    
