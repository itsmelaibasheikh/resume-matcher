from services.matcher import match_resume_to_jd

resume_text = """
Developed and maintained RESTful APIs using FastAPI and Django for a SaaS analytics platform
Used Jenkins to set up CI/CD pipelines, reducing deployment time by 40%
Led a team of 5 engineers through a major backend migration from monolith to microservices
Built ETL data pipelines using Python and Apache Airflow to process daily user analytics
Designed and optimized PostgreSQL database schemas handling over 2 million records
Implemented unit and integration tests using PyTest, achieving 85% code coverage
Containerized applications using Docker and deployed to AWS ECS
Collaborated with product managers and designers in an Agile Scrum environment
Mentored 2 junior developers and conducted code reviews
Built a real-time notification system using WebSockets and Redis pub/sub
"""

jd_text = """
Looking for a backend engineer with strong experience in CI/CD pipelines and DevOps practices
Strong leadership and team management experience required, must have led engineering teams before
Familiarity with cooking and food safety standards
Experience building and maintaining scalable REST APIs
Hands-on experience with containerization tools like Docker and Kubernetes
Experience with cloud platforms such as AWS or GCP
Solid understanding of relational databases and query optimization
Experience writing automated tests and maintaining high code coverage
Comfortable working in Agile/Scrum development environments
Experience mentoring junior engineers is a plus
"""

result = match_resume_to_jd(resume_text, jd_text)

print("Overall score:", result["overall_score"])

print("\nMatched:")
for m in result["matched"]:
    print(f"  [{m['score']}%] {m['requirement']}")
    for c in m["candidates"]:
        print(f"      -> [{c['score']}%] {c['line']}")

print("\nMissing:")
for m in result["missing"]:
    print(f"  [{m['score']}%] {m['requirement']}")