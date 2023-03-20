""" 
DESCRIPTION

The idea is for students to use the Dropbox app to submit homework to a personal folder. They edit a pre-generated text file with their written answers and submit a scan of their written work. Then I can check for correctness quickly and can go deeper with the scan. And this can all be done with a script. And Dropbox's syncing makes it possible to do live checking.

I'll have students create a folder and share it with me. Then I'll add it to their class folder. I'll create a folder for each assignment in their folder. Then I just check what's in the folder. If it's a pdf then I read it. If it's a text file then I can run things on it. 

Generate a new folder containing a text file before giving the assignment. The text file may have an outline or have html to make things prettier. Then students open the file on their phone, interact with it, and save. The generater needs to be careful to not overwrite the text file. 
"""


""" IMPORTS """

from Rubric import *
import os
from dataclasses import dataclass, field
import pandas as pd
import pickle
import shutil
import numpy as np

import ipywidgets as widgets
from ipywidgets import interact, interactive, fixed, interact_manual, FloatSlider

import ipywidgets as widgets
from IPython.display import display

from IPython.display import IFrame
from fpdf import FPDF

#from PIL import Image, ImageFile
#ImageFile.LOAD_TRUNCATED_IMAGES = True
from PyPDF2 import PdfFileMerger


assignments = [
    'MiniExam_A', 
    'MiniExam_B',
    'MiniExam_C',
    'MiniExam_D1',
    'MiniExam_D2',
    'MiniExam_E1',
    'MiniExam_E2',
    'MiniExam_F',
]

""" CLASSES """

@dataclass
class STUDENT:
    """ A Student is a member of a Course and contains Assignment instances. """
    
    name: str
    course_id: str
    path: str
    work: list = field(default_factory=dict)
    grade: float = 0
    letter: str = 'NA'

@dataclass
class COURSE:
    """ A semester long course containing Students and Assignments. """
    
    course_id: str
    semester = '2023_Spring'
    students: dict = field(default_factory=dict)
    path = '../../Library/CloudStorage/Box-Box/'
    
    def Load(self):
        """ Load the course from pickle. """
        
        if self.students == {}:
            course_name = f'{self.course_id}_{self.semester}'
            if course_name + '_Roster' in os.listdir(course_name):
                open_path = f'{course_name}/{course_name}_Roster'
                picklefile = open(open_path, 'rb')
                course = pickle.load(picklefile)
                self.students = course.students
                picklefile.close()

                print(self.course_id, 'is loaded from', open_path + '.')
            return self
        
    def Save(self):
        """ Pickle the course. """

        course_name = f'{self.course_id}_{self.semester}'
        save_to = f'{course_name}/{course_name}_Roster'
        picklefile = open(save_to, 'wb')
        pickle.dump(self, picklefile)
        picklefile.close()
        
        print(self.course_id, 'is saved to', self.semester+'.')
    
    def Add_Student(self, student_name, silent=True):
        """ Add a student if they're not already added. """
        
        course_name = self.course_id.replace('_',' ')
        student_folder = f'{course_name} - {student_name}'
        student_path = self.path + student_folder

        Student = STUDENT(student_name, self.course_id, student_path)
        self.students[student_name] = Student
        if not silent:
            print(student_name,'added.')
            
    def Drop_Student(self, student_name):
        """ Drop a student by name. """
        
        new_students = {s:self.students[s] for s in self.students if s != student_name}
        print(student_name, 'has been dropped.')
        print(self.students[student_name])

        self.students = new_students
                
    def Make_Roster(self, silent=True):
        """ Collect the names from the box folder. """
        
        format_prefix = self.course_id.replace("_",' ')
        folder_prefix = f'{format_prefix} - '
                
        for thing in os.listdir(self.path):
            thing_path = os.path.join(self.path, thing)
            if os.path.isdir(thing_path) and folder_prefix in thing:
                student_name = thing.replace(folder_prefix,'')
                
                if student_name not in self.students:
                    self.Add_Student(student_name, silent=silent)
                else:
                    if self.students[student_name] == []:
                        self.Add_Student(student_name, silent=silent)
                
    def Make_Folder(self, student, folder_name, force=False, silent=True):
        """ Create a folder for a student. """
        
        if (folder_name not in os.listdir(student.path)) | force:
            folder_path = os.path.join(student.path, folder_name)
            os.mkdir(folder_path)
            if not silent:
                print(student.name, 'folder', folder_name, 'created.')
            
    def Remove_Folder(self, student, folder_name, force=False, silent=True):
        """ Remove a folder for a student. """
        
        if folder_name in os.listdir(student.path):
            folder_path = os.path.join(student.path, folder_name)
            if (os.listdir(folder_path) == []) | force:
                shutil.rmtree(folder_path)
                if not silent:
                    print(student.name, 'folder', folder_name, 'removed.')
                    
    def Rename_Folder(self, student, old, new, silent=True):
        """ Rename a folder for a student. """

        if old in os.listdir(student.path):
            old = os.path.join(student.path, old)
            new = os.path.join(student.path, new)
            os.rename(old, new)
            if not silent:
                print(student.name, 'folder', old, 'renamed to', new)
                
    def Assign(self, assignment, silent=True):
        """ Give an assignment to students. """
        
        for student in self.students.values():
            assignment_name = assignment.replace('_',' ')
            if assignment_name not in os.listdir(student.path):
                self.Make_Folder(student, assignment_name, silent=silent)
            if assignment not in student.work:
                student.work[assignment] = [0, [], '', 0]
                
    def Remove(self, folder, silent=True):
        """ Remove a folder for every student. """
        
        for student in self.students.values():
            self.Remove_Folder(student, folder, silent=silent)
            
    def Rename(self, old, new, silent=True):
        """ Rename a folder for every student. """
        
        for student in self.students.values():
            self.Rename_Folder(student, old, new, silent=silent)
                
    def Force_Collect(self, student, assignment, silent=True):
        """ Collect a student's assigment. """
        
        merger = PdfFileMerger()
        assignment_name = assignment.replace('_',' ')
        
        assignment_path = os.path.join(student.path, assignment_name)
        pdf_files = [f for f in os.listdir(assignment_path) if '.pdf' in f]
        for pdf in pdf_files:
            merger.append(os.path.join(assignment_path, pdf))
        
        student_name = student.name.replace(' ','_')
        final_file_name = f'{student_name}_{assignment}.pdf'
        
        course_name = f'{self.course_id}_{self.semester}'
        final_path = os.path.join(course_name, 'Submissions', assignment)
        merger.write(os.path.join(final_path, final_file_name))
        merger.close()

    def Collect(self, assignment, force=False, silent=True):
        """ Collect a PDF file from each student. """
        
        course_name = f'{self.course_id}_{self.semester}'
        submission_path = os.path.join(course_name, 'Submissions')
        final_path = os.path.join(submission_path, assignment)
        
        if assignment not in os.listdir(submission_path):
            os.mkdir(final_path)
            
        for student in self.students.values():
            student_name = student.name.replace(' ','_')
            final_file_name = f'{student_name}_{assignment}.pdf'
                
            if (final_file_name not in os.listdir(final_path)) | force:
                self.Force_Collect(student, assignment, silent=silent)
            
    def Force_Feedback(self, student, assignment, silent=True):
        """ Return a student's feedback. """

        student_name = student.name.replace(' ','_')
        feedback_name = f'{student_name}_{assignment}_Feedback.pdf'

        course_name = f'{self.course_id}_{self.semester}'
        feedback_path = os.path.join(course_name, 'Submissions', assignment)
        
        assignment_name = assignment.replace('_',' ')
        final_path = os.path.join(student.path, assignment_name)
        
        shutil.copyfile(os.path.join(feedback_path, feedback_name), os.path.join(final_path, feedback_name))
        
        if not silent:
            print('Feedback sent to', student.name)
            
    def Return(self, assignment, force=False):
        """ Return feedback to all students. """
        
        for student in self.students.values():
            student_name = student.name.replace(' ','_')
            course_name = f'{self.course_id}_{self.semester}'
            
            assignment_name = assignment.replace('_',' ')
            final_path = os.path.join(student.path, assignment_name)
            feedback_name = f'{student_name}_{assignment}_Feedback.pdf'
            feedback_path = os.path.join(course_name, 'Submissions', assignment)
            
            if feedback_name in os.listdir(feedback_path):
                if (feedback_name not in os.listdir(final_path)) | force:
                    self.Force_Feedback(student, assignment)
                    
    def Force_ReportCard(self, student, assignment, silent=True):
        """ Return a student's feedback. """

        student_name = student.name.replace(' ','_')
        feedback_name = f'{student_name}_Report_Card.pdf'
        feedback_path = os.path.join(self.course_id, 'Submissions')
        final_path = student.path

        shutil.copyfile(os.path.join(feedback_path, feedback_name), os.path.join(final_path, feedback_name))
        
        if not silent:
            print('Report Card sent to', student.name)
            
    def ReportCard(self, assignment, force=False):
        """ Return feedback to all students. """
        
        for student in self.students.values():
            student_name = student.name.replace(' ','_')
            assignment_name = assignment.replace('_',' ')
            
            final_path = student.path
            feedback_name = f'{student_name}_Report_Card.pdf'
            feedback_path = os.path.join(self.course_id, 'Submissions')
            if feedback_name in os.listdir(feedback_path):
                if (feedback_name not in os.listdir(final_path)) | force:
                    self.Force_ReportCard(student, assignment)
                    
    def Grade_Book(self):
        """ Return a gradebook. """
        Grade_Book = {}
        for name, student in self.students.items():
            Grade_Book[name] = [student.work[assignment][0] for assignment in assignments]
        Grade_Book = pd.DataFrame.from_dict(Grade_Book, orient='index', columns = assignments)
        
        H, M = [], []
        for name, data in Grade_Book.iterrows():
            assignments_h = [h for h in assignments if 'Homework' in h]
            homework_scores = np.array(sorted([i for i in data[assignments_h]]))
            homework_grade = sum(homework_scores * np.array([0, 0.05, 0.05, 0.05, 0.05, 0.05]))
            H.append(homework_grade)

            assignments_m = [m for m in assignments if 'MiniExam' in m]
            miniexam_scores = np.array(sorted([i for i in data[assignments_m]]))
            miniexam_grade = sum(miniexam_scores * np.array([0, 0.05, 0.1, 0.1, 0.2, 0.2]))
            M.append(miniexam_grade)
        Grade_Book['Homeworks'] = H
        Grade_Book['MiniExams'] = M
        
        Grade_Book['Total'] = (Grade_Book['Homeworks'] + Grade_Book['MiniExams']) / 90 * 100 #* 1.07
                
        def Assign_Letter(g):
            if g >= 97:
                return 'A+'
            if g >= 93:
                return 'A'
            if g >= 90:
                return 'A-'
            if g >= 87:
                return 'B+'
            if g >= 83:
                return 'B'
            if g >= 80:
                return 'B-'
            if g >= 77:
                return 'C+'
            if g >= 73:
                return 'C'
            if g >= 70:
                return 'C-'
            if g >= 67:
                return 'D+'
            if g >= 63:
                return 'D'
            if g >= 60:
                return 'D-'
            if g < 60:
                return 'F'
        
        Grade_Book['Letter'] = [Assign_Letter(g) for g in Grade_Book['Total']]
        
        Grade_Book = Grade_Book[Grade_Book.columns[::-1]]

        Grade_Book.to_csv('GradeBook.csv')
                
    def Grade(self):
        """ Assignment Drop Down """
        
        assignment_dropdown = list(zip(assignments, assignments))
        adrop = widgets.Dropdown(
            options=assignment_dropdown,
            value='MiniExam_A',
        )

        """ Student Drop Down """

        students = sorted([s for s in self.students])
        student_dropdown = list(zip(students, students))
        sdrop = widgets.Dropdown(
            options=student_dropdown,
            value=students[0],
        )
        
        """ Rubric """

        def Rubric_Checks(assignment_name, student_name):
            """ """
            
            student = self.students[sdrop.value]
            student_work = student.work[adrop.value]
            
            def Update_Work(_):
                
                """ Update Rubric Items """
                
                student_work[1] = [item.description for item in rubric_checks if item.value]
                
                """ Update Student Work """

                student_work[2] = comments.value

                """ Update Grade """

                rubric_items = student_work[1]

                grade = 100
                minus_points = 0

                for item in rubric_items:
                    if item != '':
                        parse = item.split(':: ')[0]
                        minus_points = minus_points + int(parse)

                point_adjustment = student_work[3]
                grade = grade + minus_points + point_adjustment
                student_work[0] = grade

                """ Make Feedback PDF """

                comment_string = student.work[adrop.value][2]
                
                Feedback_PDF(assignment_name, student_name, rubric_items, comment_string, point_adjustment, grade)

            """ Setup Rubric Check Boxes """
            
            rubric_items_base = Rubric_Items[assignment_name]
                
            rubric_checks = [widgets.Checkbox(value=False, indent=False, description=lri) for lri in rubric_items_base]
            
            rubric_comments = student_work[1]
            
            for check in rubric_checks:
                if check.description in rubric_comments:
                    check.value = True
                            
            for check in rubric_checks:
                check.observe(Update_Work)
            
            """ Setup Comment Box """

            comments_string = student_work[2]
            comments = widgets.Textarea(
                value=comments_string,
                placeholder='Leave Comments Here',
                rows=5,
            )
            comments.observe(Update_Work)
            
            """ Setup Point Adjustment """
            
            # do that here
            
            sdrop.observe(Update_Work)
            adrop.observe(Update_Work)
            
            return display(widgets.VBox(rubric_checks + [comments]))
        
        rubric_checks = widgets.interactive_output(Rubric_Checks, {'assignment_name':adrop, 'student_name':sdrop})

        """ PDF """

        def Show_PDF(student_name, assignment_name):
            """ Load and display the students assigment PDF. """
            
            student_name = student_name.replace(' ','_')
            course_name = f'{self.course_id}_{self.semester}'
            submission_path = os.path.join(course_name, 'Submissions', assignment_name)
            final_path = os.path.join(submission_path, f'{student_name}_{assignment_name}.pdf')
                        
            return display(IFrame(final_path, width=900, height=700))

        student_PDF = widgets.interactive_output(Show_PDF, {'student_name':sdrop, 'assignment_name':adrop})

        right = widgets.VBox([adrop, sdrop] + [rubric_checks])
        left_right = widgets.HBox([student_PDF, right])

        return display(left_right)
    
        
def Save_Course(econ, course_title = 'Fall_2022'):
    """ Pickle the course. """
    
    picklefile = open(course_title, 'wb')
    pickle.dump(econ,picklefile)
    picklefile.close()
    
def Load_Course(course_title = 'Fall_2022'):
    """ Load the course from pickle. """
    
    picklefile = open(course_title, 'rb')
    econ = pickle.load(picklefile)
    picklefile.close()
    return econ


""" DEFINITIONS """


def Feedback_PDF(assignment_name, student_name, rubric_items, comment_string, point_adjustment, grade):
    """ Save Feedback As a PDF """
    
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Times", size = 32)
    pdf.multi_cell(190, 20, txt = student_name + ' | ' + assignment_name.replace('_',' '), align = 'C')
    pdf.set_font("Times", size = 12)
    pdf.multi_cell(190, 5, txt = "Good feedback is important to mastery. The rubric is the measure of mastery for every student. Train yourself to focus on the comments and not on the points. The feedback on your work is much more important than the grade. Don't hesitate to reach out with questions.", align = 'J')
    pdf.multi_cell(190, 5, txt = "-Taylor", align = 'C')
    pdf.multi_cell(190, 10, txt = '', align = 'L')
    
    pdf.set_font("Times", size = 24)
    pdf.multi_cell(190, 10, txt = "Rubric Comments", align = 'L')
    if rubric_items == []:
        rubric_items = ['Nothing to correct. Nice work!']
    for item in rubric_items:
        pdf.set_font("Times", size = 14)
        pdf.multi_cell(190, 10, txt = item, align = 'L')
    pdf.multi_cell(190, 10, txt = '', align = 'L')
    
    if comment_string != '':
        pdf.set_font("Times", size = 24)
        pdf.multi_cell(190, 10, txt = "Other Comments", align = 'L')
        pdf.set_font("Times", size = 14)
        pdf.multi_cell(190, 10, txt = comment_string, align = 'L')
        pdf.multi_cell(190, 10, txt = '', align = 'L')
    
    if point_adjustment != 0:
        pdf.set_font("Times", size = 24)
        pdf.multi_cell(190, 10, txt = "Point Adjustment", align = 'L')
        pdf.set_font("Times", size = 14)
        pdf.multi_cell(190, 20, txt = str(point_adjustment), align = 'L')
        pdf.multi_cell(190, 10, txt = '', align = 'L')
    
    pdf.set_font("Times", size = 24)
    pdf.multi_cell(190, 10, txt = "Grade", align = 'L')
    pdf.set_font("Times", size = 10)
    pdf.multi_cell(190, 5, txt = "... but train yourself to focus on the comments and not so much on the grade itself.", align = 'J')
    pdf.set_font("Times", size = 14)
    pdf.multi_cell(190, 10, txt = str(grade) + ' out of 100', align = 'L')
    pdf.multi_cell(190, 10, txt = '', align = 'L')
    
    final_path = 'Econ_101_2023_Spring/Submissions/' + assignment_name + '/'
    pdf.output(final_path + student_name.replace(' ','_') + '_' + assignment_name + '_Feedback.pdf')
    #pdf.output('Feedback.pdf')
            
            
            
            
