import shutil
from datetime import date
from datetime import timedelta
from datetime import datetime
import time
import re
import os
import yaml

# Load configuration

with open("config.yml", 'r') as ymlfile:
    config=yaml.safe_load(ymlfile)

#Constants
TASKS_FILE = config['path']['tasks']
ROUTINES_FILE = config['path']['routines']
REMINDERS_FILE = config['path']['reminders']
REPEAT_FILE = config['path']['repeat']
ARCHIVE_FILE = config['path']['archive']
STATISTICS_FILE = config['path']['statistics']
SPANISHDATEMAPPING = {
        "Mon": "l",
        "Tue": "m",
        "Wed": "x",
        "Thu": "j",
        "Fri": "v",
        "Sat": "s",
        "Sun": "d",

        }

# Manages the recurrence logic so recurring tasks are added to the main task list with the defined frequency
def recurrentTasks():
    #Get date information
        fullDate = time.strftime("%Y-%m-%d")
	monthDate = time.strftime("%m-%d")
	dayDate = time.strftime("%d").lstrip('0')
	weekDate = time.strftime("%a")
	weekDate = SPANISHDATEMAPPING.get(weekDate)

	#Save the content of the current tasks file in order to replicate it later
	with open(TASKS_FILE, 'r') as original:
		data = original.readlines()

	inProject = []
	inRoutine = []
	inReminder = []

	with open(REPEAT_FILE) as old, open('newtest', 'w') as new:
	    for line in old:
	    	# First let's find out if there is a due field
	    	if '@due' in line and '@no' not in line:
					result = re.search('@due\((.*?)\)', line).group(1)
					if result == fullDate or result == monthDate or result == dayDate or weekDate in result:
						# if the due field matches one of the matching rules, it's processed.
						# Now let's check if the task has a project defined
						hasProject = re.search('@project\((.*?)\)', line)
						# Now let's check if the task is from a routine
						isRoutine = re.search('@routine', line)
						# Check if the task is a reminder
						isReminder = re.search('@remind', line)
						# First we clean the task name to remove tags
						tagList = line.split('@')
						finalLineList = [x for x in tagList if not x.startswith('due(') and not x.startswith('project(') and not x.startswith('goal(') and not x.startswith('routine')]
						finalLine = '@'.join(finalLineList)
						if not hasProject and not isReminder:
							# Non-project tasks are inserted right away
							new.write('\t' + finalLine.strip() + '\n')
						elif isReminder:
							inReminder.append(['', '\t' + finalLine.strip() + '\n'])
						else:
							if not isRoutine:
								# In-project tasks are inserted in a list to be dealt with later
								inProject.append([hasProject.group(1)+':', '\t' + finalLine.strip() + '\n'])
							else:
								inRoutine.append([hasProject.group(1)+':', '\t' + finalLine.strip() + '\n'])


	# First we fill the task file
	tasksLeft = list(inProject)

	with open('newtest', 'a') as new:
		# Insert the previously existing tasks in the file. We'll use this loop to find projects and insert in-project tasks
		for line in data:
			new.write(line)
			if line.strip().endswith(':'):
				# The line is a project. We check our in-project list to check if any task belong there
				for task in inProject:
					if task[0].strip().capitalize() in line.strip().capitalize():
						# Task is inserted after the project line, and also removed from the list of tasks left
						new.write(task[1])
						tasksLeft.remove(task)

	if(len(tasksLeft) > 0):
		# if this is true, there are some tasks with non-existing projects.
		# In this case we insert them at the beginning so the user can deal with it faster
		with file('newtest', 'r') as original:
			data = original.read()
		with file('newtest', 'w') as original:
			for task in tasksLeft:
				original.write(task[1])
			original.write(data)

	# Finally we overwrite the old file
	shutil.move('newtest', TASKS_FILE)

	# Now we fill the Routines list
	# tasksInRoutineLeft = list(inRoutine)
    #
	# with open('newRoutines', 'w') as new:
	# 	# Insert the previously existing tasks in the file. We'll use this loop to find projects and insert in-project tasks
	# 	currentProject = 'empty'
	# 	for task in tasksInRoutineLeft:
	# 		if currentProject not in task[0].strip().capitalize():
	# 			if 'empty' not in currentProject:
	# 				new.write('\n')
	# 			new.write(task[0].strip().capitalize() + '\n')
	# 			currentProject = task[0].strip().capitalize()
	# 		new.write(task[1])

	# Finally we overwrite the old file
	# shutil.move('newRoutines', ROUTINES_FILE)
    #
	# # Now we fill the Reminders list
	# tasksInRemindersLeft = list(inReminder)
    #
	# with open('newReminders', 'w') as new:
	# 	new.write('Dirty: true\n')
	# 	# Insert the previously existing tasks in the file. We'll use this loop to find projects and insert in-project tasks
	# 	for task in tasksInRemindersLeft:
	# 		new.write(task[1])
    #
	# # Finally we overwrite the old file
	# shutil.move('newReminders', REMINDERS_FILE)


def setReminders():
	with open(TASKS_FILE, 'r') as tasks:
		for task in tasks:
			if '@remind' in task and '@done' not in task:
				alarmTime = re.search('@remind\((.*?)\)', task).group(1)
				alarmDesc = re.sub(r'@.*\(.*\)', '', task.strip())
				alertDate = datetime.now()
				final_datetime = datetime.strptime(datetime.strftime(alertDate, '%Y %m %d') + ' ' + alarmTime, '%Y %m %d %H:%M')
				remind.new_reminder(final_datetime, alarmDesc)

# Move done tasks in the archive project to an archive file
def archiveDoneTasks():
	with file(TASKS_FILE, 'r') as original:
		data = original.readlines()

	archiveStart = False
	with open(TASKS_FILE, 'w') as old, open(ARCHIVE_FILE, 'a') as archive:
		archive.write("\nArchived on "+time.strftime("%Y-%m-%d")+":\n")
		# We read the file until we found the Archive section.
		for line in data:
			if archiveStart:
				archive.write(line.lstrip())
			else:
				old.write(line)
			if 'Archive:' in line:
				archiveStart = True

# Mark duplicate files as '@late' and removes any duplication
def markDuplicates():
	with file(TASKS_FILE, 'r') as original:
		data = original.readlines()

	i=0
	with open(TASKS_FILE, 'w') as new:
		for line in data:
			i=i+1
			index = line.find('\n')
			if line in data[i:] and line not in ['\n', '\r\n']:
				# The line exists in the data in a future line, and it's not empty
				# If we wanted to mark the line somehow we can do it here
				new.write(line)
			elif (line in data[:i-1] or line[:index] + ' @late' + line[index:] in data[:i-1]) and line not in ['\n', '\r\n']:
				# The line exists previously (we've marked it as @late)
				print 'REMOVED'
			else:
				new.write(line)

def tail(f, n):
	stdin,stdout = os.popen2("tail -n "+n+" "+f)
	stdin.close()
	lines = stdout.readlines(); stdout.close()
	return lines

def generateStatistics():
	# First we need to get the boundaries. In this case, from Monday to Sunday last week.
	lastWeek = date.today() - timedelta(days=7)
	offset = lastWeek.weekday() % 7

	firstDay = lastWeek - timedelta(days=offset)
	lastDay = firstDay + timedelta(days=6)

	habitList = []
	with open(REPEAT_FILE, 'r') as repeat:
		for line in repeat:
			isHabit = re.search('@goal\((.*?)\)', line)
			if isHabit:
				habitList.append([re.sub(r'@.*\(.*\)','', line.replace('\n','').replace('\t','').strip()), int(isHabit.group(1)), 0, 0])

	archive = tail(ARCHIVE_FILE, "500")
	for habit in habitList:
		for archivedItem in archive:
			if habit[0] in archivedItem:
				doneDate = re.search('@done.?\((.*?)\)', archivedItem)
				if doneDate and doneDate.group(1) >= str(firstDay):
					if doneDate.group(1) > str(lastDay):
						habit[3] = habit[3] + 1
					else:
						habit[2] = habit[2] + 1

	with open(STATISTICS_FILE, 'w') as stats:
		stats.write("Baseline stats:\n\n")
		for habit in habitList:
			stats.write(habit[0] + ' ' + str(habit[1]) + ' days \n\n')
		stats.write("Stats for last week ("+str(firstDay) + " to "+str(lastDay) + '):\n\n')
		for habit in habitList:
			stats.write(habit[0] + ' ' + str(habit[2]) + '/' + str(habit[1]) + ' days\n\n')
		stats.write('Stats for current week:\n\n')
		for habit in habitList:
			stats.write(habit[0] + ' ' + str(habit[3]) + '/' + str(habit[1]) + ' days \n\n')

#Main Functions
def main():
	recurrentTasks()
	archiveDoneTasks()

if __name__ == "__main__":
    main()
