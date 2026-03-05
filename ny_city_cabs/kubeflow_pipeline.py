#!/usr/bin/env python3
"""
Kubeflow Pipeline for NYC Taxi Data ETL

This pipeline orchestrates the end-to-end ETL process for NYC taxi data:
1. Fetch data from S3
2. Transform and clean the data
3. Analyze and generate visualizations
4. Upload results back to S3

To compile: python kubeflow_pipeline.py
To upload: Use Kubeflow Pipelines UI or kfp.Client()
"""

import kfp
from kfp import dsl
from kfp.components import create_component_from_func
from typing import NamedTuple


def fetch_from_s3_op(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_region: str,
    aws_s3_endpoint: str,
    s3_bucket: str,
    raw_prefix: str = "raw_data/",
    input_key: str = "",
) -> dsl.ContainerOp:
    """Fetch NYC taxi data from S3."""
    return dsl.ContainerOp(
        name="Fetch from S3",
        image="quay.io/elyra/elyra:3.15.0-py3.10",
        command=["papermill"],
        arguments=[
            "1_fetch_from_s3.ipynb",
            "1_fetch_from_s3_output.ipynb",
        ],
        file_outputs={
            "raw_csv": "/raw/raw.csv",
            "manifest": "/raw/manifest.json",
        },
        pvolumes={"/workspace": dsl.PipelineVolume(pvc="pipeline-workspace")},
    ).set_env_variable("AWS_ACCESS_KEY_ID", aws_access_key_id) \
     .set_env_variable("AWS_SECRET_ACCESS_KEY", aws_secret_access_key) \
     .set_env_variable("AWS_DEFAULT_REGION", aws_region) \
     .set_env_variable("AWS_S3_ENDPOINT", aws_s3_endpoint) \
     .set_env_variable("AWS_S3_BUCKET", s3_bucket) \
     .set_env_variable("TAXI_RAW_PREFIX", raw_prefix) \
     .set_env_variable("TAXI_INPUT_KEY", input_key)


def etl_transform_op(
    min_duration: float = 1.0,
    max_duration: float = 180.0,
    min_distance: float = 0.1,
    max_distance: float = 50.0,
    min_total: float = 2.0,
    max_total: float = 500.0,
    max_passengers: int = 8,
) -> dsl.ContainerOp:
    """Transform and clean NYC taxi data."""
    return dsl.ContainerOp(
        name="ETL Transform",
        image="quay.io/elyra/elyra:3.15.0-py3.10",
        command=["papermill"],
        arguments=[
            "2_etl_transform.ipynb",
            "2_etl_transform_output.ipynb",
        ],
        file_outputs={
            "clean_csv": "/processed/trips_clean.csv",
            "aggregates": "/processed/aggregates_by_hour.csv",
            "quality_report": "/processed/data_quality_report.json",
        },
        pvolumes={"/workspace": dsl.PipelineVolume(pvc="pipeline-workspace")},
    ).set_env_variable("TAXI_RAW_IN", "raw/raw.csv") \
     .set_env_variable("TAXI_PROCESSED_DIR", "processed") \
     .set_env_variable("TAXI_MIN_DURATION_MIN", str(min_duration)) \
     .set_env_variable("TAXI_MAX_DURATION_MIN", str(max_duration)) \
     .set_env_variable("TAXI_MIN_DISTANCE_MI", str(min_distance)) \
     .set_env_variable("TAXI_MAX_DISTANCE_MI", str(max_distance)) \
     .set_env_variable("TAXI_MIN_TOTAL_AMOUNT", str(min_total)) \
     .set_env_variable("TAXI_MAX_TOTAL_AMOUNT", str(max_total)) \
     .set_env_variable("TAXI_MAX_PASSENGERS", str(max_passengers))


def analyze_and_plot_op(
    max_plot_distance: float = 15.0,
    max_plot_duration: float = 60.0,
    max_cost_per_mile: float = 20.0,
    max_fare: float = 100.0,
    max_tip: float = 20.0,
) -> dsl.ContainerOp:
    """Analyze data and generate visualizations."""
    return dsl.ContainerOp(
        name="Analyze and Plot",
        image="quay.io/elyra/elyra:3.15.0-py3.10",
        command=["papermill"],
        arguments=[
            "3_analyze_and_plot.ipynb",
            "3_analyze_and_plot_output.ipynb",
        ],
        file_outputs={
            "metrics": "/metrics/metrics.json",
        },
        pvolumes={"/workspace": dsl.PipelineVolume(pvc="pipeline-workspace")},
    ).set_env_variable("TAXI_PROCESSED_DIR", "processed") \
     .set_env_variable("TAXI_PLOTS_DIR", "plots") \
     .set_env_variable("TAXI_METRICS_DIR", "metrics") \
     .set_env_variable("TAXI_PLOT_MAX_DISTANCE", str(max_plot_distance)) \
     .set_env_variable("TAXI_PLOT_MAX_DURATION", str(max_plot_duration)) \
     .set_env_variable("TAXI_PLOT_MAX_COST_PER_MILE", str(max_cost_per_mile)) \
     .set_env_variable("TAXI_PLOT_MAX_FARE", str(max_fare)) \
     .set_env_variable("TAXI_PLOT_MAX_TIP", str(max_tip))


def upload_results_op(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_region: str,
    aws_s3_endpoint: str,
    s3_bucket: str,
    run_prefix: str = "results/nyc-taxi-etl",
    append_elyra_run: str = "true",
) -> dsl.ContainerOp:
    """Upload results to S3."""
    return dsl.ContainerOp(
        name="Upload Results",
        image="quay.io/elyra/elyra:3.15.0-py3.10",
        command=["papermill"],
        arguments=[
            "4_upload_results.ipynb",
            "4_upload_results_output.ipynb",
        ],
        pvolumes={"/workspace": dsl.PipelineVolume(pvc="pipeline-workspace")},
    ).set_env_variable("AWS_ACCESS_KEY_ID", aws_access_key_id) \
     .set_env_variable("AWS_SECRET_ACCESS_KEY", aws_secret_access_key) \
     .set_env_variable("AWS_DEFAULT_REGION", aws_region) \
     .set_env_variable("AWS_S3_ENDPOINT", aws_s3_endpoint) \
     .set_env_variable("AWS_S3_BUCKET", s3_bucket) \
     .set_env_variable("TAXI_RUN_PREFIX", run_prefix) \
     .set_env_variable("TAXI_APPEND_ELYRA_RUN", append_elyra_run)


@dsl.pipeline(
    name="NYC Taxi Data ETL Pipeline",
    description="End-to-end pipeline for processing NYC taxi trip data: fetch, transform, analyze, and upload results."
)
def nyc_taxi_pipeline(
    # S3 Connection Parameters
    aws_access_key_id: str = "",
    aws_secret_access_key: str = "",
    aws_region: str = "us-east-1",
    aws_s3_endpoint: str = "",
    s3_bucket: str = "",

    # Input/Output Paths
    raw_prefix: str = "raw_data/",
    input_key: str = "",
    run_prefix: str = "results/nyc-taxi-etl",

    # Data Filtering Parameters
    min_duration: float = 1.0,
    max_duration: float = 180.0,
    min_distance: float = 0.1,
    max_distance: float = 50.0,
    min_total: float = 2.0,
    max_total: float = 500.0,
    max_passengers: int = 8,

    # Plotting Parameters
    max_plot_distance: float = 15.0,
    max_plot_duration: float = 60.0,
    max_cost_per_mile: float = 20.0,
    max_fare: float = 100.0,
    max_tip: float = 20.0,
):
    """
    NYC Taxi Data ETL Pipeline

    This pipeline processes NYC taxi trip data through four stages:

    1. **Fetch from S3**: Download raw taxi data from S3-compatible storage
    2. **ETL Transform**: Clean, filter, and aggregate the data
    3. **Analyze and Plot**: Generate metrics and visualizations
    4. **Upload Results**: Upload processed data and plots back to S3

    Args:
        aws_access_key_id: AWS access key ID for S3 authentication
        aws_secret_access_key: AWS secret access key for S3 authentication
        aws_region: AWS region (default: us-east-1)
        aws_s3_endpoint: S3 endpoint URL
        s3_bucket: S3 bucket name
        raw_prefix: S3 prefix for raw input data (default: raw_data/)
        input_key: Specific S3 key for input CSV (optional)
        run_prefix: S3 prefix for output results (default: results/nyc-taxi-etl)
        min_duration: Minimum trip duration in minutes (default: 1.0)
        max_duration: Maximum trip duration in minutes (default: 180.0)
        min_distance: Minimum trip distance in miles (default: 0.1)
        max_distance: Maximum trip distance in miles (default: 50.0)
        min_total: Minimum total amount in dollars (default: 2.0)
        max_total: Maximum total amount in dollars (default: 500.0)
        max_passengers: Maximum passenger count (default: 8)
        max_plot_distance: Maximum distance for plots (default: 15.0)
        max_plot_duration: Maximum duration for plots (default: 60.0)
        max_cost_per_mile: Maximum cost per mile for plots (default: 20.0)
        max_fare: Maximum fare for plots (default: 100.0)
        max_tip: Maximum tip for plots (default: 20.0)
    """

    # Step 1: Fetch data from S3
    fetch_task = fetch_from_s3_op(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
        aws_s3_endpoint=aws_s3_endpoint,
        s3_bucket=s3_bucket,
        raw_prefix=raw_prefix,
        input_key=input_key,
    )

    # Step 2: Transform and clean data (depends on fetch)
    transform_task = etl_transform_op(
        min_duration=min_duration,
        max_duration=max_duration,
        min_distance=min_distance,
        max_distance=max_distance,
        min_total=min_total,
        max_total=max_total,
        max_passengers=max_passengers,
    )
    transform_task.after(fetch_task)

    # Step 3: Analyze and generate plots (depends on transform)
    analyze_task = analyze_and_plot_op(
        max_plot_distance=max_plot_distance,
        max_plot_duration=max_plot_duration,
        max_cost_per_mile=max_cost_per_mile,
        max_fare=max_fare,
        max_tip=max_tip,
    )
    analyze_task.after(transform_task)

    # Step 4: Upload results to S3 (depends on analyze)
    upload_task = upload_results_op(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
        aws_s3_endpoint=aws_s3_endpoint,
        s3_bucket=s3_bucket,
        run_prefix=run_prefix,
        append_elyra_run="true",
    )
    upload_task.after(analyze_task)


if __name__ == "__main__":
    # Compile the pipeline to a YAML file
    import kfp.compiler as compiler

    pipeline_filename = "nyc_taxi_pipeline.yaml"
    compiler.Compiler().compile(nyc_taxi_pipeline, pipeline_filename)
    print(f"Pipeline compiled successfully: {pipeline_filename}")
    print("\nTo upload this pipeline to Kubeflow:")
    print("1. Open Kubeflow Pipelines UI")
    print("2. Click 'Upload pipeline'")
    print(f"3. Select the file: {pipeline_filename}")
    print("\nOr use the Python SDK:")
    print("```python")
    print("import kfp")
    print("client = kfp.Client(host='<your-kubeflow-host>')")
    print(f"client.upload_pipeline(pipeline_package_path='{pipeline_filename}',")
    print("                       pipeline_name='NYC Taxi ETL Pipeline')")
    print("```")
