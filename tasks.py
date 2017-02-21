import shutil
from datetime import date
from datetime import timedelta
from datetime import datetime
import time
import re
import os

# Load configuration

#Constants
TASKS_FILE = 'Tareas.taskpaper'
REPEAT_FILE = 'Repetir.taskpaper'
ARCHIVE_FILE = 'Archive.taskpaper'
SPANISHDATEMAPPING = {
        "Mon": "l",
        "Tue": "m",
        "Wed": "x",
        "Thu": "j",
        "Fri": "v",
        "Sat": "s",
        "Sun": "d"
        }

#Get current date information
fullDate = time.strftime("%Y-%m-%d")
monthDate = time.strftime("%m-%d")
dayDate = time.strftime("%d").lstrip('0')
weekDate = time.strftime("%a")
weekDate = SPANISHDATEMAPPING.get(weekDate)

# Manages the recurrence logic so recurring tasks are added to the main task list with the defined frequency
def recurrentTasks(data):

    inProject = []

    with open(REPEAT_FILE) as old, open('newtest', 'w') as new:
        for line in old:
            # First let's find out if there is a due field
            if '@due' in line and '@no' not in line:
                result = re.search('@due\((.*?)\)', line).group(1)
                if result == fullDate or result == monthDate or result == dayDate or weekDate in result:
                    # if the due field matches one of the matching rules, it's processed.
                    # Now let's check if the task has a project defined
                    hasProject = re.search('@project\((.*?)\)', line)
                    # First we clean the task name to remove tags
                    tagList = line.split('@')
                    finalLineList = [x for x in tagList if not x.startswith('due(') and not x.startswith('project(') and not x.startswith('done')]
                    finalLine = '@'.join(finalLineList)
                    if not hasProject:
                        # Non-project tasks are inserted right away
                        new.write('\t' + finalLine.strip() + '\n')
                    else:
                        # In-project tasks are inserted in a list to be dealt with later
                        inProject.append([hasProject.group(1)+':', '\t' + finalLine.strip() + '\n'])

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

def tail(f, n):
    stdin,stdout = os.popen2("tail -n "+n+" "+f)
    stdin.close()
    lines = stdout.readlines(); stdout.close()
    return lines

#Main Functions
def main():
    #Save the content of the current tasks file in order to replicate it later
    with open(TASKS_FILE, 'r') as original:
        data = original.readlines()
    recurrentTasks(data)
    archiveDoneTasks()

if __name__ == "__main__":
    main()
