import shutil
import sys
from datetime import date, datetime, timedelta
from glob import glob
import time
import re
import os

inputFolder = sys.argv[1]

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

# Gets the content of the freq in date format
def getFreqTagAsDate(doneValue, freqValue):
    doneDate = datetime.strptime(doneValue, "%Y-%m-%d")
    periodCode = freqValue[-1]
    periodAmount = freqValue[:-1]
    basetime = timedelta(days=0)
    if periodCode == 'd':
        baseTime = timedelta(days=+int(periodAmount))
    if periodCode == 'w':
        baseTime = timedelta(days=+int(periodAmount)*7)
    if periodCode == 'm':
        baseTime = timedelta(days=+int(periodAmount)*30)
    if periodCode == 'y':
        baseTime = timedelta(days=+int(periodAmount)*365)

    newDt = doneDate + baseTime

    return newDt.strftime("%Y-%m-%d")

# Removes the "done" and "project" tags from a task
def cleanLine(line):
    tagList = line.split('@')
    finalLineList = [x for x in tagList if not x.startswith('project') and not x.startswith('done')]
    return '@'.join(finalLineList) + '\n'



# Manages the recurrence logic so recurring tasks are added to the main task list with the defined frequency
def recurrentTasks(data):

    resultTasks = []
    archive = False

    for line in data:
        try:
            # First let's find out if there is a done field
            doneValue = getTag('done', line)
            # if we already reached the Archive, we set the Archive flag to true
            if 'Archive:' in line:
                archive = True
            if doneValue and archive:
                # done -> check if there is recurrence
                dueValue = getTag('due', line)
                freqValue = getTag('freq', line)
                if dueValue and not freqValue:
                    # done and due, not freq -> Check if the due period match
                    if dueValue == fullDate or dueValue == monthDate or dueValue == dayDate or weekDate in dueValue:
                        # if the due field matches one of the matching rules, it's processed.
                        # First we clean the task name to remove unwanted
                        finalLine = cleanLine(line)
                        resultTasks.insert(0, finalLine)
                    else:
                        # done, due, not matching -> Keep it for the future due
                        resultTasks.append(line)
                if freqValue:
                    freqDate = getFreqTagAsDate(doneValue, freqValue)
                    if dueValue:
                        # freq and due value. We need to get the dates.
                        if freqDate <= fullDate and dueValue == weekDate:
                            finalLine = cleanLine(line)
                            resultTasks.insert(0, finalLine)
                        else:
                            resultTasks.append(line)
                    else:
                        # freq, not due value.
                        if freqDate <= fullDate:
                            finalLine = cleanLine(line)
                            resultTasks.insert(0, finalLine)
                        else:
                            resultTasks.append(line)
            else:
                # Not done -> copied to new file
                resultTasks.append(line)
        except ValueError:
            resultTasks.append(line + '@ERROR')

    return resultTasks

def getTasksToArchive(data):
    tasksToArchive = []
    archive = False

    for line in data:
        if 'Archive:' in line:
            archive = True
        # First let's find out if there is a due field
        if archive and getTag('done', line) and not getTag('due', line) and not getTag('freq', line):
            # done and no due/freq: Archive this task
            tasksToArchive.append(line)

    return tasksToArchive

#Main Functions
def main():
    # Recursively get all taskpaper file in the input path
    result = [y for x in os.walk(inputFolder) for y in glob(os.path.join(x[0], '*.taskpaper'))]
    archiveTasks = []
    archiveFile = 'Archive.taskpaper'

    for inputFile in result:
        # If this is an archive file, changes the archive file var and skips the processing
        if 'Archive.taskpaper' in inputFile:
            print 'Archive file is ' + inputFile
            archiveFile = inputFile
        else:
            #Save the content of the current tasks file in order to replicate it later
            with open(inputFile, 'r') as original:
                data = original.readlines()

            resultingTasks = recurrentTasks(data)
            archiveTasks = archiveTasks + getTasksToArchive(data)

            if resultingTasks == data:
                print inputFile + ': No changes in task file'
            else:
                print inputFile
                with open(inputFile, 'w') as updated:
                    for line in resultingTasks:
                        updated.write(line.strip() + '\n')

    if len(archiveTasks) == 0:
        print "No archived tasks"
    else:
        with open(archiveFile, 'a') as archive:
            archive.write("\nArchived on "+time.strftime("%Y-%m-%d")+":\n")
            for line in archiveTasks:
                archive.write(line.strip() + '\n')

if __name__ == "__main__":
    main()
