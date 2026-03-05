# NYC Taxi Data Pipeline

This project contains two pipeline implementations for processing NYC taxi trip data:

1. **Elyra Pipeline** - Visual pipeline for JupyterLab/Elyra
2. **Kubeflow Pipeline** - Python-based pipeline for Kubeflow Pipelines

## Pipeline Architecture

The pipeline consists of four sequential stages:

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Fetch from S3  │ --> │ ETL Transform│ --> │ Analyze and Plot │ --> │ Upload Results  │
└─────────────────┘     └──────────────┘     └──────────────────┘     └─────────────────┘
```

### Stage Details

1. **Fetch from S3** (`1_fetch_from_s3.ipynb`)
   - Downloads raw CSV data from S3-compatible storage
   - Creates manifest file for tracking
   - **Outputs**: `raw/raw.csv`, `raw/manifest.json`

2. **ETL Transform** (`2_etl_transform.ipynb`)
   - Cleans and validates data
   - Derives new features (trip_duration_min, cost_per_mile)
   - Filters outliers and invalid records
   - Aggregates data by hour
   - **Outputs**: `processed/trips_clean.csv`, `processed/aggregates_by_hour.csv`, `processed/data_quality_report.json`

3. **Analyze and Plot** (`3_analyze_and_plot.ipynb`)
   - Computes summary metrics
   - Generates 10 visualization plots (ggplot2-styled)
   - **Outputs**: `metrics/metrics.json`, `plots/*.png`

4. **Upload Results** (`4_upload_results.ipynb`)
   - Uploads processed data, plots, and metrics to S3
   - Creates timestamped run folders
   - **Location**: `s3://bucket/results/nyc-taxi-etl/run_YYYY-MM-DD_HH-MM/`

---

## 1. Elyra Pipeline

### Prerequisites

- JupyterLab with Elyra extension installed
- Kubeflow Pipelines or Apache Airflow runtime configured in Elyra
- S3-compatible storage with credentials

### Installation

```bash
# Install JupyterLab and Elyra
pip install jupyterlab elyra

# Install Elyra pipeline editor extension
jupyter lab build
```

### Usage

1. **Open the Pipeline in JupyterLab**:
   ```bash
   jupyter lab
   # Navigate to nyc_taxi_pipeline.pipeline
   ```

2. **Configure Runtime**:
   - In JupyterLab, go to Settings → Elyra → Runtime Images/Runtimes
   - Add your Kubeflow or Airflow runtime configuration

3. **Set Environment Variables**:
   - Right-click each node to edit properties
   - Update the environment variables with your S3 credentials:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_S3_ENDPOINT`
     - `AWS_S3_BUCKET`

4. **Run the Pipeline**:
   - Click the "Run Pipeline" button (play icon)
   - Select your runtime
   - Monitor execution in Kubeflow/Airflow UI

### Pipeline Features

- **Visual Editor**: Drag-and-drop interface for pipeline design
- **Dependency Management**: Automatic handling of file dependencies
- **Environment Variables**: Configurable per-node settings
- **Output Tracking**: Specified outputs are automatically passed between nodes
- **Runtime Agnostic**: Works with Kubeflow Pipelines or Apache Airflow

---

## 2. Kubeflow Pipeline

### Prerequisites

- Kubeflow Pipelines installed on Kubernetes cluster
- `kfp` Python SDK installed
- S3-compatible storage with credentials

### Installation

```bash
# Install Kubeflow Pipelines SDK
pip install -r pipeline_requirements.txt
```

### Compile the Pipeline

```bash
# Compile the pipeline to YAML
python kubeflow_pipeline.py
```

This generates `nyc_taxi_pipeline.yaml`.

### Upload to Kubeflow

**Option 1: Using the UI**

1. Open Kubeflow Pipelines UI
2. Click "Upload pipeline"
3. Select `nyc_taxi_pipeline.yaml`
4. Click "Create"

**Option 2: Using Python SDK**

```python
import kfp

# Connect to Kubeflow
client = kfp.Client(host='<your-kubeflow-host>')

# Upload pipeline
pipeline_id = client.upload_pipeline(
    pipeline_package_path='nyc_taxi_pipeline.yaml',
    pipeline_name='NYC Taxi ETL Pipeline'
)

# Create and run experiment
experiment = client.create_experiment(name='NYC Taxi Analysis')

run = client.run_pipeline(
    experiment_id=experiment.id,
    job_name='nyc-taxi-run-001',
    pipeline_id=pipeline_id,
    params={
        'aws_access_key_id': 'YOUR_ACCESS_KEY',
        'aws_secret_access_key': 'YOUR_SECRET_KEY',
        's3_bucket': 'your-bucket-name',
        'aws_s3_endpoint': 'https://s3.amazonaws.com',
        'aws_region': 'us-east-1',
    }
)
```

### Pipeline Parameters

The Kubeflow pipeline accepts the following parameters:

#### S3 Connection
- `aws_access_key_id`: AWS access key
- `aws_secret_access_key`: AWS secret key
- `aws_region`: AWS region (default: `us-east-1`)
- `aws_s3_endpoint`: S3 endpoint URL
- `s3_bucket`: S3 bucket name

#### Paths
- `raw_prefix`: S3 prefix for input data (default: `raw_data/`)
- `input_key`: Specific input file key (optional)
- `run_prefix`: S3 prefix for outputs (default: `results/nyc-taxi-etl`)

#### Data Filtering
- `min_duration`: Min trip duration in minutes (default: `1.0`)
- `max_duration`: Max trip duration in minutes (default: `180.0`)
- `min_distance`: Min trip distance in miles (default: `0.1`)
- `max_distance`: Max trip distance in miles (default: `50.0`)
- `min_total`: Min total fare (default: `2.0`)
- `max_total`: Max total fare (default: `500.0`)
- `max_passengers`: Max passenger count (default: `8`)

#### Plotting
- `max_plot_distance`: Max distance for plots (default: `15.0`)
- `max_plot_duration`: Max duration for plots (default: `60.0`)
- `max_cost_per_mile`: Max cost/mile for plots (default: `20.0`)
- `max_fare`: Max fare for plots (default: `100.0`)
- `max_tip`: Max tip for plots (default: `20.0`)

---

## Storage Requirements

### Persistent Volume

Both pipelines require a persistent volume for sharing data between steps:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-workspace
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
```

Apply with:
```bash
kubectl apply -f pvc.yaml -n kubeflow
```

---

## Monitoring and Troubleshooting

### View Pipeline Runs

**Elyra**:
- Check Kubeflow Pipelines UI for run status
- View notebook outputs in the run details
- Check pod logs for debugging

**Kubeflow**:
- Navigate to "Runs" in Kubeflow UI
- Click on run name to see DAG and step status
- View logs for each step by clicking on the node

### Common Issues

1. **S3 Connection Failed**
   - Verify credentials are correct
   - Check endpoint URL format (include `http://` or `https://`)
   - Ensure network connectivity to S3

2. **No CSV Found**
   - Verify `raw_prefix` matches your S3 structure
   - Check bucket permissions
   - Ensure CSV files exist in the specified location

3. **Memory Issues**
   - Increase pod memory limits in pipeline definition
   - Sample large datasets before processing
   - Adjust filtering parameters to reduce data volume

4. **Missing Dependencies**
   - Ensure runtime image has all required packages
   - Update `runtime_image` to custom image if needed
   - Check pip install commands in notebooks run successfully

---

## Output Structure

After successful execution, results are uploaded to S3:

```
s3://bucket/results/nyc-taxi-etl/run_2026-03-05_14-30/
├── processed/
│   ├── trips_clean.csv
│   ├── aggregates_by_hour.csv
│   └── data_quality_report.json
├── plots/
│   ├── trip_distance_hist.png
│   ├── trip_duration_hist.png
│   ├── trips_by_hour.png
│   ├── cost_per_mile_hist.png
│   ├── total_fare_hist.png
│   ├── revenue_by_hour.png
│   ├── avg_metrics_by_hour.png
│   ├── distance_vs_fare_scatter.png
│   ├── payment_type_distribution.png
│   └── tip_amount_hist.png
├── metrics/
│   └── metrics.json
└── raw/
    └── manifest.json
```

---

## Customization

### Custom Docker Image

If you need additional dependencies, create a custom Docker image:

```dockerfile
FROM quay.io/elyra/elyra:3.15.0-py3.10

# Install additional packages
RUN pip install --no-cache-dir \
    scikit-learn==1.3.0 \
    xgboost==2.0.0

# Copy notebooks
COPY *.ipynb /workspace/
```

Build and push:
```bash
docker build -t your-registry/nyc-taxi-pipeline:latest .
docker push your-registry/nyc-taxi-pipeline:latest
```

Update `runtime_image` in pipeline to use your custom image.

### Scheduling

**Kubeflow Recurring Runs**:
1. In Kubeflow UI, go to "Runs"
2. Click "Create recurring run"
3. Set schedule (cron format)
4. Configure parameters

**Elyra with Airflow**:
- Configure Airflow DAG scheduling
- Set cron expression for periodic execution

---

## License

MIT License - See project root for details.

## Support

For issues or questions:
- Open an issue in the project repository
- Check Elyra documentation: https://elyra.readthedocs.io/
- Check Kubeflow documentation: https://www.kubeflow.org/docs/
