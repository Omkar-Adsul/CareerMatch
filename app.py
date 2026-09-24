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

from config import Config


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
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not full_name or not email or not password:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(url_for("register"))

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            # Check existing email
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
                    "warning"
                )

                return redirect(url_for("register"))

            password_hash = generate_password_hash(password)

            # Create user
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

            user_id = cur.fetchone()[0]

            # Create profile
            cur.execute(
                """
                INSERT INTO user_profiles
                (
                    user_id
                )
                VALUES
                (%s)
                ON CONFLICT (user_id)
                DO NOTHING
                """,
                (user_id,)
            )

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception as e:

            conn.rollback()

            print("REGISTER ERROR:", e)

            flash(
                "Registration failed.",
                "error"
            )

        finally:

            cur.close()
            conn.close()

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        cur = conn.cursor()

        try:

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

            if user and check_password_hash(
                user[3],
                password
            ):

                session["user_id"] = user[0]
                session["full_name"] = user[1]
                session["email"] = user[2]
                session["role"] = user[4]

                if user[4] == "admin":

                    return redirect(
                        url_for("admin_dashboard")
                    )

                return redirect(
                    url_for("dashboard")
                )

            flash(
                "Invalid email or password.",
                "error"
            )

        except Exception as e:

            print("LOGIN ERROR:", e)

            flash(
                "Unable to login.",
                "error"
            )

        finally:

            cur.close()
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

    return redirect(url_for("login"))


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session.get("role") != "admin":

        flash(
            "Admin access required.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "admin_dashboard.html"
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # Create profile if it does not exist
        cur.execute(
            """
            INSERT INTO user_profiles
            (
                user_id
            )
            VALUES
            (%s)
            ON CONFLICT (user_id)
            DO NOTHING
            """,
            (user_id,)
        )

        conn.commit()

        # User profile
        cur.execute(
            """
            SELECT
                u.full_name,
                u.email,
                p.phone,
                p.date_of_birth,
                p.gender,
                p.education,
                p.college_name,
                p.degree,
                p.graduation_year,
                p.experience_years,
                p.preferred_role,
                p.preferred_location,
                p.resume_url,
                p.profile_summary
            FROM users u

            LEFT JOIN user_profiles p
                ON u.user_id = p.user_id

            WHERE u.user_id = %s
            """,
            (user_id,)
        )

        user_data = cur.fetchone()

        # User skills
        cur.execute(
            """
            SELECT
                s.skill_id,
                s.skill_name,
                COALESCE(
                    us.proficiency,
                    us.skill_level,
                    'Beginner'
                )
            FROM user_skills us

            JOIN skills s
                ON us.skill_id = s.skill_id

            WHERE us.user_id = %s

            ORDER BY s.skill_name
            """,
            (user_id,)
        )

        user_skills = cur.fetchall()

        # All available skills
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
            user_data=user_data,
            user_skills=user_skills,
            all_skills=all_skills
        )

    except Exception as e:

        print("PROFILE ERROR:", e)

        flash(
            "Unable to load profile.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route(
    "/profile/update",
    methods=["POST"]
)
def update_profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    date_of_birth = request.form.get(
        "date_of_birth"
    ) or None

    gender = request.form.get(
        "gender",
        ""
    ).strip()

    education = request.form.get(
        "education",
        ""
    ).strip()

    college_name = request.form.get(
        "college_name",
        ""
    ).strip()

    degree = request.form.get(
        "degree",
        ""
    ).strip()

    graduation_year = request.form.get(
        "graduation_year"
    ) or None

    experience_years = request.form.get(
        "experience_years"
    ) or 0

    preferred_role = request.form.get(
        "preferred_role",
        ""
    ).strip()

    preferred_location = request.form.get(
        "preferred_location",
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

    try:

        # Update user name
        cur.execute(
            """
            UPDATE users
            SET full_name = %s
            WHERE user_id = %s
            """,
            (
                full_name,
                user_id
            )
        )

        # Update profile
        cur.execute(
            """
            UPDATE user_profiles
            SET
                phone = %s,
                date_of_birth = %s,
                gender = %s,
                education = %s,
                college_name = %s,
                degree = %s,
                graduation_year = %s,
                experience_years = %s,
                preferred_role = %s,
                preferred_location = %s,
                resume_url = %s,
                profile_summary = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
            """,
            (
                phone,
                date_of_birth,
                gender,
                education,
                college_name,
                degree,
                graduation_year,
                experience_years,
                preferred_role,
                preferred_location,
                resume_url,
                profile_summary,
                user_id
            )
        )

        conn.commit()

        session["full_name"] = full_name

        flash(
            "Profile updated successfully.",
            "success"
        )

    except Exception as e:

        conn.rollback()

        print("PROFILE UPDATE ERROR:", e)

        flash(
            "Unable to update profile.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("profile")
    )


# =========================================================
# ADD USER SKILL
# =========================================================

@app.route(
    "/profile/add-skill",
    methods=["POST"]
)
def add_skill():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    skill_id = request.form.get(
        "skill_id"
    )

    proficiency = request.form.get(
        "proficiency",
        "Beginner"
    )

    if not skill_id:

        flash(
            "Please select a skill.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:

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

            ON CONFLICT (user_id, skill_id)

            DO UPDATE SET
                skill_level = EXCLUDED.skill_level,
                proficiency = EXCLUDED.proficiency
            """,
            (
                user_id,
                skill_id,
                proficiency,
                proficiency
            )
        )

        conn.commit()

        flash(
            "Skill added successfully.",
            "success"
        )

    except Exception as e:

        conn.rollback()

        print("ADD SKILL ERROR:", e)

        flash(
            "Unable to add skill.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("profile")
    )


# =========================================================
# REMOVE USER SKILL
# =========================================================

@app.route(
    "/profile/remove-skill/<int:skill_id>",
    methods=["POST"]
)
def remove_skill(skill_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            DELETE FROM user_skills
            WHERE user_id = %s
            AND skill_id = %s
            """,
            (
                session["user_id"],
                skill_id
            )
        )

        conn.commit()

        flash(
            "Skill removed.",
            "success"
        )

    except Exception as e:

        conn.rollback()

        print("REMOVE SKILL ERROR:", e)

        flash(
            "Unable to remove skill.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("profile")
    )


# =========================================================
# PART 4
# JOBS & INTERNSHIPS
# =========================================================

@app.route("/jobs")
def jobs():

    if "user_id" not in session:

        return redirect(
            url_for("login")
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

    conn = get_db_connection()
    cur = conn.cursor()

    try:

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
                )
            """

            search_value = "%" + search + "%"

            params.extend([
                search_value,
                search_value
            ])

        # Job type
        if job_type:

            query += """
                AND j.job_type = %s
            """

            params.append(job_type)

        # Location
        if location:

            query += """
                AND j.location ILIKE %s
            """

            params.append(
                "%" + location + "%"
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
            params
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

        print("JOBS ERROR:", e)

        flash(
            "Unable to load jobs.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# JOB DETAILS
# =========================================================

@app.route(
    "/job/<int:job_id>"
)
def job_details(job_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # Job details
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
                "Job or internship not found.",
                "error"
            )

            return redirect(
                url_for("jobs")
            )

        # Required skills
        cur.execute(
            """
            SELECT
                s.skill_name,
                js.importance
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

        # Existing application
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
                session["user_id"],
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

        print("JOB DETAILS ERROR:", e)

        flash(
            "Unable to load job details.",
            "error"
        )

        return redirect(
            url_for("jobs")
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# APPLY FOR JOB
# =========================================================

@app.route(
    "/apply/<int:job_id>",
    methods=["POST"]
)
def apply_job(job_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # Check active job
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
                "This opportunity is no longer available.",
                "error"
            )

            return redirect(
                url_for("jobs")
            )

        # Check duplicate application
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

        existing_application = cur.fetchone()

        if existing_application:

            flash(
                "You have already applied for this opportunity.",
                "warning"
            )

            return redirect(
                url_for(
                    "job_details",
                    job_id=job_id
                )
            )

        # Insert application
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
                session["user_id"],
                job_id
            )
        )

        conn.commit()

        flash(
            "Application submitted successfully!",
            "success"
        )

    except Exception as e:

        conn.rollback()

        print(
            "APPLICATION ERROR:",
            e
        )

        flash(
            "Unable to submit application.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for(
            "job_details",
            job_id=job_id
        )
    )


# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route("/my-applications")
def my_applications():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT
                a.application_id,
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
            "Unable to load applications.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# TEST DATABASE
# =========================================================

@app.route("/test-db")
def test_db():

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT current_database();"
        )

        database_name = cur.fetchone()[0]

        cur.close()
        conn.close()

        return f"""
        Database connection successful.<br>
        Database: {database_name}
        """

    except Exception as e:

        return f"""
        Database connection failed.<br>
        Error: {e}
        """, 500


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "OK",
        "application": "CareerMatch"
    }


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong.</p>
    """, 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )