# ClassScheduleCalendar

ONLY for UC Merced, Berkeley and Riverside Systems.

This project is designed to extract course information, instructor details, and meeting times from a course schedule HTML page. The parsed information is then used to optionally generate `.ics` calendar files for each course.


## Features

- Extracts course title, start date, and end date.
- Extracts instructor name, email, and CRN.
- Extracts meeting details including date range, days of the week, time, location, and class type.
- Optionally generates `.ics` calendar files for the extracted course meeting information.

## Dependencies

- **BeautifulSoup4**: Used for parsing the HTML content.
- **ics**: Used for generating `.ics` calendar files.
- **pytz**: Timezone library used to handle time localization.
- **datetime** and **re**: Standard Python libraries for date manipulation and regular expressions.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/MacroXie04/ClassScheduleCalendar.git
    ```

2. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Place the HTML file containing the course schedule in the root directory of the project (e.g., `index.html`).

2. Run the script:

    ```bash
    python course_schedule_parser.py
    ```

3. The script will process each course and ask if you would like to create a `.ics` calendar file for the course. 

4. The generated calendar files will be saved in the root directory with a name based on the course title.

