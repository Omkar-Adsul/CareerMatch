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
            return render_template("register.html")

        conn = None
        cur = None

        try:

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT user_id
                FROM users
                WHERE email = %s
            """, (email,))

            existing_user = cur.fetchone()

            if existing_user:
                flash("Email already registered.", "error")
                return render_template("register.html")

            password_hash = generate_password_hash(password)

            cur.execute("""
                INSERT INTO users
                (
                    full_name,
                    email,
                    password_hash,
                    role,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'user',
                    CURRENT_TIMESTAMP
                )
            """, (
                full_name,
                email,
                password_hash
            ))

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
                "Registration failed: " + str(e),
                "error"
            )

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
                flash("Invalid email or password.", "error")
                return render_template("login.html")

            if not check_password_hash(
                user["password_hash"],
                password
            ):
                flash("Invalid email or password.", "error")
                return render_template("login.html")

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

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute("""
            SELECT COUNT(*) AS total_jobs
            FROM jobs
            WHERE is_active = TRUE
        """)

        total_jobs = cur.fetchone()["total_jobs"]

        cur.execute("""
            SELECT COUNT(*) AS total_applications
            FROM applications
            WHERE user_id = %s
        """, (session["user_id"],))

        total_applications = cur.fetchone()["total_applications"]

        cur.execute("""
            SELECT COUNT(*) AS total_recommendations
            FROM jobs
            WHERE is_active = TRUE
        """)

        total_recommendations = cur.fetchone()["total_recommendations"]

        return render_template(
            "dashboard.html",
            total_jobs=total_jobs,
            total_applications=total_applications,
            total_recommendations=total_recommendations
        )

    except Exception as e:

        print("DASHBOARD ERROR:", e)

        flash(
            "Unable to load dashboard.",
            "error"
        )

        return redirect(url_for("index"))

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

        # Total users
        cur.execute("""
            SELECT COUNT(*) AS total_users
            FROM users
            WHERE role <> 'admin'
        """)

        total_users = cur.fetchone()["total_users"]

        # Total jobs
        cur.execute("""
            SELECT COUNT(*) AS total_jobs
            FROM jobs
        """)

        total_jobs = cur.fetchone()["total_jobs"]

        # Active jobs
        cur.execute("""
            SELECT COUNT(*) AS active_jobs
            FROM jobs
            WHERE is_active = TRUE
        """)

        active_jobs = cur.fetchone()["active_jobs"]

        # Applications
        cur.execute("""
            SELECT COUNT(*) AS total_applications
            FROM applications
        """)

        total_applications = cur.fetchone()["total_applications"]

        # Recent jobs
        cur.execute("""
            SELECT
                job_id,
                title,
                company_name,
                job_type,
                location,
                application_deadline,
                is_active,
                created_at
            FROM jobs
            ORDER BY created_at DESC
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
            ORDER BY a.applied_at DESC
            LIMIT 5
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

        cur.execute("""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                p.*
            FROM users u
            LEFT JOIN user_profiles p
                ON u.user_id = p.user_id
            WHERE u.user_id = %s
        """, (session["user_id"],))

        profile_data = cur.fetchone()

        cur.execute("""
            SELECT
                skill_id,
                skill_name
            FROM skills
            ORDER BY skill_name
        """)

        skills = cur.fetchall()

        cur.execute("""
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
        """, (session["user_id"],))

        user_skills = cur.fetchall()

        return render_template(
            "profile.html",
            profile=profile_data,
            skills=skills,
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
# PROFILE UPDATE
# ============================================================

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():

    conn = None
    cur = None

    try:

        phone = request.form.get("phone")
        education = request.form.get("education")
        degree = request.form.get("degree")
        graduation_year = request.form.get("graduation_year") or None
        experience_years = request.form.get("experience_years") or None
        preferred_role = request.form.get("preferred_role")
        preferred_location = request.form.get("preferred_location")
        bio = request.form.get("bio")
        date_of_birth = request.form.get("date_of_birth") or None
        gender = request.form.get("gender")
        college_name = request.form.get("college_name")
        resume_url = request.form.get("resume_url")
        profile_summary = request.form.get("profile_summary")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT profile_id
            FROM user_profiles
            WHERE user_id = %s
        """, (session["user_id"],))

        existing = cur.fetchone()

        if existing:

            cur.execute("""
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
            """, (
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
                session["user_id"]
            ))

        else:

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
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    CURRENT_TIMESTAMP
                )
            """, (
                session["user_id"],
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
            ))

        conn.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("PROFILE UPDATE ERROR:", e)

        flash(
            "Unable to update profile: " + str(e),
            "error"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(url_for("profile"))


# ============================================================
# ADD USER SKILL
# ============================================================

@app.route("/profile/add-skill", methods=["POST"])
@login_required
def add_skill():

    conn = None
    cur = None

    try:

        skill_id = request.form.get("skill_id")
        skill_level = request.form.get("skill_level")
        proficiency = request.form.get("proficiency")

        if not skill_id:
            flash("Please select a skill.", "error")
            return redirect(url_for("profile"))

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_skill_id
            FROM user_skills
            WHERE user_id = %s
            AND skill_id = %s
        """, (
            session["user_id"],
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
                skill_level,
                proficiency,
                session["user_id"],
                skill_id
            ))

        else:

            cur.execute("""
                INSERT INTO user_skills
                (
                    user_id,
                    skill_id,
                    skill_level,
                    proficiency
                )
                VALUES (%s, %s, %s, %s)
            """, (
                session["user_id"],
                skill_id,
                skill_level,
                proficiency
            ))

        conn.commit()

        flash(
            "Skill added successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("ADD SKILL ERROR:", e)

        flash(
            "Unable to add skill: " + str(e),
            "error"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(url_for("profile"))


# ============================================================
# REMOVE USER SKILL
# ============================================================

@app.route("/profile/remove-skill/<int:skill_id>", methods=["POST"])
@login_required
def remove_skill(skill_id):

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
            session["user_id"],
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

        print("REMOVE SKILL ERROR:", e)

        flash(
            "Unable to remove skill: " + str(e),
            "error"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

    return redirect(url_for("profile"))


# ============================================================
# JOBS - USER
# ============================================================

@app.route("/jobs")
@login_required
def jobs():

    conn = None
    cur = None

    try:

        search = request.args.get("search", "").strip()
        job_type = request.args.get("job_type", "").strip()
        location = request.args.get("location", "").strip()

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

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
                    title ILIKE %s
                    OR company_name ILIKE %s
                    OR description ILIKE %s
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
                AND job_type = %s
            """

            params.append(job_type)

        if location:

            query += """
                AND location ILIKE %s
            """

            params.append("%" + location + "%")

        query += """
            ORDER BY
                application_deadline ASC NULLS LAST,
                created_at DESC
        """

        cur.execute(query, params)

        job_list = cur.fetchall()

        return render_template(
            "jobs.html",
            jobs=job_list,
            search=search,
            job_type=job_type,
            location=location
        )

    except Exception as e:

        print("JOBS ERROR:", e)

        flash(
            "Unable to load jobs: " + str(e),
            "error"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# JOB DETAILS
# ============================================================

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

        cur.execute("""
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
        """, (job_id,))

        job = cur.fetchone()

        if not job:
            flash("Job not found.", "error")
            return redirect(url_for("jobs"))

        cur.execute("""
            SELECT
                js.skill_id,
                s.skill_name,
                js.importance
            FROM job_skills js
            JOIN skills s
                ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY js.importance DESC, s.skill_name
        """, (job_id,))

        required_skills = cur.fetchall()

        cur.execute("""
            SELECT application_id
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

        print("JOB DETAILS ERROR:", e)

        flash(
            "Unable to load job details: " + str(e),
            "error"
        )

        return redirect(url_for("jobs"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# APPLY FOR JOB
# ============================================================

@app.route("/apply/<int:job_id>", methods=["POST"])
@login_required
def apply(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute("""
            SELECT job_id
            FROM jobs
            WHERE job_id = %s
            AND is_active = TRUE
        """, (job_id,))

        job = cur.fetchone()

        if not job:
            flash(
                "This opportunity is not available.",
                "error"
            )
            return redirect(url_for("jobs"))

        cur.execute("""
            SELECT application_id
            FROM applications
            WHERE user_id = %s
            AND job_id = %s
        """, (
            session["user_id"],
            job_id
        ))

        existing = cur.fetchone()

        if existing:
            flash(
                "You have already applied for this opportunity.",
                "error"
            )
            return redirect(
                url_for("job_details", job_id=job_id)
            )

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
            session["user_id"],
            job_id
        ))

        conn.commit()

        flash(
            "Application submitted successfully.",
            "success"
        )

        return redirect(url_for("my_applications"))

    except Exception as e:

        if conn:
            conn.rollback()

        print("APPLY ERROR:", e)

        flash(
            "Unable to apply: " + str(e),
            "error"
        )

        return redirect(
            url_for("job_details", job_id=job_id)
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

        cur.execute("""
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
        """, (session["user_id"],))

        applications = cur.fetchall()

        return render_template(
            "my_applications.html",
            applications=applications
        )

    except Exception as e:

        print("MY APPLICATIONS ERROR:", e)

        flash(
            "Unable to load applications: " + str(e),
            "error"
        )

        return redirect(url_for("dashboard"))

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

        # ----------------------------------------------------
        # USER PROFILE
        # ----------------------------------------------------

        cur.execute("""
            SELECT
                preferred_role,
                preferred_location,
                education,
                degree,
                experience_years
            FROM user_profiles
            WHERE user_id = %s
        """, (session["user_id"],))

        profile = cur.fetchone()

        # ----------------------------------------------------
        # USER SKILLS
        # ----------------------------------------------------

        cur.execute("""
            SELECT
                us.skill_id,
                s.skill_name,
                us.skill_level,
                us.proficiency
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
        """, (session["user_id"],))

        user_skills = cur.fetchall()

        user_skill_ids = {
            skill["skill_id"]
            for skill in user_skills
        }

        # ----------------------------------------------------
        # ACTIVE JOBS
        # ----------------------------------------------------

        cur.execute("""
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
                application_link
            FROM jobs
            WHERE is_active = TRUE
            ORDER BY created_at DESC
        """)

        jobs_list = cur.fetchall()

        recommendations_list = []

        for job in jobs_list:

            cur.execute("""
                SELECT
                    js.skill_id,
                    js.importance,
                    s.skill_name
                FROM job_skills js
                JOIN skills s
                    ON js.skill_id = s.skill_id
                WHERE js.job_id = %s
            """, (job["job_id"],))

            required_skills = cur.fetchall()

            # ------------------------------------------------
            # SKILL SCORE - 50%
            # ------------------------------------------------

            if required_skills:

                total_importance = sum(
                    skill["importance"] or 1
                    for skill in required_skills
                )

                matched_importance = sum(
                    skill["importance"] or 1
                    for skill in required_skills
                    if skill["skill_id"] in user_skill_ids
                )

                skill_score = (
                    matched_importance /
                    total_importance
                ) * 100

            else:

                skill_score = 0

            # ------------------------------------------------
            # ROLE SCORE - 20%
            # ------------------------------------------------

            role_score = 0

            preferred_role = (
                profile["preferred_role"]
                if profile
                else None
            )

            if preferred_role:

                if (
                    preferred_role.lower()
                    in job["title"].lower()
                ):

                    role_score = 100

                elif (
                    job["title"].lower()
                    in preferred_role.lower()
                ):

                    role_score = 100

                else:

                    role_words = set(
                        preferred_role.lower().split()
                    )

                    job_words = set(
                        job["title"].lower().split()
                    )

                    if role_words & job_words:
                        role_score = 50

            # ------------------------------------------------
            # LOCATION SCORE - 15%
            # ------------------------------------------------

            location_score = 0

            preferred_location = (
                profile["preferred_location"]
                if profile
                else None
            )

            if preferred_location and job["location"]:

                if (
                    preferred_location.lower()
                    in job["location"].lower()
                ):

                    location_score = 100

                elif (
                    job["location"].lower()
                    in preferred_location.lower()
                ):

                    location_score = 100

            # ------------------------------------------------
            # EDUCATION SCORE - 10%
            # ------------------------------------------------

            education_score = 0

            education_values = []

            if profile:

                if profile["education"]:
                    education_values.append(
                        profile["education"].lower()
                    )

                if profile["degree"]:
                    education_values.append(
                        profile["degree"].lower()
                    )

            job_education = (
                job["education_required"] or ""
            ).lower()

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

                if education_words & job_education_words:
                    education_score = 50

            # ------------------------------------------------
            # EXPERIENCE SCORE - 5%
            # ------------------------------------------------

            experience_score = 0

            if profile:

                user_experience = (
                    float(profile["experience_years"])
                    if profile["experience_years"]
                    else 0
                )

                required_experience = (
                    job["experience_required"] or ""
                ).lower()

                if (
                    "fresher" in required_experience
                    or "0" in required_experience
                ):

                    experience_score = 100

                elif user_experience > 0:

                    experience_score = 50

            # ------------------------------------------------
            # FINAL SCORE
            # ------------------------------------------------

            final_score = (
                skill_score * 0.50
                + role_score * 0.20
                + location_score * 0.15
                + education_score * 0.10
                + experience_score * 0.05
            )

            final_score = round(
                final_score,
                2
            )

            if final_score >= 90:
                category = "Excellent Match"

            elif final_score >= 75:
                category = "Strong Match"

            elif final_score >= 60:
                category = "Good Match"

            elif final_score >= 40:
                category = "Partial Match"

            else:
                category = "Low Match"

            recommendations_list.append({
                "job": job,
                "score": final_score,
                "category": category,
                "skill_score": round(skill_score, 2),
                "role_score": round(role_score, 2),
                "location_score": round(location_score, 2),
                "education_score": round(education_score, 2),
                "experience_score": round(experience_score, 2)
            })

        recommendations_list.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return render_template(
            "recommendations.html",
            recommendations=recommendations_list
        )

    except Exception as e:

        print("RECOMMENDATIONS ERROR:", e)

        flash(
            "Unable to generate recommendations: " + str(e),
            "error"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN - MANAGE JOBS
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

        cur.execute("""
            SELECT
                job_id,
                title,
                company_name,
                job_type,
                location,
                application_deadline,
                is_active,
                created_at
            FROM jobs
            ORDER BY created_at DESC
        """)

        jobs_list = cur.fetchall()

        total_opportunities = len(jobs_list)

        active_count = sum(
            1 for job in jobs_list
            if job["is_active"]
        )

        inactive_count = (
            total_opportunities - active_count
        )

        internship_count = sum(
            1 for job in jobs_list
            if job["job_type"]
            and job["job_type"].lower() == "internship"
        )

        return render_template(
            "admin_jobs.html",
            jobs=jobs_list,
            total_opportunities=total_opportunities,
            active_count=active_count,
            inactive_count=inactive_count,
            internship_count=internship_count
        )

    except Exception as e:

        print("ADMIN JOBS ERROR:", e)

        flash(
            "Unable to load jobs: " + str(e),
            "error"
        )

        return redirect(url_for("admin_dashboard"))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ADMIN - ADD JOB
# ============================================================

@app.route("/admin/jobs/add", methods=["GET", "POST"])
@admin_required
def admin_add_job():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        company_name = request.form.get(
            "company_name",
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

        description = request.form.get(
            "description",
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
        ) or None

        salary_max = request.form.get(
            "salary_max"
        ) or None

        application_deadline = request.form.get(
            "application_deadline"
        ) or None

        application_link = request.form.get(
            "application_link",
            ""
        ).strip()

        is_active = (
            request.form.get("is_active") == "on"
            or request.form.get("is_active") == "true"
            or request.form.get("is_active") == "1"
        )

        if not title or not company_name or not job_type:

            flash(
                "Title, company name and opportunity type are required.",
                "error"
            )

            return render_template(
                "admin_add_job.html"
            )

        conn = None
        cur = None

        try:

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
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
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    CURRENT_TIMESTAMP
                )
                RETURNING job_id
            """, (
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
            ))

            job_id = cur.fetchone()[0]

            conn.commit()

            flash(
                "Opportunity added successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "admin_job_skills",
                    job_id=job_id
                )
            )

        except Exception as e:

            if conn:
                conn.rollback()

            print("ADMIN ADD JOB ERROR:", e)

            flash(
                "Unable to add opportunity: " + str(e),
                "error"
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
    "/admin/jobs/<int:job_id>/edit",
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

            job_type = request.form.get(
                "job_type",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            description = request.form.get(
                "description",
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
            ) or None

            salary_max = request.form.get(
                "salary_max"
            ) or None

            application_deadline = request.form.get(
                "application_deadline"
            ) or None

            application_link = request.form.get(
                "application_link",
                ""
            ).strip()

            is_active = (
                request.form.get("is_active") == "on"
                or request.form.get("is_active") == "true"
                or request.form.get("is_active") == "1"
            )

            cur.execute("""
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
            """, (
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
            ))

            conn.commit()

            flash(
                "Opportunity updated successfully.",
                "success"
            )

            return redirect(
                url_for("admin_jobs")
            )

        cur.execute("""
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
        """, (job_id,))

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

        print("ADMIN EDIT JOB ERROR:", e)

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
# ADMIN - ACTIVATE / DEACTIVATE JOB
# ============================================================

@app.route(
    "/admin/jobs/<int:job_id>/toggle",
    methods=["POST"]
)
@admin_required
def admin_toggle_job(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE jobs
            SET is_active = NOT is_active
            WHERE job_id = %s
        """, (job_id,))

        conn.commit()

        flash(
            "Opportunity status updated.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("TOGGLE JOB ERROR:", e)

        flash(
            "Unable to change opportunity status: " + str(e),
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
# ADMIN - DELETE JOB
# ============================================================

@app.route(
    "/admin/jobs/<int:job_id>/delete",
    methods=["POST"]
)
@admin_required
def admin_delete_job(job_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        # Delete job skills first
        cur.execute("""
            DELETE FROM job_skills
            WHERE job_id = %s
        """, (job_id,))

        # Delete applications
        cur.execute("""
            DELETE FROM applications
            WHERE job_id = %s
        """, (job_id,))

        # Delete job
        cur.execute("""
            DELETE FROM jobs
            WHERE job_id = %s
        """, (job_id,))

        conn.commit()

        flash(
            "Opportunity deleted successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("DELETE JOB ERROR:", e)

        flash(
            "Unable to delete opportunity: " + str(e),
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
        # GET JOB
        # ----------------------------------------------------

        cur.execute("""
            SELECT
                job_id,
                title,
                company_name,
                job_type,
                location
            FROM jobs
            WHERE job_id = %s
        """, (job_id,))

        job = cur.fetchone()

        if not job:

            flash(
                "Job or internship not found.",
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

            importance = request.form.get(
                "importance",
                "3"
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

            try:

                importance = int(
                    importance
                )

            except ValueError:

                importance = 3

            if importance < 1:
                importance = 1

            if importance > 5:
                importance = 5

            # Check existing skill

            cur.execute("""
                SELECT job_skill_id
                FROM job_skills
                WHERE job_id = %s
                AND skill_id = %s
            """, (
                job_id,
                skill_id
            ))

            existing_skill = cur.fetchone()

            if existing_skill:

                cur.execute("""
                    UPDATE job_skills
                    SET importance = %s
                    WHERE job_id = %s
                    AND skill_id = %s
                """, (
                    importance,
                    job_id,
                    skill_id
                ))

                flash(
                    "Skill already exists. Importance updated.",
                    "success"
                )

            else:

                cur.execute("""
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
                """, (
                    job_id,
                    skill_id,
                    importance
                ))

                flash(
                    "Skill added successfully.",
                    "success"
                )

            conn.commit()

            return redirect(
                url_for(
                    "admin_job_skills",
                    job_id=job_id
                )
            )

        # ----------------------------------------------------
        # ALL SKILLS
        # ----------------------------------------------------

        cur.execute("""
            SELECT
                skill_id,
                skill_name
            FROM skills
            ORDER BY skill_name
        """)

        all_skills = cur.fetchall()

        # ----------------------------------------------------
        # ASSIGNED JOB SKILLS
        # ----------------------------------------------------

        cur.execute("""
            SELECT
                js.job_skill_id,
                js.skill_id,
                js.importance,
                s.skill_name
            FROM job_skills js
            JOIN skills s
                ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY s.skill_name
        """, (job_id,))

        job_skills = cur.fetchall()

        selected_skill_ids = {
            skill["skill_id"]
            for skill in job_skills
        }

        return render_template(
            "admin_job_skills.html",
            job=job,
            all_skills=all_skills,
            job_skills=job_skills,
            selected_skill_ids=selected_skill_ids
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
# ADMIN - DELETE JOB SKILL
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

        cur.execute("""
            DELETE FROM job_skills
            WHERE job_skill_id = %s
            AND job_id = %s
        """, (
            job_skill_id,
            job_id
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
            "DELETE JOB SKILL ERROR:",
            e
        )

        flash(
            "Unable to remove skill: " + str(e),
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
# TEST DATABASE
# ============================================================

@app.route("/test-db")
def test_db():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute("SELECT version();")

        version = cur.fetchone()[0]

        return (
            "CareerMatch Database Connected<br><br>"
            + version
        )

    except Exception as e:

        return (
            "Database Connection Failed:<br>"
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
        "INTERNAL SERVER ERROR:",
        error
    )

    return """
    <h1>CareerMatch - Internal Server Error</h1>
    <p>Please check the Flask terminal for the complete error.</p>
    """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )