from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


def prepare_forecasting_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare data for time series forecasting."""
    # Get monthly totals by category
    monthly_category = (
        df.groupby(["Month", "Product Category"], as_index=False)["Sales Amount"]
        .sum()
        .sort_values(["Product Category", "Month"])
    )
    
    # Get overall monthly totals
    monthly_total = (
        df.groupby("Month", as_index=False)["Sales Amount"]
        .sum()
        .sort_values("Month")
    )
    
    return monthly_category, monthly_total


def forecast_sales(
    df: pd.DataFrame, months_ahead: int = 6
) -> dict[str, Any]:
    """
    Forecast future sales using linear regression with time-based features.
    """
    monthly_category, monthly_total = prepare_forecasting_data(df)
    
    # Prepare data for overall sales forecast
    X = np.arange(len(monthly_total)).reshape(-1, 1)
    y = monthly_total["Sales Amount"].values
    
    # Train model
    model = LinearRegression()
    model.fit(X, y)
    
    # Generate future predictions
    future_X = np.arange(len(monthly_total), len(monthly_total) + months_ahead).reshape(-1, 1)
    predictions = model.predict(future_X)
    
    # Create forecast dataframe
    last_month = pd.Period(monthly_total["Month"].iloc[-1], freq="M")
    future_months = [str(last_month + i) for i in range(1, months_ahead + 1)]
    
    forecast_df = pd.DataFrame({
        "Month": future_months,
        "Predicted_Sales": np.maximum(predictions, 0).round(2),  # Ensure non-negative
    })
    
    # Calculate metrics
    trend = "Upward" if model.coef_[0] > 0 else "Downward"
    trend_strength = abs(float(model.coef_[0]))
    average_historical = float(y.mean())
    average_predicted = float(predictions.mean())
    confidence = min(95, max(70, 100 - (abs(average_predicted - average_historical) / average_historical * 100)))
    
    # Category-wise forecast
    category_forecasts = {}
    for category in monthly_category["Product Category"].unique():
        cat_data = monthly_category[monthly_category["Product Category"] == category]
        if len(cat_data) >= 2:
            X_cat = np.arange(len(cat_data)).reshape(-1, 1)
            y_cat = cat_data["Sales Amount"].values
            
            model_cat = LinearRegression()
            model_cat.fit(X_cat, y_cat)
            
            future_X_cat = np.arange(len(cat_data), len(cat_data) + months_ahead).reshape(-1, 1)
            pred_cat = model_cat.predict(future_X_cat)
            
            category_forecasts[category] = {
                "predictions": np.maximum(pred_cat, 0).round(2).tolist(),
                "trend": "Upward" if model_cat.coef_[0] > 0 else "Downward",
                "growth_rate": float(model_cat.coef_[0] / y_cat.mean() * 100),
            }
    
    return {
        "forecast_months": future_months,
        "overall_forecast": forecast_df.to_dict("records"),
        "trend": trend,
        "trend_strength": round(trend_strength, 2),
        "average_historical_sales": round(average_historical, 2),
        "average_predicted_sales": round(average_predicted, 2),
        "confidence_score": round(confidence, 1),
        "category_forecasts": category_forecasts,
        "historical_data": {
            "months": monthly_total["Month"].tolist(),
            "sales": monthly_total["Sales Amount"].round(2).tolist(),
        },
    }


def generate_forecast_insights(forecast_result: dict[str, Any]) -> list[str]:
    """Generate business insights from forecast data."""
    insights = []
    
    # Overall trend
    trend = forecast_result["trend"]
    trend_strength = forecast_result["trend_strength"]
    insights.append(f"Overall Sales Trend: {trend}")
    insights.append(f"Trend strength: {trend_strength:.2f} units/month")
    
    # Sales projection
    avg_predicted = forecast_result["average_predicted_sales"]
    avg_historical = forecast_result["average_historical_sales"]
    change_pct = ((avg_predicted - avg_historical) / avg_historical * 100)
    insights.append(
        f"Predicted average monthly sales: ${avg_predicted:.2f} "
        f"({change_pct:+.1f}% vs historical average)"
    )
    
    # Confidence
    confidence = forecast_result["confidence_score"]
    insights.append(f"Forecast Confidence: {confidence:.1f}%")
    
    # Top growth categories
    category_forecasts = forecast_result["category_forecasts"]
    if category_forecasts:
        top_growth = max(
            category_forecasts.items(),
            key=lambda x: x[1]["growth_rate"]
        )
        if top_growth[1]["growth_rate"] > 0:
            insights.append(
                f"Strongest growth expected in {top_growth[0]}: "
                f"{top_growth[1]['growth_rate']:.1f}% monthly growth"
            )
        
        declining = [
            (cat, data["growth_rate"])
            for cat, data in category_forecasts.items()
            if data["growth_rate"] < -1
        ]
        if declining:
            worst = min(declining, key=lambda x: x[1])
            insights.append(
                f"Potential decline in {worst[0]}: "
                f"{worst[1]:.1f}% monthly decline"
            )
    
    # Recommendations
    insights.append("")
    insights.append("Recommendations:")
    if trend == "Downward":
        insights.append("- Implement promotional campaigns to reverse downward trend")
        insights.append("- Review pricing strategy and product positioning")
    else:
        insights.append("- Prepare inventory for increased demand")
        insights.append("- Plan marketing initiatives for growth categories")
    
    insights.append("- Monitor actual sales against predictions monthly")
    insights.append("- Adjust forecast models as new data becomes available")
    
    return insights
