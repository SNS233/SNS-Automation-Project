# MASTER BOREWELL & TUBEWELL MANAGEMENT PORTAL

A professional, enterprise-grade web application built to streamline, track, and manage borewell and tubewell marking workflows across thousands of villages, integrated with Microsoft SQL Server, GIS KML processing, and assisted workflows for [Village Well Detector](https://generate.snsies.com/).

---

## 🌟 Key Capabilities & Features

### 1. High-Performance Excel / CSV Importer
- **Drag-and-Drop File Upload**: Supports `.xlsx`, `.xls`, and `.csv`.
- **Intelligent Header Detection**: Automatically identifies source columns (`Zone`, `District_Name`, `Subdistrict_Name`, `Village name`, `Village Code`, and optional fields).
- **Interactive Column Mapping**: Allows re-mapping if uploaded Excel files have varying column names.
- **Client-Side Preview**: Inspects rows instantly before submitting to the database.
- **Duplicate Resolution**: Choose between **Skip duplicates**, **Update existing records**, or **Import as separate**.
- **Data Validation & Error Reporting**: Invalid rows (missing village codes or mandatory names) are not discarded silently; an error Excel report is generated with exact row numbers and failure reasons.
- **Batch History**: Audit log tracking all historical uploads with record statistics.

### 2. Executive Analytics Dashboard
- **8 Dynamic KPI Cards**: Total Villages, Pending Villages, In Progress, Completed, Total Dugwells, Total Borewells, KML Files Stored, and Needs Review.
- **Dynamic Calculation**: All values are computed from real SQL Server records (zero hardcoded statistics).
- **Interactive Visualizations**:
  - Village Status Breakdown (Doughnut Chart)
  - District-wise Progress & Completion Rates (Horizontal Bar Chart)
- **Overall Progress Percentage**: Real-time progress tracking bar.
- **Recent Activity**: Quick access to recently processed villages and newly uploaded KML files.

### 3. All Villages Management Table
- **Strict Business Column Order**:
  1. Checkbox &bull; 2. Zone &bull; 3. District Name &bull; 4. Subdistrict Name &bull; 5. Village Name &bull; 6. Village Code &bull; 7. GEB Connection &bull; 8. Google Search Original Nos &bull; 9. Google Edited Nos and Final KML &bull; 10. Total &bull; 11. Dugwells &bull; 12. Bores &bull; 13. KML File Link &bull; 14. Status Badge &bull; 15. Remark &bull; 16. Actions
- **Powerful Search & Filters**: Search by Village Name, Village Code, or District; filter by District, Subdistrict, Zone, or Processing Status.
- **Pagination**: Scalable server-side pagination (20, 50, 100 rows per page) preventing browser memory slowdowns.
- **Bulk Operations**: Multi-select villages to perform bulk status updates or export selected records.
- **Inline & Modal Editing**: Edit counts, remarks, and metadata with instantaneous DB persistence.

### 4. Village Processing Queue & Assisted Workflow
- **Focused Workbench**: Single-village distraction-free environment.
- **Assisted Workflow for `generate.snsies.com`**:
  - **One-Click Copy**: Copies village name and code to the clipboard for instant search in the external portal.
  - **Open Existing Marking Portal**: Launches `https://generate.snsies.com/` directly in a new browser tab.
  - **KML Dropzone**: Drag and drop the downloaded KML file directly into the workbench.
  - **Auto-Verification**: Compares file name and code confidence, validates coordinates, and suggests well counts.
  - **Form Validation**: Guard rules prevent accidentally marking a village as "Done" without a verified KML file (unless explicitly overridden with an audit remark).
  - **Queue Navigation**: Seamless `Previous Village` and `Next Pending Village` buttons.

### 5. KML & GIS Processing Engine
- **Namespace-Resilient XML Parser**: Handles standard KML 2.2, Google Earth extensions, and `.kmz` compressed archives.
- **Geometry Extraction**: Parses `Point`, `Polygon`, `LineString`, and `MultiGeometry` placemarks.
- **Placemark Breakdown**: Reports distinct counts for Points, Polygons, and Lines.
- **Candidate Classification**: Transparently detects borewell/tubewell or dugwell keywords in placemark names/descriptions while keeping counts fully verifiable by human review.
- **Interactive Leaflet GIS Map**:
  - OpenStreetMap base layer
  - Vector rendering of placemarks and polygon boundaries
  - Automatic centroid calculation and bounding box fitting
  - Clickable popup bubbles displaying coordinates and feature details
- **File Versioning**: When a replacement KML is uploaded, previous versions are archived with timestamps in `KMLFiles`.

### 6. Excel Export Matching Original Template
- **Exact Business Schema**:
  `Zone` | `District_Name` | `Subdistrict_Name` | `Village name` | `Village Code` | `Geb Connection` | `Google search original Nos` | `Google edited Nos and final KML` | `Total` | `Dugwells` | `Bores` | `KML link` | `KML status (in progress/done)` | `Remark`
- **Flexible Scope**: Export All, Selected records, By District, or By Status (Completed, Pending, Needs Review).
- **Format Integrity**: Preserves `Village Code` as text (`@` formatting) to prevent loss of leading zeros or numeric scientific truncation.
- **Working Hyperlinks**: Populates functional KML download URLs for all villages with uploaded files.
- **Professional Formatting**: Styled navy header row, freeze panes, auto-filters, custom column widths, and a dedicated **Summary Report** sheet.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+), Leaflet.js, Chart.js, SheetJS, Lucide Icons |
| **Backend** | Python 3.11+, Flask 3.x, REST API architecture |
| **Database** | Microsoft SQL Server (2017/2019/2022/Azure SQL) with `pyodbc` |
| **Data Processing** | `openpyxl`, `pandas`, `xml.etree.ElementTree`, `zipfile` |
| **Deployment** | Hostinger cPanel / Cloud Python App (`passenger_wsgi.py`), Standalone WSGI (`wsgi.py`) |

---

## 📁 Project Structure

```
d:\Automation Project\
├── app.py                      # Flask Application Factory & UI routes
├── config.py                   # Central environment configuration
├── db.py                       # Microsoft SQL Server connection manager & migrations
├── wsgi.py                     # Standard WSGI entrypoint
├── passenger_wsgi.py           # Hostinger / cPanel WSGI entrypoint
├── schema.sql                  # Complete SQL Server schema creation script
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── .env                        # Local active configuration
├── DEPLOYMENT_GUIDE.md         # Comprehensive Hostinger & SQL Server deployment guide
├── test_suite.py               # End-to-end backend & database verification suite
├── test_api.py                 # REST API HTTP endpoint test suite
├── services/
│   ├── auth_service.py         # Session authentication & password hashing
│   ├── excel_service.py        # Excel import, header detection, error reports, and export
│   ├── kml_service.py          # KML/KMZ parsing, geometry extraction, and GeoJSON generator
│   ├── village_service.py      # Database queries, queue navigation, and metrics aggregation
│   └── integration_adapter.py  # Modular adapter for generate.snsies.com
├── routes/
│   ├── auth_routes.py          # /api/auth endpoints
│   ├── dashboard_routes.py     # /api/dashboard metrics
│   ├── village_routes.py       # /api/villages CRUD, search, pagination, bulk status
│   ├── import_routes.py        # /api/import preview, batch processing, and history
│   ├── kml_routes.py           # /api/kml upload, download, and GeoJSON preview
│   ├── export_routes.py        # /api/export Excel generator
│   └── settings_routes.py      # /api/settings and database diagnostics
├── templates/
│   ├── login.html              # Secure company-style login page
│   └── index.html              # Main single-page application dashboard
├── static/
│   ├── css/
│   │   └── style.css           # Modern GIS/admin dashboard styling
│   └── js/
│       └── app.js              # SPA router, Leaflet map renderer, Chart.js controllers
└── uploads/
    ├── excel/                  # Stored original Excel imports
    ├── kml/                    # Stored KML files with versioning
    └── errors/                 # Generated invalid-row error reports
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+ installed
- Microsoft SQL Server installed and running (or Azure SQL / Remote SQL Server)
- Microsoft ODBC Driver 17 or 18 for SQL Server

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Verify Database & Initialize
The database `BorewellPortalDB` will be automatically initialized when the application starts, or you can verify it directly:
```powershell
python -c "import db; db.init_db()"
```

### 4. Run Automated Test Suites
Verify all database, KML, and Excel functionalities:
```powershell
python test_suite.py
python test_api.py
```

### 5. Launch the Web Server
```powershell
python app.py
```
Open your browser at:
```
http://127.0.0.1:5000
```
Default administrator credentials:
- **Username**: `admin`
- **Password**: `Admin@123`

---

## 🔒 External Portal Integration Architecture (`generate.snsies.com`)

The portal is designed with a **Modular Integration Layer**:
1. **Assisted Manual Workflow (Default & Active)**:
   - Does not require or store third-party credentials.
   - Respects website security, terms of service, and human review boundaries.
   - Provides one-click clipboard copying of the village name & code.
   - Opens `https://generate.snsies.com/` directly in an adjacent tab.
   - Allows dragging the downloaded KML into the portal workbench.
   - Validates that the KML belongs to the active village.
   - Renders the placemarks on an interactive Leaflet map for immediate visual confirmation.
2. **Pluggable API Adapter**:
   - `services/integration_adapter.py` includes a clean interface (`BaseMarkingPortalAdapter` / `DirectApiAdapter`) ready to connect to authorized REST APIs or webhooks if the site owners provide developer documentation in the future.

---

## 📋 Verification & Testing Checklist

- [x] **SQL Server Connection**: Verified on Microsoft SQL Server 2022 via `pyodbc` and `ODBC Driver 18`.
- [x] **Database Schema**: Tables `Users`, `ImportBatches`, `Villages`, `KMLFiles`, `ProcessingHistory`, `ApplicationSettings` created with proper foreign keys and indexes.
- [x] **Excel Import**: Successfully tested with sample villages (`Sarsav`, `Saroli`, `Parvath`, `Navabhaga`, `Mondhri`, `Masota`, `Dadhav`, `Biladiya`).
- [x] **Header Detection**: Auto-maps canonical headers with fallback manual column mapping.
- [x] **Invalid Row Trapping**: Invalid rows captured and written to a downloadable Excel error report.
- [x] **KML Parsing**: Extracted Points, Polygons, and coordinate bounds into standard GeoJSON.
- [x] **GIS Map Preview**: Leaflet map renders points with interactive popups and auto-zoom.
- [x] **Queue Workbench**: Seamless previous/next navigation, counts editing, and KML association.
- [x] **Excel Export**: All 14 columns matching template generated with working KML download hyperlinks, frozen headers, and summary statistics.
- [x] **Authentication**: Secure password hashing with Werkzeug PBKDF2 and session cookies.
- [x] **Hostinger Compatibility**: Provided `passenger_wsgi.py`, `wsgi.py`, and complete deployment guide.
