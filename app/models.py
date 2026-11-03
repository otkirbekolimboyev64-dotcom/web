 	from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    ForeignKey, Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False)  # admin, teacher
    phone = Column(String(20), nullable=True)
    telegram_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    duration_months = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    groups = relationship("Group", back_populates="course")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    course = relationship("Course", back_populates="groups")
    teacher = relationship("User")
    students = relationship("Student", back_populates="group")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    parent_phone = Column(String(20), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    monthly_fee = Column(Float, nullable=False)
    telegram_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("Group", back_populates="students")
    payments = relationship("Payment", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(String(7), nullable=False) # YYYY-MM
    status = Column(String(20), default="paid")
    note = Column(String(300), nullable=True)
    paid_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="payments")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    note = Column(String(300), nullable=True)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    student = relationship("Student", back_populates="attendances")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    student = relationship("Student", back_populates="grades")
cd ~/Desktop/web-excel/oquv-markaz
cat > app/models.py << 'EOF'
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    ForeignKey, Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False)  # admin, teacher
    phone = Column(String(20), nullable=True)
    telegram_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    duration_months = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    groups = relationship("Group", back_populates="course")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    course = relationship("Course", back_populates="groups")
    teacher = relationship("User")
    students = relationship("Student", back_populates="group")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    parent_phone = Column(String(20), nullable=False)
    parent_name = Column(String(150), nullable=True)
    
    # Faqat group_id qoldirildi, course_id o'chirildi
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    
    monthly_fee = Column(Float, nullable=False)
    telegram_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("Group", back_populates="students")
    payments = relationship("Payment", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(String(7), nullable=False) # YYYY-MM
    status = Column(String(20), default="paid")
    note = Column(String(300), nullable=True)
    paid_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="payments")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    note = Column(String(300), nullable=True)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    student = relationship("Student", back_populates="attendances")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    student = relationship("Student", back_populates="grades")
EOF
