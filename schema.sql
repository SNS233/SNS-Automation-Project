-- =====================================================================
-- MASTER BOREWELL & TUBEWELL MANAGEMENT PORTAL
-- Microsoft SQL Server Database Schema
-- Compatible with SQL Server 2017, 2019, 2022 and Azure SQL
-- =====================================================================

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BorewellPortalDB')
BEGIN
    CREATE DATABASE BorewellPortalDB;
END
GO

USE BorewellPortalDB;
GO

-- 1. Users Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
BEGIN
    CREATE TABLE Users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(100) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        full_name NVARCHAR(150),
        role NVARCHAR(50) DEFAULT 'admin',
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- 2. ImportBatches Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ImportBatches')
BEGIN
    CREATE TABLE ImportBatches (
        id INT IDENTITY(1,1) PRIMARY KEY,
        filename NVARCHAR(255) NOT NULL,
        file_path NVARCHAR(500),
        total_rows INT DEFAULT 0,
        valid_rows INT DEFAULT 0,
        invalid_rows INT DEFAULT 0,
        duplicate_rows INT DEFAULT 0,
        status NVARCHAR(50) DEFAULT 'completed',
        error_report_path NVARCHAR(500),
        created_at DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- 3. Villages Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Villages')
BEGIN
    CREATE TABLE Villages (
        id INT IDENTITY(1,1) PRIMARY KEY,
        batch_id INT NULL CONSTRAINT FK_Villages_Batch FOREIGN KEY REFERENCES ImportBatches(id) ON DELETE SET NULL,
        zone NVARCHAR(100) NULL,
        district_name NVARCHAR(150) NOT NULL,
        subdistrict_name NVARCHAR(150) NOT NULL,
        village_name NVARCHAR(150) NOT NULL,
        village_code NVARCHAR(100) NOT NULL,
        geb_connection NVARCHAR(100) NULL,
        google_search_orig_nos INT DEFAULT 0,
        google_edited_nos INT DEFAULT 0,
        total_wells INT DEFAULT 0,
        dugwells INT DEFAULT 0,
        bores INT DEFAULT 0,
        kml_status NVARCHAR(50) DEFAULT 'Pending',
        remark NVARCHAR(MAX) NULL,
        processing_order INT DEFAULT 0,
        is_locked BIT DEFAULT 0,
        last_processed_at DATETIME2 NULL,
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );

    CREATE INDEX IX_Villages_VillageCode ON Villages(village_code);
    CREATE INDEX IX_Villages_Status ON Villages(kml_status);
    CREATE INDEX IX_Villages_District ON Villages(district_name);
    CREATE INDEX IX_Villages_Subdistrict ON Villages(subdistrict_name);
END
GO

-- 4. KMLFiles Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'KMLFiles')
BEGIN
    CREATE TABLE KMLFiles (
        id INT IDENTITY(1,1) PRIMARY KEY,
        village_id INT NOT NULL CONSTRAINT FK_KML_Village FOREIGN KEY REFERENCES Villages(id) ON DELETE CASCADE,
        village_code NVARCHAR(100) NOT NULL,
        original_filename NVARCHAR(255) NOT NULL,
        stored_filename NVARCHAR(255) NOT NULL,
        file_path NVARCHAR(500) NOT NULL,
        file_size BIGINT DEFAULT 0,
        point_count INT DEFAULT 0,
        polygon_count INT DEFAULT 0,
        linestring_count INT DEFAULT 0,
        total_placemarks INT DEFAULT 0,
        geojson_data NVARCHAR(MAX) NULL,
        bounds_json NVARCHAR(500) NULL,
        version INT DEFAULT 1,
        is_active BIT DEFAULT 1,
        validation_status NVARCHAR(50) DEFAULT 'Valid',
        created_at DATETIME2 DEFAULT GETDATE()
    );

    CREATE INDEX IX_KMLFiles_VillageId ON KMLFiles(village_id);
    CREATE INDEX IX_KMLFiles_VillageCode ON KMLFiles(village_code);
    CREATE INDEX IX_KMLFiles_IsActive ON KMLFiles(is_active);
END
GO

-- 5. ProcessingHistory Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ProcessingHistory')
BEGIN
    CREATE TABLE ProcessingHistory (
        id INT IDENTITY(1,1) PRIMARY KEY,
        village_id INT NOT NULL CONSTRAINT FK_History_Village FOREIGN KEY REFERENCES Villages(id) ON DELETE CASCADE,
        previous_status NVARCHAR(50),
        new_status NVARCHAR(50),
        action_note NVARCHAR(500),
        changed_by NVARCHAR(100) DEFAULT 'System',
        created_at DATETIME2 DEFAULT GETDATE()
    );

    CREATE INDEX IX_History_VillageId ON ProcessingHistory(village_id);
END
GO

-- 6. ApplicationSettings Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ApplicationSettings')
BEGIN
    CREATE TABLE ApplicationSettings (
        id INT IDENTITY(1,1) PRIMARY KEY,
        setting_key NVARCHAR(100) NOT NULL UNIQUE,
        setting_value NVARCHAR(MAX),
        updated_at DATETIME2 DEFAULT GETDATE()
    );

    -- Default settings
    INSERT INTO ApplicationSettings (setting_key, setting_value)
    VALUES 
        ('marking_portal_url', 'https://generate.snsies.com/'),
        ('auto_calc_total', 'true'),
        ('kml_storage_dir', 'uploads/kml'),
        ('app_name', 'Master Borewell & Tubewell Management Portal');
END
GO

-- 7. Persons Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Persons')
BEGIN
    CREATE TABLE Persons (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(150) NOT NULL,
        email NVARCHAR(150) NULL,
        phone NVARCHAR(50) NULL,
        role NVARCHAR(100) DEFAULT 'Field Surveyor',
        is_active BIT DEFAULT 1,
        notes NVARCHAR(MAX) NULL,
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- 8. VillageAssignments Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'VillageAssignments')
BEGIN
    CREATE TABLE VillageAssignments (
        id INT IDENTITY(1,1) PRIMARY KEY,
        village_id INT NOT NULL,
        person_id INT NOT NULL,
        assigned_by NVARCHAR(100) DEFAULT 'Admin',
        assigned_at DATETIME2 DEFAULT GETDATE(),
        unassigned_at DATETIME2 NULL,
        status NVARCHAR(50) DEFAULT 'Active'
    );
END
GO

-- 9. Add Assignment & GEB columns to Villages if they do not exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Villages') AND name = 'assigned_person_id')
BEGIN
    ALTER TABLE Villages ADD assigned_person_id INT NULL;
    ALTER TABLE Villages ADD assigned_person_name NVARCHAR(150) NULL;
    ALTER TABLE Villages ADD assigned_at DATETIME2 NULL;
    ALTER TABLE Villages ADD assignment_status NVARCHAR(50) DEFAULT 'Unassigned';
    ALTER TABLE Villages ADD electric_kuva INT DEFAULT 0;
    ALTER TABLE Villages ADD electric_bor INT DEFAULT 0;
    ALTER TABLE Villages ADD total_electric INT DEFAULT 0;
    ALTER TABLE Villages ADD solar_bor_kuva INT DEFAULT 0;
    ALTER TABLE Villages ADD total_electric_solar INT DEFAULT 0;
    ALTER TABLE Villages ADD raw_geb_data NVARCHAR(MAX) NULL;
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Villages') AND name = 'generated_review_url')
BEGIN
    ALTER TABLE Villages ADD generated_review_url NVARCHAR(500) NULL;
    ALTER TABLE Villages ADD work_status NVARCHAR(50) DEFAULT 'Not Done';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Persons') AND name = 'user_id')
BEGIN
    ALTER TABLE Persons ADD user_id INT NULL;
END
GO

-- 10. AdminNotifications Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AdminNotifications')
BEGIN
    CREATE TABLE AdminNotifications (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        user_name NVARCHAR(150) NOT NULL,
        village_id INT NOT NULL,
        village_name NVARCHAR(150) NOT NULL,
        message NVARCHAR(500) NOT NULL,
        is_read BIT DEFAULT 0,
        created_at DATETIME2 DEFAULT GETDATE()
    );

    CREATE INDEX IX_AdminNotifications_IsRead ON AdminNotifications(is_read);
END
GO


