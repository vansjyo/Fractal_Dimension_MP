# -*- coding: utf-8 -*-
"""ParallelTrial_Nolds.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GIIluvEwYqAPP5Z4U8OemaA3zCd9zgMo

## > Import libraries
"""

## Install and Import packages
import time
import numpy as np
import pandas as pd
from scipy.io import loadmat
from tabulate import tabulate
from sklearn import preprocessing
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter
import multiprocessing as mp
import math
import dill

"""## > VarshaPendyala
> https://github.com/varshapendyala/Manifold-Learning
"""

def intrinsic_est(lookup,original_data):	
	C = correlation_dim(original_data)
	print(c)
	intrinsic_dim = lookup(C)
	print(intrinsic_dim)
	return intrinsic_dim 


def Distance(xi):
	MinDist = 1e20
	MaxDist = 0
	Radius = np.zeros(32)
	for i in range(xi.shape[0]-1,0,-1):
		Distances = DistVectPoint(xi[0:i,:],xi[i,:])
		#print i
		DistanceNoZero = ElimZero(Distances, 1e-10)
		minval = min(DistanceNoZero)
		maxval = max(Distances)
		if MinDist > minval :
			MinDist = minval
		if MaxDist < maxval :
			MaxDist = maxval
	for k in range(32):
		Radius[k] = np.exp(np.log(MinDist)+(k+1)*(np.log(MaxDist)-np.log(MinDist))/32)
	return Radius
	
def ElimZero(Distances,Tolerance):
	SigDist = Distances-Tolerance
	SigDist = ((np.sign(np.sign(SigDist*-1)-0.5))+1)*1e20
	DistanceNoZero = Distances + SigDist
	return DistanceNoZero

def BinFilling(xi,Radius):
	NoPoints = xi.shape[0]
	BinCount = np.zeros(32)
	for i in range(xi.shape[0]-1,0,-1):
		Distances = DistVectPoint(xi[0:i,:],xi[i,:])
		for j in range(32):
			BinCount[j] = BinCount[j] + CountPoints(Distances,Radius[j])
	BinCount = BinCount/((NoPoints)*(NoPoints-1)/2)
	return BinCount

def DistVectPoint(data,point):
	Diffe = np.zeros((data.shape[0],data.shape[1]))
	for i in range(data.shape[1]):
		Diffe[:,i] = data[:,i] - point[i]
	Diffe = Diffe**2
	Distances = np.sum(Diffe,1)
	Distances = np.sqrt(Distances)
	return Distances

def CountPoints(Distances, Threshold):
	NumofPoints = np.size(Distances)
	ThresholdMatr = np.ones(NumofPoints)*Threshold
	CountVect = np.sum(Distances<ThresholdMatr)
	return CountVect

def Slope(Radius,BinCount,centre,high):
	lnRadius = np.log(Radius)
	lnBinCount = np.log(BinCount)
	Max = 0
	Min = lnBinCount[0]
	IntervalHigh = (Max-Min)*high 
	Top = -((Max-Min)*(1-centre)) + (IntervalHigh/2)
	Base = -((Max-Min)*(1-centre)) - (IntervalHigh/2)
	RelDataX = []
	RelDataY = []
 
	for i in range(32):
		if ((lnBinCount[i] >= Base) and (lnBinCount[i]<=Top)):
			RelDataX.append(lnRadius[i])
			RelDataY.append(lnBinCount[i])
			
	RelDataX = np.array(RelDataX)
	RelDataY = np.array(RelDataY)
	P = np.polyfit(RelDataX,RelDataY,1)
	Slope = P[0]
	return Slope

def correlation_dim(d_data):
 
	Radius = Distance(d_data)
	BinCount = BinFilling(d_data,Radius)
	RadiusNormal = Radius/Radius[31]
	#plt.loglog(RadiusNormal,BinCount,basex=np.e,basey=np.e)
	Slp = Slope(Radius,BinCount,0.6,0.125)
	#plt.show()	
	return Slp

def tryme(j, i, x):

    #find FD - capture time 
    start_time = time.time()
    h = correlation_dim(x)
    duration = (time.time() - start_time)
    
    #deleting a band
    x1 = np.delete(x, j, 1)
    
    #find partial FD
    h1 = correlation_dim(x1)
    
    #find absolute difference between FD and partial FD 
    diff = abs(h1-h) 
    
    #sanity check
    print("X shape: ", x.shape, " X1 shape: ", x1.shape)
    print("iteration variable I", i)  
    print("iteration variable J", j)
    print("Difference is: ", diff)
    print("------- Time taken: ", duration, " seconds -------")
    
    return [diff, h1, duration]


## Main - Find optimal Dimension - Supervised

if __name__ == '__main__':
    
    #load data
    img = loadmat('PaviaU.mat')
    img_gt = loadmat('PaviaU_gt.mat')
    img = img['paviaU']
    img_gt = img_gt['paviaU_gt']
    height, width, bands = img.shape[0], img.shape[1], img.shape[2]

    #reshape data to 2-D array and normalize the reflectance values
    img = np.reshape(img, [height*width, bands])
    img_gt = np.reshape(img_gt, [height*width,])
    min_max_scaler = preprocessing.MinMaxScaler()
    img = min_max_scaler.fit_transform(img.astype('float32')) 
    num_classes = len(np.unique(img_gt))
        
    #separate background and selet 2000 points
    img_cp = img
    x = img[img_gt!=0,:]
    x = x[:2000,:]
    
    #x_list = manager.list(x.tolist())
    
    #stoarage
    diff = np.arange(bands*bands*1.0).reshape((bands, bands))*0 + 1
    h1_matrix = np.arange(bands*bands*1.0).reshape((bands, bands))*0 + 1
    dur_matrix = np.arange(bands*bands*1.0).reshape((bands, bands))*0
    table = [] 
    FD_plot = []
   
    #sanity checks
    h = correlation_dim(x)
    print("Number of processors: ", mp.cpu_count())
    print("Number of Classes: ", num_classes)
    print("X shape: ", x.shape) 
    print("FD of X is: ", h)
    
    #setting optimal dimension as 15 so that we can get the etire plot/graph
    opt_dim = 15
    limit = 5
    
    #Iterating after removal of one band with min Fractal change
    for i in range(bands-limit):
    
        #Iterating to find band with min Fractal change
        pool = mp.Pool(24)
        myrange = [(iter, i, x) for iter in range(bands-i)]
        output = pool.starmap(tryme, myrange)
        pool.close()
        pool.join()
        
        #extracting returned parameters
        output_array = np.array(output)
        diff[i,0:(bands-i)] = output_array[:,0]
        h1_matrix[i,0:(bands-i)] = output_array[:,1]
        dur_matrix[i,0:(bands-i)] = output_array[:,2]
        
        #compute index of min difference in FD and partial FD
        min_index_col = np.argmin(diff[i,], axis=0) 
        
        #Store details
        table.append([ i, diff[i,min_index_col], min_index_col, x.shape,  h1_matrix[i,min_index_col]])
        FD_plot.append(h1_matrix[i, min_index_col])
        
        #sanity checks
        print("current x shape: ", x.shape)
        print("min diff(FD) column index: ", min_index_col)
        print("************************ I have completed a loop   *************************")
        
        #reset `x` and `img_cp` after deleting band causing min change in FD or having highest correlation
        x = np.delete(x, min_index_col, 1)
        img_cp = np.delete(img_cp, min_index_col, 1)
        
        #save result
        if i>=70 and i<=(bands-opt_dim-1):
            name_x = "Pavia_test_DR_" + str(bands-i-1) + ".npy"
            name_img = "Pavia_test_DR_img_" + str(bands-i-1) + ".npy"
            np.save(name_x, x)
            np.save(name_img, img_cp)
            

    """## > Results

    ### > Table
    """

    #defining table headers
    headers = ["Iteration", "Minimum fractal Diff", "Band with Min Diff", "New Shape", "New X"]
    print(tabulate(table, headers, tablefmt="github"))
    
    #save the info table in a CSV file
    df = pd.DataFrame(table, columns= headers)
    df.to_csv (r'Pavia_Test_FD_iter.csv', index = False, header=True)

    """### > Plot Difference"""

    #make an array of the min differences (change in FD) 
    min_fd = np.min(diff, axis=1)

    #plot the differnce as function of removed bands
    fig = plt.figure()
    plt.plot(min_fd[:93])
    fig.suptitle('Fractal Dimension Difference vs Bands Removed')
    plt.xlabel('ith iteration (i bands removed)')
    plt.ylabel('Difference in FD')
    
    #save the result
    fig.savefig('Pavia_Test_diff.jpg',dpi=300)
    

    """### > Smooth"""

    #smooth the fractal plot over a zoomed window frame
    y = savgol_filter(min_fd[70:93], 9,3)
    
    #display the smoothed plot and save the results
    fig1 = plt.figure()
    plt.plot(y)
    
    #save result
    fig1.savefig('Pavia_Test_smoothdiff.jpg',dpi=300)
    
    """### > Plot Partial FD"""

    #plot the differnce as function of removed bands
    fig = plt.figure()
    plt.plot(FD_plot[:93])
    fig.suptitle('New Fractal Dimension vs Bands Removed')
    plt.xlabel('ith iteration (i bands removed)')
    plt.ylabel('New Fractal Dimension')
    
    #save the result
    fig.savefig('Pavia_Test_newFD.jpg',dpi=300)
    
    """### > Save time duration """

    #save the duration matrix in a CSV file
    df = pd.DataFrame(dur_matrix)
    df.to_csv (r'Pavia_Test_Duration.csv', index = False)

