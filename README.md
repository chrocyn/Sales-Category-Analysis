# Sales by Category Analysis

This project analyzes sales performance across product categories to uncover revenue trends, profitability patterns, and category-level business insights. It is designed as a practical starter project for academic work, portfolio use, or internal business analysis.

## Project Objectives

- Analyze sales distribution across product categories
- Identify top-performing and underperforming categories
- Evaluate revenue, quantity sold, and profit contribution
- Discover monthly and seasonal sales trends
- Support data-driven business decisions with charts and summary outputs

## Project Structure

```text
sales_category_analysis/
|-- app.py
|-- data/
|   `-- sales_data.csv
|-- output/
|-- reports/
|   `-- project_report.md
|-- sql/
|   `-- category_analysis_queries.sql
|-- static/
|   |-- generated/
|   `-- styles.css
|-- src/
|   `-- analyze_sales.py
|-- templates/
|   |-- login.html
|   |-- home.html
|   |-- upload.html
|   |-- analysis.html
|   `-- visualizations.html
|-- uploads/
`-- requirements.txt
```

## Dataset Fields

The sample dataset includes:

- `Order Date`
- `Region`
- `Product Category`
- `Product Name`
- `Sales Amount`
- `Quantity Sold`
- `Profit`

## Tools and Technologies

- Python
- Flask
- Pandas
- Matplotlib
- Seaborn
- SQL

## How to Run

### Windows PowerShell

1. Open PowerShell in the project folder:

```powershell
cd "C:\Users\Ashwin Ezra\OneDrive\Desktop\sales_category_analysis"
```

2. Create a virtual environment if needed:

```powershell
python -m venv .venv
```

3. Install dependencies:

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

4. Start the web app:

```powershell
& ".\.venv\Scripts\python.exe" .\app.py
```

5. Open this address in your browser:

```text
http://127.0.0.1:5000
```

6. Login with the default demo credentials:

```text
username: admin
password: admin123
```

7. Upload your CSV file or use the sample dataset from the upload page.

## Script-Only Mode

If you only want to generate the CSV outputs and charts without using the webpage, run:

```powershell
& ".\.venv\Scripts\python.exe" .\src\analyze_sales.py
```

This writes the outputs into the `output\` folder.

### Generic Python Command

If you are not using the virtual environment, you can also run:

```bash
pip install -r requirements.txt
python app.py
```

## Expected Output

The web app provides five pages:

- Login page
- Home page
- Upload page
- Analysis page
- Visualization page

The analysis pipeline generates:

- Cleaned category summary table
- Monthly sales trend table
- Bar chart for sales by category
- Pie chart for revenue contribution
- Line chart for monthly category trends
- Text summary with key findings

## Business Value

This project helps teams:

- Focus on high-performing categories
- Detect weak categories early
- Improve inventory and pricing decisions
- Support targeted promotions and marketing

## Future Enhancements

- Predictive sales forecasting
- Interactive dashboard using Power BI or Tableau
- Customer segmentation analysis
- External market trend integration
