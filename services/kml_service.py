import os
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from werkzeug.utils import secure_filename
import db
from config import Config

def strip_namespace(tag):
    """Strip XML namespace prefix from element tag."""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag


def parse_coordinates_text(coord_text):
    """Parse KML coordinate string 'lon,lat,alt lon,lat,alt ...' into list of [lon, lat]."""
    coords = []
    if not coord_text:
        return coords
    
    # Split by whitespace or newlines
    tokens = coord_text.strip().split()
    for token in tokens:
        parts = token.strip().split(',')
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                coords.append([lon, lat])
            except (ValueError, TypeError):
                continue
    return coords


def parse_kml_content(kml_bytes_or_str):
    """
    Parse KML or KMZ content into geometry counts, GeoJSON, bounding box, and placemarks.
    Resilient across KML 2.0, 2.1, 2.2, KMZ, and various namespace declarations.
    """
    if isinstance(kml_bytes_or_str, str):
        content_bytes = kml_bytes_or_str.encode('utf-8', errors='replace')
    else:
        content_bytes = kml_bytes_or_str

    # Check if KMZ (zip format)
    is_kmz = False
    try:
        import io
        if zipfile.is_zipfile(io.BytesIO(content_bytes)):
            is_kmz = True
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                # Find .kml file inside zip
                kml_names = [n for n in z.namelist() if n.lower().endswith('.kml')]
                if not kml_names:
                    raise ValueError("KMZ archive does not contain any .kml file")
                # Default to doc.kml or first kml
                target = 'doc.kml' if 'doc.kml' in kml_names else kml_names[0]
                content_bytes = z.read(target)
    except zipfile.BadZipFile:
        pass

    # Clean XML content: remove namespaces for easy uniform traversal
    xml_str = content_bytes.decode('utf-8', errors='replace')
    # Strip default XML namespace attributes like xmlns="http://www.opengis.net/kml/2.2"
    cleaned_xml = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', xml_str, count=0)

    try:
        root = ET.fromstring(cleaned_xml)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML / KML format: {str(e)}")

    features = []
    point_count = 0
    polygon_count = 0
    linestring_count = 0
    other_geom_count = 0

    detected_borewells = 0
    detected_dugwells = 0

    all_lats = []
    all_lons = []

    # Find all Placemark elements
    placemarks = root.findall('.//Placemark')

    for idx, pm in enumerate(placemarks):
        name_el = pm.find('name')
        name = name_el.text.strip() if name_el is not None and name_el.text else f"Feature {idx + 1}"
        
        desc_el = pm.find('description')
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""

        # Check for hints in name or description
        combined_text = f"{name} {desc}".lower()
        is_bore_candidate = bool(re.search(r'\b(bore|bores|borewell|bore-well|tubewell|tube-well)\b', combined_text))
        is_dug_candidate = bool(re.search(r'\b(dug|dugwell|dug-well|openwell|open-well)\b', combined_text))

        if is_bore_candidate:
            detected_borewells += 1
        if is_dug_candidate:
            detected_dugwells += 1

        feature_geometries = []

        # 1. Point
        for pt in pm.findall('.//Point'):
            coords_el = pt.find('coordinates')
            if coords_el is not None and coords_el.text:
                coords = parse_coordinates_text(coords_el.text)
                if coords:
                    lon, lat = coords[0]
                    all_lons.append(lon)
                    all_lats.append(lat)
                    point_count += 1
                    feature_geometries.append({
                        "type": "Point",
                        "coordinates": [lon, lat]
                    })

        # 2. Polygon
        for poly in pm.findall('.//Polygon'):
            outer = poly.find('.//outerBoundaryIs//coordinates')
            if outer is not None and outer.text:
                coords = parse_coordinates_text(outer.text)
                if coords:
                    for lon, lat in coords:
                        all_lons.append(lon)
                        all_lats.append(lat)
                    polygon_count += 1
                    feature_geometries.append({
                        "type": "Polygon",
                        "coordinates": [coords]
                    })

        # 3. LineString
        for ls in pm.findall('.//LineString'):
            coords_el = ls.find('coordinates')
            if coords_el is not None and coords_el.text:
                coords = parse_coordinates_text(coords_el.text)
                if coords:
                    for lon, lat in coords:
                        all_lons.append(lon)
                        all_lats.append(lat)
                    linestring_count += 1
                    feature_geometries.append({
                        "type": "LineString",
                        "coordinates": coords
                    })

        # Build GeoJSON feature(s)
        for geom in feature_geometries:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": idx + 1,
                    "name": name,
                    "description": desc,
                    "geometry_type": geom["type"],
                    "candidate_type": "Borewell" if is_bore_candidate else ("Dugwell" if is_dug_candidate else "Unknown")
                },
                "geometry": geom
            })

    total_placemarks = len(placemarks)

    # Compute bounds and center
    bounds = None
    center = [23.0, 72.5]  # Default Gujarat / Central India view if empty
    if all_lats and all_lons:
        min_lat = min(all_lats)
        max_lat = max(all_lats)
        min_lon = min(all_lons)
        max_lon = max(all_lons)
        bounds = [min_lat, min_lon, max_lat, max_lon]
        center = [(min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0]

    geojson_collection = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_placemarks": total_placemarks,
            "point_count": point_count,
            "polygon_count": polygon_count,
            "linestring_count": linestring_count,
            "detected_borewells": detected_borewells,
            "detected_dugwells": detected_dugwells,
            "bounds": bounds,
            "center": center,
            "is_kmz": is_kmz
        }
    }

    return {
        "is_valid": True,
        "total_placemarks": total_placemarks,
        "point_count": point_count,
        "polygon_count": polygon_count,
        "linestring_count": linestring_count,
        "detected_borewells": detected_borewells,
        "detected_dugwells": detected_dugwells,
        "bounds": bounds,
        "center": center,
        "geojson": geojson_collection,
        "is_empty": (total_placemarks == 0 and point_count == 0 and polygon_count == 0)
    }


def save_kml_for_village(village_id, file_storage_or_bytes, original_filename, village_code=None):
    """
    Validate, parse, store on disk, and register KML file in SQL Server.
    Handles versioning: marks old files for this village as is_active=0.
    """
    Config.ensure_dirs()

    # Read bytes
    if hasattr(file_storage_or_bytes, 'read'):
        content_bytes = file_storage_or_bytes.read()
    else:
        content_bytes = file_storage_or_bytes

    if not content_bytes or len(content_bytes) < 10:
        raise ValueError("The uploaded KML file is empty or corrupted.")

    # Parse and validate
    parsed = parse_kml_content(content_bytes)
    if not parsed["is_valid"]:
        raise ValueError("Invalid KML / KMZ structure.")

    # Get village info if village_code not provided
    village = db.query_one("SELECT id, village_code, village_name, district_name FROM Villages WHERE id = ?", (village_id,))
    if not village:
        raise ValueError(f"Village with ID {village_id} not found.")

    v_code = village['village_code']
    safe_vcode = re.sub(r'[^a-zA-Z0-9_-]', '_', str(v_code))
    
    # Check existing version
    existing_kml = db.query_one("SELECT MAX(version) AS max_ver FROM KMLFiles WHERE village_id = ?", (village_id,))
    next_version = (existing_kml['max_ver'] or 0) + 1 if existing_kml else 1

    # Stored filename
    clean_orig_name = secure_filename(original_filename) or f"{safe_vcode}.kml"
    stored_filename = f"v_{village_id}_{safe_vcode}_v{next_version}_{clean_orig_name}"
    file_path = Config.KML_UPLOAD_DIR / stored_filename

    # Save to disk
    with open(file_path, 'wb') as f:
        f.write(content_bytes)

    file_size = len(content_bytes)
    geojson_str = json.dumps(parsed["geojson"])
    bounds_str = json.dumps(parsed["bounds"]) if parsed["bounds"] else None

    # Deactivate prior versions
    db.execute_non_query(
        "UPDATE KMLFiles SET is_active = 0 WHERE village_id = ?",
        (village_id,)
    )

    # Insert into KMLFiles table
    insert_sql = """
    INSERT INTO KMLFiles (
        village_id, village_code, original_filename, stored_filename, file_path,
        file_size, point_count, polygon_count, linestring_count, total_placemarks,
        geojson_data, bounds_json, version, is_active, validation_status, created_at
    )
    OUTPUT INSERTED.id
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'Valid', GETDATE())
    """
    kml_id = db.execute_scalar_insert(
        insert_sql,
        (
            village_id, v_code, original_filename, stored_filename, str(file_path),
            file_size, parsed["point_count"], parsed["polygon_count"], parsed["linestring_count"],
            parsed["total_placemarks"], geojson_str, bounds_str, next_version
        )
    )

    # Update village status to 'KML Downloaded' if it was Pending or In Progress
    current_status = db.query_one("SELECT kml_status, google_edited_nos, total_wells, bores FROM Villages WHERE id = ?", (village_id,))
    new_status = current_status['kml_status']
    if current_status['kml_status'] in ('Pending', 'Ready to Process', 'In Progress', 'Marking Completed'):
        new_status = 'KML Downloaded'
        db.execute_non_query(
            "UPDATE Villages SET kml_status = ?, updated_at = GETDATE() WHERE id = ?",
            (new_status, village_id)
        )
        # Log in history
        db.execute_non_query(
            "INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note) VALUES (?, ?, ?, ?)",
            (village_id, current_status['kml_status'], new_status, f"KML file '{original_filename}' uploaded (v{next_version}) with {parsed['point_count']} points")
        )

    return {
        "kml_id": kml_id,
        "village_id": village_id,
        "version": next_version,
        "stored_filename": stored_filename,
        "total_placemarks": parsed["total_placemarks"],
        "point_count": parsed["point_count"],
        "polygon_count": parsed["polygon_count"],
        "linestring_count": parsed["linestring_count"],
        "detected_borewells": parsed["detected_borewells"],
        "detected_dugwells": parsed["detected_dugwells"],
        "bounds": parsed["bounds"],
        "center": parsed["center"],
        "is_empty": parsed["is_empty"]
    }
