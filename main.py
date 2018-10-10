# main
# Created by Marko Ritachka on 1/25/18.
import sys
import math
import ctypes
import os
import ctypes
import time
from PIL import Image

x = 0
y = 1
z = 2
mn = 0
mx = 1

voxelXYres = 100
limitTol = 1.2	#How much bigger should the voxel grid be from the model

_tbo = ctypes.CDLL('lib_tbo.so')
_tbo.triBoxOverlap.argtypes = (ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float))

def faceInVoxel(face, voxel):
	global _tbo
	
	#	face is a list of x,y,z coordinates
	#	voxel is a list of x,y,z [min,max] bounds
	boxCenter = [0,0,0]
	boxCenter[x] = (voxel[x][0] + voxel[x][1])/2
	boxCenter[y] = (voxel[y][0] + voxel[y][1])/2
	boxCenter[z] = (voxel[z][0] + voxel[z][1])/2
	
	boxHalfSize = [0,0,0]
	boxHalfSize[x] = (voxel[x][1] - voxel[x][0])/2
	boxHalfSize[y] = (voxel[y][1] - voxel[y][0])/2
	boxHalfSize[z] = (voxel[z][1] - voxel[z][0])/2
	
	facePoint1 = face[0]
	facePoint2 = face[1]
	facePoint3 = face[2]
		
	threeArray = ctypes.c_float * 3
	result = _tbo.triBoxOverlap(threeArray(*boxCenter), threeArray(*boxHalfSize), threeArray(*facePoint1), threeArray(*facePoint2), threeArray(*facePoint3))
	return int(result)
	
def getModelBounds(faces):
	global limitTol
	modelBounds = [[0,0],[0,0],[0,0]]
	modelBounds[x][mn] = faces[0][0][x]
	modelBounds[x][mx] = faces[0][0][x]
	modelBounds[y][mn] = faces[0][0][y]
	modelBounds[y][mx] = faces[0][0][y]
	modelBounds[z][mn] = faces[0][0][z]
	modelBounds[z][mx] = faces[0][0][z]
	for face in faces:
		for point in face:
			if point[x] < modelBounds[x][mn]: modelBounds[x][mn] = point[x]
			if point[x] > modelBounds[x][mx]: modelBounds[x][mx] = point[x]
			if point[y] < modelBounds[y][mn]: modelBounds[y][mn] = point[y]
			if point[y] > modelBounds[y][mx]: modelBounds[y][mx] = point[y]
			if point[z] < modelBounds[z][mn]: modelBounds[z][mn] = point[z]
			if point[z] > modelBounds[z][mx]: modelBounds[z][mx] = point[z]
	return modelBounds
		
gcodeBounds = [[0,0],[0,0],[0,0]]
setXGcodeBounds = False
setYGcodeBounds = False
setZGcodeBounds = False
def updateGcodeBounds(xVal, yVal, zVal):
	global setXGcodeBounds
	global setYGcodeBounds
	global setZGcodeBounds
	if xVal is not None and not setXGcodeBounds:
		gcodeBounds[x][mn] = xVal
		gcodeBounds[x][mx] = xVal
		setXGcodeBounds = True
	if yVal is not None and not setYGcodeBounds:
		gcodeBounds[y][mn] = yVal
		gcodeBounds[y][mx] = yVal
		setYGcodeBounds = True
	if zVal is not None and not setZGcodeBounds:
		gcodeBounds[z][mn] = zVal
		gcodeBounds[z][mx] = zVal
		setZGcodeBounds = True
		
	else:
		if xVal is not None:
			if xVal < gcodeBounds[x][mn]: gcodeBounds[x][mn] = xVal
			if xVal > gcodeBounds[x][mx]: gcodeBounds[x][mx] = xVal
		if yVal is not None:
			if yVal < gcodeBounds[y][mn]: gcodeBounds[y][mn] = yVal
			if yVal > gcodeBounds[y][mx]: gcodeBounds[y][mx] = yVal
		if zVal is not None:
			if zVal < gcodeBounds[z][mn]: gcodeBounds[z][mn] = zVal
			if zVal > gcodeBounds[z][mx]: gcodeBounds[z][mx] = zVal

# Read the gcode and determine layer height
gcodeLines = [line.rstrip('\n') for line in open(sys.argv[1])]
zHeights = []
finishedStartup = False
reachedEnd = False
for line in gcodeLines:
	if (line[0:13] == ';LAYER_COUNT:'): layerCount = int(line[13:])
	if (line == ';LAYER:0'): finishedStartup = True
	if (line[0:14] == ';TIME_ELAPSED:'): reachedEnd = True
	newLine = line.split(' ')
	if newLine[0] == 'G0' and newLine[-1][0] == 'Z':
		zHeights.append(newLine[-1][1:])
	if finishedStartup and not reachedEnd and (newLine[0] == 'G0' or newLine[0] == 'G1'):
		for niblet in newLine:
			if niblet[0] == 'X': updateGcodeBounds(float(niblet[1:]), None, None)
			if niblet[0] == 'Y': updateGcodeBounds(None, float(niblet[1:]), None)
			if niblet[0] == 'Z': updateGcodeBounds(None, None, float(niblet[1:]))
						
# Read the material file and store colors
materialLines = [line.rstrip('\n') for line in open(sys.argv[3])]
currentMaterial = ''
materialLookup = {}
for line in materialLines:
	if (line[0:7] == 'newmtl '): currentMaterial = line[7:]
	elif (line[0:2] == 'Kd'):
		segments = line.split(' ')
		color = (int(float(segments[1])*255), int(float(segments[2])*255), int(float(segments[3])*255))
		materialLookup[currentMaterial] = color
		
allHeights = []
for index in range(1,len(zHeights)):
	allHeights.append(float(zHeights[index])-float(zHeights[index-1]))
layerHeight = round(max(set(allHeights), key=allHeights.count),12)


# Read the 3d model file
objFile = [line.rstrip('\n') for line in open(sys.argv[2])]
modelVertices = []
modelTextures = []
modelFaces = []
normalizedModelFaces = []
currentMat = ''
for line in objFile:
	line = line.replace('\t','').split(' ')
	
	# Fix weird Meshmixer format 123//123 len=8
	fixedLine = False
	for nibIndex in range(0,len(line)):
		if len(line[nibIndex]) >= 4 and line[nibIndex][int(len(line[nibIndex])/2)-1:int(len(line[nibIndex])/2)+1] == '//':
			line[nibIndex] = line[nibIndex][0:int(len(line[nibIndex])/2)-1]
			fixedLine = True
	if fixedLine: line = list(filter(None, line))
	
	if (len(line) == 2) and line[0] == 'usemtl': currentMat = line[1]
	elif len(line) == 4 and line[0] == 'v':
		xVal = float(line[1])
		yVal = float(line[2])
		zVal = float(line[3])
		modelVertices.append([xVal,yVal,zVal])
	elif len(line) == 7 and line[0] == 'v':
			xVal = float(line[1])
			yVal = float(line[2])
			zVal = float(line[3])
			modelVertices.append([xVal,yVal,zVal])
	elif len(line) == 4 and line[0] == 'f':
		modelFaces.append([
			modelVertices[int(line[1])-1],
			modelVertices[int(line[2])-1],
			modelVertices[int(line[3])-1]	])
		modelTextures.append(currentMat)
	elif len(line) == 5 and line[0] == 'f':
		modelFaces.append([
			modelVertices[int(line[1])-1],
			modelVertices[int(line[2])-1],
			modelVertices[int(line[4])-1]	])
		modelFaces.append([
			modelVertices[int(line[2])-1],
			modelVertices[int(line[3])-1],
			modelVertices[int(line[4])-1]	])
		modelTextures.append(currentMat)
		modelTextures.append(currentMat)
		
def normalizeModelFaces():
	modelBounds = getModelBounds(modelFaces)
	xShift = -((modelBounds[x][mn]+modelBounds[x][mx])/2)
	yShift = -((modelBounds[y][mn]+modelBounds[y][mx])/2)
	zShift = -(modelBounds[z][mn])
	for face in modelFaces:
		newFace = []
		for point in face:
			newPoint = [point[x]+xShift, point[y]+yShift, point[z]+zShift]
			newFace.append(newPoint)
		normalizedModelFaces.append(newFace)

normalizeModelFaces()
modelBounds = getModelBounds(normalizedModelFaces)
xVoxelSize = (limitTol*(modelBounds[x][mx]-modelBounds[x][mn]))/voxelXYres
yVoxelSize = (limitTol*(modelBounds[y][mx]-modelBounds[y][mn]))/voxelXYres
zVoxelSize = layerHeight
# Pad X/Y with limitTol on both sides, but only on top for Z
voxelGrid = [[[(0,0,0,0) for zi in range(layerCount)] for yi in range(voxelXYres)] for xi in range(voxelXYres)]
layerVoxelGrid = [[[(0,0,0,0) for yi in range(voxelXYres)] for xi in range(voxelXYres)] for zi in range(layerCount)]



def getVoxelOfModelPoint(point):
	xVoxelEnd = (-(voxelXYres/2)+1)*xVoxelSize
	xVoxel = 0
	while point[x] > xVoxelEnd:
		xVoxelEnd += xVoxelSize
		xVoxel += 1
		
	yVoxelEnd = (-(voxelXYres/2)+1)*yVoxelSize
	yVoxel = 0
	while point[y] > yVoxelEnd:
		yVoxelEnd += yVoxelSize
		yVoxel += 1
		
	zVoxelEnd = layerHeight
	zVoxel = 0
	while point[z] > zVoxelEnd:
		zVoxelEnd += layerHeight
		zVoxel += 1
	return [xVoxel, yVoxel, zVoxel]
	
def getVoxelBounds(face):
	vox1 = getVoxelOfModelPoint(face[0])
	bounds = [[vox1[x],vox1[x]], [vox1[y],vox1[y]], [vox1[z],vox1[z]]]
	for point in face:
		voxes = getVoxelOfModelPoint(point)
		if voxes[x] < bounds[x][mn]: bounds[x][mn] = voxes[x]
		if voxes[x] > bounds[x][mx]: bounds[x][mx] = voxes[x]
		if voxes[y] < bounds[y][mn]: bounds[y][mn] = voxes[y]
		if voxes[y] > bounds[y][mx]: bounds[y][mx] = voxes[y]
		if voxes[z] < bounds[z][mn]: bounds[z][mn] = voxes[z]
		if voxes[z] > bounds[z][mx]: bounds[z][mx] = voxes[z]
	return bounds
	
def getVoxelProperties(xVal, yVal, zVal):
	xMin = (-(voxelXYres/2)+xVal)*xVoxelSize
	xMax = (-(voxelXYres/2)+xVal+1)*xVoxelSize
	yMin = (-(voxelXYres/2)+yVal)*yVoxelSize
	yMax = (-(voxelXYres/2)+yVal+1)*yVoxelSize
	zMin = zVal*zVoxelSize
	zMax = (zVal+1)*zVoxelSize
	return [[xMin,xMax],[yMin,yMax],[zMin,zMax]]
	
	
print("Fitting model into voxels...")
filledGrid = [[[0 for zi in range(layerCount)] for yi in range(voxelXYres)] for xi in range(voxelXYres)]
for faceIndex in range(0,len(normalizedModelFaces)):
	face = normalizedModelFaces[faceIndex]
	try: texture = materialLookup[modelTextures[faceIndex]]
	except: texture = (255,255,255)
	faceBounds = getVoxelBounds(face)
	for xVal in range(faceBounds[x][mn],faceBounds[x][mx]+1):
		for yVal in range(faceBounds[y][mn],faceBounds[y][mx]+1):
			for zVal in range(faceBounds[z][mn],faceBounds[z][mx]+1):
				if faceInVoxel(face, getVoxelProperties(xVal, yVal, zVal)):
					voxelGrid[xVal][yVal][zVal] = texture
					layerVoxelGrid[zVal][xVal][yVal] = texture
					filledGrid[xVal][yVal][zVal] = 1

exploring = []
for xi in range(0,voxelXYres):
	for yi in range(0,voxelXYres):
		for zi in range(0,layerCount):
			if filledGrid[xi][yi][zi] == 1:
				exploring.append([xi,yi,zi])

def getNeighbors(pixel):
	neighbors = []
	for xi in range(pixel[x]-1,pixel[x]+2):
		for yi in range(pixel[y]-1,pixel[y]+2):
			for zi in range(pixel[z]-1,pixel[z]+2):
				if not (xi == pixel[x] and yi == pixel[y] and zi == pixel[z]):
					if xi>=0 and xi<voxelXYres and yi>=0 and yi<voxelXYres and zi>=0 and zi<layerCount:
						neighbors.append([xi,yi,zi])
	return neighbors
	
def getAverageNeighborColor(pixel):
	colors = []
	for xi in range(pixel[x]-1,pixel[x]+2):
		for yi in range(pixel[y]-1,pixel[y]+2):
			for zi in range(pixel[z]-1,pixel[z]+2):
				if not (xi == pixel[x] and yi == pixel[y] and zi == pixel[z]):
					if xi>=0 and xi<voxelXYres and yi>=0 and yi<voxelXYres and zi>=0 and zi<layerCount:
						if voxelGrid[xi][yi][zi] != (0,0,0,0):
							colors.append(voxelGrid[xi][yi][zi])
	rVal = 0
	gVal = 0
	bVal = 0
	for color in colors:
		rVal += color[0]
		gVal += color[1]
		bVal += color[2]
	rVal = int(rVal/len(colors))
	gVal = int(gVal/len(colors))
	bVal = int(bVal/len(colors))
	return (rVal,gVal,bVal)
	
def numFilledPixels():
	count = 0
	for grid in voxelGrid:
		for row in grid:
			for item in row:
				if item != (0,0,0,0): count += 1
	return count
	
def writeColorMap(suffix):
	for index in range(0,layerCount):
		layer = layerVoxelGrid[index]
		im = Image.new('RGB', (voxelXYres, voxelXYres)).convert("RGBA")
		finalPixels = []
		for grid in layer:
			for pixel in grid:
				finalPixels.append(pixel)
		im.putdata(finalPixels)
		im.save('preview/'+str(index)+suffix+'.png')
		
print("Bleeding colors...")
filled = numFilledPixels()
while filled < voxelXYres*voxelXYres*layerCount:
	newExploring = []
	for pixel in exploring:
		for neighborPixel in getNeighbors(pixel):
			if voxelGrid[neighborPixel[x]][neighborPixel[y]][neighborPixel[z]] == (0,0,0,0):
				newColor = getAverageNeighborColor(neighborPixel)
				voxelGrid[neighborPixel[x]][neighborPixel[y]][neighborPixel[z]] = newColor
				layerVoxelGrid[neighborPixel[z]][neighborPixel[x]][neighborPixel[y]] = newColor
				newExploring.append([neighborPixel[x],neighborPixel[y],neighborPixel[z]])
				filled += 1
	exploring = newExploring

writeColorMap('')