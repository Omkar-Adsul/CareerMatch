1. Introduction
1.1 Problem Identification
In today's competitive job market, students and job seekers have access to a large number of job and internship opportunities through different websites and platforms. However, finding opportunities that match an individual's education, skills, experience, interests, and preferred location can be difficult and time-consuming.
Many users manually search through multiple job portals and examine each opportunity separately. This can result in:
•	Difficulty finding relevant jobs and internships.
•	Time-consuming manual searching.
•	Mismatch between candidate skills and job requirements.
•	Missing suitable internship or job opportunities.
•	Difficulty comparing multiple opportunities.
•	Lack of personalized recommendations.
The CareerMatch – AI-Powered Job & Internship Recommendation Platform is proposed to address these problems by analyzing the user's profile and recommending suitable job and internship opportunities.
________________________________________
1.2 Problem Statement / Definition
CareerMatch is a web-based platform designed to help students and job seekers find suitable job and internship opportunities according to their education, skills, experience, interests, and preferences.
The system collects and analyzes user profile information and compares it with the requirements of available jobs and internships. Based on the matching process, the system generates personalized recommendations and displays suitable opportunities to the user.
The system also provides facilities for users to manage their profiles, search opportunities, save opportunities, apply for opportunities, and track their applications. An administrator can manage users, jobs, internships, and skills.
________________________________________
1.3 Purpose / Objectives and Goals
Purpose
The main purpose of CareerMatch is to provide a centralized and personalized platform that simplifies the process of finding relevant jobs and internships for students and job seekers.
Objectives
1.	To develop a web-based job and internship recommendation platform.
2.	To allow users to create and manage their profiles.
3.	To store information about users, education, skills, jobs, internships, and applications.
4.	To analyze the user's skills, education, experience, and preferences.
5.	To recommend suitable jobs and internships based on profile matching.
6.	To provide a matching score for recommended opportunities.
7.	To allow users to search and view available opportunities.
8.	To allow users to save and apply for suitable opportunities.
9.	To allow users to track their applications.
10.	To provide an administrator module for managing system data.
11.	To reduce the time and effort required to find relevant opportunities.
Goals
•	Provide personalized recommendations to users.
•	Improve the relevance of job and internship searches.
•	Provide a simple and user-friendly interface.
•	Maintain organized and secure user and opportunity data.
•	Provide an efficient platform for students and job seekers.
________________________________________
1.4 Feasibility Study
A feasibility study determines whether the proposed CareerMatch system can be developed and implemented successfully.
1. Technical Feasibility
The project can be developed using commonly available technologies such as:
•	Frontend: HTML, CSS, JavaScript
•	Backend: Python / Node.js
•	Database: PostgreSQL
•	Development Environment: Visual Studio Code
•	Database Management: pgAdmin
•	Operating System: Windows
These technologies provide the required features for developing a web-based recommendation system. Therefore, the project is technically feasible.
2. Economic Feasibility
CareerMatch can be developed using freely available or open-source software and development tools. The project does not require expensive hardware or software licenses for basic development.
Therefore, the development cost can be kept relatively low, making the project economically feasible.
3. Operational Feasibility
The system is designed with a simple web interface so that students, job seekers, and administrators can use it without requiring advanced technical knowledge.
Users can create profiles, add skills and education, search opportunities, view recommendations, and manage applications.
Therefore, the system is operationally feasible.
4. Schedule Feasibility
The project can be developed in stages:
1.	Requirement analysis
2.	Database design
3.	UI development
4.	Backend development
5.	Recommendation module
6.	Integration
7.	Testing
8.	Documentation
The project can therefore be completed within an academic project schedule.
5. Security Feasibility
The system can implement basic security mechanisms such as:
•	User authentication.
•	Password hashing.
•	Role-based access for users and administrators.
•	Database access control.
•	Validation of user inputs.
Therefore, the required security mechanisms can be implemented using the selected technologies.
Feasibility Conclusion
Based on technical, economic, operational, schedule, and security considerations, the proposed CareerMatch system is feasible for academic development and practical implementation.
________________________________________
1.5 Project Scope and Limitations
Project Scope
The scope of CareerMatch includes the following functionalities:
For Students / Job Seekers:
•	User registration and login.
•	Profile creation and management.
•	Adding educational information.
•	Adding and managing skills.
•	Searching for jobs.
•	Searching for internships.
•	Viewing job and internship details.
•	Receiving personalized recommendations.
•	Viewing matching scores.
•	Saving suitable opportunities.
•	Applying for opportunities.
•	Tracking applications.
For Administrators:
•	Admin login.
•	Managing users.
•	Managing job information.
•	Managing internship information.
•	Managing skills.
•	Managing system data.
•	Monitoring applications and recommendations where required.
Recommendation System:
The recommendation module compares user information such as:
•	Education
•	Skills
•	Experience
•	Interests/preferences
•	Location
with the requirements of available opportunities and generates suitable recommendations.
Project Limitations
1.	The accuracy of recommendations depends on the quality and completeness of user profile information.
2.	The system may initially depend on manually entered or administrator-provided job and internship data.
3.	The system does not guarantee employment or internship selection.
4.	Matching scores are used to indicate profile-opportunity similarity and do not represent an employer's final selection decision.
5.	The initial project may not include direct integration with every external job portal.
6.	Real-time job availability may depend on how opportunity data is updated.
7.	Advanced AI/ML capabilities can be extended in future versions.
8.	The project is primarily designed as an academic web application and may require additional infrastructure for large-scale production deployment.



















2. Requirement Specification
2.1 System Requirements
The following hardware and software requirements are sufficient for developing and running the CareerMatch – AI-Powered Job & Internship Recommendation Platform.
A. Hardware Requirements
Component	Minimum Requirement	Recommended
Processor	Intel Core i3 / equivalent	Intel Core i5 or higher
RAM	4 GB	8 GB or higher
Storage	10 GB free space	20 GB or more
Display	1366 × 768	1920 × 1080
Network	Internet connection	Broadband/Wi-Fi
Input	Keyboard and Mouse	Keyboard and Mouse
B. Software Requirements
Software	Requirement
Operating System	Windows 10/11
Web Browser	Google Chrome / Microsoft Edge / Firefox
Code Editor	Visual Studio Code
Database	PostgreSQL
Database Management	pgAdmin
Version Control	Git / GitHub
Backend Runtime	Python / Node.js
Frontend	HTML, CSS, JavaScript
Server / Device Specification
For academic development, CareerMatch can run on a local development computer.
Application Server:
•	Windows 10/11
•	Minimum 4 GB RAM
•	Minimum 10 GB available storage
•	Python/Node.js runtime
Database Server:
•	PostgreSQL
•	Can run on the same computer during development.
•	A separate database server can be used for future deployment.
________________________________________
2.2 Technical Requirements
A. Programming Languages
Technology	Purpose
HTML	Structure of web pages
CSS	Styling and page layout
JavaScript	Client-side interaction and validation
Python / Node.js	Backend development and server-side processing
SQL	Database operations and queries
B. Database
PostgreSQL is used to store and manage the system data.
The database can contain information related to:
•	Users
•	Education
•	Skills
•	Jobs
•	Internships
•	Applications
•	Recommendations
C. Development Tools
•	Visual Studio Code – Code development
•	PostgreSQL – Database management
•	pgAdmin – Database administration
•	Git – Version control
•	GitHub – Source-code repository and project management
•	Web Browser – Testing the web application
D. Recommendation Technology
The recommendation module analyzes information such as:
•	User education
•	Skills
•	Experience
•	Interests/preferences
•	Location
The system compares these details with job and internship requirements and calculates a matching score to generate recommendations.
________________________________________
2.3 Functional Requirements
Functional requirements describe the operations that the CareerMatch system must perform.
1. User Registration
The system shall allow a new user to create an account by providing required information such as:
•	Name
•	Email
•	Password
•	Contact information
2. User Login
The system shall allow registered users to log in using their credentials.
3. Profile Management
The user shall be able to:
•	Create a profile.
•	Update profile information.
•	Add educational qualifications.
•	Add skills.
•	Update preferences and location.
•	Manage experience information.
4. Skill Management
The system shall allow users to add relevant skills to their profile.
The system shall maintain information such as:
•	Skill name
•	Skill category
•	Skill level
5. Job Search
Users shall be able to search and view available job opportunities based on relevant criteria such as:
•	Job title
•	Location
•	Skills
•	Experience
•	Job type
6. Internship Search
Users shall be able to search and view available internship opportunities based on:
•	Internship title
•	Location
•	Skills
•	Duration
•	Stipend
7. Job and Internship Recommendations
The system shall analyze the user's profile and compare it with available opportunities.
The system shall generate recommendations based on the degree of similarity between:
User Profile → Opportunity Requirements
8. Matching Score
The system shall calculate a matching score for recommended opportunities.
For example:
Python Developer — 92% Match
The score is intended to help users understand how closely an opportunity matches their profile.
9. Save Opportunity
Users shall be able to save suitable jobs or internships for later reference.
10. Apply for Opportunity
Users shall be able to initiate an application for a selected job or internship.
11. Application Tracking
Users shall be able to view the status of their applications, such as:
•	Applied
•	Under Review
•	Shortlisted
•	Rejected
•	Selected
12. Administrator Login
The system shall provide a separate administrative interface with appropriate access control.
13. User Management
The administrator shall be able to view and manage registered users.
14. Job Management
The administrator shall be able to:
•	Add jobs.
•	Update jobs.
•	Delete jobs.
•	Manage job information.
15. Internship Management
The administrator shall be able to:
•	Add internships.
•	Update internships.
•	Delete internships.
•	Manage internship information.
16. Skill Management
The administrator shall be able to manage the skills available in the system.
17. Database Management
The system shall store and retrieve user, opportunity, application, and recommendation information from the PostgreSQL database.
________________________________________
2.4 Data Requirements
A. User Data
The system shall store:
•	User ID
•	Name
•	Email
•	Password hash
•	Phone number
•	Location
•	User role
B. Education Data
The system shall store:
•	Education ID
•	User ID
•	Degree
•	Field of study
•	Institution
•	Graduation year
C. Skill Data
The system shall store:
•	Skill ID
•	Skill name
•	Skill category
•	User skill level where applicable
D. Job Data
The system shall store:
•	Job ID
•	Job title
•	Company
•	Location
•	Description
•	Required experience
•	Salary
•	Job type
•	Required skills
E. Internship Data
The system shall store:
•	Internship ID
•	Internship title
•	Company
•	Location
•	Description
•	Duration
•	Stipend
•	Required skills
F. Application Data
The system shall store:
•	Application ID
•	User ID
•	Opportunity ID
•	Opportunity type
•	Application date
•	Application status
G. Recommendation Data
The system shall store:
•	Recommendation ID
•	User ID
•	Opportunity ID
•	Opportunity type
•	Matching score
•	Recommendation creation date
________________________________________
Performance Requirements
1.	The system should provide a response within a reasonable time for normal user operations.
2.	Database queries should be optimized to retrieve information efficiently.
3.	Recommendation results should be generated without unnecessary delay.
4.	The system should support multiple users during normal academic/project usage.
5.	The database should maintain data consistency when users update their profiles or applications.
Security Requirements
1.	User passwords should be stored using secure password hashing, rather than plain text.
2.	The system should provide authentication for registered users.
3.	Administrator functions should be accessible only to authorized administrators.
4.	User data should not be accessible to unauthorized users.
5.	Input data should be validated to reduce invalid or malicious input.
6.	Database access should use appropriate authentication and permissions.
7.	User sessions should be managed securely.
8.	Sensitive information should not be unnecessarily displayed to other users.
Data Backup and Recovery
•	Important database information should be backed up regularly.
•	Database backup can be maintained using PostgreSQL backup facilities.
•	In case of data loss, the database can be restored from a valid backup.
Overall requirement: The system should provide a secure, reliable, and efficient platform for managing user profiles and recommending suitable job and internship opportunities.













3. Database Design
The CareerMatch – AI-Powered Job & Internship Recommendation Platform requires a structured relational database to store user profiles, education, skills, job opportunities, internships, applications, and recommendations.
________________________________________
3.1 Identify End Users of the System
CareerMatch has two main categories of end users:
1. Student / Job Seeker
The Student/Job Seeker is the primary user of the system.
The user can:
•	Register and log in.
•	Create and update their profile.
•	Add educational information.
•	Add and manage skills.
•	Search for jobs.
•	Search for internships.
•	View job and internship details.
•	Receive personalized recommendations.
•	View matching scores.
•	Save suitable opportunities.
•	Apply for opportunities.
•	Track application status.
2. Administrator
The Administrator manages and maintains the system.
The administrator can:
•	Log in to the administrative section.
•	Manage registered users.
•	Add, update, and delete jobs.
•	Add, update, and delete internships.
•	Manage skills.
•	Manage opportunity information.
•	Monitor system data.
End User Summary
End User	Main Responsibilities
Student / Job Seeker	Profile management, skills, education, searching, recommendations, applications
Administrator	User management, job management, internship management, skill and system management
________________________________________
3.2 Identify Entities and Attributes Through ER Diagram
The following entities are used in the CareerMatch database.
1. USER
The USER entity stores information about registered users.
Attributes:
•	user_id – Primary Key
•	name
•	email
•	password_hash
•	phone
•	location
•	role
________________________________________
2. EDUCATION
The EDUCATION entity stores the educational qualifications of users.
Attributes:
•	education_id – Primary Key
•	user_id – Foreign Key
•	degree
•	field
•	institution
•	graduation_year
________________________________________
3. SKILL
The SKILL entity stores skills available in the system.
Attributes:
•	skill_id – Primary Key
•	skill_name
•	category
________________________________________
4. USER_SKILL
USER_SKILL is an associative entity that connects users with their skills.
Attributes:
•	user_id – Primary Key / Foreign Key
•	skill_id – Primary Key / Foreign Key
•	skill_level
This table supports the many-to-many relationship between users and skills.
________________________________________
5. JOB
The JOB entity stores available job opportunities.
Attributes:
•	job_id – Primary Key
•	title
•	company
•	location
•	description
•	experience
•	salary
•	job_type
________________________________________
6. JOB_SKILL
JOB_SKILL connects jobs with the skills required for those jobs.
Attributes:
•	job_id – Primary Key / Foreign Key
•	skill_id – Primary Key / Foreign Key
This supports the many-to-many relationship between jobs and skills.
________________________________________
7. INTERNSHIP
The INTERNSHIP entity stores available internship opportunities.
Attributes:
•	internship_id – Primary Key
•	title
•	company
•	location
•	description
•	duration
•	stipend
________________________________________
8. INTERNSHIP_SKILL
INTERNSHIP_SKILL connects internships with their required skills.
Attributes:
•	internship_id – Primary Key / Foreign Key
•	skill_id – Primary Key / Foreign Key
This supports the many-to-many relationship between internships and skills.
________________________________________
9. APPLICATION
The APPLICATION entity stores information about applications submitted by users.
Attributes:
•	application_id – Primary Key
•	user_id – Foreign Key
•	opportunity_id
•	opportunity_type
•	application_date
•	status
________________________________________
10. RECOMMENDATION
The RECOMMENDATION entity stores personalized recommendations generated for users.
Attributes:
•	recommendation_id – Primary Key
•	user_id – Foreign Key
•	opportunity_id
•	opportunity_type
•	matching_score
•	created_at
________________________________________
ER Relationship Overview
The main relationships are:
USER 1 ─────────── N EDUCATION

USER 1 ─────────── N USER_SKILL N ─────────── 1 SKILL

JOB 1 ──────────── N JOB_SKILL N ──────────── 1 SKILL

INTERNSHIP 1 ───── N INTERNSHIP_SKILL N ───── 1 SKILL

USER 1 ─────────── N APPLICATION

USER 1 ─────────── N RECOMMENDATION
Therefore:
•	One user can have multiple education records.
•	One user can have multiple skills.
•	One skill can belong to multiple users.
•	One job can require multiple skills.
•	One skill can be required by multiple jobs.
•	One internship can require multiple skills.
•	One skill can be required by multiple internships.
•	One user can submit multiple applications.
•	One user can receive multiple recommendations.
________________________________________
3.3 Identify All Tables, Fields and Relationships Between Tables
Table 1: USER
Field	Data Type	Key	Description
user_id	INT	PK	Unique user ID
name	VARCHAR	—	User's name
email	VARCHAR	—	User email
password_hash	VARCHAR	—	Hashed password
phone	VARCHAR	—	Contact number
location	VARCHAR	—	User location
role	VARCHAR	—	Student/Admin
Primary Key: user_id
________________________________________
Table 2: EDUCATION
Field	Data Type	Key	Description
education_id	INT	PK	Unique education ID
user_id	INT	FK	Related user
degree	VARCHAR	—	Degree name
field	VARCHAR	—	Field of study
institution	VARCHAR	—	Institution name
graduation_year	INT	—	Year of graduation
Primary Key: education_id
Foreign Key: user_id → USER(user_id)
Relationship:
USER 1 : N EDUCATION
________________________________________
Table 3: SKILL
Field	Data Type	Key	Description
skill_id	INT	PK	Unique skill ID
skill_name	VARCHAR	—	Name of skill
category	VARCHAR	—	Skill category
Primary Key: skill_id
________________________________________
Table 4: USER_SKILL
Field	Data Type	Key	Description
user_id	INT	PK, FK	User ID
skill_id	INT	PK, FK	Skill ID
skill_level	VARCHAR	—	Beginner/Intermediate/Advanced
Composite Primary Key: (user_id, skill_id)
Foreign Keys:
•	user_id → USER(user_id)
•	skill_id → SKILL(skill_id)
Relationship:
USER N : M SKILL
________________________________________
Table 5: JOB
Field	Data Type	Key	Description
job_id	INT	PK	Unique job ID
title	VARCHAR	—	Job title
company	VARCHAR	—	Company name
location	VARCHAR	—	Job location
description	TEXT	—	Job description
experience	VARCHAR	—	Required experience
salary	DECIMAL	—	Salary
job_type	VARCHAR	—	Full-time/Part-time/etc.
Primary Key: job_id
________________________________________
Table 6: JOB_SKILL
Field	Data Type	Key	Description
job_id	INT	PK, FK	Job ID
skill_id	INT	PK, FK	Required skill ID
Composite Primary Key: (job_id, skill_id)
Foreign Keys:
•	job_id → JOB(job_id)
•	skill_id → SKILL(skill_id)
Relationship:
JOB N : M SKILL
________________________________________
Table 7: INTERNSHIP
Field	Data Type	Key	Description
internship_id	INT	PK	Unique internship ID
title	VARCHAR	—	Internship title
company	VARCHAR	—	Company name
location	VARCHAR	—	Internship location
description	TEXT	—	Internship description
duration	VARCHAR	—	Internship duration
stipend	DECIMAL	—	Internship stipend
Primary Key: internship_id
________________________________________
Table 8: INTERNSHIP_SKILL
Field	Data Type	Key	Description
internship_id	INT	PK, FK	Internship ID
skill_id	INT	PK, FK	Required skill ID
Composite Primary Key: (internship_id, skill_id)
Foreign Keys:
•	internship_id → INTERNSHIP(internship_id)
•	skill_id → SKILL(skill_id)
Relationship:
INTERNSHIP N : M SKILL
________________________________________
Table 9: APPLICATION
Field	Data Type	Key	Description
application_id	INT	PK	Unique application ID
user_id	INT	FK	Applicant user
opportunity_id	INT	—	Job/Internship ID
opportunity_type	VARCHAR	—	Job or Internship
application_date	DATE	—	Date of application
status	VARCHAR	—	Current application status
Primary Key: application_id
Foreign Key: user_id → USER(user_id)
Relationship:
USER 1 : N APPLICATION
________________________________________
Table 10: RECOMMENDATION
Field	Data Type	Key	Description
recommendation_id	INT	PK	Unique recommendation ID
user_id	INT	FK	Recommended user
opportunity_id	INT	—	Job/Internship ID
opportunity_type	VARCHAR	—	Job or Internship
matching_score	DECIMAL	—	Profile matching percentage
created_at	TIMESTAMP	—	Recommendation date/time
Primary Key: recommendation_id
Foreign Key: user_id → USER(user_id)
Relationship:
USER 1 : N RECOMMENDATION
________________________________________
ER Diagram

 

Database Design Summary
The CareerMatch database consists of 10 main tables:
1.	USER
2.	EDUCATION
3.	SKILL
4.	USER_SKILL
5.	JOB
6.	JOB_SKILL
7.	INTERNSHIP
8.	INTERNSHIP_SKILL
9.	APPLICATION
10.	RECOMMENDATION
This database structure supports the main CareerMatch functions: user profile management, skill management, job/internship management, personalized recommendations, and application tracking.



















System Design
4.1 Class diagram
 


4.2 object diagram
 


4.3 Component Diagram


 






4.4 Deployment Diagram

 
4.5 Use Case Diagram

User 
 












Admin

 













5.6 Activity Diagram
 
5.7 Sequence Diagram
 




