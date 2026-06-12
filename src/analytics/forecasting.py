import os
import sys
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import get_connection

def load_city_scores(city_name: str) -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT s.date_id, s.total_stress_score
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        WHERE c.name = ?
          AND s.total_stress_score IS NOT NULL
        ORDER BY s.date_id
    """, conn, params=(city_name,))
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def get_city_id(city_name: str) -> int:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT city_id FROM dim_city WHERE name = ?", (city_name,))
    row = cur.fetchone()
    conn.close()
    return row["city_id"] if row else None

def run_arima_forecast(df: pd.DataFrame, steps: int = 30) -> pd.DataFrame:
    from statsmodels.tsa.arima.model import ARIMA

    series = df.set_index("date_id")["total_stress_score"]
    model  = ARIMA(series, order=(2, 1, 2))
    fitted = model.fit()
    forecast = fitted.get_forecast(steps=steps)
    mean     = forecast.predicted_mean
    ci       = forecast.conf_int()

    future_dates = pd.date_range(
        start=series.index[-1] + timedelta(days=1),
        periods=steps,
        freq="D"
    )

    result = pd.DataFrame({
        "forecast_date":   future_dates,
        "predicted_score": mean.values.clip(0, 100).round(2),
        "lower_bound":     ci.iloc[:, 0].values.clip(0, 100).round(2),
        "upper_bound":     ci.iloc[:, 1].values.clip(0, 100).round(2),
        "model":           "ARIMA",
    })

    return result

def run_prophet_forecast(df: pd.DataFrame, steps: int = 30) -> pd.DataFrame:
    from prophet import Prophet

    prophet_df = df.rename(columns={"date_id": "ds", "total_stress_score": "y"})
    model      = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.95,
        changepoint_prior_scale=0.05,
    )
    model.fit(prophet_df)

    future   = model.make_future_dataframe(periods=steps)
    forecast = model.predict(future)

    forecast_only = forecast.tail(steps)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    result = pd.DataFrame({
        "forecast_date":   forecast_only["ds"].values,
        "predicted_score": forecast_only["yhat"].clip(0, 100).round(2).values,
        "lower_bound":     forecast_only["yhat_lower"].clip(0, 100).round(2).values,
        "upper_bound":     forecast_only["yhat_upper"].clip(0, 100).round(2).values,
        "model":           "Prophet",
    })

    return result

def save_forecasts(city_id: int, forecasts_df: pd.DataFrame):
    conn   = get_connection()
    cursor = conn.cursor()
    saved  = 0

    for _, row in forecasts_df.iterrows():
        date_str = pd.Timestamp(row["forecast_date"]).strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO city_forecasts
                (city_id, forecast_date, model, predicted_score, lower_bound, upper_bound)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(city_id, forecast_date, model) DO UPDATE SET
                predicted_score = excluded.predicted_score,
                lower_bound     = excluded.lower_bound,
                upper_bound     = excluded.upper_bound
        """, (
            city_id,
            date_str,
            row["model"],
            float(row["predicted_score"]),
            float(row["lower_bound"]),
            float(row["upper_bound"]),
        ))
        saved += 1

    conn.commit()
    conn.close()
    return saved

def run_forecasting(steps: int = 30):
    print("=" * 55)
    print("Analytics — Forecasting (ARIMA + Prophet)")
    print("=" * 55)

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT name FROM dim_city ORDER BY name")
    cities = [r["name"] for r in cur.fetchall()]
    conn.close()

    total_saved = 0

    for city_name in cities:
        print(f"\n  {city_name}...")
        city_id = get_city_id(city_name)
        df      = load_city_scores(city_name)

        if len(df) < 60:
            print(f"    Not enough data (need 60+ days, got {len(df)}). Skipping.")
            continue

        all_forecasts = []

        try:
            arima_fc = run_arima_forecast(df, steps)
            all_forecasts.append(arima_fc)
            print(f"    ARIMA: {steps} days forecast done. "
                  f"Next 7d avg: {arima_fc['predicted_score'].head(7).mean():.1f}")
        except Exception as e:
            print(f"    ARIMA failed: {e}")

        try:
            prophet_fc = run_prophet_forecast(df, steps)
            all_forecasts.append(prophet_fc)
            print(f"    Prophet: {steps} days forecast done. "
                  f"Next 7d avg: {prophet_fc['predicted_score'].head(7).mean():.1f}")
        except Exception as e:
            print(f"    Prophet failed: {e}")

        if all_forecasts:
            combined = pd.concat(all_forecasts, ignore_index=True)
            saved    = save_forecasts(city_id, combined)
            total_saved += saved

    print(f"\nForecasting complete. {total_saved} forecast rows saved.")

if __name__ == "__main__":
    run_forecasting()