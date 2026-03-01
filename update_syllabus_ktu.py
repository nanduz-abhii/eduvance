import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'majorp.settings')
django.setup()

from EduVance.models import Subject, SubjectDetail

def update_syllabus():
    dept_name = "AI & DS"
    
    # Comprehensive KTU 2019 Scheme AI & DS Syllabus Data
    syllabus_data = {
        "1": {
            "major1": "Linear Algebra and Calculus",
            "major2": "Engineering Physics A",
            "major3": "Engineering Graphics",
            "minorsone": "Intro to AI & Data Science",
            "aeca": "Life Skills",
            "mdc": "Sustainable Engineering",
            "sec": "Physics Lab / Workshop",
            "elective1": "None",
            "elective2": "None",
            "vac1": "None",
            "vac2": "None",
            "minortwo": "None",
            "aecb": "None"
        },
        "2": {
            "major1": "Vector Calculus, Diff Eq & Transforms",
            "major2": "Engineering Chemistry",
            "major3": "Programming in C",
            "aecb": "Professional Communication",
            "mdc": "Basics of Civil & Mechanical Engg",
            "sec": "Chemistry Lab / Programming Lab",
            "minorsone": "None",
            "minortwo": "None",
            "aeca": "None",
            "vac1": "None",
            "vac2": "None",
            "elective1": "None",
            "elective2": "None"
        },
        "3": {
            "major1": "Discrete Mathematical Structures",
            "major2": "Data Structures",
            "major3": "Computer Organization & Architecture",
            "aeca": "Constitution of India",
            "minorsone": "Minor Track I",
            "sec": "Data Structures Lab / OOP Lab",
            "major2": "Logic System Design", # Correcting major for S3 AD
            "mdc": "None",
            "minortwo": "None",
            "aecb": "None",
            "vac1": "None",
            "vac2": "None",
            "elective1": "None",
            "elective2": "None"
        },
        "4": {
            "major1": "Prob, Stat & Numerical Methods",
            "major2": "Design and Analysis of Algorithms",
            "major3": "Database Management Systems",
            "aecb": "Professional Ethics",
            "minortwo": "Minor Track II",
            "sec": "Algorithm Lab / Database Lab",
            "major2": "Introduction to AI & DS", # Adjusted for S4 AD KTU
            "aeca": "None",
            "mdc": "None",
            "minorsone": "None",
            "vac1": "None",
            "vac2": "None",
            "elective1": "None",
            "elective2": "None"
        },
        "5": {
            "major1": "Statistical Inference & Data Modelling",
            "major2": "Foundations of Machine Learning",
            "major3": "Computer Networks",
            "elective1": "Program Elective I",
            "minorsone": "Minor Track III",
            "sec": "Machine Learning Lab",
            "major3": "Formal Languages & Automata", # S5 Core
            "aeca": "None",
            "aecb": "None",
            "mdc": "Industrial Economics & Management", # Humanities
            "minortwo": "None",
            "vac1": "None",
            "vac2": "None",
            "elective2": "None"
        },
        "6": {
            "major1": "Applied Machine Learning",
            "major2": "Natural Language Processing",
            "major3": "Artificial Intelligence",
            "elective2": "Program Elective II",
            "minortwo": "Minor Track IV / Honors",
            "sec": "AI & ML Lab",
            "mdc": "Disaster Management / Humanities",
            "aeca": "None",
            "aecb": "None",
            "minorsone": "None",
            "vac1": "None",
            "vac2": "None",
            "elective1": "None"
        },
        "7": {
            "major1": "Deep Learning",
            "major2": "Reinforcement Learning",
            "major3": "Big Data Systems",
            "elective1": "Program Elective III",
            "elective2": "Program Elective IV",
            "minorsone": "Minor Track V",
            "sec": "DL Lab / Seminar / Project Phase I",
            "aeca": "None",
            "aecb": "None",
            "mdc": "None",
            "minortwo": "None",
            "vac1": "None",
            "vac2": "None"
        },
        "8": {
            "major1": "Ethics and Responsible AI",
            "major2": "Optimization Techniques",
            "elective1": "Program Elective V",
            "elective2": "Open Elective",
            "sec": "Project Phase II",
            "major3": "None",
            "minorsone": "None",
            "minortwo": "None",
            "aeca": "None",
            "aecb": "None",
            "mdc": "None",
            "vac1": "None",
            "vac2": "None"
        }
    }

    print(f"Starting syllabus update for {dept_name}...")
    
    for sem, data in syllabus_data.items():
        # Get or create Subject
        subject_obj, created = Subject.objects.get_or_create(dept=dept_name, sem=sem)
        if created:
            print(f"Created Subject: {dept_name} Sem {sem}")
        
        # Get or create SubjectDetail
        detail, created = SubjectDetail.objects.get_or_create(subject=subject_obj)
        
        detail.major1 = data.get("major1")
        detail.major2 = data.get("major2")
        detail.major3 = data.get("major3")
        detail.minorsone = data.get("minorsone")
        detail.minortwo = data.get("minortwo")
        detail.aeca = data.get("aeca")
        detail.aecb = data.get("aecb")
        detail.mdc = data.get("mdc")
        detail.vac1 = data.get("vac1")
        detail.vac2 = data.get("vac2")
        detail.sec = data.get("sec")
        detail.elective1 = data.get("elective1")
        detail.elective2 = data.get("elective2")
        
        detail.save()
        print(f"Updated SubjectDetail for Sem {sem}")

    print("Syllabus update complete!")

if __name__ == "__main__":
    update_syllabus()
