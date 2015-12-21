import os
import argparse
from time import sleep 
import sys
import time

from bs4 import BeautifulSoup
from urllib2 import urlopen 
from urllib import urlretrieve
import csv

BASE_URL = "http://calphotos.berkeley.edu/cgi-bin/img_query?rel-taxon=begins+with&where-taxon="
IMAGE_BASE_URL = "http://calphotos.berkeley.edu"

def read_csv(file):
	names = []
	with open (file, 'rU') as csvfile:
	    reader = csv.reader(csvfile)
	    for row in reader:
	        names.append(row)
	return names

def plant_urls(plants):
	""" create intial link to plant image index page """
	urls = []

	for plant in plants:
		np = plant[0].rstrip().replace(' ', '+')
		urls.append(BASE_URL + np)
	return urls 

def large_image_urls(urls, limit, log):
	""" on each plant image index page, get the first 'limit' large image urls
		and return a dictionary of plant-names and urls.
		Ex. 
			{'Plant-name' : [url, url, ... ,n],
			 'Plant-name2' : [url, url, ... ,n]}	

		alt-tag name is capitalized.
	 """

	not_found = []
	img_urls = {}
	print "Creating links."
	for url in urls:
		try:
			int_urls = []
			name = url.split('=')[-1].replace('+', ' ').capitalize()
			hyphen_name = name.replace(' ', '-')
			soup = BeautifulSoup(urlopen(url).read())
			# Check if there are any imgs.  Not found page
			# has no img tags.
			if not soup.img:
				print "No images found for " + name
				not_found.append(name)
				pass

			images = soup.find_all(alt=name, limit=limit)
			for image in images:
				int_urls.append(image.parent)

			limit_urls = []
			for url in int_urls:
				limit_urls.append(IMAGE_BASE_URL + url.attrs['href'])

			# if no images found, don't put in the img_urls dict
			if len(limit_urls) == limit:
				img_urls[hyphen_name] = limit_urls

			sleep(1)
		except:
			print "error getting link"
			pass

	print "Finished creating links."

	if log:
		write_log(log, not_found)

	return img_urls

def create_jpg_urls(urls):
	""" take the image urls and create the url to download the jpeg file 
		returns a dictionary
		{'plant-name', [url.jpeg, url.jpeg ... n]}
	"""
	prefix = IMAGE_BASE_URL + '/imgs/512x768/'
	jpg_dict = {}
	for name in urls:
		jpg_urls = []
		for url in urls[name]:
			num = url.split('=')[1]
			num = num.split('+')
			part1 = num[0] + '_' + num[1] + '/'
			part2 = num[2] + '/' + num[3] + '.jpeg' 
			jpg_urls.append(prefix + part1 + part2)
		jpg_dict[name] = jpg_urls

	return jpg_dict

def download_jpgs(urls, folder):
 	folder = add_slash(folder)

 	if(dir_check(folder)):
 		print "Using folder: " + folder

 	for name in urls:
 		i = 0
		print name
 		for url in urls[name]:
 			try:
	 			urlretrieve(url, folder + name + str(i) + '.jpeg', reporthook)
	 			print "\r"	
	 			sleep(1)
	 			i += 1
	 		except: 
	 			print "Error downloading " + url
	 			pass

	print "\nDownload finished"

def reporthook(count, block_size, total_size):
	""" from http://blog.moleculea.com/2012/10/04/urlretrieve-progres-indicator/
	"""
	percent = min(int(count * block_size * 100 / total_size), 100)
	sys.stdout.write("\r%d%%" % (percent))
	sys.stdout.flush()

def add_slash(folder):
	""" Check if folder has trailing slash and append if necessary. """
 	if folder[-1] != '/':
 		folder = folder + '/'
	return folder

def dir_check(folder):
	""" Check if directory exists and create it if not"""
	try:
		if not os.path.exists(folder):
			os.makedirs(folder)
	except:
		print "Error: Could not create directory"
		return False 

	return True

def write_log(log, not_found):
	""" Check for .csv format and write to file """
	if log[-4:] != '.csv':
		log = log + '.csv'

	with open(log, 'wb') as csvfile:
		writer = csv.writer(csvfile, delimiter=' ')
		for plant in not_found:
			name_only = plant.split('/')[-1].replace('-', ' ')
			writer.writerow([name_only])

	print "{0} names logged to {1}".format(len(not_found), log) 
 


def main():
	""" Handle command-line input and run main script """
	parser = argparse.ArgumentParser(description='Scrape calphotos website and download images.')
	parser.add_argument('csv', type=str, help='CSV of binomial names.')
	parser.add_argument('folder', type=str, 
		help='Directory where images will be saved.')
	parser.add_argument('--limit', type=int, metavar='N', 
		help='Number of images to download. Defaults to 5.')
	parser.add_argument('--log', type=str, metavar='File', 
		help='Log file (CSV) for plants not found. If not provided, log is not created.')
	args = parser.parse_args()

	if not args.limit:
		args.limit = 5

	names = read_csv(args.csv)
	urls = plant_urls(names)
	img_urls = large_image_urls(urls, args.limit, args.log)
	jpg_urls = create_jpg_urls(img_urls)
	download_jpgs(jpg_urls, args.folder)


if __name__ == '__main__':
	main()