# DROP TABLE
jobs_table_drop = "DROP TABLE IF EXISTS Jobs"
skill_table_drop = "DROP TABLE IF EXISTS Skill"
job_skill_table_drop = "DROP TABLE IF EXISTS Job_Skill"
industry_table_drop = "DROP TABLE IF EXISTS Industry"
jobs_industry_table_drop = "DROP TABLE IF EXISTS Job_Industry"
specialization_table_drop = "DROP TABLE IF EXISTS Specialization"
jobs_specialization_table_drop = "DROP TABLE IF EXISTS Job_Specialization"
role_table_drop = "DROP TABLE IF EXISTS Role"
jobs_role_table_drop = "DROP TABLE IF EXISTS Job_Role"
qualification_table_drop = "DROP TABLE IF EXISTS Qualification"
jobs_qualification_table_drop = "DROP TABLE IF EXISTS Job_Qualification"
jobFunctions_table_drop = "DROP TABLE IF EXISTS JobFunctions"
jobs_jobFunctions_table_drop = "DROP TABLE IF EXISTS Job_JobFunctions"
company_table_drop = "DROP TABLE IF EXISTS Company"
location_table_drop = "DROP TABLE IF EXISTS Location"

cleaned_jobs_data_table_drop = "DROP TABLE IF EXISTS cleaned_jobs_data"


# CREATE TABLE
jobs_table_create = ( """
    CREATE TABLE Jobs (
        job_id SERIAL PRIMARY KEY,
        link VARCHAR(255),
        title VARCHAR(255),
        job_description TEXT,
        experience VARCHAR(255),
        salary VARCHAR(255),
        employment_type VARCHAR(255),
        vacancies INTEGER,
        company_id INTEGER REFERENCES Company(company_id),
        location_id INTEGER REFERENCES Location(location_id)
    );
""" )

skill_table_create = ( """
    CREATE TABLE Skill (
        skill_id SERIAL PRIMARY KEY,
        skills VARCHAR(255) NOT NULL
    );
""" )

job_skill_table_create = ( """
    CREATE TABLE Job_Skill (
        job_skill_id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES Jobs(job_id),
        skill_id INTEGER REFERENCES Skill(skill_id)
    );
""" )

industry_table_create = ( """
    CREATE TABLE Industry (
        industry_id SERIAL PRIMARY KEY,
        industry VARCHAR(255) NOT NULL
    );
""" )

jobs_industry_table_create = ( """
    CREATE TABLE Job_Industry (
        job_industry_id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES Jobs(job_id),
        industry_id INTEGER REFERENCES Industry(industry_id)
    );
""" )

specialization_table_create = ( """
    CREATE TABLE Specialization (
        specialization_id SERIAL PRIMARY KEY,
        specialization VARCHAR(255) NOT NULL
    );
""" )

jobs_specialization_table_create = ( """
    CREATE TABLE Job_Specialization (
        job_specialization_id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES Jobs(job_id),
        specialization_id INTEGER REFERENCES Specialization(specialization_id)
    );
""" )

role_table_create = ( """
    CREATE TABLE Role (
        role_id SERIAL PRIMARY KEY,
        role VARCHAR(255) NOT NULL
    );
""" )

jobs_role_table_create = ( """
    CREATE TABLE Job_Role (
        job_role_id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES Jobs(job_id),
        role_id INTEGER REFERENCES Role(role_id)
    );
""" )

qualification_table_create = ( """
    CREATE TABLE Qualification (
        qualification_id SERIAL PRIMARY KEY,
        qualification VARCHAR(255) NOT NULL
    );
""" )

jobs_qualification_table_create = ( """
    CREATE TABLE Job_Qualification (
        job_qualification_id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES Jobs(job_id),
        qualification_id INTEGER REFERENCES Qualification(qualification_id)
    );
""" )

jobFunctions_table_create = ( """
    CREATE TABLE JobFunctions (
        jobfunction_id SERIAL PRIMARY KEY,
        jobfunctions VARCHAR(255) NOT NULL
    );
""" )

jobs_jobFunctions_table_create = ( """
    CREATE TABLE Job_JobFunctions (
        job_jobfunctions_id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES Jobs(job_id),
        jobfunction_id INTEGER REFERENCES JobFunctions(jobfunction_id)
    );
""" )

company_table_create = ( """
    CREATE TABLE Company (
        company_id SERIAL PRIMARY KEY,
        company VARCHAR(255) NOT NULL
    );
""" )

location_table_create = ( """
    CREATE TABLE Location (
        location_id SERIAL PRIMARY KEY,
        location VARCHAR(255) NOT NULL
    );
""" )

cleaned_jobs_data_table_create = ( """
    CREATE TABLE cleaned_jobs_data (
        title TEXT,
        link TEXT,
        company_name TEXT,
        job_description TEXT,
        skills TEXT,
        location TEXT,
        experience TEXT,
        salary TEXT,
        job_id TEXT PRIMARY KEY,
        job_function TEXT,
        industry TEXT,
        specialization TEXT,
        role TEXT,
        qualification TEXT,
        employment_type TEXT,
        vacancies INT
    );
""" )


# QUERY LISTS
create_table_queries = [
    company_table_create,
    location_table_create,
    jobs_table_create,
    skill_table_create,
    job_skill_table_create,
    industry_table_create,
    jobs_industry_table_create,
    specialization_table_create,
    jobs_specialization_table_create,
    role_table_create,
    jobs_role_table_create,
    qualification_table_create,
    jobs_qualification_table_create,
    jobFunctions_table_create,
    jobs_jobFunctions_table_create,
    cleaned_jobs_data_table_create
]

drop_table_queries = [
    jobs_table_drop,
    skill_table_drop,
    job_skill_table_drop,
    industry_table_drop,
    jobs_industry_table_drop,
    specialization_table_drop,
    jobs_specialization_table_drop,
    role_table_drop,
    jobs_role_table_drop,
    qualification_table_drop,
    jobs_qualification_table_drop,
    jobFunctions_table_drop,
    jobs_jobFunctions_table_drop,
    company_table_drop,
    location_table_drop,
    cleaned_jobs_data_table_drop
]