
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
app.config.from_object(Config)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    return psycopg2.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        database=app.config["DB_NAME"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"]
    )


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# ADMIN REQUIRED
# ============================================================

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    if "user_id" in session:

        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        conn = None
        cur = None

        try:

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

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
                flash("Email already registered.", "error")
                return redirect(url_for("register"))

            password_hash = generate_password_hash(password)

            cur.execute(
                """
                INSERT INTO users
                (
                    full_name,
                    email,
                    password_hash,
                    role
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    full_name,
                    email,
                    password_hash,
                    "user"
                )
            )

            conn.commit()

            flash("Registration successful. Please login.", "success")

            return redirect(url_for("login"))

        except Exception as e:

            if conn:
                conn.rollback()

            print("REGISTER ERROR:", e)

            flash(
                "Registration failed: " + str(e),
                "error"
            )

            return redirect(url_for("register"))

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = None
        cur = None

        try:

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

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

                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            if not check_password_hash(
                user["password_hash"],
                password
            ):

                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        except Exception as e:

            print("LOGIN ERROR:", e)

            flash(
                "Login failed: " + str(e),
                "error"
            )

            return redirect(url_for("login"))

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("index"))


# ============================================================
# USER DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        user_id = session["user_id"]

        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM jobs
            WHERE is_active = TRUE
            """
        )

        jobs_count = cur.fetchone()["count"]

        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM applications
            WHERE user_id = %s
            """,
            (user_id,)
        )

        applications_count = cur.fetchone()["count"]

        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM jobs
            WHERE is_active = TRUE
            """
        )

        recommendations_count = cur.fetchone()["count"]

        return render_template(
            "dashboard.html",
            jobs_count=jobs_count,
            applications_count=applications_count,
            recommendations_count=recommendations_count
        )

    except Exception as e:

        print("DASHBOARD ERROR:", e)

        flash(
            "Unable to load dashboard: " + str(e),
            "error"
        )

        return render_template(
            "dashboard.html",
            jobs_count=0,
            applications_count=0,
            recommendations_count=0
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
        cur = conn.cursor(cursor_factory=RealDictCursor)

        user_id = session["user_id"]

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

        user_data = cur.fetchone()

        if not user_data:

            flash("User not found.", "error")

            return redirect(url_for("dashboard"))

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

        if profile_data:

            user_profile = dict(profile_data)

            user_profile.update({
                "user_id": user_data["user_id"],
                "full_name": user_data["full_name"],
                "email": user_data["email"],
                "role": user_data["role"]
            })

        else:

            user_profile = {
                "profile_id": None,
                "user_id": user_data["user_id"],
                "full_name": user_data["full_name"],
                "email": user_data["email"],
                "role": user_data["role"],
                "phone": None,
                "education": None,
                "degree": None,
                "graduation_year": None,
                "experience_years": None,
                "preferred_role": None,
                "preferred_location": None,
                "bio": None,
                "resume_path": None,
                "profile_image": None,
                "updated_at": None,
                "date_of_birth": None,
                "gender": None,
                "college_name": None,
                "resume_url": None,
                "profile_summary": None
            }

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

        return render_template(
            "profile.html",
            user_profile=user_profile,
            all_skills=all_skills,
            user_skills=user_skills
        )

    except Exception as e:

        print("PROFILE ERROR:", e)

        flash(
            "Unable to load profile: " + str(e),
            "error"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# UPDATE PROFILE
# ============================================================

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        phone = request.form.get("phone", "").strip()
        education = request.form.get("education", "").strip()
        degree = request.form.get("degree", "").strip()
        graduation_year = request.form.get("graduation_year") or None
        experience_years = request.form.get("experience_years") or None
        preferred_role = request.form.get("preferred_role", "").strip()
        preferred_location = request.form.get(
            "preferred_location",
            ""
        ).strip()
        bio = request.form.get("bio", "").strip()
        date_of_birth = request.form.get("date_of_birth") or None
        gender = request.form.get("gender", "").strip()
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
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT profile_id
            FROM user_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )

        existing_profile = cur.fetchone()

        if existing_profile:

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
                    phone,
                    education,
                    degree,
                    graduation_year,
                    experience_years,
                    preferred_role,
                    preferred_location,
                    bio,
                    date_of_birth,
                    gender,
                    college_name,
                    resume_url,
                    profile_summary,
                    user_id
                )
            )

        else:

            cur.execute(
                """
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
                    bio,
                    date_of_birth,
                    gender,
                    college_name,
                    resume_url,
                    profile_summary,
                    updated_at
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    user_id,
                    phone,
                    education,
                    degree,
                    graduation_year,
                    experience_years,
                    preferred_role,
                    preferred_location,
                    bio,
                    date_of_birth,
                    gender,
                    college_name,
                    resume_url,
                    profile_summary
                )
            )

        conn.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(url_for("profile"))

    except Exception as e:

        if conn:
            conn.rollback()

        print("UPDATE PROFILE ERROR:", e)

        flash(
            "Unable to update profile: " + str(e),
            "error"
        )

        return redirect(url_for("profile"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADD USER SKILL
# ============================================================

@app.route("/profile/add-skill", methods=["POST"])
@login_required
def add_skill():

    conn = None
    cur = None

    try:

        user_id = session["user_id"]

        skill_id = request.form.get("skill_id")

        skill_level = request.form.get(
            "skill_level",
            "Beginner"
        )

        proficiency = request.form.get(
            "proficiency"
        ) or None

        if not skill_id:

            flash(
                "Please select a skill.",
                "error"
            )

            return redirect(
                url_for("profile")
            )

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

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

        existing_skill = cur.fetchone()

        if existing_skill:

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
                    proficiency,
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
                VALUES (%s, %s, %s, %s)
                """,
                (
                    user_id,
                    skill_id,
                    skill_level,
                    proficiency
                )
            )

        conn.commit()

        flash(
            "Skill added successfully.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("ADD SKILL ERROR:", e)

        flash(
            "Unable to add skill: " + str(e),
            "error"
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
# REMOVE USER SKILL
# ============================================================

@app.route(
    "/profile/remove-skill/<int:skill_id>",
    methods=["POST"]
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

        return redirect(
            url_for("profile")
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "REMOVE SKILL ERROR:",
            e
        )

        flash(
            "Unable to remove skill: " + str(e),
            "error"
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
# JOBS
# ============================================================

@app.route("/jobs")
@login_required
def jobs():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

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

        query = """
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
            WHERE is_active = TRUE
        """

        params = []

        if search:

            query += """
                AND (
                    LOWER(title) LIKE LOWER(%s)
                    OR LOWER(company_name) LIKE LOWER(%s)
                    OR LOWER(description) LIKE LOWER(%s)
                )
            """

            search_value = "%" + search + "%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])

        if job_type:

            query += """
                AND LOWER(job_type) = LOWER(%s)
            """

            params.append(job_type)

        if location:

            query += """
                AND LOWER(location) LIKE LOWER(%s)
            """

            params.append(
                "%" + location + "%"
            )

        query += """
            ORDER BY created_at DESC
        """

        cur.execute(
            query,
            tuple(params)
        )

        jobs_list = cur.fetchall()

        return render_template(
            "jobs.html",
            jobs=jobs_list
        )

    except Exception as e:

        print(
            "JOBS ERROR:",
            e
        )

        flash(
            "Unable to load jobs: " + str(e),
            "error"
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

@app.route("/jobs/<int:job_id>")
@login_required
def job_details(job_id):

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
                "error"
            )

            return redirect(
                url_for("jobs")
            )

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
            ORDER BY js.importance DESC
            """,
            (job_id,)
        )

        skills = cur.fetchall()

        cur.execute(
            """
            SELECT application_id
            FROM applications
            WHERE user_id = %s
              AND job_id = %s
            """,
            (
                session["user_id"],
                job_id
            )
        )

        application = cur.fetchone()

        return render_template(
            "job_details.html",
            job=job,
            skills=skills,
            application=application
        )

    except Exception as e:

        print(
            "JOB DETAILS ERROR:",
            e
        )

        flash(
            "Unable to load job details: " + str(e),
            "error"
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
    "/jobs/<int:job_id>/apply",
    methods=["POST"]
)
@login_required
def apply_job(job_id):

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
            SELECT job_id
            FROM jobs
            WHERE job_id = %s
              AND is_active = TRUE
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Job is not available.",
                "error"
            )

            return redirect(
                url_for("jobs")
            )

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
                "error"
            )

            return redirect(
                url_for(
                    "job_details",
                    job_id=job_id
                )
            )

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
                %s,
                CURRENT_TIMESTAMP
            )
            """,
            (
                user_id,
                job_id,
                "Applied"
            )
        )

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
            "APPLY JOB ERROR:",
            e
        )

        flash(
            "Unable to apply: " + str(e),
            "error"
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

@app.route("/my-applications")
@login_required
def my_applications():

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
                a.application_id,
                a.status,
                a.applied_at,
                j.job_id,
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
            (session["user_id"],)
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

        flash(
            "Unable to load applications: " + str(e),
            "error"
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

@app.route("/recommendations")
@login_required
def recommendations():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        user_id = session["user_id"]

        # ====================================================
        # USER PROFILE
        # ====================================================

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

        # ====================================================
        # USER SKILLS
        # ====================================================

        cur.execute(
            """
            SELECT
                us.skill_id,
                s.skill_name,
                us.skill_level,
                us.proficiency
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
            """,
            (user_id,)
        )

        user_skills = cur.fetchall()

        user_skill_ids = {
            skill["skill_id"]
            for skill in user_skills
        }

        # ====================================================
        # ACTIVE JOBS
        # ====================================================

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
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            """
        )

        jobs_list = cur.fetchall()

        recommendations_list = []

        # ====================================================
        # CALCULATE MATCHING
        # ====================================================

        for job in jobs_list:

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
                ORDER BY js.importance DESC
                """,
                (job["job_id"],)
            )

            required_skills = cur.fetchall()

            matched_skills = []
            missing_skills = []

            for skill in required_skills:

                if skill["skill_id"] in user_skill_ids:

                    matched_skills.append(
                        skill["skill_name"]
                    )

                else:

                    missing_skills.append(
                        skill["skill_name"]
                    )

            # ------------------------------------------------
            # SKILL SCORE
            # ------------------------------------------------

            if required_skills:

                total_importance = sum(
                    float(
                        skill["importance"] or 1
                    )
                    for skill in required_skills
                )

                matched_importance = sum(
                    float(
                        skill["importance"] or 1
                    )
                    for skill in required_skills
                    if skill["skill_id"] in user_skill_ids
                )

                if total_importance > 0:

                    skill_score = (
                        matched_importance
                        / total_importance
                    ) * 100

                else:

                    skill_score = 0

            else:

                skill_score = 100

            # ------------------------------------------------
            # ROLE SCORE
            # ------------------------------------------------

            role_score = 0

            preferred_role = (
                profile["preferred_role"]
                if profile
                else None
            )

            if preferred_role and job["title"]:

                preferred_role_lower = (
                    preferred_role
                    .lower()
                    .strip()
                )

                job_title_lower = (
                    job["title"]
                    .lower()
                    .strip()
                )

                if preferred_role_lower in job_title_lower:

                    role_score = 100

                elif job_title_lower in preferred_role_lower:

                    role_score = 100

                else:

                    role_words = set(
                        preferred_role_lower.split()
                    )

                    job_words = set(
                        job_title_lower.split()
                    )

                    if role_words & job_words:

                        role_score = 50

            # ------------------------------------------------
            # LOCATION SCORE
            # ------------------------------------------------

            location_score = 0

            preferred_location = (
                profile["preferred_location"]
                if profile
                else None
            )

            if preferred_location and job["location"]:

                preferred_location_lower = (
                    preferred_location
                    .lower()
                    .strip()
                )

                job_location_lower = (
                    job["location"]
                    .lower()
                    .strip()
                )

                if preferred_location_lower in job_location_lower:

                    location_score = 100

                elif job_location_lower in preferred_location_lower:

                    location_score = 100

                else:

                    preferred_location_words = set(
                        preferred_location_lower.split()
                    )

                    job_location_words = set(
                        job_location_lower.split()
                    )

                    if (
                        preferred_location_words
                        & job_location_words
                    ):

                        location_score = 50

            # ------------------------------------------------
            # EDUCATION SCORE
            # ------------------------------------------------

            education_score = 0

            if profile and job["education_required"]:

                job_education = (
                    job["education_required"]
                    .lower()
                )

                education_values = []

                if profile["education"]:

                    education_values.append(
                        profile["education"].lower()
                    )

                if profile["degree"]:

                    education_values.append(
                        profile["degree"].lower()
                    )

                for education in education_values:

                    if education in job_education:

                        education_score = 100
                        break

                    education_words = set(
                        education.split()
                    )

                    job_education_words = set(
                        job_education.split()
                    )

                    if (
                        education_words
                        & job_education_words
                    ):

                        education_score = 50
                        break

            # ------------------------------------------------
            # EXPERIENCE SCORE
            # ------------------------------------------------

            experience_score = 0

            if profile:

                if profile["experience_years"]:

                    user_experience = float(
                        profile["experience_years"]
                    )

                else:

                    user_experience = 0

                required_experience = (
                    job["experience_required"]
                    or ""
                )

                required_experience = (
                    required_experience.lower()
                )

                if not required_experience:

                    experience_score = 100

                elif "fresher" in required_experience:

                    experience_score = 100

                elif "0" in required_experience:

                    experience_score = 100

                elif user_experience > 0:

                    experience_score = 50

            # =================================================
            # FINAL MATCH SCORE
            # =================================================

            match_score = (
                skill_score * 0.50
                + role_score * 0.20
                + location_score * 0.15
                + education_score * 0.10
                + experience_score * 0.05
            )

            match_score = round(
                match_score,
                2
            )

            # =================================================
            # MATCH CATEGORY
            # =================================================

            if match_score >= 90:

                match_category = "Excellent Match"

            elif match_score >= 75:

                match_category = "Strong Match"

            elif match_score >= 60:

                match_category = "Good Match"

            elif match_score >= 40:

                match_category = "Partial Match"

            else:

                match_category = "Low Match"

            recommendation = dict(job)

            recommendation.update({

                "match_score":
                    match_score,

                "match_category":
                    match_category,

                "matched_skills":
                    matched_skills,

                "missing_skills":
                    missing_skills,

                "skill_score":
                    round(
                        skill_score,
                        2
                    ),

                "role_score":
                    round(
                        role_score,
                        2
                    ),

                "location_score":
                    round(
                        location_score,
                        2
                    ),

                "education_score":
                    round(
                        education_score,
                        2
                    ),

                "experience_score":
                    round(
                        experience_score,
                        2
                    )
            })

            recommendations_list.append(
                recommendation
            )

        recommendations_list.sort(
            key=lambda job: job["match_score"],
            reverse=True
        )

        return render_template(
            "recommendations.html",
            recommendations=recommendations_list
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "RECOMMENDATIONS ERROR:",
            e
        )

        flash(
            "Unable to generate recommendations: "
            + str(e),
            "error"
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
# ADMIN DASHBOARD
# ============================================================


@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Total users
        cur.execute("""
            SELECT COUNT(*) AS count
            FROM users
            WHERE role = 'user'
        """)
        users_count = cur.fetchone()["count"]

        # Total jobs
        cur.execute("""
            SELECT COUNT(*) AS count
            FROM jobs
        """)
        jobs_count = cur.fetchone()["count"]

        # Total applications
        cur.execute("""
            SELECT COUNT(*) AS count
            FROM applications
        """)
        applications_count = cur.fetchone()["count"]

        # Active jobs
        cur.execute("""
            SELECT COUNT(*) AS count
            FROM jobs
            WHERE is_active = TRUE
        """)
        active_jobs_count = cur.fetchone()["count"]

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
            ORDER BY created_at DESC NULLS LAST,
                     job_id DESC
            LIMIT 5
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
            ORDER BY a.applied_at DESC NULLS LAST,
                     a.application_id DESC
            LIMIT 5
        """)
        recent_applications = cur.fetchall()

        return render_template(
            "admin_dashboard.html",
            users_count=users_count,
            jobs_count=jobs_count,
            applications_count=applications_count,
            active_jobs_count=active_jobs_count,
            recent_jobs=recent_jobs,
            recent_applications=recent_applications
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN DASHBOARD ERROR:", e)

        flash(
            "Unable to load admin dashboard: " + str(e),
            "error"
        )

        return redirect(url_for("index"))

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN USERS
# ============================================================

@app.route("/admin/users")
@admin_required
def admin_users():

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
                role,
                created_at
            FROM users
            ORDER BY created_at DESC
            """
        )

        users = cur.fetchall()

        return render_template(
            "admin_users.html",
            users=users
        )

    except Exception as e:

        print(
            "ADMIN USERS ERROR:",
            e
        )

        flash(
            "Unable to load users: " + str(e),
            "error"
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
# ADMIN JOBS
# ============================================================

@app.route("/admin/jobs")
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

        flash(
            "Unable to load jobs: " + str(e),
            "error"
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
# ADMIN ADD JOB
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

        try:

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

            salary_min = (
                request.form.get("salary_min")
                or None
            )

            salary_max = (
                request.form.get("salary_max")
                or None
            )

            application_deadline = (
                request.form.get(
                    "application_deadline"
                )
                or None
            )

            application_link = request.form.get(
                "application_link",
                ""
            ).strip()

            is_active = (
                request.form.get("is_active")
                == "on"
            )

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
                    is_active,
                    created_at
                )
                VALUES
                (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP
                )
                RETURNING job_id
                """,
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
                "Unable to add job: " + str(e),
                "error"
            )

            return redirect(
                url_for("admin_jobs")
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
# ADMIN EDIT JOB
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

        # ----------------------------------------------------
        # UPDATE JOB
        # ----------------------------------------------------

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

            salary_min = (
                request.form.get("salary_min")
                or None
            )

            salary_max = (
                request.form.get("salary_max")
                or None
            )

            application_deadline = (
                request.form.get(
                    "application_deadline"
                )
                or None
            )

            application_link = request.form.get(
                "application_link",
                ""
            ).strip()

            # Checkbox:
            # checked = active
            # unchecked = inactive
            is_active = (
                "is_active" in request.form
            )

            # ------------------------------------------------
            # UPDATE DATABASE
            # ------------------------------------------------

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
                    job_id
                )
            )

            conn.commit()

            flash(
                "Opportunity updated successfully.",
                "success"
            )

            return redirect(
                url_for("admin_jobs")
            )

        # ----------------------------------------------------
        # LOAD JOB
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
                is_active
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Opportunity not found.",
                "error"
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
            "Unable to edit opportunity: " + str(e),
            "error"
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
# ADMIN TOGGLE JOB STATUS
# ============================================================

@app.route(
    "/admin/jobs/toggle/<int:job_id>",
    methods=["POST"]
)
@admin_required
def admin_toggle_job(job_id):

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
                is_active
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,)
        )

        job = cur.fetchone()

        if not job:

            flash(
                "Opportunity not found.",
                "error"
            )

            return redirect(
                url_for("admin_jobs")
            )

        new_status = not job["is_active"]

        cur.execute(
            """
            UPDATE jobs
            SET is_active = %s
            WHERE job_id = %s
            """,
            (
                new_status,
                job_id
            )
        )

        conn.commit()

        if new_status:

            flash(
                "Opportunity activated successfully.",
                "success"
            )

        else:

            flash(
                "Opportunity deactivated successfully.",
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
            "Unable to change opportunity status: "
            + str(e),
            "error"
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
# ADMIN DELETE JOB
# ============================================================

@app.route(
    "/admin/jobs/delete/<int:job_id>",
    methods=["POST"]
)
@admin_required
def admin_delete_job(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        # Delete applications first
        cur.execute(
            """
            DELETE FROM applications
            WHERE job_id = %s
            """,
            (job_id,)
        )

        # Delete job skills
        cur.execute(
            """
            DELETE FROM job_skills
            WHERE job_id = %s
            """,
            (job_id,)
        )

        # Delete job
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
            "Unable to delete job: " + str(e),
            "error"
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
# ADMIN MANAGE JOB SKILLS
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
        # JOB
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
                "error"
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

            importance = (
                request.form.get(
                    "importance"
                )
                or 1
            )

            if not skill_id:

                flash(
                    "Please select a skill.",
                    "error"
                )

                return redirect(
                    url_for(
                        "admin_job_skills",
                        job_id=job_id
                    )
                )

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
                    SET importance = %s
                    WHERE job_skill_id = %s
                    """,
                    (
                        importance,
                        existing["job_skill_id"]
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
                    (%s, %s, %s)
                    """,
                    (
                        job_id,
                        skill_id,
                        importance
                    )
                )

            conn.commit()

            flash(
                "Job skill added successfully.",
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
                js.skill_id,
                js.importance,
                s.skill_name
            FROM job_skills js
            JOIN skills s
                ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY js.importance DESC
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
            "Unable to manage job skills: "
            + str(e),
            "error"
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
# ADMIN DELETE JOB SKILL
# ============================================================

@app.route(
    "/admin/jobs/<int:job_id>/skills/delete/<int:job_skill_id>",
    methods=["POST"]
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
            "Job skill deleted successfully.",
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
            "Unable to delete job skill: "
            + str(e),
            "error"
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
# ADMIN APPLICATIONS
# ============================================================

@app.route("/admin/applications")
@admin_required
def admin_applications():

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
                a.application_id,
                a.status,
                a.applied_at,
                u.full_name,
                u.email,
                j.job_id,
                j.title,
                j.company_name
            FROM applications a
            JOIN users u
                ON a.user_id = u.user_id
            JOIN jobs j
                ON a.job_id = j.job_id
            ORDER BY a.applied_at DESC
            """
        )

        applications = cur.fetchall()

        return render_template(
            "admin_applications.html",
            applications=applications
        )

    except Exception as e:

        print(
            "ADMIN APPLICATIONS ERROR:",
            e
        )

        flash(
            "Unable to load applications: "
            + str(e),
            "error"
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
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )

