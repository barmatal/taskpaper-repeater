import shutil
import sys
from datetime import date
from datetime import timedelta
from datetime import datetime
import time
import re
import os

inputFile = sys.argv[1]

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

# Gets the content of a tag
def getTag(tagName, line):
    pattern = '@' + tagName + '\((.*?)\)'
    match = re.search(pattern, line)
    if match:
        return match.group(1)
    else:
        return match

def cleanLine(line):
    tagList = line.split('@')
    finalLineList = [x for x in tagList if not x.startswith('project') and not x.startswith('done')]
    return '@'.join(finalLineList) + '\n'

# Manages the recurrence logic so recurring tasks are added to the main task list with the defined frequency
def recurrentTasks(data):

    # inProject = []
    resultTasks = []

    for line in data:
        # First let's find out if there is a due field
        if getTag('done', line):
            # done -> check if there is recurrence
            dueValue = getTag('due', line)
            if dueValue:
                # done and due -> Check if the due period match
                if dueValue == fullDate or dueValue == monthDate or dueValue == dayDate or weekDate in dueValue:
                    # if the due field matches one of the matching rules, it's processed.
                    # Now let's check if the task has a project defined
                    hasProject = getTag('project', line)
                    # First we clean the task name to remove tags
                    finalLine = cleanLine(line)

                    if not hasProject:
                        # Non-project tasks are inserted right away
                        resultTasks.insert(0, finalLine)
                    else:
                        # In-project tasks are inserted in a list to be dealt with later
                        # inProject.append([hasProject+':', '\t' + finalLine.strip() + '\n'])
                        resultTasks.insert(0, finalLine)
                else:
                    # done, due, not matching
                    resultTasks.append(line)
                # else:
                    # done, not due -> Archive
        else:
            # Not done -> copied to new file
            resultTasks.append(line)

    # # First we fill the task file
    # tasksLeft = list(inProject)

    # with open('newtest', 'a') as new:
    #     # Insert the previously existing tasks in the file. We'll use this loop to find projects and insert in-project tasks
    #     for line in data:
    #         new.write(line)
    #         if line.strip().endswith(':'):
    #             # The line is a project. We check our in-project list to check if any task belong there
    #             for task in inProject:
    #                 if task[0].strip().capitalize() in line.strip().capitalize():
    #                     # Task is inserted after the project line, and also removed from the list of tasks left
    #                     new.write(task[1])
    #                     tasksLeft.remove(task)

    # if(len(tasksLeft) > 0):
    #     # if this is true, there are some tasks with non-existing projects.
    #     # In this case we insert them at the beginning so the user can deal with it faster
    #     with file('newtest', 'r') as original:
    #         data = original.read()
    #     with file('newtest', 'w') as original:
    #         for task in tasksLeft:
    #             original.write(task[1])
    #         original.write(data)

    # # Finally we overwrite the old file
    # shutil.move('newtest', TASKS_FILE)
    return resultTasks

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
    with open(inputFile, 'r') as original:
        data = original.readlines()
    output = recurrentTasks(data)
    # with open(inputFile, 'w') as updated:
    with open('Tareas_output.taskpaper', 'w') as updated:
        for line in output:
            updated.write(line)
    # archiveDoneTasks()

if __name__ == "__main__":
    main()
