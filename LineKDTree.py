import KDTree as kdtree
import sys

class Line:
	def __init__(self, start, stop):
		self.start = start
		self.stop = stop
		self.pts = []
	def other(self, pt):
		if self.start == pt:
			return self.stop
		else:
			return self.start
	def __str__(self):
		return str(self.start) + str(self.stop)
	
	def getPts(self):
		if not self.pts:
			self.pts.append(Pnt(self.start, self))
			self.pts.append(Pnt(self.stop, self))
		return self.pts
		

class Pnt:
	def __init__(self, pt, line):
		self.pt = pt;
		self.line = line;
	def __iter__(self):
		return self.pt.__iter__()

	def __getitem__(self, x):
		return self.pt.__getitem__(x)
		
	def __len__(self):
		return len(self.pt)
		
	def __str__(self):
		return self.pt.__str__()

class LineTree:
	def __init__(self, lines):
		self.num_lines = len(lines)
		pts = []
		for line in lines:
			for pt in line.getPts():
				pts.append(pt)
			
		self.tree = kdtree.create(pts)
	
	# returns the line and point which is has an end point closest to the input
	def nearest_neighbor(self, pt):
		root, dist = self.tree.search_nn( pt)
		print(dist)
		closeest_pt = root.data
		return closeest_pt.pt, closeest_pt.line
		
	def	isempty(self):
		return self.tree.data is None
		
	def RemoveLine(self, line):
	#	print "remove " + str(line)
		for pt in line.getPts():
			self.tree = self.tree.remove(pt)
		self.num_lines = self.num_lines -1

		

if __name__ == "__main__":
	lines = [Line((1,1), (1,0)), Line((0,0),(1,0))]
	tree = LineTree(lines)
	start_point, line = tree.nearest_neighbor([-1000,-1000]);
	tree.RemoveLine(line)
	while not tree.isempty():
		end_point = line.other(start_point)
		start_point, line = tree.nearest_neighbor(end_point);
		tree.RemoveLine(line)
		sys.stdin.read(1)
		print(kdtree.visualize(tree.tree))
		print(tree.num_lines)
		print(start_point)
		print(line)
