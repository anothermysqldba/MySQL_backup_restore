#!/usr/bin/python
#
# Copyright (c) 2013, anothermysqldba.blogspot.com  or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# A copy of the GNU General Public License
# Is available here: http://www.gnu.org/licenses/gpl-3.0.txt 
# OR you can write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import os
import errno
import sys, getopt
import subprocess
import commands
from optparse import OptionParser
import time 
from datetime import date
import datetime

############################
# CONFIGURE FOR YOUR SYSTEM#
###########################
# THE ROOT DIRECTORY OF ALL YOUR BACKUPS (DO NOT LEAVE IT AS /tmp/backups)
backup_root_directory = '/tmp/backups/'

# THE LOCATION OF YOUR xtrabackup FILE 
percona_xtrabackup_location = '/bin/innobackupex'

# MYSQL DATA DIR LOCATION
datadir='/var/lib/mysql/'

# TURN DEBUG ON 1 OR OFF 0 OR VERBOSE 3
debug=1

# DEFAULT USERNAME
db_username='root'

# DEFAULT PASSWORD 
db_password="" 

# DEFAULTS FILE
default_file='/etc/my.cnf'

###########################

# Get Current Working Directory
cwddirname, filename = os.path.split(os.path.abspath(__file__))

# Set the location for last checkpoint directory
checkpoint_dir=os.path.join(cwddirname, "last_checkpoint")

# SET THE LOCATION FOR FULLBACKUP DIRECTORY LOCATION
mysqlfullbackupdir =os.path.join(cwddirname, "MYSQL_FULLBACKUP_DIR")

#INCREMENTAL LOG FILE
incremental_run_log="_incremental_runs.log"

#PID FILE
pid = str(os.getpid())
pidfile = cwddirname + "/backup_restore.pid"
if os.path.isfile(pidfile):
    print "%s already exists, exiting" % pidfile
    sys.exit()
else:
    file(pidfile, 'w').write(pid)

# TODAY's DATE
today = date.today()

#CHECK FILE PARSE OPTIONS
# http://www.alexonlinux.com/pythons-optparse-for-human-beings
#PARSER Constants
NAME = "Backup and/or Restore  backup_restore.py "
DESCRIPTION = "This program enables you to backup full and incremental backups then prepare and restore them using Percona's Xtrabackup"
P_NAME=os.path.basename(__file__)
USAGE_A = " --process=[fullbackup,incremental,prepare,restore] --help --version --showcommands=1"
USAGE = "%prog " + USAGE_A 
VERSION = "%prog version 1.0"
DEFAULT_TXT = "You can set DEFAULT at start of the script"

#Arguement Information
parser = OptionParser(usage=USAGE,description=DESCRIPTION,version=VERSION )
parser.add_option("--process", action="store", dest="process",
                  type="string", default=None,
                  help="What would you like to do --process= [fullbackup,incremental,prepare,restore] ")
parser.add_option("--debug", action="store", dest="debug",
                  type="int", default=None,
                  help="TURN DEBUG ON 1 OR OFF 0 OR VERBOSE 3 ")
parser.add_option("--showcommands", action="store", dest="showcommands",
                  type="int", default=None,
                  help="Shows the commands instead of executing them execpt for the restore section because we go through that step by step, for the xtrabackup and rsync that would be preformed")
parser.add_option("--backup_root_directory", action="store", dest="backup_root_directory",
                  type="string", default=backup_root_directory,
                  help="THE ROOT DIRECTORY OF ALL YOUR BACKUPS, You can set DEFAULT at start of the script")
parser.add_option("--percona_xtrabackup_location", action="store", dest="percona_xtrabackup_location",
                  type="string", default= percona_xtrabackup_location,
                  help="THE LOCATION OF YOUR xtrabackup FILE, " + DEFAULT_TXT )
parser.add_option("--datadir", action="store", dest="datadir",
                  type="string", default=datadir,
                  help="MYSQL DATA DIR LOCATION, " + DEFAULT_TXT )
parser.add_option("--username", action="store", dest="username",
                  type="string", default=db_username,
                  help="MySQL Username, " + DEFAULT_TXT )
parser.add_option("--password", action="store", dest="password",
                  type="string", default=db_password,
                  help="MySQL Password, " + DEFAULT_TXT )
parser.add_option("--default_file", action="store", dest="default_file",
                  type="string", default=default_file,
                  help="MySQL my.cnf file location, " + DEFAULT_TXT )
parser.add_option("--options", action="store", dest="percona_options",
                  type="string", default='',
                  help="Additional Options for innobackupex ")


# Gather our Arguements 
options, args = parser.parse_args()

# SET THE DEFAULTS 
if options.backup_root_directory is None:
        options.backup_root_directory=backup_root_directory

if options.datadir is None:
        options.datadir=datadir

if options.debug is None:
  options.debug=debug

if options.showcommands is None:
        options.showcommands=0

if options.username is None:
        options.username=db_username

if options.password is None:
        options.pasword=db_password

if options.default_file is None:
        options.default_file=default_file

if options.percona_options is None:
        options.percona_options=''


# IF ARGUEMENT IS for FULLBACKUP
if options.process == "fullbackup":

        if options.debug > 0: 
		print "We will run a full backup";

	# CREATE THE ROOT BACKUP DIRECTORY IF IT DOES NOT YET EXIST
	#if not os.path.exists(options.backup_root_directory):
	#	os.makedirs(options.backup_root_directory)

	#CREATE A NEW DIRECTORY FOR TODAY
	path=os.path.join(options.backup_root_directory,str(today))
	#if not os.path.exists(path):
	#	os.makedirs(path)

	# CREATE THE CHECKPOINT DIR IF DOES NOT YET EXIST	
	if not os.path.exists(checkpoint_dir):
                os.makedirs(checkpoint_dir)

	# CREATE THE FULLBACKUP FILE WITH LOCATION IN IT 
	with open (mysqlfullbackupdir,'w') as f: f.write (path)

	# SET LOG FILE INFO
	log_file=path + "_fullbackup.log"

	if options.debug > 0:	
		print "Logging information to " + log_file 	

	# THE FULL BACKUP COMMAND HERE 
	# http://www.percona.com/doc/percona-xtrabackup/2.1/innobackupex/creating_a_backup_ibk.html
	# http://anothermysqldba.blogspot.com/2013/06/percona-xtrabackupinnobackupex-backup.html
	command= options.percona_xtrabackup_location + " --defaults-file="+ options.default_file  +" --no-lock --user="+ options.username + " --password="+ options.password +"  --no-timestamp --extra-lsndir="+ checkpoint_dir  +" "+ options.percona_options  + " " + path + " &> " + log_file
	command2= options.percona_xtrabackup_location + " --apply-log  " + path + " &>> " + log_file

	if options.debug > 1:
                print command
		print command2

	# EXCUTE THE COMMAND
	if options.showcommands == 1:
		print command
		print command2

	else:
		subprocess.call( command , stderr=subprocess.STDOUT,shell=True)
		subprocess.call( command2 , stderr=subprocess.STDOUT,shell=True)

	# build the incremental file just in case we use it later
        backup_log = path + incremental_run_log;
        f = open(backup_log,'w')
        f.write('' )
        f.write('\n')
        f.close()

# IF ARGUEMENT IS for INCREMENTAL
elif options.process == "incremental":
	if options.debug > 0:	
		print "We will run an incremental backup";

	# READ FROM mysqlfullbackupdir 
	add_backup_to_this_dir = open(mysqlfullbackupdir, 'r').read()

	# GET THE CURRENT TIMESTAMP FOR A DIR NAME
	# PLACE A RUNTIME DATE in this folder
	ts = time.time()
	incremental_folder = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H%M%S')

	#CREATE A NEW DIRECTORY FOR TODAY
	path=os.path.join(options.backup_root_directory,'INCREMENTAL',str(incremental_folder))
        #path=os.path.join(add_backup_to_this_dir,'INCREMENTAL',str(incremental_folder))
        if not os.path.exists(path):
                os.makedirs(path)

	if options.debug > 0:
                print " I WILL PLACE THE INCREMENTAL BACKUP IN THIS FOLDER " + path 
	logpath=os.path.join( add_backup_to_this_dir)
	log_file= logpath + incremental_run_log
	log_file2= path + incremental_run_log

	command= options.percona_xtrabackup_location + " --incremental --no-lock --user="+ options.username + " --password="+ options.password +"  --no-timestamp  --incremental-basedir="+ checkpoint_dir +" --extra-lsndir="+ checkpoint_dir  +" "+ options.percona_options + "  " + path + " &> " + log_file2

	if options.debug > 0:
                print "Logging information to " + log_file2

	if options.debug > 1:
                print command 

	# EXCUTE THE COMMAND
	if options.showcommands == 1:
		print command

	else:
        	subprocess.call( command , stderr=subprocess.STDOUT,shell=True)


	# LOG THAT WE DID THIS ACTION
	backup_log = add_backup_to_this_dir + incremental_run_log;
	f = open(backup_log,'a')
	f.write(path )
	f.write('\n')
	f.close()	
	if options.debug > 1:
		print " LOOK IN " + backup_log


# IF ARGUEMENT IS for PREPARE the backup to be restored  
elif options.process == "prepare":
	if options.debug > 0:
		print "We will prepare the incrementals and full backup to be restored ";

	# READ FROM mysqlfullbackupdir        
	restore_to_this_dir = open(mysqlfullbackupdir, 'r').read()

	# INCREMENTALS ROOT DIR 
	incremental_root_dirs = restore_to_this_dir + incremental_run_log; 

	if options.debug > 1:
		print "Will prepare in this dir: " + restore_to_this_dir ;


	# Read More here: http://www.percona.com/doc/percona-xtrabackup/2.1/howtos/recipes_xbk_inc.html
	# http://www.percona.com/doc/percona-xtrabackup/2.1/innobackupex/incremental_backups_innobackupex.html
	# Prepare the base backup ie : xtrabackup --prepare --apply-log-only --target-dir=/data/backups/mysql/ 
	command=options.percona_xtrabackup_location = " --apply-log --redo-only  " + restore_to_this_dir + " &>> prepare.log"

	# EXCUTE THE COMMAND
	if options.showcommands == 1:
		print command
	else:
     		subprocess.call( command , stderr=subprocess.STDOUT,shell=True)


	num_lines = sum(1 for line in open(incremental_root_dirs))
	x = 1
	
	with open(incremental_root_dirs ,'r') as f:
		for inc_dir in f:
			inc_dir = inc_dir.replace("\n", "");
			if inc_dir == "":
				continue

				command2=options.percona_xtrabackup_location = " --apply-log --redo-only  " + restore_to_this_dir + " --incremental-dir="+ inc_dir  +" &>> prepare.log"
	
			if options.debug > 1:
                                print "Apply the incremental backup to the full backup  " + command2
	
			# EXCUTE THE COMMAND
			if options.showcommands == 1:
				print command2
			else:
                        	subprocess.call( command2 , stderr=subprocess.STDOUT,shell=True)

			x = x + 1 

			if not inc_dir: continue	
		
			
	command3=options.percona_xtrabackup_location = " --apply-log  " + restore_to_this_dir + " &>> prepare.log"	
        # EXCUTE THE COMMAND
	if options.showcommands == 1:
        	print command3
        else:
        	subprocess.call( command3 , stderr=subprocess.STDOUT,shell=True)
        

# IF ARGUEMENT IS for RESTORE
elif options.process == "restore":

	if options.showcommands == 1:
		print "show command is not relevant here.";	
		sys.exit(1)	

	# READ FROM mysqlfullbackupdir
        restore_from_dir = open(mysqlfullbackupdir, 'r').read()

        if options.debug > 0:
                print "We will restore the incrementals and full backup";

	print"Are you sure you are ready to restore? [Y|N]"
	check= raw_input('--> ')
	check.upper()
	if check== "Y":
		print "OK we will continue and get your feedback as we go... "
	else:
		sys.exit(1)

	print"DID YOU RUN PREPARE ALREADY? [Y|N]"
        check= raw_input('--> ')
        check.upper()
        if check== "Y":
                print "Good just making sure... "
	else:
                sys.exit(1)

	print"CAN I MAKE SURE THE DATABASE IS OFF? [Y|N]"
        check= raw_input('--> ')
        check.upper()
        if check== "Y":
                print "OK shutting down... "
		os.system("/etc/init.d/mysql stop");
	else:
                sys.exit(1)

	print"CAN I REMOVE EVERYTHING IN THE MYSQL DATADIR: " + options.datadir  +  "? [Y|N]"
        check= raw_input('--> ')
        check.upper()
        if check== "Y":
                print "OK REMOVING... from " + options.datadir
		os.system("rm -Rf " + options.datadir);
	else:
                sys.exit(1)

	print"CAN I RESTORE NOW:  (" + restore_from_dir  + ") to the DATADIR: " + options.datadir  +  "? [Y|N]"
        check= raw_input('--> ')
        check.upper()
        if check== "Y":
                print "OK EXECUTING COPY BACK ... "
		# http://www.percona.com/doc/percona-xtrabackup/2.1/innobackupex/incremental_backups_innobackupex.html
		# http://anothermysqldba.blogspot.com/2013/06/percona-xtrabackupinnobackupex-backup.html
		command=options.percona_xtrabackup_location = " --copy-back   " + restore_from_dir 
                subprocess.call( command , stderr=subprocess.STDOUT,shell=True)
        else:
                sys.exit(1)

	print"CAN I UPDATE PERMISSIONS ON THE DATADIR: " + options.datadir  +  "? [Y|N]"
        check= raw_input('--> ')
        check.upper()
        if check== "Y":
                print "OK UPDATING... "
		os.system("chown -R mysql:mysql " + options.datadir);
        else:
                sys.exit(1)

	print"CAN I START THE MYSQL DATABASE? [Y|N]"
        check= raw_input('--> ')
        check.upper() 
        if check== "Y": 
                print "OK STARTING... "
		os.system("/etc/init.d/mysql start");
        else:
                sys.exit(1)



# IF ARGUEMENT IS NOT SET TO WHAT WE WANT 
else:
	print "Better safe than sorry, tell me what you want me to do"
	print P_NAME + USAGE_A
	print "You can run 1 fullbackup a day otherwise remove the previous version"

# REMOVE THE PID FILE
os.unlink(pidfile)
sys.exit(0)
