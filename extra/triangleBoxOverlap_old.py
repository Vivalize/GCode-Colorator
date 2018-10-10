x = 0
y = 1
z = 2

def cross(v1, v2):
	dest = [0,0,0]
	dest[0] = v1[1] * v2[2] - v1[2] * v2[1]
	dest[1] = v1[2] * v2[0] - v1[0] * v2[2]
	dest[2] = v1[0] * v2[1] - v1[1] * v2[0]
	return dest

def dot(v1, v2):
	return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
	
def sub(v1, v2):
	dest = [0,0,0]
	dest[0] = v1[0] - v2[0]
	dest[1] = v1[1] - v2[1]
	dest[2] = v1[2] - v2[2]
	return dest
	
def findMinMax(x0, x1, x2):
	minVal = x0
	maxVal = x0
	if (x1 < minVal): minVal = x1
	if (x1 > maxVal): maxVal = x1
	if (x2 < minVal): minVal = x2
	if (x2 > maxVal): maxVal = x2
	return [minVal, maxVal]
	
def planeBoxOverlap(normal, vert, maxbox):
	vmin = [0,0,0]
	vmax = [0,0,0]
	for q in range(x, z+1):
		v = vert[q]
		if (normal[q]>0):
			vmin[q] = -maxbox[q] - v
			vmax[q] = maxbox[q] - v
		else:
			vmin[q] = maxbox[q] - v
			vmax[q] = -maxbox[q] - v
	if (dot(normal, vmin) > 0): return 0
	if (dot(normal, vmax) >= 0): return 1
	return 0
	
def axisTest_X01(a, b, fa, fb, v0, v1, v2, boxHalfSize):
	p0 = a*v0[y] - b*v0[z]
	p2 = a*v2[y] - b*v2[z]
	if (p0 < p2):
		minVal = p0
		maxVal = p2
	else:
		minVal = p2
		maxVal = p0
	rad = fa * boxHalfSize[y] + fb * boxHalfSize[z]
	if (minVal > rad or maxVal < -rad): return 0
	
def axisTest_X2(a, b, fa, fb, v0, v1, v2, boxHalfSize):
	p0 = a*v0[y] - b*v0[z]
	p1 = a*v1[y] - b*v1[z]
	if (p0 < p1):
		minVal = p0
		maxVal = p1
	else:
		minVal = p1
		maxVal = p0
	rad = fa * boxHalfSize[y] + fb * boxHalfSize[z]
	if (minVal > rad or maxVal < -rad): return 0
	
def axisTest_Y02(a, b, fa, fb, v0, v1, v2, boxHalfSize):
	p0 = -a*v0[x] + b*v0[z]
	p2 = -a*v2[x] + b*v2[z]
	if (p0 < p2):
		minVal = p0
		maxVal = p2
	else:
		minVal = p2
		maxVal = p0
	rad = fa * boxHalfSize[x] + fb * boxHalfSize[z]
	if (minVal > rad or maxVal < -rad): return 0
	
def axisTest_Y1(a, b, fa, fb, v0, v1, v2, boxHalfSize):
	p0 = -a*v0[x] + b*v0[z]
	p1 = -a*v1[x] + b*v1[z]
	if (p0 < p1):
		minVal = p0
		maxVal = p1
	else:
		minVal = p1
		maxVal = p0
	rad = fa * boxHalfSize[x] + fb * boxHalfSize[z]
	if (minVal > rad or maxVal < -rad): return 0
	
def axisTest_Z12(a, b, fa, fb, v0, v1, v2, boxHalfSize):
	p1 = a*v1[x] - b*v1[y]
	p2 = a*v2[x] - b*v2[y]
	if (p2 < p1):
		minVal = p2
		maxVal = p1
	else:
		minVal = p1
		maxVal = p2
	rad = fa * boxHalfSize[x] + fb * boxHalfSize[y]
	if (minVal > rad or maxVal < -rad): return 0
	
def axisTest_Z0(a, b, fa, fb, v0, v1, v2, boxHalfSize):
	p0 = a*v0[x] - b*v0[y]
	p1 = a*v1[x] - b*v1[y]
	if (p0 < p1):
		minVal = p0
		maxVal = p1
	else:
		minVal = p1
		maxVal = p0
	rad = fa * boxHalfSize[x] + fb * boxHalfSize[y]
	if (minVal > rad or maxVal < -rad): return 0
	
def triBoxOverlap(boxCenter, boxHalfSize, triVerts):
	v0 = sub(triVerts[0], boxCenter)
	v1 = sub(triVerts[1], boxCenter)
	v2 = sub(triVerts[2], boxCenter)
	
	e0 = sub(v1, v0)
	e1 = sub(v2, v1)
	e2 = sub(v0, v2)
	
	fex = abs(e0[x])
	fey = abs(e0[y])
	fez = abs(e0[z])
	if axisTest_X01(e0[z], e0[y], fez, fey, v0, v1, v2, boxHalfSize) == 0: return 0
	if axisTest_Y02(e0[z], e0[x], fez, fex, v0, v1, v2, boxHalfSize) == 0: return 0
	if axisTest_Z12(e0[y], e0[x], fey, fex, v0, v1, v2, boxHalfSize) == 0: return 0
	
	fex = abs(e1[x])
	fey = abs(e1[y])
	fez = abs(e1[z])
	if axisTest_X01(e1[z], e1[y], fez, fey, v0, v1, v2, boxHalfSize) == 0: return 0
	if axisTest_Y02(e1[z], e1[x], fez, fex, v0, v1, v2, boxHalfSize) == 0: return 0
	if axisTest_Z0(e1[y], e1[x], fey, fex, v0, v1, v2, boxHalfSize) == 0: return 0
	
	fex = abs(e2[x])
	fey = abs(e2[y])
	fez = abs(e2[z])
	if axisTest_X2(e2[z], e2[y], fez, fey, v0, v1, v2, boxHalfSize) == 0: return 0
	if axisTest_Y1(e2[z], e2[x], fez, fex, v0, v1, v2, boxHalfSize) == 0: return 0
	if axisTest_Z12(e2[y], e2[x], fey, fex, v0, v1, v2, boxHalfSize) == 0: return 0
	
	minMax = findMinMax(v0[x], v1[x], v2[x])
	if (minMax[0] > boxHalfSize[x] or minMax[1] < -boxHalfSize[x]): return 0
		
	minMax = findMinMax(v0[y], v1[y], v2[y])
	if (minMax[0] > boxHalfSize[y] or minMax[1] < -boxHalfSize[y]): return 0
	
	minMax = findMinMax(v0[y], v1[y], v2[y])
	if (minMax[0] > boxHalfSize[y] or minMax[1] < -boxHalfSize[y]): return 0
	
	normal = cross(e0, e1)
	if (not planeBoxOverlap(normal, v0, boxHalfSize)): return 0
	
	return 1
	
def faceInVoxel(face, voxel):
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
	
	return triBoxOverlap(boxCenter, boxHalfSize, face)
	
#boxCenter = [0,0,0]
#boxHalfSize = [5,5,5]
#triVerts = [[6,6,6], [20,20,20], [11,11,11]]
#
#print(triBoxOverlap(boxCenter, boxHalfSize, triVerts))
	
	
v1 = [1,2,3]
v2 = [4,5,6]
print(cross(v1, v2))