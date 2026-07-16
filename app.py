import os
import secrets
from functools import wraps
from pathlib import Path

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.utils import secure_filename

from src.analyze_sales import DATA_FILE, REQUIRED_COLUMNS, analyze_sales_file
from src.predict_sales import forecast_sales, generate_forecast_insights


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "static" / "generated"
ALLOWED_EXTENSIONS = {".csv"}
APP_USERNAME = os.environ.get("APP_USERNAME", "admin")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "admin123")


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(16))
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# Configure server-side sessions to avoid cookie size limit
SESSION_DIR = Path(__file__).resolve().parent / "flask_sessions"
SESSION_DIR.mkdir(exist_ok=True)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_FILE_DIR"] = str(SESSION_DIR)
Session(app)


def ensure_directories() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def is_logged_in() -> bool:
    return bool(session.get("user"))


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def normalize_value(value):
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def serialize_frame(df, limit: int = 12) -> list[dict]:
    rows = df.head(limit).to_dict(orient="records")
    return [
        {key: normalize_value(value) for key, value in row.items()}
        for row in rows
    ]


def serialize_analysis(result: dict, dataset_label: str, source_name: str) -> dict:
    # Convert DataFrame to records for serialization with proper normalization
    clean_data = result.get("clean_data")
    if clean_data is not None:
        clean_data_records = clean_data.to_dict(orient="records")
        clean_data_records = [
            {key: normalize_value(value) for key, value in row.items()}
            for row in clean_data_records
        ]
    else:
        clean_data_records = []
    
    return {
        "dataset_label": dataset_label,
        "source_name": source_name,
        "overview": result["overview"],
        "findings": result["findings"],
        "required_columns": sorted(REQUIRED_COLUMNS),
        "category_rows": serialize_frame(result["category_summary"]),
        "monthly_rows": serialize_frame(result["monthly_summary"]),
        "region_rows": serialize_frame(result["region_summary"]),
        "charts": result["charts"],
        "chart_version": secrets.token_hex(4),
        "clean_data": clean_data_records,
    }


def run_analysis(file_path: Path, dataset_label: str, source_name: str) -> None:
    result = analyze_sales_file(file_path, output_dir=GENERATED_DIR)
    session["analysis"] = serialize_analysis(result, dataset_label, source_name)


@app.route("/")
@login_required
def home():
    analysis = session.get("analysis")
    return render_template("home.html", analysis=analysis)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == APP_USERNAME and password == APP_PASSWORD:
            session.clear()
            session["user"] = username
            flash("Login successful. You can upload a dataset and start analyzing.", "success")
            return redirect(url_for("home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html", demo_username=APP_USERNAME, demo_password=APP_PASSWORD)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        action = request.form.get("action")
        print(f"\n{'='*50}")
        print(f"DEBUG: Upload POST received - action: {action}")
        print(f"DEBUG: request.files keys: {list(request.files.keys())}")
        print(f"DEBUG: request.form keys: {list(request.form.keys())}")

        if action == "sample":
            try:
                print(f"DEBUG: Loading sample data from {DATA_FILE}")
                if not DATA_FILE.exists():
                    raise FileNotFoundError(f"Sample data file not found: {DATA_FILE}")
                run_analysis(DATA_FILE, "Sample dataset", DATA_FILE.name)
                print(f"DEBUG: Sample analysis completed successfully")
                flash("Sample dataset loaded and analyzed successfully.", "success")
                return redirect(url_for("analysis"))
            except Exception as exc:
                print(f"DEBUG: Sample analysis error: {exc}")
                import traceback
                print(traceback.format_exc())
                flash(f"Sample dataset analysis failed: {str(exc)}", "error")
                return redirect(url_for("upload"))

        # Check if file is in request
        if "sales_file" not in request.files:
            print("DEBUG: No sales_file in request.files")
            flash("No file part in the request. Please select a file.", "error")
            return redirect(url_for("upload"))

        file = request.files.get("sales_file")
        print(f"DEBUG: File object: {file}, filename: {file.filename if file else None}")
        
        if file is None or file.filename == "":
            print("DEBUG: File is None or empty filename")
            flash("Please choose a CSV file to upload.", "error")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            print(f"DEBUG: File extension not allowed: {file.filename}")
            flash("Only CSV files are supported for analysis.", "error")
            return redirect(url_for("upload"))

        try:
            ensure_directories()
            filename = secure_filename(file.filename)
            print(f"DEBUG: Original filename: {file.filename}, secure filename: {filename}")
            if not filename:
                flash("Invalid filename. Please use a valid CSV filename.", "error")
                return redirect(url_for("upload"))
            
            saved_path = UPLOAD_DIR / filename
            print(f"DEBUG: Saving file to {saved_path}")
            file.save(saved_path)
            
            # Verify file was saved
            if not saved_path.exists():
                print(f"DEBUG: File not found after save at {saved_path}")
                flash("File could not be saved. Please try again.", "error")
                return redirect(url_for("upload"))
            
            file_size = saved_path.stat().st_size
            print(f"DEBUG: File saved successfully, file size: {file_size} bytes")
            
            # Read and validate the CSV
            print(f"DEBUG: Reading and validating CSV file...")
            try:
                import pandas as pd
                df = pd.read_csv(saved_path)
                print(f"DEBUG: CSV loaded - Shape: {df.shape}, Columns: {list(df.columns)}")
                
                # Check required columns
                missing_cols = REQUIRED_COLUMNS - set(df.columns)
                if missing_cols:
                    print(f"DEBUG: Missing required columns: {missing_cols}")
                    flash(f"CSV file is missing required columns: {', '.join(missing_cols)}", "error")
                    return redirect(url_for("upload"))
                
                print(f"DEBUG: All required columns present")
            except Exception as e:
                print(f"DEBUG: Error reading CSV: {e}")
                flash(f"Error reading CSV file: {e}", "error")
                return redirect(url_for("upload"))
            
            # Run analysis
            print(f"DEBUG: Running analysis on {saved_path}")
            run_analysis(saved_path, "Uploaded dataset", filename)
            print("DEBUG: Analysis completed successfully")
            flash("File uploaded and analyzed successfully.", "success")
            return redirect(url_for("analysis"))
            
        except Exception as exc:
            import traceback
            error_msg = str(exc)
            print(f"DEBUG: Upload error: {error_msg}")
            print(traceback.format_exc())
            flash(f"Analysis failed: {error_msg}", "error")
            return redirect(url_for("upload"))

    analysis = session.get("analysis")
    return render_template("upload.html", analysis=analysis)


@app.route("/analysis")
@login_required
def analysis():
    analysis_data = session.get("analysis")
    if analysis_data is None:
        flash("Upload a CSV file or use the sample dataset before opening the analysis page.", "info")
        return redirect(url_for("upload"))
    return render_template("analysis.html", analysis=analysis_data)


@app.route("/visualizations")
@login_required
def visualizations():
    analysis_data = session.get("analysis")
    if analysis_data is None:
        flash("Upload a CSV file or use the sample dataset before opening the visualization page.", "info")
        return redirect(url_for("upload"))
    return render_template("visualizations.html", analysis=analysis_data)


@app.route("/predict")
@login_required
def predict():
    analysis_data = session.get("analysis")
    if analysis_data is None:
        flash("Upload a CSV file or use the sample dataset before opening the predictions page.", "info")
        return redirect(url_for("upload"))
    
    try:
        clean_data_records = analysis_data.get("clean_data", [])
        if not clean_data_records:
            flash("Prediction data unavailable. Please re-upload or reload the dataset.", "error")
            return redirect(url_for("upload"))
        
        # Reconstruct DataFrame from records
        clean_data = pd.DataFrame(clean_data_records)
        
        # Ensure date column is datetime
        if "Order Date" in clean_data.columns:
            clean_data["Order Date"] = pd.to_datetime(clean_data["Order Date"], errors="coerce")
        
        # Generate forecast
        forecast_result = forecast_sales(clean_data, months_ahead=6)
        insights = generate_forecast_insights(forecast_result)
        
        session["forecast"] = {
            "forecast_months": forecast_result["forecast_months"],
            "overall_forecast": forecast_result["overall_forecast"],
            "trend": forecast_result["trend"],
            "trend_strength": forecast_result["trend_strength"],
            "average_historical_sales": forecast_result["average_historical_sales"],
            "average_predicted_sales": forecast_result["average_predicted_sales"],
            "confidence_score": forecast_result["confidence_score"],
            "category_forecasts": forecast_result["category_forecasts"],
            "historical_data": forecast_result["historical_data"],
            "insights": insights,
        }
    except Exception as exc:
        flash(f"Prediction generation failed: {exc}", "error")
        return redirect(url_for("analysis"))
    
    return render_template("predict.html", analysis=analysis_data, forecast=session.get("forecast"))


if __name__ == "__main__":
    ensure_directories()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)