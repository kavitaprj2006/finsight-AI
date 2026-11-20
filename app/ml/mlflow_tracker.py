"""
FinSight AI - MLflow Experiment Tracking & Registry Integration
"""
from typing import Dict, Any, Optional
import os
from datetime import datetime, timezone
from app.config import settings
from app.core.logger import logger
from app.database.repository import Repository

class MLflowTracker:
    def __init__(self):
        self.tracking_uri = settings.MLFLOW_TRACKING_URI
        self.is_mlflow_available = False
        self._init_mlflow()

    def _init_mlflow(self):
        try:
            import mlflow
            mlflow.set_tracking_uri(self.tracking_uri)
            self.is_mlflow_available = True
            logger.info(f"MLflow initialized with tracking URI: {self.tracking_uri}")
        except Exception as e:
            logger.warning(f"MLflow not available or failed initialization: {e}. Using DB-backed experiment tracker.")
            self.is_mlflow_available = False

    def log_run(
        self,
        experiment_name: str,
        model_name: str,
        task_type: str,
        market: str,
        symbol: str,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        version: str = "v1.0"
    ) -> str:
        """
        Logs parameters, metrics, and metadata to MLflow and local database.
        Returns a run_id string.
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{model_name.replace(' ', '_').lower()}"
        artifact_uri = f"{self.tracking_uri}/{experiment_name}/{run_id}"

        # 1. Log to MLflow if available
        if self.is_mlflow_available:
            try:
                import mlflow
                mlflow.set_experiment(experiment_name)
                with mlflow.start_run(run_name=f"{model_name}_{symbol}") as run:
                    run_id = run.info.run_id
                    mlflow.log_params(params)
                    mlflow.log_metrics(metrics)
                    mlflow.set_tags({
                        "task_type": task_type,
                        "market": market,
                        "symbol": symbol,
                        "version": version
                    })
                    artifact_uri = run.info.artifact_uri
            except Exception as e:
                logger.warning(f"Error logging to MLflow directly: {e}")

        # 2. Persist to Relational Database for reliable UI presentation
        try:
            Repository.record_ml_experiment(
                experiment_name=experiment_name,
                run_id=run_id,
                model_name=model_name,
                task_type=task_type,
                market=market,
                symbol=symbol,
                parameters=params,
                metrics=metrics,
                artifact_uri=artifact_uri
            )
        except Exception as e:
            logger.warning(f"Error saving experiment metadata to database: {e}")

        return run_id

mlflow_tracker = MLflowTracker()
