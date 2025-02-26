from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QLabel,
    QListWidget, QMenuBar, QMainWindow, QHBoxLayout, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QFileDialog, QListWidgetItem, QSlider, QComboBox
)
from PyQt6.QtGui import QAction
import sys
from database import fetch_all_experiences, add_job_experience, search_experiences_by_skills
from ai_matching import analyze_job_description, generate_resume
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document


class ResumeWizardApp(QMainWindow):
    """Main application GUI."""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_experiences()
        self.last_generated_resume = ""

    def initUI(self):
        """Initialize GUI layout."""
        self.setWindowTitle("Resume Wizard")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        help_menu = menubar.addMenu("Help")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Export Buttons Layout
        export_button_layout = QHBoxLayout()

        self.export_pdf_button = QPushButton("Export as PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        export_button_layout.addWidget(self.export_pdf_button)

        self.export_word_button = QPushButton("Export as Word")
        self.export_word_button.clicked.connect(self.export_to_word)
        export_button_layout.addWidget(self.export_word_button)

        layout.addLayout(export_button_layout)

        # Job Description Input
        self.label = QLabel("Paste Job Description Here:")
        layout.addWidget(self.label)

        self.job_desc_input = QTextEdit()
        layout.addWidget(self.job_desc_input)

        # AI Customization - Creativity Level
        self.creativity_label = QLabel("AI Creativity Level:")
        layout.addWidget(self.creativity_label)

        self.creativity_slider = QSlider(Qt.Orientation.Horizontal)
        self.creativity_slider.setMinimum(0)
        self.creativity_slider.setMaximum(100)
        self.creativity_slider.setValue(50)  # Default: Balanced Creativity
        layout.addWidget(self.creativity_slider)

        # AI Customization - Resume Style
        self.resume_style_label = QLabel("Resume Style:")
        layout.addWidget(self.resume_style_label)

        self.resume_style_dropdown = QComboBox()
        self.resume_style_dropdown.addItems(["Professional", "Casual", "Technical", "Concise"])
        layout.addWidget(self.resume_style_dropdown)

        # Experience Selection List
        self.experience_selection_label = QLabel("Select Relevant Job Experiences:")
        layout.addWidget(self.experience_selection_label)

        self.experience_selection_list = QListWidget()
        self.experience_selection_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.experience_selection_list)

        # Resume Preview
        self.resume_preview_label = QLabel("Generated Resume (Editable):")
        layout.addWidget(self.resume_preview_label)

        self.resume_preview = QTextEdit()
        layout.addWidget(self.resume_preview)

        # Buttons Layout
        button_layout = QHBoxLayout()

        self.analyze_button = QPushButton("Analyze Job Description")
        self.analyze_button.clicked.connect(self.analyze_job_description)
        button_layout.addWidget(self.analyze_button)

        self.generate_resume_button = QPushButton("Generate Resume")
        self.generate_resume_button.clicked.connect(self.generate_resume)
        button_layout.addWidget(self.generate_resume_button)

        self.add_experience_button = QPushButton("Add Job Experience")
        self.add_experience_button.clicked.connect(self.show_add_experience_dialog)
        button_layout.addWidget(self.add_experience_button)

        layout.addLayout(button_layout)
        central_widget.setLayout(layout)

    def export_to_pdf(self):
        """Export the generated resume to a PDF file with narrow margins and compact formatting."""
        resume_text = self.resume_preview.toPlainText().strip()

        if not resume_text:
            QMessageBox.warning(self, "Error", "Cannot export an empty resume.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Resume as PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            # Remove asterisks and extra spacing
            formatted_text = resume_text.replace("**", "").strip()
            formatted_text = "\n".join([line.strip() for line in formatted_text.split("\n") if line.strip()])

            pdf_canvas = canvas.Canvas(file_path, pagesize=letter)

            # Set Narrow Margins
            left_margin = 30  # Narrower left margin
            top_margin = 770  # Start closer to the top
            line_spacing = 12  # Reduce space between lines

            pdf_canvas.setFont("Helvetica", 10)
            y_position = top_margin

            for line in formatted_text.split("\n"):
                if y_position < 40:  # Start a new page if needed
                    pdf_canvas.showPage()
                    pdf_canvas.setFont("Helvetica", 10)
                    y_position = top_margin
                pdf_canvas.drawString(left_margin, y_position, line)
                y_position -= line_spacing

            pdf_canvas.save()
            QMessageBox.information(self, "Success", "Resume successfully exported as PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def export_to_word(self):
        """Export the generated resume to a Word file with better formatting and narrow margins."""
        resume_text = self.resume_preview.toPlainText().strip()

        if not resume_text:
            QMessageBox.warning(self, "Error", "Cannot export an empty resume.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Resume as Word", "", "Word Files (*.docx)")
        if not file_path:
            return

        try:
            from docx.shared import Inches

            doc = Document()

            # Set Narrow Margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.5)
                section.right_margin = Inches(0.5)

            # Remove asterisks and extra blank lines
            formatted_text = resume_text.replace("**", "").strip()
            formatted_text = "\n".join([line.strip() for line in formatted_text.split("\n") if line.strip()])

            for line in formatted_text.split("\n"):
                doc.add_paragraph(line)

            doc.save(file_path)
            QMessageBox.information(self, "Success", "Resume successfully exported as Word document.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export Word document: {str(e)}")

    def load_experiences(self):
        """Load job experiences from the database into the selection list."""
        self.experience_selection_list.clear()
        experiences = fetch_all_experiences()

        if not experiences:
            self.experience_selection_list.addItem("No job experiences found in database.")
            return

        for job_title, company, responsibilities in experiences:
            display_text = f"{job_title} at {company}: {responsibilities[:50]}..."
            item = QListWidgetItem(display_text)
            item.setData(1, (job_title, company, responsibilities))  # Store full experience data
            self.experience_selection_list.addItem(item)

    def show_add_experience_dialog(self):
        """Display the pop-up form to add job experiences."""
        dialog = AddExperienceDialog(self)
        if dialog.exec():
            self.load_experiences()  # Refresh the experience list after adding

    def analyze_job_description(self):
        """Analyze job description, extract key skills, and highlight matched job experiences."""
        job_desc = self.job_desc_input.toPlainText().strip()

        if not job_desc:
            QMessageBox.warning(self, "Error", "Please paste a job description first.")
            return

        ai_result = analyze_job_description(job_desc)

        if "error" in ai_result:
            self.resume_preview.setPlainText(ai_result["error"])
            return

        extracted_skills = ai_result["skills"]
        self.resume_preview.setPlainText(f"Extracted Skills:\n- " + "\n- ".join(extracted_skills))

        # Fetch all stored experiences
        all_experiences = fetch_all_experiences()

        # Find experiences that match AI-extracted skills
        matched_experiences = search_experiences_by_skills(extracted_skills)

        self.experience_selection_list.clear()

        if not all_experiences:
            self.experience_selection_list.addItem("No job experiences found in database.")
            return

        # Display matched experiences at the top
        for job_title, company, responsibilities in matched_experiences:
            item = QListWidgetItem(f"[MATCH] {job_title} at {company}: {responsibilities[:50]}...")
            item.setData(1, (job_title, company, responsibilities))
            self.experience_selection_list.addItem(item)

        # Display remaining experiences below (if they weren’t matched)
        for job_title, company, responsibilities in all_experiences:
            if (job_title, company, responsibilities) not in matched_experiences:
                item = QListWidgetItem(f"{job_title} at {company}: {responsibilities[:50]}...")
                item.setData(1, (job_title, company, responsibilities))
                self.experience_selection_list.addItem(item)

    def generate_resume(self):
        """Generate a tailored resume using AI and selected experiences."""
        job_desc = self.job_desc_input.toPlainText()

        if not job_desc:
            QMessageBox.warning(self, "Error", "Please paste a job description first.")
            return

        selected_experiences = [item.data(1) for item in self.experience_selection_list.selectedItems()]
        if not selected_experiences:
            QMessageBox.warning(self, "Error", "Please select at least one experience.")
            return

        resume_result = generate_resume(job_desc, selected_experiences)

        if "error" in resume_result:
            self.resume_preview.setPlainText(resume_result["error"])
            return

        self.resume_preview.setPlainText(resume_result["resume"])

    def show_about(self):
        """Display About information."""
        about_text = (
            "Resume Wizard\n"
            "Version 1.0\n"
            "Developed by Sergei Krivenkov\n"
            "Date: February 20, 2025\n\n"
            "This application helps generate and optimize resumes by analyzing job descriptions "
            "and matching relevant job experiences."
        )
        QMessageBox.about(self, "About Resume Wizard", about_text)


class AddExperienceDialog(QDialog):
    """Pop-up form for adding job experiences."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Job Experience")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.job_title_input = QLineEdit()
        self.company_input = QLineEdit()
        self.responsibilities_input = QTextEdit()

        form_layout.addRow("Job Title:", self.job_title_input)
        form_layout.addRow("Company:", self.company_input)
        form_layout.addRow("Responsibilities:", self.responsibilities_input)
        layout.addLayout(form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_experience)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_experience(self):
        """Save job experience to the database."""
        job_title = self.job_title_input.text().strip()
        company = self.company_input.text().strip()
        responsibilities = self.responsibilities_input.toPlainText().strip()

        if not job_title or not company or not responsibilities:
            QMessageBox.warning(self, "Error", "All fields must be filled out.")
            return

        try:
            add_job_experience(job_title, company, responsibilities)
            QMessageBox.information(self, "Success", "Job experience added successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResumeWizardApp()
    window.show()
    sys.exit(app.exec())
