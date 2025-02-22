import requests

def schedule_retrieve(term, course_list):
    schedule_list = []
    weirdCourses = []
    initial = requests.get(
        'https://aurora-registration.umanitoba.ca/StudentRegistrationSsb/ssb/registration',
    )
    jsessid = initial.cookies.get('JSESSIONID') 
    bigip = initial.cookies.get('BIGipServer~INB_SSB_Flex~Banner_Self_Service_Registration_BANPROD_pool') 
    # print(initial.cookies)
    # print(bigip)
    # print(jsessid)
    # print("------------------------------------------------------------------------------------------")

    cookies = {
        'JSESSIONID': jsessid,
        # 'JSESSIONID': '0375AE205210D5AF299A3D3BBBDB29CE',
        # 'JSESSIONID': '0F054497B1DA98EB79BF383BB0078825',
        'BIGipServer~INB_SSB_Flex~Banner_Self_Service_Registration_BANPROD_pool': bigip,
        # 'BIGipServer~INB_SSB_Flex~Banner_Self_Service_Registration_BANPROD_pool': '4245749770.64288.0000',
        # 'BIGipServer~INB_SSB_Flex~Banner_Self_Service_Registration_BANPROD_pool': '4245749770.64288.0000',
        # 'TS01c6c21c': '010e840441656c87d50be754efbe377328100e278cf1105cdcc8792cc459755707899d2d14a58aceff1c4324af59151e9744128f07',
    }

    headers1 = {
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://aurora-registration.umanitoba.ca/StudentRegistrationSsb/ssb/term/termSelection?mode=search',
        'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'X-Synchronizer-Token': 'd378c5b1-0180-49be-ba32-1c33dd5ffd41',
        'sec-ch-ua-mobile': '?0',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    params1 = {
        'mode': 'search',
    }

    data1 = {
        'term': term,
        'studyPath': '',
        'studyPathText': '',
        'startDatepicker': '',
        'endDatepicker': '',
        'uniqueSessionId': 'dahb61732862880802',
    }

    requests.post(
        'https://aurora-registration.umanitoba.ca/StudentRegistrationSsb/ssb/term/search',
        cookies=cookies,
        params=params1,
        headers=headers1,
        data=data1,
    )

    # print(response1.text)
    # print('--------------------------------------------------------------------------------------------------------------')

    for courseName in course_list:
        scheduleA = {} 
        scheduleB = {}
        scheduleC = {}
        subj, crse = list(courseName.items())[0]
        response_json = get_Course(cookies, term, subj, crse)

        # Extract the list of courses
        # courses = response_json["data"]
        courses = response_json["data"]
        # print(courses)
        if courses:
            for course in courses:
                class_name = course['subject'] + course['courseNumber'] + course['sequenceNumber']
                if len(course['meetingsFaculty']) > 0:
                    if course['meetingsFaculty'][0]['meetingTime']['beginTime'] is None:
                        continue
                    time = timeFormatConvert(course['meetingsFaculty'][0]['meetingTime']['beginTime'], 
                                            course['meetingsFaculty'][0]['meetingTime']['endTime'])
                    day = daysFormatConvert(course['meetingsFaculty'][0]['meetingTime']['monday'], 
                                            course['meetingsFaculty'][0]['meetingTime']['tuesday'],
                                            course['meetingsFaculty'][0]['meetingTime']['wednesday'], 
                                            course['meetingsFaculty'][0]['meetingTime']['thursday'], 
                                            course['meetingsFaculty'][0]['meetingTime']['friday'])
                enrolled = str(course['enrollment']) + "/" + str(course['maximumEnrollment'])
                wailist =  str(course['waitCount']) + "/" + str(course['waitCapacity'])
                if len(course['faculty']) > 0:
                    instructor = course['faculty'][0]['displayName']
                else:
                    instructor = ""
                if len(course['meetingsFaculty']) > 0:
                    location = course['meetingsFaculty'][0]['meetingTime']['buildingDescription']
                else:
                    location = ""
                crn = "CRN=" + course['courseReferenceNumber']
                status = course['openSection']
                title = course['courseTitle']
                if course['sequenceNumber'][0] == 'A':
                    scheduleA[class_name] = [time, day, crn, enrolled, wailist, instructor, location, status, title]
                elif course['sequenceNumber'][0] == 'B':
                    scheduleB[class_name] = [time, day, crn, enrolled, wailist, instructor, location, status, title]
                if len(course['meetingsFaculty']) == 2: # weird course with two meeting times
                    time = timeFormatConvert(course['meetingsFaculty'][1]['meetingTime']['beginTime'], 
                                            course['meetingsFaculty'][1]['meetingTime']['endTime'])
                    day = daysFormatConvert(course['meetingsFaculty'][1]['meetingTime']['monday'], 
                                            course['meetingsFaculty'][1]['meetingTime']['tuesday'],
                                            course['meetingsFaculty'][1]['meetingTime']['wednesday'], 
                                            course['meetingsFaculty'][1]['meetingTime']['thursday'], 
                                            course['meetingsFaculty'][1]['meetingTime']['friday'])
                    scheduleC[class_name] = [time, day, crn, enrolled, wailist, instructor, location, status, title]
            if len(scheduleA) != 0:
                    schedule_list.append(scheduleA)
            if len(scheduleB) != 0:
                    schedule_list.append(scheduleB)  # separate A and B sections into different dicts to choose only one class from each  
            if len(scheduleC) != 0:
                weirdCourses.append(subj+crse)
                schedule_list.append(scheduleC)
            # print(schedule_list)
            # print("-----------------------------------------------------------")    
        else:
            return (subj+crse, weirdCourses)
    return (schedule_list, weirdCourses)

def get_Course(cookies, term, subj, crse):
    # print(subj + crse)

    headers2 = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'Connection': 'keep-alive',
        # 'Cookie': 'JSESSIONID=29CC92D84A925B6D5D811C609398F48F; BIGipServer~INB_SSB_Flex~Banner_Self_Service_Registration_BANPROD_pool=739377162.64288.0000; TS01c6c21c=010e840441656c87d50be754efbe377328100e278cf1105cdcc8792cc459755707899d2d14a58aceff1c4324af59151e9744128f07',
        'Referer': 'https://aurora-registration.umanitoba.ca/StudentRegistrationSsb/ssb/classSearch/classSearch',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Synchronizer-Token': '1a55dcbc-40e0-4d5e-a23d-afaf826ea2a1',
        'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params2 = {
        'txt_subject': subj,
        'txt_courseNumber': crse,
        'txt_term': term,
        'startDatepicker': '',
        'endDatepicker': '',
        'uniqueSessionId': '4glf81732858879229',
        'pageOffset': '0',
        'pageMaxSize': '10',
        'sortColumn': 'subjectDescription',
        'sortDirection': 'asc',
    }

    response2 = requests.get(
        'https://aurora-registration.umanitoba.ca/StudentRegistrationSsb/ssb/searchResults/searchResults',
        params=params2,
        cookies=cookies,
        headers=headers2,
    )

    # print(response2.url)
    # print(response2.json())
    # print("-----------------------------------------------------------------------------------------------------------------")

    requests.post(
        'https://aurora-registration.umanitoba.ca/StudentRegistrationSsb/ssb/classSearch/resetDataForm',
        cookies=cookies,
        headers=headers2,
    )

    return response2.json()

def timeFormatConvert(startTime, endTime):
    startHour = startTime[0:2]
    startMinute = startTime[2:4]
    endHour = endTime[0:2]
    endMinute = endTime[2:4]

    # start time
    if (int(startHour) < 12):
        newStartTime = startHour + ":" + startMinute + " am"
    elif (int(startHour) == 12):
        newStartTime = startHour + ":" + startMinute + " pm"
    else:
        startHour = int(startHour)%12
        if (startHour < 10):
            startHour = "0" + str(startHour)
        else:
            startHour = str(startHour)

        newStartTime = startHour + ":" + startMinute + " pm"

    # end time
    if (int(endHour) < 12):
        newEndTime = endHour + ":" + endMinute + " am"
    elif (int(endHour) == 12):
        newEndTime = endHour + ":" + endMinute + " pm"
    else:
        endHour = int(endHour)%12
        if (endHour < 10):
            endHour = "0" + str(endHour)
        else:
            endHour = str(endHour)

        newEndTime = endHour + ":" + endMinute + " pm"

    return (newStartTime + "-" + newEndTime)

def daysFormatConvert(monday, tuesday, wednesday, thursday, friday):
    days = ""
    if monday:
        days += "M"
    if tuesday:
        days += "T"
    if wednesday:
        days += "W"
    if thursday:
        days += "R"
    if friday:
        days += "F"
        
    return days


# result, w = schedule_retrieve("202490", [{"COMP": "1020"}])
# print(result)

