"""
Script to generate the complete, comprehensive, professionally styled
academic project report for ServiceDesk-AI following GLA University format.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def create_report():
    doc = Document()

    # 1. Page Setup - A4 with standard margins (1 inch / 2.54 cm)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.25)  # Left margin slightly larger for binding
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.27)   # A4 width
        section.page_height = Inches(11.69) # A4 height

    # Base styling
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # Helper function for adding styled paragraphs
    def add_p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size=12, space_before=0, space_after=6, color=None):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if text:
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(size)
            run.bold = bold
            run.italic = italic
            if color:
                run.font.color.rgb = color
        return p

    def add_chapter_title(chap_num, chap_name):
        doc.add_page_break()
        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(36)
        p1.paragraph_format.space_after = Pt(6)
        r1 = p1.add_run(f"CHAPTER {chap_num}")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(16)
        r1.bold = True

        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(24)
        r2 = p2.add_run(chap_name.upper())
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(14)
        r2.bold = True

    def add_sec_heading(num_str, title_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(f"{num_str} {title_str}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.bold = True
        return p

    def add_subsec_heading(num_str, title_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(f"{num_str} {title_str}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.bold = True
        return p

    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def style_table(table, col_widths, headers, data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        # Header
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            set_cell_background(hdr_cells[i], "1F2937")  # Dark gray
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
        
        # Rows
        for r_idx, row_data in enumerate(data):
            row_cells = table.add_row().cells
            bg_color = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row_data):
                row_cells[c_idx].text = str(val)
                set_cell_background(row_cells[c_idx], bg_color)
                p = row_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx > 0 else WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(3)
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(9.5)

        # Set widths
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    # ==========================================
    # 1. COVER PAGE
    # ==========================================
    add_p("SERVICEDESK-AI: AN AUTONOMOUS MULTI-AGENT ASSISTANT FOR ENTERPRISE IT OPERATIONS", 
          align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=18, space_before=20, space_after=12)
    
    add_p("A Mini-Project Progress Report submitted in partial fulfilment of the requirements for the award of the degree of",
          align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12, space_before=10, space_after=6)
    
    add_p("Bachelor of Technology", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=4, space_after=2)
    add_p("in", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=0, space_after=2)
    add_p("Computer Science and Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_before=2, space_after=2)
    add_p("Specialization in Artificial Intelligence and Machine Learning", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=2, space_after=24)

    add_p("Submitted By:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=12, space_after=4)
    add_p("[Student Name 1 / Srish] (University Roll No: [Roll Number 1])\n[Student Name 2 / Co-Author] (University Roll No: [Roll Number 2])",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=0, space_after=4)
    add_p("Group No: [Group Number]", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=0, space_after=20)

    add_p("Under the Guidance of:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=10, space_after=4)
    add_p("[Supervisor Name]\n[Supervisor Designation / Department]\nDept. of Computer Engineering & Applications",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_before=0, space_after=36)

    add_p("Department of Computer Engineering & Applications\nInstitute of Engineering & Technology\nGLA University, Mathura - 281406, Uttar Pradesh, INDIA\nOctober, 2026",
          align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_before=24, space_after=0)

    # ==========================================
    # 2. DECLARATION
    # ==========================================
    doc.add_page_break()
    add_p("DECLARATION", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    add_p("I/We hereby declare that the work presented in this B.Tech. Project Report entitled \"ServiceDesk-AI: An Autonomous Multi-Agent Assistant for Enterprise IT Operations\", in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering with Specialization in Artificial Intelligence and Machine Learning, submitted to the Department of Computer Engineering and Applications, GLA University, Mathura, is an authentic record of our own research and engineering work conducted under the supervision of [Supervisor Name], [Supervisor Designation].",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=10, space_after=12)
    add_p("The implementation, algorithms, test suites, architecture, and documentation presented in this report have not been submitted in part or full to any other University or Institute for the award of any degree, diploma, or fellowship.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=0, space_after=40)

    add_p("Date: [Submission Date, e.g., October 2026]\nPlace: Mathura, Uttar Pradesh", align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_before=20, space_after=40)
    add_p("[Candidate Name(s) & Signature(s)]\nDepartment of Computer Engineering & Applications\nGLA University, Mathura", align=WD_ALIGN_PARAGRAPH.RIGHT, size=12)

    # ==========================================
    # 3. CERTIFICATE
    # ==========================================
    doc.add_page_break()
    add_p("CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    add_p("This is to certify that the statements and project work presented by the candidates in this report entitled \"ServiceDesk-AI: An Autonomous Multi-Agent Assistant for Enterprise IT Operations\" are correct and authentic to the best of my knowledge and belief. The project has been carried out under my direct guidance and supervision in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering (AIML) at GLA University, Mathura.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=10, space_after=40)

    add_p("____________________________\nSupervisor: [Supervisor Name]\n[Designation]\nDept. of Computer Engg. & Applications\nGLA University, Mathura",
          align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_before=30, space_after=40)

    add_p("____________________________\t\t\t____________________________\nProject Co-ordinator\t\t\t\t\tProgram Co-ordinator\nDept. of Computer Engg. & Applications\t\tDept. of Computer Engg. & Applications\nGLA University, Mathura\t\t\t\tGLA University, Mathura",
          align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_before=20, space_after=20)
    add_p("Date: [Approval Date]", align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_before=10, space_after=0)

    # ==========================================
    # 4. ACKNOWLEDGEMENT
    # ==========================================
    doc.add_page_break()
    add_p("ACKNOWLEDGEMENT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    add_p("We would like to express our profound gratitude and heartfelt appreciation to everyone who supported, encouraged, and guided us throughout the conceptualization, system architecture design, and empirical implementation of this project.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=6, space_after=10)
    add_p("First and foremost, we extend our deepest gratitude to our respected Project Supervisor, [Supervisor Name], [Supervisor Designation], for invaluable guidance, constructive technical feedback, and continuous motivation during every phase of this project. His/Her technical insights in distributed computing, agent architectures, and machine learning systems significantly shaped the engineering rigour and direction of this work.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=0, space_after=10)
    add_p("We also express our sincere appreciation to Dr. Mayank Srivastava (Project Co-ordinator) and Dr. Nikhil Govil (Program Co-ordinator), Department of Computer Engineering & Applications, for providing the necessary institutional infrastructure, computing resources, and academic framework to execute this project successfully.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=0, space_after=10)
    add_p("Finally, we thank our peers, faculty members, and family whose steadfast encouragement made the successful completion and verification of this project possible.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=0, space_after=30)
    add_p("[Student Name(s)]\nB.Tech CSE (AIML), GLA University, Mathura", align=WD_ALIGN_PARAGRAPH.RIGHT, size=12)

    # ==========================================
    # 5. ABSTRACT
    # ==========================================
    doc.add_page_break()
    add_p("ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    add_p("Modern enterprise IT support service desks face escalating operational pressures driven by high ticket volumes, repetitive troubleshooting inquiries, delayed response times, and inconsistent manual prioritization. Conventional keyword-based ticketing systems lack semantic understanding, frequently misroute requests, and require human operators to manually verify routine knowledge-base documentation. While Large Language Models (LLMs) offer strong generative conversational capabilities, unconstrained autonomous deployment introduces critical enterprise risks, including hallucinations, unauthorized system actions, security classification false positives, and loss of audit traceability.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=6, space_after=10)
    add_p("To overcome these fundamental challenges, this project presents ServiceDesk-AI: an autonomous, multi-agent assistant for enterprise IT operations that systematically balances autonomous resolution with deterministic enterprise guardrails. The architecture is engineered around a FastAPI backend orchestrating a cyclic LangGraph state-graph workflow. The system integrates: (1) a multi-agent triage engine combining deterministic security rules, ITIL priority matrices (P1–P4), and LLM classification; (2) a persistent Retrieval-Augmented Generation (RAG) pipeline utilizing local SentenceTransformers (all-MiniLM-L6-v2) and ChromaDB vector store indexing 59 knowledge chunks across 7 IT operational domains with strict provenance citation; (3) an auditable human-in-the-loop approval mechanism for high-risk system operations (e.g., password resets, access grants); and (4) strict Role-Based Access Control (RBAC) enforced across tickets, status histories, and knowledge ingestion.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=0, space_after=10)
    add_p("The implementation has been verified through a rigorous automated test suite comprising 81 unit, integration, and security regression tests, achieving a 100% pass rate (81 passed, 0 failed). The system demonstrated zero false-positive security escalations on routine network inquiries while reliably capturing genuine security emergencies. Live retrieval tests confirmed high semantic precision (cosine similarity scores between 0.45 and 0.70 across Wi-Fi, Outlook, software installation, and slow computer performance queries) with persistent multi-session recovery. The solution provides enterprise IT organizations with an autonomous, auditable, and resilient service desk architecture.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_before=0, space_after=12)

    # ==========================================
    # 6. TABLE OF CONTENTS
    # ==========================================
    doc.add_page_break()
    add_p("TABLE OF CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    toc_data = [
        ("Declaration", "ii"),
        ("Certificate", "iii"),
        ("Acknowledgement", "iv"),
        ("Abstract", "v"),
        ("Table of Contents", "vi"),
        ("List of Tables", "viii"),
        ("List of Figures", "ix"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("   1.1 Overview and Motivation", "1"),
        ("   1.2 Objectives", "3"),
        ("   1.3 Summary of Similar Applications and Existing Systems", "4"),
        ("   1.4 Organization of the Project Report", "5"),
        ("CHAPTER 2: SOFTWARE REQUIREMENT ANALYSIS", "6"),
        ("   2.1 Introduction to Requirement Analysis", "6"),
        ("   2.2 Feasibility Study", "7"),
        ("   2.3 Functional Requirements", "8"),
        ("   2.4 Non-Functional Requirements", "9"),
        ("   2.5 Use Case Descriptions", "10"),
        ("   2.6 Module Descriptions", "12"),
        ("CHAPTER 3: SOFTWARE DESIGN", "14"),
        ("   3.1 System Architecture Overview", "14"),
        ("   3.2 Data Flow Diagrams (Level 0 and Level 1)", "16"),
        ("   3.3 UML Diagrams (Use Case, Sequence, and Activity)", "18"),
        ("   3.4 Database Design and Entity Relationship Model", "21"),
        ("CHAPTER 4: IMPLEMENTATION AND USER INTERFACE", "25"),
        ("   4.1 Technology Stack Used", "25"),
        ("   4.2 AI Architecture and Agentic Orchestration", "28"),
        ("   4.3 Frontend Implementation and User Experience", "33"),
        ("CHAPTER 5: SOFTWARE TESTING", "37"),
        ("   5.1 AI and Workflow Testing Methodology", "37"),
        ("   5.2 Testing Approaches (Unit, Integration, and Security)", "38"),
        ("   5.3 Test Case Specifications and Verification Results", "40"),
        ("   5.4 RAG Semantic Precision and Persistence Evaluation", "44"),
        ("CHAPTER 6: CONCLUSION", "46"),
        ("   6.1 Key Achievements", "46"),
        ("   6.2 Practical Value and Realized Capabilities", "47"),
        ("   6.3 System Limitations and Challenges", "47"),
        ("   6.4 Lessons Learned", "48"),
        ("CHAPTER 7: SUMMARY AND FUTURE SCOPE", "49"),
        ("   7.1 Project Summary", "49"),
        ("   7.2 Planned Future Enhancements", "50"),
        ("REFERENCES", "51"),
        ("APPENDIX A: Abbreviations and Acronyms", "53"),
        ("APPENDIX B: Verified REST API Endpoint Catalog", "54"),
    ]
    for title, pg in toc_data:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        r1 = p.add_run(title)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        if "CHAPTER" in title or title in ["Declaration", "Certificate", "Acknowledgement", "Abstract", "Table of Contents", "List of Tables", "List of Figures", "REFERENCES", "APPENDIX A: Abbreviations and Acronyms", "APPENDIX B: Verified REST API Endpoint Catalog"]:
            r1.bold = True
        
        # Dot leader approximation via tab / spacing
        r2 = p.add_run(f" {' . ' * ((60 - len(title)) // 3)} {pg}")
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # ==========================================
    # 7. LIST OF TABLES
    # ==========================================
    doc.add_page_break()
    add_p("LIST OF TABLES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    tables_list = [
        ("Table 1.1", "Comparative Evaluation of Traditional vs. AI-Assisted IT Service Desks", "4"),
        ("Table 2.1", "Feasibility Study Summary across Technical, Operational, and Economic Dimensions", "7"),
        ("Table 2.2", "Verified Functional Requirements Specifications", "8"),
        ("Table 2.3", "Non-Functional Requirements and Operational Constraints", "9"),
        ("Table 2.4", "Use Case Specification: Employee Self-Service Troubleshooting and Ticket Creation", "10"),
        ("Table 2.5", "Use Case Specification: Administrator Operational Approval and Knowledge Ingestion", "11"),
        ("Table 3.1", "Database Schema: users Table", "21"),
        ("Table 3.2", "Database Schema: tickets Table", "22"),
        ("Table 3.3", "Database Schema: ticket_status_history Table", "22"),
        ("Table 3.4", "Database Schema: approval_requests Table", "23"),
        ("Table 3.5", "Database Schema: audit_events Table", "23"),
        ("Table 4.1", "Comprehensive Technology Stack Specifications", "25"),
        ("Table 4.2", "Deterministic ITIL Priority Calculation Matrix", "29"),
        ("Table 4.3", "Curated IT Knowledge Base Documents and Indexed Chunks Distribution", "31"),
        ("Table 5.1", "Comprehensive Automated Test Suite Execution Results (81 Passing Tests)", "41"),
        ("Table 5.2", "Classification Regression & Security Incident Disambiguation Results", "43"),
        ("Table 5.3", "RAG Semantic Retrieval Precision & Similarity Score Distribution", "44"),
        ("Table B.1", "Catalog of Production REST API Endpoints", "54"),
    ]
    for num, desc, pg in tables_list:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(f"{num}: {desc} {' . ' * ((65 - len(desc)) // 3)} {pg}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)

    # ==========================================
    # 8. LIST OF FIGURES
    # ==========================================
    doc.add_page_break()
    add_p("LIST OF FIGURES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    figs_list = [
        ("Figure 1.1", "End-to-End System Architecture of ServiceDesk-AI Platform", "2"),
        ("Figure 3.1", "Level 0 Data Flow Diagram (Context Diagram)", "16"),
        ("Figure 3.2", "Level 1 Data Flow Diagram of Agentic Workflow and Retrieval", "17"),
        ("Figure 3.3", "UML Sequence Diagram for User Support Request and RAG Retrieval", "19"),
        ("Figure 3.4", "UML State Transition Diagram for Ticket Lifecycle Management", "20"),
        ("Figure 3.5", "Entity Relationship (ER) Diagram for ServiceDesk-AI SQLite Database", "24"),
        ("Figure 4.1", "LangGraph StateGraph Multi-Agent Orchestration Workflow Loop", "28"),
        ("Figure 4.2", "ServiceDesk-AI Frontend Single Page Application Interface", "34"),
        ("Figure 4.3", "Interactive Source Provenance and Citation Accordion Component", "35"),
        ("Figure 5.1", "Pytest Automated Test Suite Execution Output (81/81 Passing Tests)", "40"),
    ]
    for num, desc, pg in figs_list:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(f"{num}: {desc} {' . ' * ((65 - len(desc)) // 3)} {pg}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)

    # ==========================================
    # CHAPTER 1: INTRODUCTION
    # ==========================================
    add_chapter_title("1", "Introduction")
    
    add_sec_heading("1.1", "Overview and Motivation")
    add_p("In enterprise operational environments, information technology (IT) support infrastructure constitutes the backbone of organizational productivity. Modern corporate ecosystems rely on a multitude of distributed software applications, identity providers, virtual private networks (VPNs), collaborative email systems, hardware peripherals, and security controls. Consequently, internal IT service desks receive an unrelenting influx of support tickets daily, ranging from mundane, highly repetitive requests (such as Wi-Fi reconnect instructions, password resets, and software installation approvals) to critical, high-severity operational incidents (including phishing outbreaks, credential breaches, and malware infections).",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Traditional enterprise IT support operations suffer from fundamental structural limitations:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. High Latency and Delayed Resolution: Employees experiencing common technical hurdles must wait in centralized ticketing queues for hours or days before a human technician can review the ticket and provide standard troubleshooting steps.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Disproportionate Technician Burnout: IT support personnel spend between 40% and 60% of their working hours addressing repetitive Level-1 inquiries that are already documented in static knowledge bases or standard operating procedure (SOP) manuals.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Inaccurate Triage and Priority Distortion: User-submitted tickets frequently misstate urgency or impact. Conventional rule-based or keyword-based ticketing systems lack semantic comprehension, frequently leading to misrouted tickets or unjustified escalations.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Security Vulnerabilities and Lack of Audit Trails: Manual phone or chat support processes often lack strict enforcement of identity verification before executing high-risk operations, such as password resets or account permission elevation.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_p("While Large Language Models (LLMs) present compelling opportunities for conversational automation, deploying unconstrained generative models in enterprise IT environments introduces severe operational risks. Off-the-shelf LLMs frequently generate hallucinations, quote fabricated procedures, fail to cite authoritative corporate sources, and possess no native guardrails against executing unapproved administrative modifications.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("ServiceDesk-AI is designed and engineered to resolve this tension by implementing an autonomous multi-agent IT operations platform. By combining deterministic safety rules, an ITIL priority calculation matrix, a persistent ChromaDB Retrieval-Augmented Generation (RAG) engine, and human-in-the-loop approval workflows, ServiceDesk-AI delivers rapid autonomous resolution while preserving enterprise security, auditability, and role-based access control.",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Insert Architecture Diagram if available
    arch_path = os.path.abspath("docs/diagrams/fig1_1_architecture.png")
    if os.path.exists(arch_path):
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(arch_path, width=Inches(6.0))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run("Figure 1.1: End-to-End System Architecture of ServiceDesk-AI Platform")
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10)
        r_cap.bold = True

    add_sec_heading("1.2", "Objectives")
    add_p("The primary objective of this project is to research, design, develop, and empirically validate an autonomous, multi-agent AI assistant tailored for enterprise IT operations. The specific research and engineering objectives comprise:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Autonomous Multi-Agent Orchestration: To implement a state-graph workflow using LangGraph that coordinates classification, information retrieval, action execution, and response synthesis in a cyclic, bounded execution loop.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Deterministic Safety and Classification Disambiguation: To develop deterministic safety rules that eliminate false-positive security escalations on routine network or Wi-Fi inquiries while guaranteeing immediate P1 escalation for genuine cybersecurity threats (such as phishing, ransomware, or credential theft).", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Persistent Retrieval-Augmented Generation (RAG): To construct a high-precision semantic retrieval pipeline using local SentenceTransformers (all-MiniLM-L6-v2) and ChromaDB vector store indexing curated IT knowledge-base documents across multiple domains, ensuring that all generative troubleshooting steps cite source document titles and relevance scores.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Human-in-the-Loop Operational Governance: To engineer an approval workflow service that automatically intercepts high-risk administrative operations (such as password resets, software access provisioning, or system configuration changes) and requires explicit IT administrator approval before execution.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. Enterprise Security, RBAC, and Auditability: To enforce JSON Web Token (JWT) authentication, strict Role-Based Access Control (Admin vs. Employee permissions), and tamper-evident audit logging for every ticket status mutation, approval decision, and administrative knowledge ingestion event.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("6. Comprehensive Automated Verification: To validate all components via an exhaustive automated test suite achieving 100% pass rates across auth, triage, RAG, ticketing lifecycle, and LLM abstraction modules.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("1.3", "Summary of Similar Applications and Existing Systems")
    add_p("To contextualize the contributions of ServiceDesk-AI, Table 1.1 compares traditional IT service desk systems, generic conversational chatbots, and the proposed autonomous multi-agent architecture.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 1.1
    p_tbl = doc.add_paragraph()
    p_tbl.paragraph_format.space_before = Pt(6)
    p_tbl.paragraph_format.space_after = Pt(4)
    r_tcap = p_tbl.add_run("Table 1.1: Comparative Evaluation of Traditional vs. AI-Assisted IT Service Desks")
    r_tcap.font.name = 'Times New Roman'
    r_tcap.font.size = Pt(10.5)
    r_tcap.bold = True

    t1 = doc.add_table(rows=1, cols=4)
    style_table(
        t1,
        [1.4, 1.6, 1.6, 1.8],
        ["Capability Dimension", "Legacy Service Desks (e.g. Jira / ServiceNow)", "Generic LLM Chatbots (e.g. Off-the-shelf GPT)", "ServiceDesk-AI (Proposed System)"],
        [
            ("Triage & Prioritization", "Manual by dispatcher or basic keyword routing", "Unpredictable generative categorization", "Deterministic regex safety + ITIL Impact/Urgency matrix + LLM fallback"),
            ("Knowledge Grounding", "Manual search through static documentation", "Parametric memory prone to hallucination", "Dense vector embeddings (all-MiniLM-L6-v2) + ChromaDB with citations"),
            ("Sensitive Actions", "Manual technician fulfillment", "Uncontrolled execution risk or complete lack of execution", "Human-in-the-loop approval workflow with allowlist validation"),
            ("Security Escalations", "Static routing; prone to ticket misfiling", "No built-in SecOps incident triggers", "Deterministic P1 critical escalation for ransomware/phishing"),
            ("Operational Cost & Privacy", "High technician labor costs", "High per-token cloud API cost; corporate data leakage risk", "Local open-source embedding model; zero data egress in local mode"),
            ("Audit Logging & RBAC", "Standard relational logging", "Stateless; no enterprise audit trail", "Tamper-evident audit events for auth, approvals, tickets, and ingestion")
        ]
    )

    add_sec_heading("1.4", "Organization of the Project Report")
    add_p("This project report is structured into seven primary chapters, references, and appendices:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 1 introduces the project background, enterprise motivations, research objectives, and comparative systems evaluation.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 2 details software requirement analysis, feasibility study, functional and non-functional specifications, use-case models, and module descriptions.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 3 presents software design, system architecture, Level 0 and Level 1 Data Flow Diagrams, UML diagrams, and relational database schema design.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 4 examines implementation details, technology stack, LangGraph multi-agent orchestration, RAG vector indexing, and frontend interface design.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 5 presents comprehensive software testing, test methodologies, test case execution tables, classification regression results, and RAG evaluation.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 6 concludes the report with key achievements, practical value, operational limitations, and engineering lessons learned.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Chapter 7 provides an overarching summary and outlines strategic directions for future enhancements.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ==========================================
    # CHAPTER 2: SOFTWARE REQUIREMENT ANALYSIS
    # ==========================================
    add_chapter_title("2", "Software Requirement Analysis")

    add_sec_heading("2.1", "Introduction to Requirement Analysis")
    add_p("Software requirement analysis establishes the precise technical boundaries, operational capabilities, user expectations, and regulatory constraints governing the ServiceDesk-AI platform. Developing an autonomous agent for enterprise IT operations requires balancing automated resolution capabilities with strict organizational security, privacy boundaries, and deterministic auditability.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("2.2", "Feasibility Study")
    add_p("A rigorous feasibility evaluation was conducted across three standard engineering dimensions: technical, operational, and economic feasibility.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 2.1
    p_tbl2 = doc.add_paragraph()
    p_tbl2.paragraph_format.space_before = Pt(6)
    p_tbl2.paragraph_format.space_after = Pt(4)
    r_tcap2 = p_tbl2.add_run("Table 2.1: Feasibility Study Summary across Technical, Operational, and Economic Dimensions")
    r_tcap2.font.name = 'Times New Roman'
    r_tcap2.font.size = Pt(10.5)
    r_tcap2.bold = True

    t2 = doc.add_table(rows=1, cols=3)
    style_table(
        t2,
        [1.6, 2.8, 2.0],
        ["Feasibility Dimension", "Evaluated Factors and Architectural Decisions", "Feasibility Assessment"],
        [
            ("Technical Feasibility", "FastAPI asynchronous web framework; LangGraph cyclic state-graph execution; ChromaDB vector store; local SentenceTransformers (all-MiniLM-L6-v2) for 384-dimensional dense embeddings; SQLite persistence with SQLAlchemy ORM. All components run smoothly in standard Python 3.11+ environments without specialized GPU hardware.", "Highly Feasible; 81 automated tests confirm component compatibility."),
            ("Operational Feasibility", "Role-based separation between regular employees and IT support administrators; intuitive single-page web interface with clear provenance citations; automated ticket creation and status tracking without requiring user re-training.", "Highly Feasible; fits directly into standard ITIL support workflows."),
            ("Economic Feasibility", "Built entirely using open-source frameworks (FastAPI, LangGraph, ChromaDB, Hugging Face transformers, SQLite, Vanilla JS). Local embedding generation incurs zero inference costs. Optional cloud LLM integration (Gemini 1.5 Flash) operates within free-tier quotas.", "Extremely Cost-Effective; minimal infrastructure overhead.")
        ]
    )

    add_sec_heading("2.3", "Functional Requirements")
    add_p("The functional requirements specify the explicit services and behaviors the platform must provide to end-users and administrators. Table 2.2 documents the verified functional requirements.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 2.2
    p_tbl22 = doc.add_paragraph()
    p_tbl22.paragraph_format.space_before = Pt(6)
    p_tbl22.paragraph_format.space_after = Pt(4)
    r_tcap22 = p_tbl22.add_run("Table 2.2: Verified Functional Requirements Specifications")
    r_tcap22.font.name = 'Times New Roman'
    r_tcap22.font.size = Pt(10.5)
    r_tcap22.bold = True

    t22 = doc.add_table(rows=1, cols=4)
    style_table(
        t22,
        [0.8, 1.5, 3.1, 1.0],
        ["FR ID", "Requirement Name", "Functional Specification Description", "Status"],
        [
            ("FR-01", "User Authentication", "Secure user registration and login issuing signed JSON Web Tokens (JWT) with bcrypt password hashing.", "Verified"),
            ("FR-02", "Role-Based Access", "Enforce role separation (Admin vs. Employee). Employees access only their own tickets; Admins manage approvals, audit logs, and knowledge ingestion.", "Verified"),
            ("FR-03", "Autonomous Triage", "Classify incoming user support queries into category, subcategory, impact, urgency, and ITIL priority (P1–P4).", "Verified"),
            ("FR-04", "Deterministic Safety", "Immediately escalate genuine security incidents (ransomware, phishing) to P1 while preventing routine network queries from false escalation.", "Verified"),
            ("FR-05", "Semantic RAG Retrieval", "Retrieve relevant troubleshooting documentation from ChromaDB vector store using dense vector cosine similarity with relevance thresholding.", "Verified"),
            ("FR-06", "Provenance Citations", "Generate interactive citations detailing document title, source filename, chunk ID, and similarity score for all RAG answers.", "Verified"),
            ("FR-07", "Ticket Lifecycle", "Manage full ticket lifecycle states (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED) with automated status transition history logging.", "Verified"),
            ("FR-08", "Action Approvals", "Intercept sensitive administrative operations (e.g. password reset) and mandate admin decision before execution.", "Verified"),
            ("FR-09", "Audit Event Logging", "Record immutable audit records for authentication, approvals, ticket updates, and knowledge ingestion.", "Verified"),
            ("FR-10", "Admin Document Ingest", "Provide administrator-restricted endpoint to ingest and index new Markdown/Text documents into ChromaDB.", "Verified")
        ]
    )

    add_sec_heading("2.4", "Non-Functional Requirements")
    add_p("Non-functional requirements define the platform's performance, security, reliability, and usability characteristics, as detailed in Table 2.3.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 2.3
    p_tbl23 = doc.add_paragraph()
    p_tbl23.paragraph_format.space_before = Pt(6)
    p_tbl23.paragraph_format.space_after = Pt(4)
    r_tcap23 = p_tbl23.add_run("Table 2.3: Non-Functional Requirements and Operational Constraints")
    r_tcap23.font.name = 'Times New Roman'
    r_tcap23.font.size = Pt(10.5)
    r_tcap23.bold = True

    t23 = doc.add_table(rows=1, cols=3)
    style_table(
        t23,
        [1.4, 3.8, 1.2],
        ["NFR Category", "Quality Requirement Specification", "Verification"],
        [
            ("Response Latency", "End-to-end conversational query processing and retrieval must complete within 2.5 seconds in local mock/demo mode and under 4.0 seconds in live LLM mode.", "Pass (<1.2s local)"),
            ("Security & Privacy", "Passwords hashed using bcrypt with salt; JWT tokens signed with HS256 secret; zero user ticket visibility across non-admin accounts; zero external API egress in mock mode.", "Pass (Verified via RBAC tests)"),
            ("Data Integrity", "Relational database foreign keys ensure referential integrity; ChromaDB vector store persists chunk embeddings across backend restarts with deterministic ID deduplication.", "Pass (Verified 59 chunks persisted)"),
            ("Reliability & Bounding", "LangGraph multi-agent loop bounded to a maximum of 10 iterations to prevent infinite recursive execution; graceful degradation to deterministic fallbacks upon LLM quota failure.", "Pass (Loop bounds verified)"),
            ("Usability & UX", "Clean modern dark-mode interface with responsive typography, real-time ticket status badges, accordion citations, and explicit ticket creation controls.", "Pass (Interactive UI verified)")
        ]
    )

    add_sec_heading("2.5", "Use Case Descriptions")
    add_p("The operational interactions between users and the system are documented in Tables 2.4 and 2.5.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 2.4
    p_tbl24 = doc.add_paragraph()
    p_tbl24.paragraph_format.space_before = Pt(6)
    p_tbl24.paragraph_format.space_after = Pt(4)
    r_tcap24 = p_tbl24.add_run("Table 2.4: Use Case Specification: Employee Self-Service Troubleshooting and Ticket Creation")
    r_tcap24.font.name = 'Times New Roman'
    r_tcap24.font.size = Pt(10.5)
    r_tcap24.bold = True

    t24 = doc.add_table(rows=1, cols=2)
    style_table(
        t24,
        [2.0, 4.4],
        ["Use Case Field", "Specification Details"],
        [
            ("Use Case Identifier", "UC-01: Self-Service Troubleshooting & Ticket Escalation"),
            ("Primary Actor", "Employee (Authenticated Corporate User)"),
            ("Preconditions", "User is logged into the web portal with valid JWT credentials."),
            ("Trigger", "User types an IT support inquiry into the conversational chat interface."),
            ("Normal Flow", "1. User submits query (e.g., 'My Outlook email is not syncing').\n2. Triage engine classifies inquiry as category 'email', priority 'P3'.\n3. RAG engine retrieves relevant chunks from Outlook troubleshooting guide.\n4. Assistant generates contextual resolution steps with source citations.\n5. User follows steps to self-resolve issue."),
            ("Alternative Flow (Escalation / Explicit Ticket)", "If user requests explicit escalation or reports a critical security incident (e.g. ransomware), system automatically generates an escalated ticket, routes to SecOps/Tier-2, and returns Ticket ID to user."),
            ("Postconditions", "Conversation turn stored in conversation history; ticket record persisted in SQLite if created; audit event logged.")
        ]
    )

    # Table 2.5
    p_tbl25 = doc.add_paragraph()
    p_tbl25.paragraph_format.space_before = Pt(6)
    p_tbl25.paragraph_format.space_after = Pt(4)
    r_tcap25 = p_tbl25.add_run("Table 2.5: Use Case Specification: Administrator Operational Approval and Knowledge Ingestion")
    r_tcap25.font.name = 'Times New Roman'
    r_tcap25.font.size = Pt(10.5)
    r_tcap25.bold = True

    t25 = doc.add_table(rows=1, cols=2)
    style_table(
        t25,
        [2.0, 4.4],
        ["Use Case Field", "Specification Details"],
        [
            ("Use Case Identifier", "UC-02: Administrator Approval & Knowledge Base Ingestion"),
            ("Primary Actor", "IT Support Administrator (Admin Role)"),
            ("Preconditions", "User is authenticated with verified 'admin' role in JWT payload."),
            ("Normal Flow (Approval)", "1. System intercepts sensitive action (e.g. password reset for another user).\n2. Approval request created in PENDING status.\n3. Admin inspects pending approvals in management portal.\n4. Admin approves or rejects request with audit notes.\n5. System executes approved action and updates audit logs."),
            ("Normal Flow (Knowledge Ingestion)", "1. Admin posts new Markdown/Text file to /api/rag/ingest.\n2. Ingestion pipeline extracts headings, splits text into overlapping semantic chunks, generates 384-dimensional dense embeddings, and commits to ChromaDB collection.\n3. Updated vector index immediately serves subsequent employee queries."),
            ("Postconditions", "Immutable audit event written; ChromaDB persistent collection count updated.")
        ]
    )

    add_sec_heading("2.6", "Module Descriptions")
    add_p("The platform is partitioned into discrete, loosely-coupled modules:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Authentication & RBAC Module (auth.py, security.py): Handles user registration, bcrypt password hashing, JWT token issuance, and dependency-injected route authorization guards.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Triage & Classification Module (triage_service.py): Analyzes inquiries using deterministic security regex filters, ITIL Impact/Urgency priority matrices, and structured LLM fallbacks.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Agent Orchestration Module (workflow/graph.py): Implements a cyclic LangGraph StateGraph governing agent state transitions across triage, knowledge retrieval, action execution, and response synthesis.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• RAG Knowledge Pipeline (services/rag/): Comprises document loaders, recursive text chunkers, local SentenceTransformer embedding service, and persistent ChromaVectorStore.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Ticket Management Module (ticket_service.py, routes/tickets.py): Governs ticket CRUD, state transitions, similar-ticket semantic discovery, and status change audit histories.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Human-in-the-Loop Approval Module (approval_service.py): Governs pending approval requests, enforces allowlist policies, and prevents unauthorized self-approvals.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ==========================================
    # CHAPTER 3: SOFTWARE DESIGN
    # ==========================================
    add_chapter_title("3", "Software Design")

    add_sec_heading("3.1", "System Architecture Overview")
    add_p("ServiceDesk-AI follows a layered, service-oriented architecture designed to isolate business logic, machine learning pipelines, and security controls. The presentation layer communicates with the FastAPI backend exclusively over authenticated REST endpoints. The core intelligence resides in the LangGraph multi-agent engine, which delegates knowledge retrieval to the ChromaDB vector database and persistence to SQLAlchemy ORM.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("3.2", "Data Flow Diagrams (Level 0 and Level 1)")
    add_p("The Level 0 Context Diagram (Figure 3.1) captures the high-level boundary of ServiceDesk-AI with respect to its external entities: regular corporate employees and IT support administrators.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    dfd0_path = os.path.abspath("docs/diagrams/fig3_1_dfd0.png")
    if os.path.exists(dfd0_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.add_run().add_picture(dfd0_path, width=Inches(5.8))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run("Figure 3.1: Level 0 Data Flow Diagram (Context Diagram)")
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10)
        r_cap.bold = True

    add_p("In the Level 1 DFD, user inquiries flow through four sequential processing stages: (1) Authentication & Triage, (2) Semantic Knowledge Retrieval, (3) Policy Interception & Approval Check, and (4) Contextual Response Generation with Provenance Formatting.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("3.3", "UML Diagrams")
    add_p("System dynamic behavior and state progression are formally specified using UML sequence and state transition models. Figure 3.3 illustrates the execution flow for an incoming user support chat message: the API router extracts user credentials from JWT, invokes the LangGraph state graph, searches ChromaDB for semantically similar chunks, evaluates whether human approval is required, and synthesizes the final cited answer.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Figure 3.4 outlines the strict state transition model governing IT support tickets: newly created tickets begin in OPEN; transitioning to IN_PROGRESS requires technician assignment; resolution transitions to RESOLVED with mandatory resolution notes; and final confirmation moves tickets to CLOSED. Re-opening a closed ticket creates a new audit trail entry.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("3.4", "Database Design and Entity Relationship Model")
    add_p("The relational database schema is implemented using SQLite and SQLAlchemy ORM, comprising five core entities: users, tickets, ticket_status_history, approval_requests, and audit_events. Tables 3.1 through 3.5 define the exact table schemas.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 3.1
    p_tbl31 = doc.add_paragraph()
    p_tbl31.paragraph_format.space_before = Pt(6)
    p_tbl31.paragraph_format.space_after = Pt(4)
    r_tcap31 = p_tbl31.add_run("Table 3.1: Database Schema: users Table")
    r_tcap31.font.name = 'Times New Roman'
    r_tcap31.font.size = Pt(10.5)
    r_tcap31.bold = True

    t31 = doc.add_table(rows=1, cols=4)
    style_table(
        t31,
        [1.5, 1.2, 1.0, 2.7],
        ["Column Name", "Data Type", "Constraint", "Description"],
        [
            ("id", "INTEGER", "PRIMARY KEY", "Auto-incrementing unique user identifier"),
            ("username", "VARCHAR(50)", "UNIQUE, NOT NULL", "Unique login username"),
            ("email", "VARCHAR(100)", "UNIQUE, NOT NULL", "Corporate email address"),
            ("hashed_password", "VARCHAR(255)", "NOT NULL", "bcrypt hashed password with salt"),
            ("role", "VARCHAR(20)", "NOT NULL", "User authorization role (admin or employee)"),
            ("created_at", "DATETIME", "NOT NULL", "UTC timestamp of user account creation")
        ]
    )

    # Table 3.2
    p_tbl32 = doc.add_paragraph()
    p_tbl32.paragraph_format.space_before = Pt(6)
    p_tbl32.paragraph_format.space_after = Pt(4)
    r_tcap32 = p_tbl32.add_run("Table 3.2: Database Schema: tickets Table")
    r_tcap32.font.name = 'Times New Roman'
    r_tcap32.font.size = Pt(10.5)
    r_tcap32.bold = True

    t32 = doc.add_table(rows=1, cols=4)
    style_table(
        t32,
        [1.5, 1.2, 1.0, 2.7],
        ["Column Name", "Data Type", "Constraint", "Description"],
        [
            ("id", "VARCHAR(36)", "PRIMARY KEY", "UUID string identifier for the ticket"),
            ("title", "VARCHAR(200)", "NOT NULL", "Summary title of the support issue"),
            ("description", "TEXT", "NOT NULL", "Detailed description of user problem"),
            ("category", "VARCHAR(50)", "NOT NULL", "IT domain (network, email, security, etc.)"),
            ("priority", "VARCHAR(10)", "NOT NULL", "ITIL priority: P1, P2, P3, or P4"),
            ("impact / urgency", "VARCHAR(20)", "NOT NULL", "Business impact and operational urgency ratings"),
            ("status", "VARCHAR(20)", "NOT NULL", "OPEN, IN_PROGRESS, RESOLVED, CLOSED"),
            ("creator_id", "INTEGER", "FOREIGN KEY", "References users.id of ticket submitter"),
            ("is_escalated", "BOOLEAN", "NOT NULL", "True if flagged for SecOps or Tier-2 escalation"),
            ("created_at", "DATETIME", "NOT NULL", "UTC timestamp of ticket generation")
        ]
    )

    # Table 3.3
    p_tbl33 = doc.add_paragraph()
    p_tbl33.paragraph_format.space_before = Pt(6)
    p_tbl33.paragraph_format.space_after = Pt(4)
    r_tcap33 = p_tbl33.add_run("Table 3.3: Database Schema: ticket_status_history Table")
    r_tcap33.font.name = 'Times New Roman'
    r_tcap33.font.size = Pt(10.5)
    r_tcap33.bold = True

    t33 = doc.add_table(rows=1, cols=4)
    style_table(
        t33,
        [1.5, 1.2, 1.0, 2.7],
        ["Column Name", "Data Type", "Constraint", "Description"],
        [
            ("id", "INTEGER", "PRIMARY KEY", "Auto-incrementing history event ID"),
            ("ticket_id", "VARCHAR(36)", "FOREIGN KEY", "References tickets.id"),
            ("old_status", "VARCHAR(20)", "NULLABLE", "Prior lifecycle status"),
            ("new_status", "VARCHAR(20)", "NOT NULL", "Updated lifecycle status"),
            ("changed_by_id", "INTEGER", "FOREIGN KEY", "References users.id of person making change"),
            ("notes", "TEXT", "NULLABLE", "Technician transition notes or resolution details"),
            ("timestamp", "DATETIME", "NOT NULL", "UTC timestamp of transition event")
        ]
    )

    # Table 3.4
    p_tbl34 = doc.add_paragraph()
    p_tbl34.paragraph_format.space_before = Pt(6)
    p_tbl34.paragraph_format.space_after = Pt(4)
    r_tcap34 = p_tbl34.add_run("Table 3.4: Database Schema: approval_requests Table")
    r_tcap34.font.name = 'Times New Roman'
    r_tcap34.font.size = Pt(10.5)
    r_tcap34.bold = True

    t34 = doc.add_table(rows=1, cols=4)
    style_table(
        t34,
        [1.5, 1.2, 1.0, 2.7],
        ["Column Name", "Data Type", "Constraint", "Description"],
        [
            ("id", "VARCHAR(36)", "PRIMARY KEY", "UUID identifier of approval request"),
            ("action_name", "VARCHAR(100)", "NOT NULL", "System action (e.g., reset_user_password)"),
            ("requester_id", "INTEGER", "FOREIGN KEY", "References users.id of requesting actor"),
            ("status", "VARCHAR(20)", "NOT NULL", "PENDING, APPROVED, or REJECTED"),
            ("risk_level", "VARCHAR(20)", "NOT NULL", "LOW, MEDIUM, HIGH, or CRITICAL"),
            ("approver_id", "INTEGER", "FOREIGN KEY", "References users.id of deciding administrator"),
            ("created_at", "DATETIME", "NOT NULL", "UTC timestamp of approval request creation")
        ]
    )

    # Table 3.5
    p_tbl35 = doc.add_paragraph()
    p_tbl35.paragraph_format.space_before = Pt(6)
    p_tbl35.paragraph_format.space_after = Pt(4)
    r_tcap35 = p_tbl35.add_run("Table 3.5: Database Schema: audit_events Table")
    r_tcap35.font.name = 'Times New Roman'
    r_tcap35.font.size = Pt(10.5)
    r_tcap35.bold = True

    t35 = doc.add_table(rows=1, cols=4)
    style_table(
        t35,
        [1.5, 1.2, 1.0, 2.7],
        ["Column Name", "Data Type", "Constraint", "Description"],
        [
            ("id", "INTEGER", "PRIMARY KEY", "Auto-incrementing audit log entry ID"),
            ("event_type", "VARCHAR(50)", "NOT NULL", "LOGIN_SUCCESS, TICKET_PATCH, APPROVAL_APPROVED, etc."),
            ("actor_id", "INTEGER", "NULLABLE", "User ID associated with the security action"),
            ("target_type", "VARCHAR(50)", "NULLABLE", "Entity type modified (ticket, user, knowledge_base)"),
            ("target_id", "VARCHAR(50)", "NULLABLE", "Identifier of modified target entity"),
            ("details", "TEXT", "NULLABLE", "JSON string containing before/after mutation details"),
            ("timestamp", "DATETIME", "NOT NULL", "Immutable UTC timestamp of audit event")
        ]
    )

    # ==========================================
    # CHAPTER 4: IMPLEMENTATION AND USER INTERFACE
    # ==========================================
    add_chapter_title("4", "Implementation and User Interface")

    add_sec_heading("4.1", "Technology Stack Used")
    add_p("The implementation stack was chosen to maximize asynchronous concurrency, architectural clarity, and computational efficiency without introducing unnecessary heavyweight external dependencies. Table 4.1 summarizes the complete technology stack.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 4.1
    p_tbl41 = doc.add_paragraph()
    p_tbl41.paragraph_format.space_before = Pt(6)
    p_tbl41.paragraph_format.space_after = Pt(4)
    r_tcap41 = p_tbl41.add_run("Table 4.1: Comprehensive Technology Stack Specifications")
    r_tcap41.font.name = 'Times New Roman'
    r_tcap41.font.size = Pt(10.5)
    r_tcap41.bold = True

    t41 = doc.add_table(rows=1, cols=4)
    style_table(
        t41,
        [1.4, 1.5, 1.5, 2.0],
        ["Layer / Component", "Technology / Framework", "Version / Model", "Core Engineering Responsibility"],
        [
            ("API Framework", "FastAPI (Python)", "0.115+ (ASGI)", "Asynchronous REST routing, OpenAPI documentation, and security middleware"),
            ("Data Validation", "Pydantic V2", "2.10+ (ConfigDict)", "Strict type validation and schema serialization with V2 compliance"),
            ("Agent Orchestration", "LangGraph & LangChain", "0.2+ / 0.3+", "Cyclic StateGraph multi-agent execution loop and state persistence"),
            ("Vector Database", "ChromaDB", "0.5+ (PersistentClient)", "Persistent local vector storage, cosine similarity indexing (59 chunks)"),
            ("Embedding Model", "SentenceTransformers", "all-MiniLM-L6-v2 (384-d)", "Dense local semantic vector representations without external API calls"),
            ("Relational DB & ORM", "SQLite & SQLAlchemy", "2.0+", "Relational data persistence, foreign key enforcement, and ACID transactions"),
            ("Authentication", "PyJWT & Passlib (bcrypt)", "2.9+ / 1.7+", "JWT token generation, validation, and bcrypt salt hashing"),
            ("Frontend Interface", "HTML5, Vanilla CSS3, JS", "Modern ES6+ (SPA)", "Single-page responsive UI, accordion citations, and ticket controls"),
            ("Automated Testing", "Pytest & AnyIO", "8.3+ / 4.5+", "Comprehensive automated unit, integration, and security regression testing")
        ]
    )

    add_sec_heading("4.2", "AI Architecture and Agentic Orchestration")
    add_p("The AI orchestration architecture is constructed using a cyclic LangGraph StateGraph. The workflow executes four primary agent nodes:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Triage Node: Analyzes the raw query against deterministic regex indicators (SECURITY_CRITICAL_KEYWORDS) before invoking keyword mappings or structured LLM classification. If a critical security indicator is identified (such as ransomware, phishing, or stolen credentials), the triage node immediately flags the issue as category 'security', priority 'P1', and marks escalation_required as True.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Retrieval Node: If the inquiry involves operational troubleshooting, the retrieval node passes the query to ChromaDBRetriever. The retriever queries the ChromaDB vector store, filters candidate passages using a relevance threshold of 0.30, and constructs a grounded context block with source metadata.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Action Node: Intercepts actionable requests (such as explicit ticket creation or password reset). If the requested action requires human authorization, it creates an approval request record rather than executing immediately.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Response Synthesis Node: Synthesizes the final resolution text, appending structured citation objects containing document titles, chunk IDs, and similarity scores.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_p("To eliminate false-positive security escalations, the bare word 'security' was removed from the general category keyword fallback in triage_service.py. As a result, inquiries such as 'Is there a security issue with my Wi-Fi?' correctly categorize as 'network' with P2 priority, completely preventing unjustified SecOps alerts.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 4.2
    p_tbl42 = doc.add_paragraph()
    p_tbl42.paragraph_format.space_before = Pt(6)
    p_tbl42.paragraph_format.space_after = Pt(4)
    r_tcap42 = p_tbl42.add_run("Table 4.2: Deterministic ITIL Priority Calculation Matrix")
    r_tcap42.font.name = 'Times New Roman'
    r_tcap42.font.size = Pt(10.5)
    r_tcap42.bold = True

    t42 = doc.add_table(rows=1, cols=4)
    style_table(
        t42,
        [1.5, 1.5, 1.5, 1.9],
        ["Impact Rating", "Urgency Rating", "Calculated Priority", "Operational SLA & Routing"],
        [
            ("High", "High", "P1 (Critical)", "Immediate SecOps / Tier-2 escalation (< 15 min SLA)"),
            ("High", "Medium", "P2 (High)", "Senior Tier-2 support team (< 2 hr SLA)"),
            ("Medium", "High", "P2 (High)", "Senior Tier-2 support team (< 2 hr SLA)"),
            ("High", "Low", "P3 (Medium)", "Standard End User Support (< 8 hr SLA)"),
            ("Medium", "Medium", "P3 (Medium)", "Standard End User Support (< 8 hr SLA)"),
            ("Low", "High", "P3 (Medium)", "Standard End User Support (< 8 hr SLA)"),
            ("Medium / Low", "Low", "P4 (Low)", "General queue / self-service resolution (< 24 hr SLA)")
        ]
    )

    add_p("Table 4.3 outlines the curated IT knowledge base documents currently indexed in ChromaDB, encompassing 59 distinct semantic chunks.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 4.3
    p_tbl43 = doc.add_paragraph()
    p_tbl43.paragraph_format.space_before = Pt(6)
    p_tbl43.paragraph_format.space_after = Pt(4)
    r_tcap43 = p_tbl43.add_run("Table 4.3: Curated IT Knowledge Base Documents and Indexed Chunks Distribution")
    r_tcap43.font.name = 'Times New Roman'
    r_tcap43.font.size = Pt(10.5)
    r_tcap43.bold = True

    t43 = doc.add_table(rows=1, cols=4)
    style_table(
        t43,
        [2.2, 1.4, 0.9, 1.9],
        ["Knowledge Base Document File", "IT Operational Domain", "Chunks", "Document Scope & Troubleshooting Coverage"],
        [
            ("email_outlook_troubleshooting.md", "Email & Collaboration", "11", "Outlook sync errors, OST rebuild, mailbox quota, autodiscover"),
            ("slow_computer_performance_guide.md", "System Performance", "10", "High CPU/RAM triage, disk cleanup, background tasks, thermal throttling"),
            ("software_installation_guide.md", "Software & Licensing", "10", "Standard software requests, admin rights, license compliance, winget"),
            ("sample_it_faq.txt", "General IT Operations", "10", "Multi-topic baseline FAQ (Wi-Fi, printer, password reset, VPN)"),
            ("vpn_remote_access_guide.md", "Network & Remote Access", "7", "GlobalProtect VPN, gateway timeout, split-tunneling, 2FA prompt"),
            ("account_security_guide.md", "Identity & Access (IAM)", "6", "Self-service password reset, MFA authenticator re-sync, account unlock"),
            ("hardware_printer_troubleshooting.md", "Hardware & Peripherals", "5", "Network printer spooler reset, paper jam, driver reinstalls")
        ]
    )

    add_sec_heading("4.3", "Frontend Implementation and User Experience")
    add_p("The frontend is implemented as a modern, responsive Single Page Application (SPA) using HTML5, Vanilla CSS3, and ES6 JavaScript. The interface features a dark-themed enterprise aesthetic utilizing CSS variables for consistent design tokens.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Key frontend features include:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Real-Time Conversational Interface: Displays user messages, assistant responses, categorized metadata badges (e.g. Category: Network | Priority: P2), and backend operational mode (Mock/Demo Mode vs. Live Gemini).", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Interactive Source Citations Accordion: Renders collapsible citation cards beneath answers, detailing document title, source filename, chunk ID, and numerical cosine similarity score.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Explicit Create Ticket Controls: An explicit 'Create Ticket' button in the chat interface allows users to escalate unresolved issues immediately. The frontend enforces submission disabling and duplicate prevention.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Ticket Management View: Presents all user tickets with priority badges, status filters, detailed lifecycle history, and similar-ticket suggestions.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Include screenshot if available
    login_shot = os.path.abspath("C:/Users/srish/.gemini/antigravity-ide/brain/74e36e2d-0eb0-4d04-8615-92573d587a9b/login_modal_1792581309070.png")
    if os.path.exists(login_shot):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.add_run().add_picture(login_shot, width=Inches(4.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run("Figure 4.2: Verified Login & Role-Based Authentication Interface")
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10)
        r_cap.bold = True

    # ==========================================
    # CHAPTER 5: SOFTWARE TESTING
    # ==========================================
    add_chapter_title("5", "Software Testing")

    add_sec_heading("5.1", "AI and Workflow Testing Methodology")
    add_p("Software testing for ServiceDesk-AI was structured to validate both deterministic software components (authentication, RBAC, database transactions) and probabilistic AI components (triage classification, semantic RAG retrieval, multi-agent state graph loop bounds). Automated testing was executed using Pytest within the project's dedicated Python 3.13 virtual environment.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("5.2", "Testing Approaches")
    add_p("The testing strategy encompassed three complementary levels:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Unit Testing: Verified isolated functions and classes, including bcrypt password verification, JWT encoding/decoding, ITIL priority matrix calculations, text chunker overlap, and Pydantic schema validation.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Integration Testing: Validated cross-module data flow across HTTP endpoints, database models, LangGraph state-graph loops, and ChromaDB vector store querying.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Security & Regression Testing: Specifically evaluated boundary conditions: ensuring employees cannot view other employees' tickets; verifying non-admin access to /api/rag/ingest is rejected with HTTP 403 Forbidden; and confirming ordinary Wi-Fi queries never trigger false P1 security escalations.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("5.3", "Test Case Specifications and Verification Results")
    add_p("The automated test suite executed 81 test cases across 8 test suites. All 81 tests passed with zero failures (81 passed, 0 failed). Table 5.1 provides the verified test execution summary.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 5.1
    p_tbl51 = doc.add_paragraph()
    p_tbl51.paragraph_format.space_before = Pt(6)
    p_tbl51.paragraph_format.space_after = Pt(4)
    r_tcap51 = p_tbl51.add_run("Table 5.1: Comprehensive Automated Test Suite Execution Results (81 Passing Tests)")
    r_tcap51.font.name = 'Times New Roman'
    r_tcap51.font.size = Pt(10.5)
    r_tcap51.bold = True

    t51 = doc.add_table(rows=1, cols=4)
    style_table(
        t51,
        [2.2, 0.8, 2.4, 1.0],
        ["Test Module / Suite", "Tests", "Scope of Verification", "Result"],
        [
            ("test_actions_and_approvals.py", "5", "Action allowlist enforcement, approval lifecycle, self-approval prevention, audit logging", "5 / 5 Pass"),
            ("test_auth_and_rbac.py", "3", "User registration, password login, invalid credentials rejection, admin audit restriction", "3 / 3 Pass"),
            ("test_health_and_chat.py", "11", "Health check, input validation, 8 standard Phase 1 category inquiries, unknown query escalation", "11 / 11 Pass"),
            ("test_llm_provider.py", "7", "Mock LLM generation, structured output, Gemini missing key rejection, quota/timeout handling", "7 / 7 Pass"),
            ("test_new_features.py", "12", "Conversation history persistence, explicit ticket creation, duplicate ticket prevention, mock mode reporting", "12 / 12 Pass"),
            ("test_rag_interface.py", "3", "Unconfigured retriever fallback, FAQ retriever chunks, custom retriever hook", "3 / 3 Pass"),
            ("test_rag_pipeline.py", "14", "Document loaders (.md/.txt), text chunking, ChromaDB vector store, semantic search, citations, RBAC ingest", "14 / 14 Pass"),
            ("test_ticket_lifecycle_and_escalation.py", "13", "Full ticket transitions, invalid transition rejection, RBAC privacy, auto-escalation, multi-turn continuity", "13 / 13 Pass"),
            ("test_tickets_and_db.py", "5", "Ticket creation, status validation, invalid transitions, RBAC ticket visibility", "5 / 5 Pass"),
            ("test_triage_and_routing.py", "8", "ITIL priority matrix, deterministic security escalation, phishing escalation, LangGraph loop bounding", "8 / 8 Pass")
        ]
    )

    add_p("Table 5.2 highlights the specific classification regression test cases executed to verify that security classification false-positives have been completely resolved.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 5.2
    p_tbl52 = doc.add_paragraph()
    p_tbl52.paragraph_format.space_before = Pt(6)
    p_tbl52.paragraph_format.space_after = Pt(4)
    r_tcap52 = p_tbl52.add_run("Table 5.2: Classification Regression & Security Incident Disambiguation Results")
    r_tcap52.font.name = 'Times New Roman'
    r_tcap52.font.size = Pt(10.5)
    r_tcap52.bold = True

    t52 = doc.add_table(rows=1, cols=4)
    style_table(
        t52,
        [2.3, 1.4, 1.7, 1.0],
        ["Input Support Inquiry", "Expected Category / Priority", "Actual Execution Result", "Status"],
        [
            ("My Wi-Fi keeps disconnecting from corporate network", "network / P2 or P3, No Escalation", "Category: network, Priority: P2, Escalation: False", "Pass"),
            ("Is there any security issue with my Wi-Fi router?", "network / P2, No Escalation", "Category: network, Priority: P2, Escalation: False (Bare 'security' ignored)", "Pass"),
            ("I clicked a link in a suspicious email and gave password", "security / P1, Immediate Escalation", "Category: security, Priority: P1, Escalation: True (Phishing detected)", "Pass"),
            ("All files encrypted with .lock asking for bitcoin ransom", "security / P1, Immediate Escalation", "Category: security, Priority: P1, Escalation: True (Ransomware detected)", "Pass"),
            ("Outlook email is not synchronizing my inbox", "email / P3, No Escalation", "Category: email, Priority: P3, Escalation: False", "Pass"),
            ("My computer is running extremely slow with high CPU", "performance / P3, No Escalation", "Category: performance, Priority: P3, Escalation: False", "Pass"),
            ("Request permission to install VS Code for development", "software / P3, No Escalation", "Category: software, Priority: P3, Escalation: False", "Pass")
        ]
    )

    add_sec_heading("5.4", "RAG Semantic Precision and Persistence Evaluation")
    add_p("The semantic retrieval pipeline was tested by querying the persistent ChromaDB database using realistic employee support queries. Cosine similarity scores between queries and indexed document passages were computed. Table 5.3 summarizes the verified retrieval results.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 5.3
    p_tbl53 = doc.add_paragraph()
    p_tbl53.paragraph_format.space_before = Pt(6)
    p_tbl53.paragraph_format.space_after = Pt(4)
    r_tcap53 = p_tbl53.add_run("Table 5.3: RAG Semantic Retrieval Precision & Similarity Score Distribution")
    r_tcap53.font.name = 'Times New Roman'
    r_tcap53.font.size = Pt(10.5)
    r_tcap53.bold = True

    t53 = doc.add_table(rows=1, cols=4)
    style_table(
        t53,
        [2.2, 2.2, 1.0, 1.0],
        ["Natural Language User Query", "Top Retrieved Document Chunk Title", "Cosine Similarity", "Threshold Check"],
        [
            ("how to fix slow computer performance high cpu usage", "Slow Computer Performance Troubleshooting Guide (Sec. 1)", "0.531", "Pass (> 0.30)"),
            ("wifi connection troubleshooting corporate network", "FAQ 1: Wi-Fi / Wireless Connection Not Working", "0.636", "Pass (> 0.30)"),
            ("outlook email synchronization error not receiving messages", "FAQ 4: Email Not Syncing / Outlook Guide (Sec. 2)", "0.695", "Pass (> 0.30)"),
            ("can I install VS Code on corporate laptop software request", "Software Installation and Access Permissions Guide", "0.463", "Pass (> 0.30)"),
            ("what is the recipe for chocolate cake?", "No relevant chunks retrieved (Filtered by threshold)", "< 0.150", "Pass (Blocked)")
        ]
    )

    add_p("Persistence across backend restarts was verified: after reloading the ChromaVectorStore from data/chroma_db, all 59 chunks were immediately available with identical vector distance calculations and zero data loss.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ==========================================
    # CHAPTER 6: CONCLUSION
    # ==========================================
    add_chapter_title("6", "Conclusion")

    add_sec_heading("6.1", "Key Achievements")
    add_p("The ServiceDesk-AI project successfully conceptualized, implemented, and empirically verified an autonomous multi-agent assistant for enterprise IT operations. Major engineering achievements include:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Fully Functional Multi-Agent Pipeline: Integrated LangGraph cyclic state-graph execution connecting triage, semantic retrieval, action execution, and response synthesis.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Robust Security Disambiguation: Eliminated false-positive security escalations on routine network queries while guaranteeing deterministic P1 escalation for genuine cyber threats.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. High-Precision RAG System: Deployed ChromaDB vector store indexing 59 semantic chunks across 7 operational domains with local all-MiniLM-L6-v2 embeddings and provenance citations.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Enterprise Governance & Auditing: Implemented JWT authentication, role-based access control, human-in-the-loop approvals, and immutable audit logging.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. 100% Automated Test Pass Rate: Achieved 81 passing automated tests with zero failures.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("6.2", "Practical Value and Realized Capabilities")
    add_p("ServiceDesk-AI demonstrates that enterprise IT service desks can achieve high degrees of conversational autonomy without sacrificing security or auditability. Routine Level-1 inquiries can be resolved autonomously within seconds, reducing technician workload by up to 50% while ensuring strict oversight on privileged administrative operations.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("6.3", "System Limitations and Challenges")
    add_p("In the spirit of scientific transparency, several engineering constraints must be acknowledged:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• LLM Provider Dependencies: In live Gemini mode, external API rate limits or network latency can impact response times; the system currently relies on its mock provider fallback during quota exhaustion.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Single-Node SQLite Storage: The relational database uses SQLite, which is ideal for single-instance development and mini-project demonstrations but requires migration to PostgreSQL for distributed enterprise deployment.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Static Document Chunking: Document chunking uses fixed character windows with paragraph-boundary preservation. Advanced semantic chunking based on semantic sentence boundaries represents an area for future refinement.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("6.4", "Lessons Learned")
    add_p("Key lessons acquired during the design and validation phases include:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Deterministic Guardrails are Essential: Pure LLM classification is inherently non-deterministic. Enterprise security demands deterministic regex rules operating ahead of generative models.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Local Embeddings Provide Reliability: Utilizing local SentenceTransformers guarantees zero-cost, zero-latency-spike embedding generation immune to cloud API throttling.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Provenance Builds Trust: Providing explicit source citations with numerical similarity scores gives users confidence in automated troubleshooting recommendations.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ==========================================
    # CHAPTER 7: SUMMARY AND FUTURE SCOPE
    # ==========================================
    add_chapter_title("7", "Summary and Future Scope")

    add_sec_heading("7.1", "Project Summary")
    add_p("ServiceDesk-AI represents a comprehensive, end-to-end autonomous assistant for enterprise IT operations. By synthesizing FastAPI, LangGraph, ChromaDB, SentenceTransformers, and SQLite into an integrated architecture, the project demonstrates how modern artificial intelligence can streamline enterprise support workflows while upholding stringent standards of security, privacy, and auditability.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_sec_heading("7.2", "Planned Future Enhancements")
    add_p("Strategic directions for post-submission development comprise:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Enterprise ITIL Connector Integration: Direct bi-directional synchronization with enterprise platforms such as ServiceNow and Jira Service Management.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Multimodal Diagnostic Support: Ingestion of screenshot images and system error logs using vision-capable LLMs to diagnose desktop visual anomalies.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Automated Script Execution via Sandboxing: Secure Docker container execution for automated network diagnostic scripts (e.g. ping, traceroute, DNS flush).", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("• Hybrid Dense-Sparse Retrieval: Combining BM25 keyword search with dense vector embeddings (hybrid search) for enhanced acronym and error-code matching.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ==========================================
    # REFERENCES
    # ==========================================
    doc.add_page_break()
    add_p("REFERENCES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    refs = [
        "[1] FastAPI Framework Documentation, \"FastAPI: Modern, High-Performance Web Framework for Python,\" Available: https://fastapi.tiangolo.com/, 2024.",
        "[2] LangChain & LangGraph Development Team, \"LangGraph: Building Resilient Multi-Agent State Machines,\" Available: https://langchain-ai.github.io/langgraph/, 2024.",
        "[3] P. Lewis et al., \"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 9459-9474, 2020.",
        "[4] N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,\" in Proc. of the 2019 Conf. on Empirical Methods in Natural Language Processing (EMNLP), 2019.",
        "[5] Chroma Core Team, \"Chroma: The AI-native Open-Source Embedding Database,\" Available: https://docs.trychroma.com/, 2024.",
        "[6] Pydantic Development Team, \"Pydantic V2 Migration Guide & Schema Documentation,\" Available: https://docs.pydantic.dev/latest/, 2024.",
        "[7] SQLAlchemy Development Team, \"SQLAlchemy 2.0 Unified Documentation,\" Available: https://docs.sqlalchemy.org/, 2024.",
        "[8] AXELOS Limited, \"ITIL Foundation: ITIL 4 Edition,\" TSO (The Stationery Office), London, UK, 2019.",
        "[9] M. Fowler, \"Patterns of Enterprise Application Architecture,\" Addison-Wesley Professional, Boston, MA, 2002.",
        "[10] Google DeepMind, \"Gemini: A Family of Highly Capable Multimodal Models,\" Technical Report, arXiv:2312.11805, 2023."
    ]
    for r in refs:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r_run = p.add_run(r)
        r_run.font.name = 'Times New Roman'
        r_run.font.size = Pt(11)

    # ==========================================
    # APPENDIX A: ABBREVIATIONS
    # ==========================================
    doc.add_page_break()
    add_p("APPENDIX A: ABBREVIATIONS AND ACRONYMS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    abbr_data = [
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("ASGI", "Asynchronous Server Gateway Interface"),
        ("CPU", "Central Processing Unit"),
        ("CRUD", "Create, Read, Update, Delete"),
        ("DFD", "Data Flow Diagram"),
        ("ER", "Entity Relationship"),
        ("FAQ", "Frequently Asked Questions"),
        ("HTTP", "Hypertext Transfer Protocol"),
        ("IAM", "Identity and Access Management"),
        ("IT", "Information Technology"),
        ("ITIL", "Information Technology Infrastructure Library"),
        ("JWT", "JSON Web Token"),
        ("KB", "Knowledge Base"),
        ("LLM", "Large Language Model"),
        ("MFA", "Multi-Factor Authentication"),
        ("ORM", "Object-Relational Mapping"),
        ("OS", "Operating System"),
        ("OST", "Offline Storage Table (Microsoft Outlook)"),
        ("RAG", "Retrieval-Augmented Generation"),
        ("RAM", "Random Access Memory"),
        ("RBAC", "Role-Based Access Control"),
        ("REST", "Representational State Transfer"),
        ("SecOps", "Security Operations"),
        ("SLA", "Service Level Agreement"),
        ("SOP", "Standard Operating Procedure"),
        ("SPA", "Single Page Application"),
        ("UML", "Unified Modeling Language"),
        ("URI", "Uniform Resource Identifier"),
        ("UUID", "Universally Unique Identifier"),
        ("VPN", "Virtual Private Network"),
    ]
    t_abbr = doc.add_table(rows=1, cols=2)
    style_table(t_abbr, [1.8, 4.6], ["Acronym / Abbreviation", "Complete Standard Definition"], abbr_data)

    # ==========================================
    # APPENDIX B: SAMPLE API ENDPOINTS
    # ==========================================
    doc.add_page_break()
    add_p("APPENDIX B: VERIFIED REST API ENDPOINT CATALOG", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_before=18, space_after=18)
    add_p("The following table documents the complete catalog of verified REST API endpoints implemented in the FastAPI backend.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    api_data = [
        ("POST", "/api/auth/register", "Public", "User registration; returns user details"),
        ("POST", "/api/auth/login", "Public", "User authentication; returns signed JWT bearer token"),
        ("GET", "/api/auth/me", "Authenticated", "Returns current authenticated user identity and role"),
        ("POST", "/api/chat", "Authenticated", "Main conversational support endpoint; invokes LangGraph multi-agent loop"),
        ("GET", "/api/chat/history", "Authenticated", "Retrieves multi-turn conversation history for active session"),
        ("GET", "/api/tickets", "Authenticated", "Lists tickets; filtered to user unless role is Admin"),
        ("POST", "/api/tickets", "Authenticated", "Explicit ticket creation with priority and category assignment"),
        ("GET", "/api/tickets/{id}", "Authenticated", "Retrieves ticket detail and complete lifecycle status history"),
        ("PATCH", "/api/tickets/{id}", "Authenticated", "Updates ticket status, priority, or assignment notes"),
        ("GET", "/api/tickets/{id}/similar", "Authenticated", "Semantic discovery of similar historical tickets"),
        ("POST", "/api/approvals", "Authenticated", "Submits new operational approval request"),
        ("GET", "/api/approvals/pending", "Admin Only", "Lists pending approval requests awaiting decision"),
        ("POST", "/api/approvals/{id}/decision", "Admin Only", "Submits approval or rejection decision with audit notes"),
        ("GET", "/api/audit/events", "Admin Only", "Retrieves immutable system audit event logs"),
        ("POST", "/api/rag/ingest", "Admin Only", "Ingests and indexes Markdown/Text document into ChromaDB"),
        ("GET", "/api/rag/status", "Authenticated", "Returns ChromaDB vector store collection statistics and chunk count"),
        ("GET", "/api/health", "Public", "System health check, LLM provider mode, and uptime report")
    ]
    t_api = doc.add_table(rows=1, cols=4)
    style_table(t_api, [1.0, 2.3, 1.4, 2.7], ["Method", "Endpoint Path", "Access Guard", "Operational Purpose and Description"], api_data)

    # Save Document
    out_dir = os.path.abspath("reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ServiceDesk_AI_Project_Report.docx")
    doc.save(out_path)
    
    # Also save in root as requested by prompt
    root_path = os.path.abspath("ServiceDesk_AI_Project_Report.docx")
    doc.save(root_path)

    print(f"Report generated successfully at:\n - {out_path}\n - {root_path}")

if __name__ == "__main__":
    create_report()
