from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow frontend to connect from different port

# Database setup
DATABASE = 'jobs.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                salary TEXT,
                experience TEXT,
                job_type TEXT,
                remote BOOLEAN,
                tags TEXT,
                description TEXT,
                posted_date TEXT,
                benefits TEXT,
                applications_count INTEGER DEFAULT 0
            )
        """)

def seed_sample_data():
    """Add sample jobs to database"""
    sample_jobs = [
        {
            'title': 'Senior Software Engineer',
            'company': 'META',
            'location': 'Bengaluru, KA',
            'salary': '$120,000 - $180,000',
            'experience': 'senior',
            'job_type': 'full time',
            'remote': True,
            'tags': ['Python', 'React', 'AWS', 'Machine Learning'],
            'description': 'Join our innovative team building next-gen AI solutions.',
            'benefits': ['Health Insurance', '401k', 'Stock Options', 'Unlimited PTO'],
            'posted_date': '2024-08-10'
        },
        {
            'title': 'Frontend Developer',
            'company': 'GOOGLE',
            'location': 'New Delhi, DL',
            'salary': '$90,000 - $130,000',
            'experience': 'mid',
            'job_type': 'full time',
            'remote': False,
            'tags': ['JavaScript', 'Vue.js', 'CSS', 'Node.js'],
            'description': 'Build beautiful, responsive web applications.',
            'benefits': ['Health Insurance', 'Flexible Hours', 'Learning Budget'],
            'posted_date': '2024-08-12'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'MICROSOFT',
            'location': 'New Delhi, DL',
            'salary': '$100,000 - $150,000',
            'experience': 'mid',
            'job_type': 'contract',
            'remote': True,
            'tags': ['Docker', 'Kubernetes', 'CI/CD', 'Terraform'],
            'description': 'Manage cloud infrastructure and deployment pipelines.',
            'benefits': ['High Hourly Rate', 'Flexible Schedule'],
            'posted_date': '2024-08-11'
        },  
    ]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        if cursor.fetchone()[0] == 0:  # Only seed if empty
            for job in sample_jobs:
                cursor.execute('''
                    INSERT INTO jobs (title, company, location, salary, experience, 
                                    job_type, remote, tags, description, benefits, posted_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job['title'], job['company'], job['location'], job['salary'],
                    job['experience'], job['job_type'], job['remote'],
                    json.dumps(job['tags']), job['description'],
                    json.dumps(job['benefits']), job['posted_date']
                ))
            conn.commit()

# API Routes
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs with optional filtering"""
    try:
        # Get filter parameters from query string
        title = request.args.get('title', '').lower()
        location = request.args.get('location', '').lower()
        experience = request.args.get('experience', '')
        remote = request.args.get('remote')
        job_type = request.args.get('job_type', '')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs ORDER BY posted_date DESC")
            rows = cursor.fetchall()

            jobs = []
            for row in rows:
                job = {
                    'id': row['id'],
                    'title': row['title'],
                    'company': row['company'],
                    'location': row['location'],
                    'salary': row['salary'],
                    'experience': row['experience'],
                    'job_type': row['job_type'],
                    'remote': bool(row['remote']),
                    'tags': json.loads(row['tags'] or '[]'),
                    'description': row['description'],
                    'benefits': json.loads(row['benefits'] or '[]'),
                    'posted_date': row['posted_date'],
                    'applications_count': row['applications_count'] or 0
                }

                # Apply filters
                if title and title not in job['title'].lower():
                    continue
                if location and location not in job['location'].lower():
                    continue
                if experience and experience != job['experience']:
                    continue
                if remote is not None and job['remote'] != (remote.lower() == 'true'):
                    continue
                if job_type and job_type != job['job_type']:
                    continue

                jobs.append(job)

            return jsonify({
                'success': True,
                'data': jobs,
                'count': len(jobs)
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
def apply_to_job(job_id):
    """Apply to a job (increment application count)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if job exists
            cursor.execute("SELECT id FROM jobs WHERE id = ?", (job_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Job not found'
                }), 404
            
            # Increment application count
            cursor.execute(
                "UPDATE jobs SET applications_count = applications_count + 1 WHERE id = ?", 
                (job_id,)
            )
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def home():
    """Basic home route"""
    return jsonify({
        'message': 'JobCompare Pro API',
        'status': 'running',
        'endpoints': [
            '/api/jobs - Get all jobs',
            '/api/jobs/<id>/apply - Apply to job',
            '/api/health - Health check'
        ]
    })

if __name__ == '__main__':
    # Initialize database and add sample data
    init_db()
    seed_sample_data()
    
    print("🚀 JobCompare Pro Backend API")
    print("📍 Server: http://localhost:5000")
    print("📋 Available endpoints:")
    print("   GET  /api/jobs - Get all jobs")
    print("   POST /api/jobs/<id>/apply - Apply to job")
    print("   GET  /api/health - Health check")
    print("   GET  / - API info")
    print("\n✨ CORS enabled - Frontend can connect from any port")
    print("\n🔍 Test the API:")
    print("   http://localhost:5000/api/health")
    print("   http://localhost:5000/api/jobs")

    app.run(debug=True, host='0.0.0.0', port=5000)