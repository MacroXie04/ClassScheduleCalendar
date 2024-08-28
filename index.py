from bs4 import BeautifulSoup
import re
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz
import os

class listViewWrapper:
    """
    A class to extract course information, instructor details, and meeting times from an HTML page and optionally
    generate .ics calendar files for each course.
    """

    def __init__(self, html):
        # Parse the provided HTML content with BeautifulSoup
        self.html = BeautifulSoup(html, 'html.parser')

        # Extract key information sections from the HTML
        self.course_info = self.html.find('div', class_='list-view-course-info-div')
        self.course_time = str(self.html.find('div', class_='listViewMeetingInformation')).replace('\n', '')
        self.course_instructor = self.html.find('div', class_='listViewInstructorInformation')

        # Store processed results in a dictionary
        self.result = {
            'course_info': self.process_course_info(),
            'instructor_info': self.process_instructor_info(),
            'meeting_info': self.process_meeting_info()
        }

        # Print the processed course information
        print(f'course_info: {self.result}')

        # Prompt the user to create a calendar file for the course
        user_input = input("Do you want to create a calendar file for this course? (y/n): ")
        if user_input.lower() == 'y':
            self.create_course_calendar()

    def process_course_info(self):
        """
        Extract and return course title, start date, and end date from the course information section.
        """
        text = self.course_info.text

        # Define regular expression patterns to extract course details
        course_title_pattern = r"^(.*?)\s*\|"
        class_begin_pattern = r"Class Begin:\s*(\d{2}/\d{2}/\d{4})\s*\|"
        class_end_pattern = r"Class End:\s*(\d{2}/\d{2}/\d{4})"

        # Extract details using regular expressions
        course_title = re.search(course_title_pattern, text.strip()).group(1) if re.search(course_title_pattern, text.strip()) else None
        class_begin = re.search(class_begin_pattern, text).group(1) if re.search(class_begin_pattern, text) else None
        class_end = re.search(class_end_pattern, text).group(1) if re.search(class_end_pattern, text) else None

        # Return the extracted details in a dictionary
        return {
            'course_title': course_title,
            'class_begin': class_begin,
            'class_end': class_end,
        }

    def process_instructor_info(self):
        """
        Extract and return instructor name, email, and CRN from the instructor information section.
        """
        # Define regular expression pattern to extract instructor information
        pattern = r'Instructor:\s*</span><a[^>]+href="mailto:(?P<email>[^"]+)">(?P<instructor>[^<]+)</a>.*?CRN:\s*</span><span[^>]+>(?P<crn>\d+)</span>'

        # Convert BeautifulSoup object to string for pattern matching
        course_instructor_str = str(self.course_instructor)

        # Search for the pattern in the HTML snippet
        match = re.search(pattern, course_instructor_str, re.DOTALL)

        # If a match is found, clean up the extracted information and return it
        if match:
            cleaned_instructor = match.group('instructor').replace('\n', '').strip()
            return {
                'instructor': re.sub(r'\s+', ' ', cleaned_instructor),  # Clean extra spaces
                'instructor_email': match.group('email'),
                'crn': match.group('crn')
            }
        return {}

    def process_meeting_info(self):
        """
        Extract and return meeting details including date range, days of the week, time, location, and class type.
        """
        # Convert BeautifulSoup object to string for pattern matching
        course_time_str = str(self.course_time)

        # Find all matches for meeting times in the HTML
        matches = re.findall(r'<span class="meetingTimes">(.*?)<br/>', course_time_str)

        schedule = []

        for match in matches:
            match = str(match)
            # Extract the date range
            date_range_match = re.search(r"(\d{2}/\d{2}/\d{4}) -- (\d{2}/\d{2}/\d{4})", match)
            date_start, date_end = date_range_match.groups() if date_range_match else (None, None)

            # Extract days of the week
            days_match = re.search(r'role="group" title="Class on: (.*?)"><div', match)
            days = days_match.group(1).split(',') if days_match else []

            # Extract time range using regular expressions
            time_pattern = r'<span>(\d{2})</span>:(<span>\d{2}</span>)\s+(AM|PM)\s+-\s+<span>(\d{2})</span>:(<span>\d{2}</span>)\s+(AM|PM)'
            matches = re.findall(time_pattern, match)

            # Format the start and end time
            time_start = f"{matches[0][0]}:{matches[0][1][6:8]} {matches[0][2]}"
            time_end = f"{matches[0][3]}:{matches[0][4][6:8]} {matches[0][5]}"

            time_start = datetime.strptime(time_start, "%I:%M %p").strftime("%H:%M")
            time_end = datetime.strptime(time_end, "%I:%M %p").strftime("%H:%M")

            # Parse the HTML content with BeautifulSoup for location extraction
            soup = BeautifulSoup(match, 'html.parser')

            # Extract the class type
            type_element = soup.find('span', class_='bold', string='Type:')
            class_type = type_element.find_next_sibling(string=True).strip()

            # Extract the location information
            location_span = soup.find('span', class_='bold', string='Location:')
            building_span = location_span.find_next('span', class_='bold', string='Building:') if location_span else None
            room_span = building_span.find_next('span', class_='bold', string='Room:') if building_span else None

            # Extract the text between the spans
            location = location_span.next_sibling.strip() if location_span else None
            building = building_span.next_sibling.strip() if building_span else None
            room = room_span.next_sibling.strip() if room_span else None

            # Combine the location information
            full_location = f"Campus: {location}, Building: {building}, Room: {room}" if location and building and room else None
            location = full_location.replace('\\xa0', '') if full_location else None

            # Create a dictionary for the meeting info
            meeting_info = {
                "date_start": date_start,
                "date_end": date_end,
                "time_start": time_start,
                "time_end": time_end,
                "days": days,
                "class_type": class_type,
                "location": location
            }

            schedule.append(meeting_info)

        return schedule

    def create_course_calendar(self):
        """
        Create and save .ics calendar files for the course meetings based on extracted information.
        """
        temp = self.result

        course_info = temp['course_info']
        instructor_info = temp['instructor_info']
        meeting_info = temp['meeting_info']

        # Parse course and instructor info
        course_title = course_info.get("course_title", "Unknown Course")
        section = course_info.get("section", "")
        crn = instructor_info.get("crn", "")
        instructor_name = instructor_info.get("instructor", "Unknown Instructor")
        instructor_email = instructor_info.get("instructor_email", "")

        # Generate base file name from course title, removing invalid characters for file names
        base_file_name = re.sub(r'[\\/*?:"<>|]', "", course_title)

        # Define the California time zone
        california_tz = pytz.timezone('America/Los_Angeles')

        file_names = []

        # Parse meeting info and generate .ics files
        for idx, meeting in enumerate(meeting_info):
            # Initialize a calendar for each meeting
            calendar = Calendar()

            date_start = datetime.strptime(meeting["date_start"], "%m/%d/%Y")
            date_end = datetime.strptime(meeting["date_end"], "%m/%d/%Y")
            time_start = datetime.strptime(meeting["time_start"], "%H:%M").time()
            time_end = datetime.strptime(meeting["time_end"], "%H:%M").time()
            days = meeting["days"]
            location = meeting["location"]

            # Generate events for each day in the schedule
            current_date = date_start
            while current_date <= date_end:
                if current_date.strftime("%A") in days:
                    event = Event()
                    event.name = f"{course_title} - {meeting['class_type']}"
                    event.begin = california_tz.localize(datetime.combine(current_date, time_start))
                    event.end = california_tz.localize(datetime.combine(current_date, time_end))
                    event.location = location
                    event.description = (f"Instructor: {instructor_name} ({instructor_email})\n"
                                         f"Section: {section}\n"
                                         f"CRN: {crn}")

                    calendar.events.add(event)

                # Move to the next day
                current_date += timedelta(days=1)

            # Generate a unique file name for each meeting
            file_name = f"{base_file_name}_{meeting['class_type']}.ics"
            counter = 1
            while os.path.exists(file_name):
                file_name = f"{base_file_name}_{idx + 1}_{counter}.ics"
                counter += 1

            # Write the .ics file
            with open(file_name, "w") as f:
                f.writelines(calendar)

            file_names.append(file_name)

        return file_names


if __name__ == '__main__':
    # Read the HTML content from the file
    with open('index.html', 'r') as file:
        content = file.read()

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Find all course divs with the 'listViewWrapper' class
    list_view_divs = soup.find_all('div', class_='listViewWrapper')

    # Extract information from each class
    classes_info = [str(div) for div in list_view_divs]

    # Process each class information
    for class_info in classes_info:
        print("======================================")
        listView = listViewWrapper(class_info)