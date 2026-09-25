from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from functools import wraps
import re


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)
app.config.from_object(Config)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    return psycopg2.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        database=app.config["DB_NAME"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"]
    )


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# ADMIN REQUIRED
# =========================================================

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:

            flash("Please fill all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:

            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(url_for("register"))

        conn = None
        cur = None

        try:

            conn = get_db_connection()

            cur = conn.cursor(
                cursor_factory=RealDictCursor
            )

            # Check existing email
            cur.execute("""
                SELECT user_id
                FROM users
                WHERE email = %s
            """, (email,))

            existing_user = cur.fetchone()

            if existing_user:

                flash(
                    "Email already exists.",
                    "danger"
                )

                return redirect(url_for("register"))

            password_hash = generate_password_hash(password)

            # Create user
            cur.execute("""
                INSERT INTO users
                (
                    full_name,
                    email,
                    password_hash,
                    role
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'user'
                )
                RETURNING user_id
            """, (
                full_name,
                email,
                password_hash
            ))

            new_user = cur.fetchone()

            user_id = new_user["user_id"]

            # Create empty profile
            cur.execute("""
                INSERT INTO user_profiles
                (
                    user_id
                )
                VALUES
                (
                    %s
                )
                ON CONFLICT (user_id)
                DO NOTHING
            """, (user_id,))

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception as e:

            if conn:
                conn.rollback()

            print("REGISTER ERROR:", e)

            flash(
                "Registration failed. Please try again.",
                "danger"
            )

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:

            flash(
                "Please enter email and password.",
                "danger"
            )

            return redirect(url_for("login"))

        conn = None
        cur = None

        try:

            conn = get_db_connection()

            cur = conn.cursor(
                cursor_factory=RealDictCursor
            )

            cur.execute("""
                SELECT
                    user_id,
                    full_name,
                    email,
                    password_hash,
                    role
                FROM users
                WHERE email = %s
            """, (email,))

            user = cur.fetchone()

            if not user:

                flash(
                    "Invalid email or password.",
                    "danger"
                )

                return redirect(url_for("login"))

            if not check_password_hash(
                user["password_hash"],
                password
            ):

                flash(
                    "Invalid email or password.",
                    "danger"
                )

                return redirect(url_for("login"))

            # Save session
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash(
                "Login successful.",
                "success"
            )

            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(
                url_for("dashboard")
            )

        except Exception as e:

            print("LOGIN ERROR:", e)

            flash(
                "Login failed. Please try again.",
                "danger"
            )

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("index"))


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "admin":

        return redirect(
            url_for("admin_dashboard")
        )

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        user_id = session["user_id"]

        # User information
        cur.execute("""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.role,
                p.phone,
                p.education,
                p.degree,
                p.graduation_year,
                p.experience_years,
                p.preferred_role,
                p.preferred_location,
                p.profile_summary
            FROM users u
            LEFT JOIN user_profiles p
                ON u.user_id = p.user_id
            WHERE u.user_id = %s
        """, (user_id,))

        user_data = cur.fetchone()

        # Application count
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM applications
            WHERE user_id = %s
        """, (user_id,))

        application_count = cur.fetchone()["total"]

        # Skill count
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM user_skills
            WHERE user_id = %s
        """, (user_id,))

        skill_count = cur.fetchone()["total"]

        # Active jobs
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM jobs
            WHERE is_active = TRUE
        """)

        job_count = cur.fetchone()["total"]

        return render_template(
            "dashboard.html",
            user_data=user_data,
            application_count=application_count,
            skill_count=skill_count,
            job_count=job_count
        )

    except Exception as e:

        print("DASHBOARD ERROR:", e)

        flash(
            "Unable to load dashboard.",
            "danger"
        )

        return redirect(url_for("index"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # Total users
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'user'
        """)

        total_users = cur.fetchone()["total"]

        # Total jobs
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM jobs
        """)

        total_jobs = cur.fetchone()["total"]

        # Active jobs
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM jobs
            WHERE is_active = TRUE
        """)

        active_jobs = cur.fetchone()["total"]

        # Total applications
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM applications
        """)

        total_applications = cur.fetchone()["total"]

        # Recent jobs
        cur.execute("""
            SELECT
                job_id,
                title,
                company_name,
                job_type,
                location,
                is_active,
                created_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 10
        """)

        recent_jobs = cur.fetchall()

        # Recent applications
        cur.execute("""
            SELECT
                a.application_id,
                a.status,
                a.applied_at,
                u.full_name,
                u.email,
                j.title,
                j.company_name
            FROM applications a
            JOIN users u
                ON a.user_id = u.user_id
            JOIN jobs j
                ON a.job_id = j.job_id
            ORDER BY a.applied_at DESC
            LIMIT 10
        """)

        recent_applications = cur.fetchall()

        return render_template(
            "admin_dashboard.html",
            total_users=total_users,
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            total_applications=total_applications,
            recent_jobs=recent_jobs,
            recent_applications=recent_applications
        )

    except Exception as e:

        print(
            "ADMIN DASHBOARD ERROR:",
            e
        )

        flash(
            "Unable to load admin dashboard.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
@login_required
def profile():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        user_id = session["user_id"]

        # Make sure profile exists
        cur.execute("""
            INSERT INTO user_profiles
            (
                user_id
            )
            VALUES
            (
                %s
            )
            ON CONFLICT (user_id)
            DO NOTHING
        """, (user_id,))

        conn.commit()

        # User + Profile
        cur.execute("""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.role,

                p.phone,
                p.education,
                p.degree,
                p.graduation_year,
                p.experience_years,
                p.preferred_role,
                p.preferred_location,
                p.bio,
                p.resume_path,
                p.profile_image,
                p.updated_at,
                p.date_of_birth,
                p.gender,
                p.college_name,
                p.resume_url,
                p.profile_summary

            FROM users u

            LEFT JOIN user_profiles p
                ON u.user_id = p.user_id

            WHERE u.user_id = %s
        """, (user_id,))

        user_profile = cur.fetchone()

        # All skills
        cur.execute("""
            SELECT
                skill_id,
                skill_name
            FROM skills
            ORDER BY skill_name ASC
        """)

        all_skills = cur.fetchall()

        # User skills
        cur.execute("""
            SELECT
                us.user_skill_id,
                us.skill_id,
                s.skill_name,
                us.skill_level,
                us.proficiency

            FROM user_skills us

            JOIN skills s
                ON us.skill_id = s.skill_id

            WHERE us.user_id = %s

            ORDER BY s.skill_name ASC
        """, (user_id,))

        user_skills = cur.fetchall()

        return render_template(
            "profile.html",
            user_profile=user_profile,
            all_skills=all_skills,
            user_skills=user_skills
        )

    except Exception as e:

        print(
            "PROFILE ERROR:",
            e
        )

        flash(
            "Unable to load profile.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():

    user_id = session["user_id"]

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    education = request.form.get(
        "education",
        ""
    ).strip()

    degree = request.form.get(
        "degree",
        ""
    ).strip()

    graduation_year = request.form.get(
        "graduation_year",
        ""
    ).strip()

    experience_years = request.form.get(
        "experience_years",
        ""
    ).strip()

    preferred_role = request.form.get(
        "preferred_role",
        ""
    ).strip()

    preferred_location = request.form.get(
        "preferred_location",
        ""
    ).strip()

    date_of_birth = request.form.get(
        "date_of_birth",
        ""
    ).strip()

    gender = request.form.get(
        "gender",
        ""
    ).strip()

    college_name = request.form.get(
        "college_name",
        ""
    ).strip()

    resume_url = request.form.get(
        "resume_url",
        ""
    ).strip()

    profile_summary = request.form.get(
        "profile_summary",
        ""
    ).strip()

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        # Graduation year
        if graduation_year:

            graduation_year_value = int(
                graduation_year
            )

        else:

            graduation_year_value = None

        # Experience
        if experience_years:

            experience_years_value = float(
                experience_years
            )

        else:

            experience_years_value = None

        # Date of birth
        if date_of_birth:

            date_of_birth_value = date_of_birth

        else:

            date_of_birth_value = None

        cur.execute("""
            INSERT INTO user_profiles
            (
                user_id,
                phone,
                education,
                degree,
                graduation_year,
                experience_years,
                preferred_role,
                preferred_location,
                date_of_birth,
                gender,
                college_name,
                resume_url,
                profile_summary,
                updated_at
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP
            )

            ON CONFLICT (user_id)

            DO UPDATE SET

                phone = EXCLUDED.phone,
                education = EXCLUDED.education,
                degree = EXCLUDED.degree,
                graduation_year = EXCLUDED.graduation_year,
                experience_years = EXCLUDED.experience_years,
                preferred_role = EXCLUDED.preferred_role,
                preferred_location = EXCLUDED.preferred_location,
                date_of_birth = EXCLUDED.date_of_birth,
                gender = EXCLUDED.gender,
                college_name = EXCLUDED.college_name,
                resume_url = EXCLUDED.resume_url,
                profile_summary = EXCLUDED.profile_summary,
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            phone,
            education,
            degree,
            graduation_year_value,
            experience_years_value,
            preferred_role,
            preferred_location,
            date_of_birth_value,
            gender,
            college_name,
            resume_url,
            profile_summary
        ))

        conn.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

    except ValueError:

        if conn:
            conn.rollback()

        flash(
            "Graduation year or experience must contain valid numbers.",
            "danger"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "UPDATE PROFILE ERROR:",
            e
        )

        flash(
            "Unable to update profile.",
            "danger"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(
        url_for("profile")
    )


# =========================================================
# ADD / UPDATE USER SKILL
# =========================================================

@app.route("/profile/add-skill", methods=["POST"])
@login_required
def add_skill():

    user_id = session["user_id"]

    skill_id = request.form.get(
        "skill_id"
    )

    proficiency = request.form.get(
        "proficiency",
        ""
    ).strip()

    skill_level = request.form.get(
        "skill_level",
        ""
    ).strip()

    if not skill_id:

        flash(
            "Please select a skill.",
            "danger"
        )

        return redirect(
            url_for("profile")
        )

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # Check skill
        cur.execute("""
            SELECT skill_id
            FROM skills
            WHERE skill_id = %s
        """, (skill_id,))

        skill = cur.fetchone()

        if not skill:

            flash(
                "Selected skill does not exist.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        # Check duplicate
        cur.execute("""
            SELECT user_skill_id
            FROM user_skills
            WHERE user_id = %s
            AND skill_id = %s
        """, (
            user_id,
            skill_id
        ))

        existing = cur.fetchone()

        if existing:

            cur.execute("""
                UPDATE user_skills

                SET
                    skill_level = %s,
                    proficiency = %s

                WHERE user_id = %s
                AND skill_id = %s
            """, (
                skill_level or None,
                proficiency or None,
                user_id,
                skill_id
            ))

            flash(
                "Skill updated successfully.",
                "success"
            )

        else:

            cur.execute("""
                INSERT INTO user_skills
                (
                    user_id,
                    skill_id,
                    skill_level,
                    proficiency
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                user_id,
                skill_id,
                skill_level or None,
                proficiency or None
            ))

            flash(
                "Skill added successfully.",
                "success"
            )

        conn.commit()

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADD SKILL ERROR:",
            e
        )

        flash(
            "Unable to add skill.",
            "danger"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(
        url_for("profile")
    )


# =========================================================
# REMOVE USER SKILL
# =========================================================

@app.route("/profile/remove-skill/<int:skill_id>")
@login_required
def remove_skill(skill_id):

    user_id = session["user_id"]

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM user_skills

            WHERE user_id = %s
            AND skill_id = %s
        """, (
            user_id,
            skill_id
        ))

        conn.commit()

        flash(
            "Skill removed successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "REMOVE SKILL ERROR:",
            e
        )

        flash(
            "Unable to remove skill.",
            "danger"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(
        url_for("profile")
    )


# =========================================================
# JOBS & INTERNSHIPS
# =========================================================

@app.route("/jobs")
@login_required
def jobs():

    search = request.args.get(
        "search",
        ""
    ).strip()

    job_type = request.args.get(
        "job_type",
        ""
    ).strip()

    location = request.args.get(
        "location",
        ""
    ).strip()

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        query = """
            SELECT
                j.job_id,
                j.title,
                j.company_name,
                j.description,
                j.job_type,
                j.location,
                j.experience_required,
                j.education_required,
                j.salary_min,
                j.salary_max,
                j.application_deadline,
                j.application_link

            FROM jobs j

            WHERE j.is_active = TRUE
        """

        params = []

        # Search
        if search:

            query += """
                AND
                (
                    j.title ILIKE %s
                    OR j.company_name ILIKE %s
                    OR j.description ILIKE %s
                )
            """

            search_value = (
                f"%{search}%"
            )

            params.extend([
                search_value,
                search_value,
                search_value
            ])

        # Job type
        if job_type:

            query += """
                AND j.job_type = %s
            """

            params.append(
                job_type
            )

        # Location
        if location:

            query += """
                AND j.location ILIKE %s
            """

            params.append(
                f"%{location}%"
            )

        query += """
            ORDER BY

                CASE
                    WHEN j.application_deadline IS NULL
                    THEN 1
                    ELSE 0
                END,

                j.application_deadline ASC,

                j.created_at DESC
        """

        cur.execute(
            query,
            tuple(params)
        )

        jobs_data = cur.fetchall()

        return render_template(
            "jobs.html",
            jobs=jobs_data,
            search=search,
            job_type=job_type,
            location=location
        )

    except Exception as e:

        print(
            "JOBS ERROR:",
            e
        )

        flash(
            "Unable to load jobs.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# JOB DETAILS
# =========================================================

@app.route("/job/<int:job_id>")
@login_required
def job_details(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # Get job
        cur.execute("""
            SELECT
                j.job_id,
                j.title,
                j.company_name,
                j.description,
                j.job_type,
                j.location,
                j.experience_required,
                j.education_required,
                j.salary_min,
                j.salary_max,
                j.application_deadline,
                j.application_link,
                j.is_active,
                j.created_at

            FROM jobs j

            WHERE j.job_id = %s
        """, (job_id,))

        job = cur.fetchone()

        if not job:

            return """
                <div style="
                    font-family: Arial;
                    text-align: center;
                    padding: 50px;
                ">
                    <h2>Job Not Found</h2>

                    <p>
                        The requested opportunity does not exist.
                    </p>

                    <a href="/jobs">
                        Back to Jobs
                    </a>
                </div>
            """, 404

        # Required skills
        cur.execute("""
            SELECT
                s.skill_id,
                s.skill_name,
                js.importance

            FROM job_skills js

            JOIN skills s
                ON js.skill_id = s.skill_id

            WHERE js.job_id = %s

            ORDER BY
                js.importance DESC,
                s.skill_name ASC
        """, (job_id,))

        required_skills = cur.fetchall()

        # Existing application
        cur.execute("""
            SELECT
                application_id,
                status,
                applied_at

            FROM applications

            WHERE user_id = %s
            AND job_id = %s
        """, (
            session["user_id"],
            job_id
        ))

        existing_application = cur.fetchone()

        return render_template(
            "job_details.html",
            job=job,
            required_skills=required_skills,
            existing_application=existing_application
        )

    except Exception as e:

        print(
            "JOB DETAILS ERROR:",
            e
        )

        return """
            <div style="
                font-family: Arial;
                text-align: center;
                padding: 50px;
            ">
                <h2>Something went wrong</h2>

                <p>
                    Unable to load job details.
                </p>

                <a href="/jobs">
                    Back to Jobs
                </a>
            </div>
        """, 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# APPLY
# =========================================================

@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
@login_required
def apply(job_id):

    user_id = session["user_id"]

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # Check active job
        cur.execute("""
            SELECT
                job_id,
                title

            FROM jobs

            WHERE job_id = %s
            AND is_active = TRUE
        """, (job_id,))

        job = cur.fetchone()

        if not job:

            flash(
                "This opportunity is no longer available.",
                "danger"
            )

            return redirect(
                url_for("jobs")
            )

        # Check duplicate
        cur.execute("""
            SELECT
                application_id

            FROM applications

            WHERE user_id = %s
            AND job_id = %s
        """, (
            user_id,
            job_id
        ))

        existing_application = cur.fetchone()

        if existing_application:

            flash(
                "You have already applied for this opportunity.",
                "info"
            )

            return redirect(
                url_for(
                    "job_details",
                    job_id=job_id
                )
            )

        # Insert application
        cur.execute("""
            INSERT INTO applications
            (
                user_id,
                job_id,
                status,
                applied_at
            )

            VALUES
            (
                %s,
                %s,
                'Applied',
                CURRENT_TIMESTAMP
            )
        """, (
            user_id,
            job_id
        ))

        conn.commit()

        flash(
            "Application submitted successfully.",
            "success"
        )

        return redirect(
            url_for("my_applications")
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "APPLY ERROR:",
            e
        )

        flash(
            "Unable to submit application.",
            "danger"
        )

        return redirect(
            url_for(
                "job_details",
                job_id=job_id
            )
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route("/my-applications")
@login_required
def my_applications():

    user_id = session["user_id"]

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute("""
            SELECT
                a.application_id,
                j.job_id,
                j.title,
                j.company_name,
                j.job_type,
                j.location,
                a.status,
                a.applied_at

            FROM applications a

            JOIN jobs j
                ON a.job_id = j.job_id

            WHERE a.user_id = %s

            ORDER BY
                a.applied_at DESC
        """, (user_id,))

        applications = cur.fetchall()

        return render_template(
            "my_applications.html",
            applications=applications
        )

    except Exception as e:

        print(
            "MY APPLICATIONS ERROR:",
            e
        )

        flash(
            "Unable to load applications.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.route("/recommendations")
@login_required
def recommendations():

    user_id = session["user_id"]

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # =================================================
        # USER PROFILE
        # =================================================

        cur.execute("""
            SELECT
                p.education,
                p.degree,
                p.experience_years,
                p.preferred_role,
                p.preferred_location

            FROM user_profiles p

            WHERE p.user_id = %s
        """, (user_id,))

        user_profile = cur.fetchone()

        if not user_profile:

            user_profile = {
                "education": "",
                "degree": "",
                "experience_years": 0,
                "preferred_role": "",
                "preferred_location": ""
            }

        # =================================================
        # USER SKILLS
        # =================================================

        cur.execute("""
            SELECT
                s.skill_id,
                s.skill_name,
                us.skill_level,
                us.proficiency

            FROM user_skills us

            JOIN skills s
                ON us.skill_id = s.skill_id

            WHERE us.user_id = %s
        """, (user_id,))

        user_skills = cur.fetchall()

        user_skill_names = set()

        for skill in user_skills:

            skill_name = (
                skill["skill_name"] or ""
            ).strip().lower()

            if skill_name:

                user_skill_names.add(
                    skill_name
                )

        # =================================================
        # ACTIVE JOBS
        # =================================================

        cur.execute("""
            SELECT
                j.job_id,
                j.title,
                j.company_name,
                j.description,
                j.job_type,
                j.location,
                j.experience_required,
                j.education_required,
                j.salary_min,
                j.salary_max,
                j.application_deadline,
                j.application_link,
                j.created_at

            FROM jobs j

            WHERE j.is_active = TRUE

            ORDER BY
                j.created_at DESC
        """)

        all_jobs = cur.fetchall()

        recommendations_list = []

        # =================================================
        # USER PREFERENCES
        # =================================================

        preferred_role = (
            user_profile["preferred_role"]
            or ""
        ).strip().lower()

        preferred_location = (
            user_profile["preferred_location"]
            or ""
        ).strip().lower()

        education = (
            user_profile["education"]
            or ""
        ).strip().lower()

        degree = (
            user_profile["degree"]
            or ""
        ).strip().lower()

        try:

            user_experience = float(
                user_profile["experience_years"]
                or 0
            )

        except:

            user_experience = 0

        # =================================================
        # SCORE EACH JOB
        # =================================================

        for job in all_jobs:

            total_score = 0

            reasons = []

            matched_skills = []

            missing_skills = []

            # =================================================
            # REQUIRED SKILLS
            # =================================================

            cur.execute("""
                SELECT
                    s.skill_id,
                    s.skill_name,
                    js.importance

                FROM job_skills js

                JOIN skills s
                    ON js.skill_id = s.skill_id

                WHERE js.job_id = %s

                ORDER BY
                    js.importance DESC
            """, (job["job_id"],))

            required_skills = cur.fetchall()

            total_importance = 0

            matched_importance = 0

            for required_skill in required_skills:

                skill_name = (
                    required_skill["skill_name"]
                    or ""
                ).strip().lower()

                importance = (
                    required_skill["importance"]
                )

                try:

                    importance = int(
                        importance
                    )

                except:

                    importance = 1

                importance = max(
                    1,
                    min(5, importance)
                )

                total_importance += (
                    importance
                )

                if skill_name in user_skill_names:

                    matched_importance += (
                        importance
                    )

                    matched_skills.append(
                        required_skill["skill_name"]
                    )

                else:

                    missing_skills.append(
                        required_skill["skill_name"]
                    )

            # =================================================
            # SKILL SCORE = 50%
            # =================================================

            if total_importance > 0:

                skill_percentage = (
                    matched_importance
                    / total_importance
                ) * 100

                skill_score = (
                    skill_percentage * 0.50
                )

            else:

                skill_percentage = 100

                skill_score = 50

            total_score += skill_score

            if matched_skills:

                reasons.append(
                    "Your skill matches: "
                    + ", ".join(matched_skills)
                )

            # =================================================
            # ROLE SCORE = 20%
            # =================================================

            role_score = 0

            job_title = (
                job["title"]
                or ""
            ).strip().lower()

            if preferred_role:

                if (
                    preferred_role in job_title
                    or job_title in preferred_role
                ):

                    role_score = 20

                    reasons.append(
                        "Matches your preferred role"
                    )

                else:

                    role_words = [
                        word
                        for word in preferred_role.split()
                        if len(word) > 2
                    ]

                    if any(
                        word in job_title
                        for word in role_words
                    ):

                        role_score = 20

                        reasons.append(
                            "Related to your preferred role"
                        )

            total_score += role_score

            # =================================================
            # LOCATION SCORE = 15%
            # =================================================

            location_score = 0

            job_location = (
                job["location"]
                or ""
            ).strip().lower()

            if preferred_location and job_location:

                if (
                    preferred_location in job_location
                    or job_location in preferred_location
                ):

                    location_score = 15

                    reasons.append(
                        "Matches your preferred location"
                    )

            total_score += location_score

            # =================================================
            # EDUCATION SCORE = 10%
            # =================================================

            education_score = 0

            job_education = (
                job["education_required"]
                or ""
            ).strip().lower()

            if job_education:

                education_match = False

                if education:

                    if (
                        education in job_education
                        or job_education in education
                    ):

                        education_match = True

                if degree:

                    if degree in job_education:

                        education_match = True

                if education_match:

                    education_score = 10

                    reasons.append(
                        "Education requirement matches"
                    )

            total_score += education_score

            # =================================================
            # EXPERIENCE SCORE = 5%
            # =================================================

            experience_score = 0

            job_experience = (
                job["experience_required"]
                or ""
            ).strip().lower()

            if job_experience:

                if (
                    "fresher" in job_experience
                    or "0 year" in job_experience
                    or "0-1" in job_experience
                    or "0 – 1" in job_experience
                    or "0–1" in job_experience
                ):

                    if user_experience <= 1:

                        experience_score = 5

                        reasons.append(
                            "Suitable for your experience level"
                        )

                else:

                    numbers = re.findall(
                        r"\d+(?:\.\d+)?",
                        job_experience
                    )

                    if numbers:

                        try:

                            required_experience = float(
                                numbers[0]
                            )

                            if (
                                user_experience
                                >= required_experience
                            ):

                                experience_score = 5

                                reasons.append(
                                    "Experience requirement matches"
                                )

                        except:

                            pass

            total_score += experience_score

            # =================================================
            # LIMIT SCORE
            # =================================================

            total_score = max(
                0,
                min(100, total_score)
            )

            # =================================================
            # MATCH CATEGORY
            # =================================================

            if total_score >= 90:

                match_category = (
                    "Excellent Match"
                )

            elif total_score >= 75:

                match_category = (
                    "Strong Match"
                )

            elif total_score >= 60:

                match_category = (
                    "Good Match"
                )

            elif total_score >= 40:

                match_category = (
                    "Partial Match"
                )

            else:

                match_category = (
                    "Low Match"
                )

            # =================================================
            # DEFAULT REASON
            # =================================================

            if not reasons:

                reasons.append(
                    "This opportunity matches some of your profile information."
                )

            # =================================================
            # CREATE RESULT
            # =================================================

            job_result = dict(job)

            job_result["match_score"] = round(
                total_score,
                2
            )

            job_result["match_category"] = (
                match_category
            )

            job_result["matched_skills"] = (
                matched_skills
            )

            job_result["missing_skills"] = (
                missing_skills
            )

            job_result["reasons"] = (
                reasons
            )

            recommendations_list.append(
                job_result
            )

        # =================================================
        # SORT BY SCORE
        # =================================================

        recommendations_list.sort(
            key=lambda x: x["match_score"],
            reverse=True
        )

        return render_template(
            "recommendations.html",
            recommendations=recommendations_list,
            user_profile=user_profile,
            user_skills=user_skills
        )

    except Exception as e:

        print(
            "RECOMMENDATION ERROR:",
            e
        )

        flash(
            "Unable to generate recommendations.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# TEST DATABASE
# =========================================================

@app.route("/test-db")
def test_db():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT 1"
        )

        result = cur.fetchone()

        return {
            "status": "success",
            "database": "Connected",
            "result": result[0]
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }, 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "application": "CareerMatch"
    }


# =========================================================
# 404 ERROR
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "index.html"
    ), 404


# =========================================================
# 500 ERROR
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    return """
        <div style="
            font-family: Arial;
            text-align: center;
            padding: 60px;
        ">

            <h1>500 - Internal Server Error</h1>

            <p>
                Something went wrong on the server.
            </p>

            <a href="/">
                Go to Home
            </a>

        </div>
    """, 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )