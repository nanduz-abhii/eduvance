import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'majorp.settings')
django.setup()

from EduVance.models import Subject, SubjectDetail

def overhaul_syllabus():
    # 1. Clear existing data
    print("Clearing existing Subject and SubjectDetail records...")
    SubjectDetail.objects.all().delete()
    Subject.objects.all().delete()
    print("Data cleared.")

    departments = ["CSE", "AI & DS", "Mechanical Engineering", "Civil Engineering", "Electronics & Communication"]
    
    # Generic subjects for S1 & S2 (Common for all B.Tech branches in KTU 2019)
    s1_subjects = {
        "major1": "Linear Algebra and Calculus",
        "major2": "Engineering Physics A",
        "major3": "Engineering Graphics",
        "minorsone": "Basics of Civil & Mechanical Engg",
        "aeca": "Life Skills",
        "sec": "Physics Lab"
    }
    s2_subjects = {
        "major1": "Vector Calculus, Diff Eq & Transforms",
        "major2": "Engineering Chemistry",
        "major3": "Programming in C",
        "minorsone": "Basics of Electrical & Electronics Engg",
        "aeca": "Professional Communication",
        "sec": "Chemistry Lab"
    }

    # Department-specific data (S3 to S8)
    # Mapping to: major1, major2, major3, minorsone, aeca, sec (Filling 6 columns as requested)
    dept_curriculum = {
        "CSE": {
            "3": ["Discrete Mathematical Structures", "Data Structures", "Logic System Design", "Sustaintable Engineering", "Constitution of India", "DS Lab"],
            "4": ["Prob, Stat & Numerical Methods", "OS", "DBMS", "Computer Organization", "Professional Ethics", "DBMS Lab"],
            "5": ["Formal Languages & Automata", "Computer Networks", "Microprocessors", "Management for Engineers", "Program Elective I", "Network Lab"],
            "6": ["Compiler Design", "Computer Graphics", "Algorithm Analysis", "Disaster Management", "Program Elective II", "Compiler Lab"],
            "7": ["Machine Learning", "Distributed Computing", "Cryptography", "Program Elective III", "Open Elective", "Seminar & Project I"],
            "8": ["Data Mining", "Cloud Computing", "Program Elective IV", "Program Elective V", "Comprehensive Viva", "Project Phase II"]
        },
        "AI & DS": {
            "3": ["Discrete Math", "Data Structures", "Logic System Design", "Sustainable Engineering", "Constitution of India", "DS Lab"],
            "4": ["Prob & Stat", "Algorithm Analysis", "DBMS", "Intro to AI & DS", "Professional Ethics", "AI Lab"],
            "5": ["Stat Inference & Data Modelling", "Machine Learning", "Computer Networks", "Management for Engineers", "Program Elective I", "ML Lab"],
            "6": ["Applied ML", "NLP", "Artificial Intelligence", "Disaster Management", "Program Elective II", "AI & ML Lab"],
            "7": ["Deep Learning", "Reinforcement Learning", "Big Data Systems", "Program Elective III", "Open Elective", "Seminar & Project I"],
            "8": ["Ethics & Responsible AI", "Optimization Techniques", "Program Elective IV", "Program Elective V", "Comprehensive Viva", "Project Phase II"]
        },
        "Mechanical Engineering": {
            "3": ["Partial Diff Eq & Transforms", "Mechanics of Solids", "Thermodynamics", "Sustainable Engineering", "Constitution of India", "Civil & Mech Workshop"],
            "4": ["Prob, Stat & Numerical Methods", "Fluid Mechanics", "Manufacturing Process", "Material Science", "Professional Ethics", "Machine Drawing"],
            "5": ["Heat and Mass Transfer", "Design of Machine Elements I", "Dynamics of Machinery", "Management for Engineers", "Program Elective I", "Thermal Lab"],
            "6": ["Metrology & Instrumentation", "Design of Machine Elements II", "Advanced Manufacturing", "Disaster Management", "Program Elective II", "CADD Lab"],
            "7": ["Mechatronics", "Refrigeration & AC", "Power Plant Engineering", "Program Elective III", "Open Elective", "Seminar & Project I"],
            "8": ["Industrial Engineering", "Energy Management", "Program Elective IV", "Program Elective V", "Comprehensive Viva", "Project Phase II"]
        },
        "Civil Engineering": {
            "3": ["Partial Diff Eq & Transforms", "Mechanics of Solids", "Fluid Mechanics", "Sustainable Engineering", "Constitution of India", "Surveying Lab"],
            "4": ["Prob, Stat & Numerical Methods", "Structural Analysis I", "Surveying & Geomatics", "Material Science", "Professional Ethics", "Strength of Materials Lab"],
            "5": ["Design of Concrete Structures I", "Structural Analysis II", "Geotechnical Engineering I", "Management for Engineers", "Program Elective I", "Geotech Lab"],
            "6": ["Design of Hydraulic Structures", "Design of Steel Structures", "Transportation Engineering", "Disaster Management", "Program Elective II", "Transportation Lab"],
            "7": ["Quantity Surveying", "Environmental Engineering", "Prestressed Concrete", "Program Elective III", "Open Elective", "Seminar & Project I"],
            "8": ["Bridge Engineering", "Construction Management", "Program Elective IV", "Program Elective V", "Comprehensive Viva", "Project Phase II"]
        },
        "Electronics & Communication": {
            "3": ["Discrete Math", "Solid State Devices", "Network Theory", "Sustainable Engineering", "Constitution of India", "Logic Design Lab"],
            "4": ["Prob & Random Process", "Analog Circuits", "Signals & Systems", "Computer Architecture", "Professional Ethics", "Microcontroller Lab"],
            "5": ["Linear Integrated Circuits", "Digital Signal Processing", "Analog & Digital Communication", "Management for Engineers", "Program Elective I", "DSP Lab"],
            "6": ["Electromagnetics", "VLSI Circuit Design", "Information Theory", "Disaster Management", "Program Elective II", "Communication Lab"],
            "7": ["Microwaves & Antennas", "Embedded Systems", "Optical Fiber Comm", "Program Elective III", "Open Elective", "Seminar & Project I"],
            "8": ["Wireless Communication", "Nanotechnology", "Program Elective IV", "Program Elective V", "Comprehensive Viva", "Project Phase II"]
        }
    }

    print("Starting database population...")
    for dept in departments:
        for sem_int in range(1, 9):
            sem = str(sem_int)
            subject_obj = Subject.objects.create(dept=dept, sem=sem)
            detail = SubjectDetail.objects.create(subject=subject_obj)
            
            if sem == "1":
                curr = s1_subjects
            elif sem == "2":
                curr = s2_subjects
            else:
                s_list = dept_curriculum[dept][sem]
                curr = {
                    "major1": s_list[0],
                    "major2": s_list[1],
                    "major3": s_list[2],
                    "minorsone": s_list[3],
                    "aeca": s_list[4],
                    "sec": s_list[5]
                }
            
            detail.major1 = curr.get("major1")
            detail.major2 = curr.get("major2")
            detail.major3 = curr.get("major3")
            detail.minorsone = curr.get("minorsone")
            detail.aeca = curr.get("aeca")
            detail.sec = curr.get("sec")
            detail.save()
            
        print(f"Completed {dept} (8 Semesters).")

    print("\nSyllabus overhaul complete!")

if __name__ == "__main__":
    overhaul_syllabus()
