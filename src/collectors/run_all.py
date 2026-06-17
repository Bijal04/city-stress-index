import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.collectors import (
    tomtom_collector,
    openaq_collector,
    weather_collector,
    numbeo_collector,
    safety_collector,
)
from src.etl_loader              import run_etl
from src.feature_engineering     import run_feature_engineering
from src.scoring_engine          import run_scoring_engine
from src.analytics.run_analytics import run_all_analytics
from src.data_quality            import run_data_quality_checks
from src.logger                  import get_logger

logger = get_logger("pipeline")

def run_all():
    logger.info("=" * 55)
    logger.info("CITY STRESS INDEX — Daily Pipeline Run")
    logger.info(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    logger.info("=" * 55)

    collectors = [
        ("Traffic",     tomtom_collector),
        ("Air Quality", openaq_collector),
        ("Weather",     weather_collector),
        ("Cost",        numbeo_collector),
        ("Safety",      safety_collector),
    ]

    failed = []
    for name, collector in collectors:
        logger.info(f"Running {name} collector...")
        try:
            collector.run()
            logger.info(f"{name} collector done.")
        except Exception as e:
            logger.error(f"{name} collector FAILED: {e}")
            failed.append(name)

    logger.info("Running ETL...")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    run_etl(date_str=today)

    logger.info("Running feature engineering...")
    run_feature_engineering()

    logger.info("Running scoring engine...")
    run_scoring_engine()

    logger.info("Running analytics suite...")
    run_all_analytics()

    logger.info("Running data quality checks...")
    run_data_quality_checks()

    logger.info("=" * 55)
    if failed:
        logger.warning(f"Pipeline completed with failures: {', '.join(failed)}")
    else:
        logger.info("Full pipeline complete. All steps succeeded.")
    logger.info("=" * 55)

if __name__ == "__main__":
    run_all()