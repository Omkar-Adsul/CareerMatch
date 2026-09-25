# ============================================================
# CareerMatch - AI-Powered Job & Internship Recommendation
# Platform
# Backend: Flask + PostgreSQL
# ============================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import psycopg2
from psycopg2.extras import RealDictCursor

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps
from config import Config
import re


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)
app.config.from_object(Config)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    conn = psycopg2.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        database=app.config["DB_NAME"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"]
    )

    return conn


# ============================================================
# LOGIN REQUIRED DECORATOR
# ============================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# ADMIN REQUIRED DECORATOR
# ============================================================

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        if session.get("role") != "admin":

            flash(
                "Admin access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not full_name or not email or not password:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(
            email_pattern,
            email
        ):

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        conn = None
        cur = None

        try:

            conn = get_db_connection()

            cur = conn.cursor(
                cursor_factory=RealDictCursor
            )

            # ------------------------------------------------
            # CHECK EXISTING EMAIL
            # ------------------------------------------------

            cur.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cur.fetchone()

            if existing_user:

                flash(
                    "Email already registered.",
                    "danger"
                )

                return redirect(
                    url_for("register")
                )

            # ------------------------------------------------
            # HASH PASSWORD
            # ------------------------------------------------

            password_hash = generate_password_hash(
                password
            )

            # ------------------------------------------------
            # CREATE USER
            # ------------------------------------------------

            cur.execute(
                """
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
                """,
                (
                    full_name,
                    email,
                    password_hash
                )
            )

            new_user = cur.fetchone()

            user_id = new_user["user_id"]

            # ------------------------------------------------
            # CREATE EMPTY PROFILE
            # ------------------------------------------------

            cur.execute(
                """
                INSERT INTO user_profiles
                (
                    user_id
                )
                VALUES
                (
                    %s
                )
                """,
                (user_id,)
            )

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "REGISTER ERROR:",
                e
            )

            flash(
                "Registration failed. Please try again.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Please enter email and password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        conn = None
        cur = None

        try:

            conn = get_db_connection()

            cur = conn.cursor(
                cursor_factory=RealDictCursor
            )

            cur.execute(
                """
                SELECT
                    user_id,
                    full_name,
                    email,
                    password_hash,
                    role
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cur.fetchone()

            if not user:

                flash(
                    "Invalid email or password.",
                    "danger"
                )

                return redirect(
                    url_for("login")
                )

            if not check_password_hash(
                user["password_hash"],
                password
            ):

                flash(
                    "Invalid email or password.",
                    "danger"
                )

                return redirect(
                    url_for("login")
                )

            # ------------------------------------------------
            # CREATE SESSION
            # ------------------------------------------------

            session.clear()

            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            # ------------------------------------------------
            # ADMIN
            # ------------------------------------------------

            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            # ------------------------------------------------
            # NORMAL USER
            # ------------------------------------------------

            return redirect(
                url_for("dashboard")
            )

        except Exception as e:

            print(
                "LOGIN ERROR:",
                e
            )

            flash(
                "Login failed. Please try again.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# USER DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    # Admin should always use admin dashboard
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

        # ----------------------------------------------------
        # PROFILE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                profile_id,
                phone,
                education,
                degree,
                graduation_year,
                experience_years,
                preferred_role,
                preferred_location,
                bio,
                resume_path,
                profile_image,
                date_of_birth,
                gender,
                college_name,
                resume_url,
                profile_summary
            FROM user_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )

        profile = cur.fetchone()

        # ----------------------------------------------------
        # APPLICATION COUNT
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM applications
            WHERE user_id = %s
            """,
            (user_id,)
        )

        total_applications = cur.fetchone()["total"]

        # ----------------------------------------------------
        # RECOMMENDATION COUNT
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*)
            FROM jobs
            WHERE is_active = TRUE
            """
        )

        total_jobs = cur.fetchone()["count"]

        # ----------------------------------------------------
        # RECENT APPLICATIONS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                a.application_id,
                a.status,
                a.applied_at,
                j.job_id,
                j.title,
                j.company_name,
                j.location
            FROM applications a
            JOIN jobs j
                ON a.job_id = j.job_id
            WHERE a.user_id = %s
            ORDER BY a.applied_at DESC
            LIMIT 5
            """,
            (user_id,)
        )

        recent_applications = cur.fetchall()

        return render_template(
            "dashboard.html",
            profile=profile,
            total_applications=total_applications,
            total_jobs=total_jobs,
            recent_applications=recent_applications
        )

    except Exception as e:

        print(
            "DASHBOARD ERROR:",
            e
        )

        if conn:
            conn.rollback()

        flash(
            "Unable to load dashboard.",
            "danger"
        )

        return redirect(
            url_for("index")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

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

        # ----------------------------------------------------
        # TOTAL USERS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'user'
            """
        )

        total_users = cur.fetchone()["total"]

        # ----------------------------------------------------
        # TOTAL JOBS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM jobs
            """
        )

        total_jobs = cur.fetchone()["total"]

        # ----------------------------------------------------
        # ACTIVE JOBS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM jobs
            WHERE is_active = TRUE
            """
        )

        active_jobs = cur.fetchone()["total"]

        # ----------------------------------------------------
        # TOTAL APPLICATIONS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM applications
            """
        )

        total_applications = cur.fetchone()["total"]

        # ----------------------------------------------------
        # RECENT JOBS
        # ----------------------------------------------------

        cur.execute(
            """
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
            """
        )

        recent_jobs = cur.fetchall()

        # ----------------------------------------------------
        # RECENT APPLICATIONS
        # ----------------------------------------------------

        cur.execute(
            """
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
            """
        )

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

        if conn:
            conn.rollback()

        flash(
            "Unable to load admin dashboard. Check the terminal for the exact error.",
            "danger"
        )

        # IMPORTANT:
        # Do NOT redirect admin to /dashboard here.
        # /dashboard redirects admin back to /admin/dashboard,
        # which would create an infinite redirect loop.

        return redirect(
            url_for("index")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# PROFILE
# ============================================================

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

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                user_id,
                full_name,
                email,
                role
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cur.fetchone()

        # ----------------------------------------------------
        # PROFILE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                profile_id,
                user_id,
                phone,
                education,
                degree,
                graduation_year,
                experience_years,
                preferred_role,
                preferred_location,
                bio,
                resume_path,
                profile_image,
                updated_at,
                date_of_birth,
                gender,
                college_name,
                resume_url,
                profile_summary
            FROM user_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )

        profile_data = cur.fetchone()

        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                us.user_skill_id,
                us.skill_id,
                us.skill_level,
                us.proficiency,
                s.skill_name
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
            ORDER BY s.skill_name
            """,
            (user_id,)
        )

        user_skills = cur.fetchall()

        # ----------------------------------------------------
        # ALL SKILLS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                skill_id,
                skill_name
            FROM skills
            ORDER BY skill_name
            """
        )

        all_skills = cur.fetchall()

        return render_template(
            "profile.html",
            user=user,
            profile=profile_data,
            user_skills=user_skills,
            all_skills=all_skills
        )

    except Exception as e:

        print(
            "PROFILE ERROR:",
            e
        )

        if conn:
            conn.rollback()

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


# ============================================================
# UPDATE PROFILE
# ============================================================

@app.route(
    "/profile/update",
    methods=["POST"]
)
@login_required
def update_profile():

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

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
            "graduation_year"
        )

        experience_years = request.form.get(
            "experience_years"
        )

        preferred_role = request.form.get(
            "preferred_role",
            ""
        ).strip()

        preferred_location = request.form.get(
            "preferred_location",
            ""
        ).strip()

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        date_of_birth = request.form.get(
            "date_of_birth"
        )

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

        conn = get_db_connection()

        cur = conn.cursor()

        # ----------------------------------------------------
        # UPDATE USER
        # ----------------------------------------------------

        if full_name and email:

            cur.execute(
                """
                UPDATE users
                SET
                    full_name = %s,
                    email = %s
                WHERE user_id = %s
                """,
                (
                    full_name,
                    email,
                    user_id
                )
            )

            session["full_name"] = full_name
            session["email"] = email

        # ----------------------------------------------------
        # UPDATE PROFILE
        # ----------------------------------------------------

        cur.execute(
            """
            UPDATE user_profiles
            SET
                phone = %s,
                education = %s,
                degree = %s,
                graduation_year = %s,
                experience_years = %s,
                preferred_role = %s,
                preferred_location = %s,
                bio = %s,
                date_of_birth = %s,
                gender = %s,
                college_name = %s,
                resume_url = %s,
                profile_summary = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
            """,
            (
                phone or None,
                education or None,
                degree or None,
                graduation_year or None,
                experience_years or None,
                preferred_role or None,
                preferred_location or None,
                bio or None,
                date_of_birth or None,
                gender or None,
                college_name or None,
                resume_url or None,
                profile_summary or None,
                user_id
            )
        )

        conn.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "PROFILE UPDATE ERROR:",
            e
        )

        flash(
            "Unable to update profile.",
            "danger"
        )

        return redirect(
            url_for("profile")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADD USER SKILL
# ============================================================

@app.route(
    "/profile/add-skill",
    methods=["POST"]
)
@login_required
def add_skill():

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        skill_id = request.form.get(
            "skill_id"
        )

        skill_level = request.form.get(
            "skill_level",
            "Intermediate"
        )

        proficiency = request.form.get(
            "proficiency"
        )

        if not skill_id:

            flash(
                "Please select a skill.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        conn = get_db_connection()

        cur = conn.cursor()

        # ----------------------------------------------------
        # CHECK DUPLICATE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT user_skill_id
            FROM user_skills
            WHERE user_id = %s
            AND skill_id = %s
            """,
            (
                user_id,
                skill_id
            )
        )

        existing = cur.fetchone()

        if existing:

            cur.execute(
                """
                UPDATE user_skills
                SET
                    skill_level = %s,
                    proficiency = %s
                WHERE user_id = %s
                AND skill_id = %s
                """,
                (
                    skill_level,
                    proficiency or None,
                    user_id,
                    skill_id
                )
            )

        else:

            cur.execute(
                """
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
                """,
                (
                    user_id,
                    skill_id,
                    skill_level,
                    proficiency or None
                )
            )

        conn.commit()

        flash(
            "Skill added successfully.",
            "success"
        )

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


# ============================================================
# REMOVE USER SKILL
# ============================================================

@app.route(
    "/profile/remove-skill/<int:skill_id>",
    methods=["POST", "GET"]
)
@login_required
def remove_skill(skill_id):

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM user_skills
            WHERE user_id = %s
            AND skill_id = %s
            """,
            (
                user_id,
                skill_id
            )
        )

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


# ============================================================
# JOBS & INTERNSHIPS
# ============================================================

@app.route("/jobs")
@login_required
def jobs():

    conn = None
    cur = None

    try:

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

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        if search:

            query += """
                AND
                (
                    j.title ILIKE %s
                    OR j.company_name ILIKE %s
                    OR j.description ILIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend(
                [
                    search_value,
                    search_value,
                    search_value
                ]
            )

        # ----------------------------------------------------
        # JOB TYPE
        # ----------------------------------------------------

        if job_type:

            query += """
                AND j.job_type = %s
            """

            params.append(
                job_type
            )

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        if location:

            query += """
                AND j.location ILIKE %s
            """

            params.append(
                f"%{location}%"
            )

        query += """
            ORDER BY
                j.application_deadline ASC NULLS LAST,
                j.created_at DESC
        """

        cur.execute(
            query,
            params
        )

        jobs_list = cur.fetchall()

        return render_template(
            "jobs.html",
            jobs=jobs_list,
            search=search,
            job_type=job_type,
            location=location
        )

    except Exception as e:

        print(
            "JOBS ERROR:",
            e
        )

        if conn:
            conn.rollback()

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


# ============================================================
# JOB DETAILS
# ============================================================

@app.route(
    "/job/<int:job_id>"
)
@login_required
def job_details(job_id):

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # JOB
        # ----------------------------------------------------

        cur.execute(
            """
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
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Job not found.",
                "danger"
            )

            return redirect(
                url_for("jobs")
            )

        # ----------------------------------------------------
        # REQUIRED SKILLS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                js.job_skill_id,
                js.skill_id,
                js.importance,
                s.skill_name
            FROM job_skills js
            JOIN skills s
                ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY
                js.importance DESC,
                s.skill_name
            """,
            (job_id,)
        )

        required_skills = cur.fetchall()

        # ----------------------------------------------------
        # CHECK APPLICATION
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                application_id,
                status,
                applied_at
            FROM applications
            WHERE user_id = %s
            AND job_id = %s
            """,
            (
                user_id,
                job_id
            )
        )

        application = cur.fetchone()

        return render_template(
            "job_details.html",
            job=job,
            required_skills=required_skills,
            application=application
        )

    except Exception as e:

        print(
            "JOB DETAILS ERROR:",
            e
        )

        if conn:
            conn.rollback()

        flash(
            "Unable to load job details.",
            "danger"
        )

        return redirect(
            url_for("jobs")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# APPLY FOR JOB
# ============================================================

@app.route(
    "/apply/<int:job_id>",
    methods=["POST", "GET"]
)
@login_required
def apply(job_id):

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # CHECK JOB
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                job_id,
                title,
                is_active
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Job not found.",
                "danger"
            )

            return redirect(
                url_for("jobs")
            )

        if not job["is_active"]:

            flash(
                "This job is no longer active.",
                "warning"
            )

            return redirect(
                url_for(
                    "job_details",
                    job_id=job_id
                )
            )

        # ----------------------------------------------------
        # DUPLICATE APPLICATION CHECK
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT application_id
            FROM applications
            WHERE user_id = %s
            AND job_id = %s
            """,
            (
                user_id,
                job_id
            )
        )

        existing_application = cur.fetchone()

        if existing_application:

            flash(
                "You have already applied for this job.",
                "warning"
            )

            return redirect(
                url_for(
                    "job_details",
                    job_id=job_id
                )
            )

        # ----------------------------------------------------
        # INSERT APPLICATION
        # ----------------------------------------------------

        cur.execute(
            """
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
            """,
            (
                user_id,
                job_id
            )
        )

        conn.commit()

        flash(
            "Application submitted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "my_applications"
            )
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "APPLICATION ERROR:",
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


# ============================================================
# MY APPLICATIONS
# ============================================================

@app.route(
    "/my-applications"
)
@login_required
def my_applications():

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute(
            """
            SELECT
                a.application_id,
                a.job_id,
                a.status,
                a.applied_at,
                j.title,
                j.company_name,
                j.job_type,
                j.location,
                j.application_deadline
            FROM applications a
            JOIN jobs j
                ON a.job_id = j.job_id
            WHERE a.user_id = %s
            ORDER BY a.applied_at DESC
            """,
            (user_id,)
        )

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

        if conn:
            conn.rollback()

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


# ============================================================
# RECOMMENDATIONS
# ============================================================

@app.route(
    "/recommendations"
)
@login_required
def recommendations():

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # USER PROFILE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                preferred_role,
                preferred_location,
                education,
                degree,
                experience_years
            FROM user_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )

        profile = cur.fetchone()

        if not profile:

            profile = {}

        # ----------------------------------------------------
        # USER SKILLS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                us.skill_id,
                us.skill_level,
                us.proficiency,
                s.skill_name
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
            """,
            (user_id,)
        )

        user_skills = cur.fetchall()

        user_skill_ids = set()

        for skill in user_skills:

            user_skill_ids.add(
                skill["skill_id"]
            )

        # ----------------------------------------------------
        # ACTIVE JOBS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                job_id,
                title,
                company_name,
                description,
                job_type,
                location,
                experience_required,
                education_required,
                salary_min,
                salary_max,
                application_deadline,
                application_link,
                created_at
            FROM jobs
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            """
        )

        all_jobs = cur.fetchall()

        recommendations_list = []

        preferred_role = (
            profile.get("preferred_role")
            if profile
            else None
        )

        preferred_location = (
            profile.get("preferred_location")
            if profile
            else None
        )

        user_education = (
            profile.get("education")
            if profile
            else None
        )

        user_degree = (
            profile.get("degree")
            if profile
            else None
        )

        user_experience = (
            profile.get("experience_years")
            if profile
            else 0
        )

        if user_experience is None:
            user_experience = 0

        # ----------------------------------------------------
        # CALCULATE SCORE FOR EACH JOB
        # ----------------------------------------------------

        for job in all_jobs:

            job_id = job["job_id"]

            # ------------------------------------------------
            # JOB SKILLS
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    js.skill_id,
                    js.importance,
                    s.skill_name
                FROM job_skills js
                JOIN skills s
                    ON js.skill_id = s.skill_id
                WHERE js.job_id = %s
                """,
                (job_id,)
            )

            job_skills = cur.fetchall()

            # ------------------------------------------------
            # SKILL MATCH - 50%
            # ------------------------------------------------

            skill_score = 0

            if job_skills:

                total_importance = 0
                matched_importance = 0

                for skill in job_skills:

                    importance = skill["importance"]

                    if importance is None:
                        importance = 1

                    importance = max(
                        1,
                        min(
                            5,
                            importance
                        )
                    )

                    total_importance += importance

                    if skill["skill_id"] in user_skill_ids:

                        matched_importance += importance

                if total_importance > 0:

                    skill_score = (
                        matched_importance
                        / total_importance
                    ) * 100

            else:

                # If no skills are specified,
                # don't penalize the job completely.
                skill_score = 50

            # ------------------------------------------------
            # ROLE MATCH - 20%
            # ------------------------------------------------

            role_score = 0

            if preferred_role:

                job_title = (
                    job["title"] or ""
                ).lower()

                preferred_role_lower = (
                    preferred_role.lower()
                )

                if (
                    preferred_role_lower in job_title
                    or job_title in preferred_role_lower
                ):

                    role_score = 100

                else:

                    role_words = set(
                        preferred_role_lower.split()
                    )

                    title_words = set(
                        job_title.split()
                    )

                    if role_words.intersection(
                        title_words
                    ):

                        role_score = 70

            # ------------------------------------------------
            # LOCATION MATCH - 15%
            # ------------------------------------------------

            location_score = 0

            if preferred_location:

                job_location = (
                    job["location"] or ""
                ).lower()

                preferred_location_lower = (
                    preferred_location.lower()
                )

                if (
                    preferred_location_lower
                    in job_location
                ):

                    location_score = 100

                elif (
                    job_location
                    in preferred_location_lower
                ):

                    location_score = 100

                else:

                    preferred_words = set(
                        preferred_location_lower.split()
                    )

                    location_words = set(
                        job_location.split()
                    )

                    if preferred_words.intersection(
                        location_words
                    ):

                        location_score = 60

            # ------------------------------------------------
            # EDUCATION MATCH - 10%
            # ------------------------------------------------

            education_score = 0

            job_education = (
                job["education_required"]
                or ""
            ).lower()

            education_text = " ".join(
                [
                    str(user_education or ""),
                    str(user_degree or "")
                ]
            ).lower()

            if job_education:

                if education_text:

                    if (
                        job_education
                        in education_text
                        or education_text
                        in job_education
                    ):

                        education_score = 100

                    else:

                        education_words = set(
                            job_education.split()
                        )

                        user_education_words = set(
                            education_text.split()
                        )

                        if education_words.intersection(
                            user_education_words
                        ):

                            education_score = 60

            # ------------------------------------------------
            # EXPERIENCE MATCH - 5%
            # ------------------------------------------------

            experience_score = 0

            required_experience = (
                job["experience_required"]
                or ""
            ).lower()

            try:

                user_exp = float(
                    user_experience
                )

            except:

                user_exp = 0

            if not required_experience:

                experience_score = 100

            elif (
                "fresher"
                in required_experience
                or "0" in required_experience
            ):

                if user_exp == 0:

                    experience_score = 100

                else:

                    experience_score = 90

            else:

                numbers = re.findall(
                    r"\d+(?:\.\d+)?",
                    required_experience
                )

                if numbers:

                    required_exp = float(
                        numbers[0]
                    )

                    if user_exp >= required_exp:

                        experience_score = 100

                    elif user_exp >= (
                        required_exp * 0.5
                    ):

                        experience_score = 60

            # ------------------------------------------------
            # TOTAL SCORE
            # ------------------------------------------------

            total_score = (
                skill_score * 0.50
                + role_score * 0.20
                + location_score * 0.15
                + education_score * 0.10
                + experience_score * 0.05
            )

            total_score = round(
                total_score,
                2
            )

            # ------------------------------------------------
            # MATCH CATEGORY
            # ------------------------------------------------

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

            job_result = dict(job)

            job_result["match_score"] = (
                total_score
            )

            job_result["match_category"] = (
                match_category
            )

            job_result["skill_score"] = round(
                skill_score,
                2
            )

            job_result["role_score"] = round(
                role_score,
                2
            )

            job_result["location_score"] = round(
                location_score,
                2
            )

            job_result["education_score"] = round(
                education_score,
                2
            )

            job_result["experience_score"] = round(
                experience_score,
                2
            )

            recommendations_list.append(
                job_result
            )

        # ----------------------------------------------------
        # SORT BY MATCH SCORE
        # ----------------------------------------------------

        recommendations_list.sort(
            key=lambda x: x["match_score"],
            reverse=True
        )

        return render_template(
            "recommendations.html",
            recommendations=recommendations_list,
            profile=profile,
            user_skills=user_skills
        )

    except Exception as e:

        print(
            "RECOMMENDATIONS ERROR:",
            e
        )

        if conn:
            conn.rollback()

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


# ============================================================
# ADMIN - JOB LIST
# ============================================================

@app.route(
    "/admin/jobs"
)
@admin_required
def admin_jobs():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute(
            """
            SELECT
                job_id,
                title,
                company_name,
                job_type,
                location,
                experience_required,
                education_required,
                salary_min,
                salary_max,
                application_deadline,
                application_link,
                is_active,
                created_at
            FROM jobs
            ORDER BY created_at DESC
            """
        )

        jobs_list = cur.fetchall()

        return render_template(
            "admin_jobs.html",
            jobs=jobs_list
        )

    except Exception as e:

        print(
            "ADMIN JOBS ERROR:",
            e
        )

        if conn:
            conn.rollback()

        flash(
            "Unable to load jobs.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN - ADD JOB
# ============================================================

@app.route(
    "/admin/jobs/add",
    methods=["GET", "POST"]
)
@admin_required
def admin_add_job():

    conn = None
    cur = None

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        company_name = request.form.get(
            "company_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        job_type = request.form.get(
            "job_type",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        experience_required = request.form.get(
            "experience_required",
            ""
        ).strip()

        education_required = request.form.get(
            "education_required",
            ""
        ).strip()

        salary_min = request.form.get(
            "salary_min"
        )

        salary_max = request.form.get(
            "salary_max"
        )

        application_deadline = request.form.get(
            "application_deadline"
        )

        application_link = request.form.get(
            "application_link",
            ""
        ).strip()

        is_active = request.form.get(
            "is_active"
        )

        if is_active is None:
            is_active = True
        else:
            is_active = (
                is_active.lower()
                in ["true", "1", "yes", "on"]
            )

        if not title or not company_name:

            flash(
                "Job title and company name are required.",
                "danger"
            )

            return redirect(
                url_for("admin_add_job")
            )

        try:

            conn = get_db_connection()

            cur = conn.cursor(
                cursor_factory=RealDictCursor
            )

            cur.execute(
                """
                INSERT INTO jobs
                (
                    title,
                    company_name,
                    description,
                    job_type,
                    location,
                    experience_required,
                    education_required,
                    salary_min,
                    salary_max,
                    application_deadline,
                    application_link,
                    is_active
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
                    %s
                )
                RETURNING job_id
                """,
                (
                    title,
                    company_name,
                    description or None,
                    job_type or None,
                    location or None,
                    experience_required or None,
                    education_required or None,
                    salary_min or None,
                    salary_max or None,
                    application_deadline or None,
                    application_link or None,
                    is_active
                )
            )

            new_job = cur.fetchone()

            conn.commit()

            flash(
                "Job added successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "admin_job_skills",
                    job_id=new_job["job_id"]
                )
            )

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "ADMIN ADD JOB ERROR:",
                e
            )

            flash(
                "Unable to add job.",
                "danger"
            )

            return redirect(
                url_for("admin_add_job")
            )

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template(
        "admin_add_job.html"
    )


# ============================================================
# ADMIN - EDIT JOB
# ============================================================

@app.route(
    "/admin/jobs/edit/<int:job_id>",
    methods=["GET", "POST"]
)
@admin_required
def admin_edit_job(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        if request.method == "POST":

            title = request.form.get(
                "title",
                ""
            ).strip()

            company_name = request.form.get(
                "company_name",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            job_type = request.form.get(
                "job_type",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            experience_required = request.form.get(
                "experience_required",
                ""
            ).strip()

            education_required = request.form.get(
                "education_required",
                ""
            ).strip()

            salary_min = request.form.get(
                "salary_min"
            )

            salary_max = request.form.get(
                "salary_max"
            )

            application_deadline = request.form.get(
                "application_deadline"
            )

            application_link = request.form.get(
                "application_link",
                ""
            ).strip()

            is_active = request.form.get(
                "is_active"
            )

            if is_active is None:

                is_active = True

            else:

                is_active = (
                    is_active.lower()
                    in [
                        "true",
                        "1",
                        "yes",
                        "on"
                    ]
                )

            cur.execute(
                """
                UPDATE jobs
                SET
                    title = %s,
                    company_name = %s,
                    description = %s,
                    job_type = %s,
                    location = %s,
                    experience_required = %s,
                    education_required = %s,
                    salary_min = %s,
                    salary_max = %s,
                    application_deadline = %s,
                    application_link = %s,
                    is_active = %s
                WHERE job_id = %s
                """,
                (
                    title,
                    company_name,
                    description or None,
                    job_type or None,
                    location or None,
                    experience_required or None,
                    education_required or None,
                    salary_min or None,
                    salary_max or None,
                    application_deadline or None,
                    application_link or None,
                    is_active,
                    job_id
                )
            )

            conn.commit()

            flash(
                "Job updated successfully.",
                "success"
            )

            return redirect(
                url_for("admin_jobs")
            )

        # ----------------------------------------------------
        # GET JOB
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                job_id,
                title,
                company_name,
                description,
                job_type,
                location,
                experience_required,
                education_required,
                salary_min,
                salary_max,
                application_deadline,
                application_link,
                is_active,
                created_at
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Job not found.",
                "danger"
            )

            return redirect(
                url_for("admin_jobs")
            )

        return render_template(
            "admin_edit_job.html",
            job=job
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADMIN EDIT JOB ERROR:",
            e
        )

        flash(
            "Unable to edit job.",
            "danger"
        )

        return redirect(
            url_for("admin_jobs")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN - TOGGLE JOB STATUS
# ============================================================

@app.route(
    "/admin/jobs/toggle/<int:job_id>",
    methods=["POST", "GET"]
)
@admin_required
def admin_toggle_job(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE jobs
            SET
                is_active = NOT is_active
            WHERE job_id = %s
            """,
            (job_id,)
        )

        conn.commit()

        flash(
            "Job status updated.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADMIN TOGGLE JOB ERROR:",
            e
        )

        flash(
            "Unable to update job status.",
            "danger"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(
        url_for("admin_jobs")
    )


# ============================================================
# ADMIN - DELETE JOB
# ============================================================

@app.route(
    "/admin/jobs/delete/<int:job_id>",
    methods=["POST", "GET"]
)
@admin_required
def admin_delete_job(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        # ----------------------------------------------------
        # DELETE JOB SKILLS FIRST
        # ----------------------------------------------------

        cur.execute(
            """
            DELETE FROM job_skills
            WHERE job_id = %s
            """,
            (job_id,)
        )

        # ----------------------------------------------------
        # DELETE APPLICATIONS
        # ----------------------------------------------------

        cur.execute(
            """
            DELETE FROM applications
            WHERE job_id = %s
            """,
            (job_id,)
        )

        # ----------------------------------------------------
        # DELETE JOB
        # ----------------------------------------------------

        cur.execute(
            """
            DELETE FROM jobs
            WHERE job_id = %s
            """,
            (job_id,)
        )

        conn.commit()

        flash(
            "Job deleted successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADMIN DELETE JOB ERROR:",
            e
        )

        flash(
            "Unable to delete job.",
            "danger"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(
        url_for("admin_jobs")
    )


# ============================================================
# ADMIN - MANAGE JOB SKILLS
# ============================================================

@app.route(
    "/admin/jobs/<int:job_id>/skills",
    methods=["GET", "POST"]
)
@admin_required
def admin_job_skills(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # CHECK JOB
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                job_id,
                title,
                company_name
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Job not found.",
                "danger"
            )

            return redirect(
                url_for("admin_jobs")
            )

        # ----------------------------------------------------
        # ADD SKILL
        # ----------------------------------------------------

        if request.method == "POST":

            skill_id = request.form.get(
                "skill_id"
            )

            importance = request.form.get(
                "importance",
                "1"
            )

            try:

                importance = int(
                    importance
                )

            except:

                importance = 1

            importance = max(
                1,
                min(
                    5,
                    importance
                )
            )

            if not skill_id:

                flash(
                    "Please select a skill.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_job_skills",
                        job_id=job_id
                    )
                )

            # ----------------------------------------------
            # CHECK EXISTING SKILL
            # ----------------------------------------------

            cur.execute(
                """
                SELECT job_skill_id
                FROM job_skills
                WHERE job_id = %s
                AND skill_id = %s
                """,
                (
                    job_id,
                    skill_id
                )
            )

            existing = cur.fetchone()

            if existing:

                cur.execute(
                    """
                    UPDATE job_skills
                    SET
                        importance = %s
                    WHERE job_id = %s
                    AND skill_id = %s
                    """,
                    (
                        importance,
                        job_id,
                        skill_id
                    )
                )

            else:

                cur.execute(
                    """
                    INSERT INTO job_skills
                    (
                        job_id,
                        skill_id,
                        importance
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        job_id,
                        skill_id,
                        importance
                    )
                )

            conn.commit()

            flash(
                "Job skill saved successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "admin_job_skills",
                    job_id=job_id
                )
            )

        # ----------------------------------------------------
        # CURRENT JOB SKILLS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                js.job_skill_id,
                js.job_id,
                js.skill_id,
                js.importance,
                s.skill_name
            FROM job_skills js
            JOIN skills s
                ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY
                js.importance DESC,
                s.skill_name
            """,
            (job_id,)
        )

        job_skills = cur.fetchall()

        # ----------------------------------------------------
        # ALL SKILLS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                skill_id,
                skill_name
            FROM skills
            ORDER BY skill_name
            """
        )

        all_skills = cur.fetchall()

        return render_template(
            "admin_job_skills.html",
            job=job,
            job_skills=job_skills,
            all_skills=all_skills
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADMIN JOB SKILLS ERROR:",
            e
        )

        flash(
            "Unable to manage job skills.",
            "danger"
        )

        return redirect(
            url_for("admin_jobs")
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN - DELETE JOB SKILL
# ============================================================

@app.route(
    "/admin/jobs/<int:job_id>/skills/delete/<int:job_skill_id>",
    methods=["POST", "GET"]
)
@admin_required
def admin_delete_job_skill(
    job_id,
    job_skill_id
):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM job_skills
            WHERE job_skill_id = %s
            AND job_id = %s
            """,
            (
                job_skill_id,
                job_id
            )
        )

        conn.commit()

        flash(
            "Job skill removed successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADMIN DELETE JOB SKILL ERROR:",
            e
        )

        flash(
            "Unable to remove job skill.",
            "danger"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(
        url_for(
            "admin_job_skills",
            job_id=job_id
        )
    )


# ============================================================
# DATABASE TEST
# ============================================================

@app.route("/test-db")
def test_db():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                version()
            """
        )

        result = cur.fetchone()

        return (
            "CareerMatch Database Connected<br><br>"
            + str(result[0])
        )

    except Exception as e:

        print(
            "DATABASE TEST ERROR:",
            e
        )

        return (
            "Database connection failed:<br><br>"
            + str(e)
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "application": "CareerMatch"
    }


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "index.html"
    ), 404


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    print(
        "500 INTERNAL SERVER ERROR:",
        error
    )

    return (
        "Internal Server Error. "
        "Please check the Flask terminal for the exact error."
    ), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print(
        "=============================================="
    )

    print(
        "CareerMatch Application Starting..."
    )

    print(
        "=============================================="
    )

    try:

        test_conn = get_db_connection()

        test_conn.close()

        print(
            "CareerMatch Database Connected"
        )

    except Exception as e:

        print(
            "Database Connection Failed:",
            e
        )

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )