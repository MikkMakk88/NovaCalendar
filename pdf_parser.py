# main function should take a pathname to a pdf file as it's input and return
# a JSON with relevant information

import fitz # import PyMuPDF library (docs: https://pymupdf.readthedocs.io/en/latest/)
import re

#todo: I could try splitting the html strings if there are multiple spaces in them
#todo: I need a slighty more sophisticated method of assigning the what, where and who

def get_pos_data(data):
    """Receive an html document. 
    Return a dict of days and their corresponding left padding."""
    days = ["Mo ", "Tu ", "We ", "Th ", "Fr "]
    days_pos = {}
    # times_pos = {}
    for line in data:
        for day in days:
            if day in line["TEXT"]:
                days_pos[int(line["LEFT_PADDING"]) - 15] = day[:2] # -15 here to add some flexibility with alignment
    # create a sublist of the data starting from the first occurance of time = 09:00 and ending before the second
    start = 0
    stop = 0
    for i in range(len(data)):
        if data[i]["TEXT"] == "09:00":
            if not start:
                start = i
            else:
                stop = i
    data_sublist = data[start:stop]
    times_pos = {}
    prev = ""
    for line in data_sublist:
        if line["TEXT"] == "30":
            time = prev[:3] + "30"
            times_pos[time] = int(line["TOP_PADDING"])
        else:
            prev = line["TEXT"]
            times_pos[line["TEXT"]] = int(line["TOP_PADDING"])
    return (days_pos, times_pos)


def parse_html_data(html):
    """Parse an html file for desired data.
    Return a list of dicts containing the data."""
    match_str = {
        "TEXT" : r'pt">([\w\d /:)(\-]+)</span></p>$',
        "LEFT_PADDING" : r'left:(\d*)pt"',
        "TOP_PADDING" : r'top:(\d*)pt;'
    }
    out = []
    lines = html.split("\n")
    for line in lines:
        d = {}
        try:
            for k in match_str.keys():
                d[k] = re.search(match_str[k], line).group(1)
            out.append(d)
        except AttributeError:
            pass
    return out


# def construct_lesson_info(data):
#     """Receive data parsed from an html file. 
#     Return information about each lesson."""
#     lessons = []
#     for line in data:
#         pass


def main(pathname, debug=False):
    """Receive the path of a pdf schedule.
    Return lesson info found in the file."""   
    doc = fitz.open(pathname)
    page = doc[0]
    html = page.getText("html")
    data = parse_html_data(html)
    days_pos, times_pos = get_pos_data(data)
    lesson_data = []
    for line in data:
        if line["TEXT"] == "09:00":
            break
        lesson_data.append(line)
    # add the DAY value to each element with correct day of week
    for line in lesson_data:
        for val in sorted(days_pos.keys()):
            if int(line["LEFT_PADDING"]) > val:
                line["DAY"] = days_pos[val]
    # group all items together in a list by day of the week and sort them
    time_slots = {"Mo": [], "Tu": [], "We": [], "Th": [], "Fr": []}
    for line in lesson_data:
        if re.match(r"\d\d:\d\d", line["TEXT"]):
            time_slots[line["DAY"]].append(line["TEXT"])
    for line in lesson_data:
        if not re.match(r"\d\d:\d\d", line["TEXT"]):
            day_list = time_slots[line["DAY"]]
            for i in range(0, len(day_list), 2):
                if times_pos[day_list[i]] < int(line["TOP_PADDING"]) < times_pos[day_list[i+1]]:
                    line["START"] = day_list[i]
                    line["END"] = day_list[i+1]
    # now group all lesson elements together
    lessons = []
    for i, line in enumerate(lesson_data):
        if not re.match(r"\d\d:\d\d", line["TEXT"]):
            added = False
            for lesson in lessons:
                if line["DAY"] == lesson["DAY"] and line["START"] == lesson["WHEN_START"]:
                    if i % 3 == 1:
                        lesson["WHO"] = line["TEXT"]
                    elif i % 3 == 2:
                        lesson["WHERE"] = line["TEXT"]
                    added = True
            if not added:
                new_lesson = {}
                new_lesson["WHAT"] = line["TEXT"]
                new_lesson["WHEN_START"] = line["START"]
                new_lesson["WHEN_END"] = line["END"]
                new_lesson["DAY"] = line["DAY"]
                lessons.append(new_lesson)

    if debug:
        print("")
        # for k, v in days_pos.items():
        #     print(k, v)
        # print("")
        # for k, v in times_pos.items():
        #     print(k, v)
        # print("")
        # print(time_slots)
        # print("")
        for line in lesson_data:
            print(line)
        print("")
        for lesson in lessons:
            for k, v in lesson.items():
                print(k, v)
            print("")
        pass


if __name__ == "__main__":
    folder = "pdf_files"
    filename = "schedulegenerator.pdf"
    # filename = "document.pdf"
    fullpath = folder + "/" + filename
    main(fullpath, debug=True)