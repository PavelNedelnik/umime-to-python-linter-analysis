"""Configuration."""

import os
from pathlib import Path

import yaml


def deep_update(base, overrides):
    """Update config with overrides."""
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config():
    """Load configuration from YAML files."""
    CONFIG_ENV = os.getenv("CONFIG_ENV", "debug")

    # Load base config
    with open("config/base.yaml") as f:
        cfg = yaml.safe_load(f)

    # Load environment-specific overrides
    env_path = f"config/{CONFIG_ENV}.yaml"
    if Path(env_path).exists():
        env_cfg = yaml.safe_load(open(env_path))
        deep_update(cfg, env_cfg)

    # ---- Dynamic logic ----
    debug = cfg["debug"]
    code = cfg["unique_code"]

    # Storage
    storage = Path(cfg["paths"]["storage_root"]) / code
    images = Path(cfg["paths"]["images_root"]) / code
    survey_data = Path(cfg["paths"]["survey_data"]) / code

    # Raw data sources
    raw_submissions = Path(cfg["paths"]["raw_submission_log"])
    raw_defect_table = Path(cfg["paths"]["raw_defect_table"])
    raw_survey_dir = Path(cfg["paths"]["raw_survey_responses"])
    raw_survey_feedback = raw_survey_dir / "feedback.csv"
    raw_survey_responses = raw_survey_dir / "responses.csv"

    # Data partitions
    train_set = storage / "train_set"
    evaluation_set = storage / "evaluation_set"
    teacher_hold_out_set = storage / "teacher_hold_out_set"
    student_hold_out_set = storage / "student_hold_out_set"

    # Cached results
    # models are stored here, because they are trained on both the train and evaluation sets
    evaluation_trained_heuristics = evaluation_set / "trained_heuristics"
    evaluation_prioritizations = evaluation_set / "evaluation_prioritizations"
    hold_out_trained_heuristics = teacher_hold_out_set / "trained_heuristics"
    model_metrics = evaluation_set / "model_metrics"
    teacher_hold_out_prioritizations = teacher_hold_out_set / "teacher_hold_out_prioritizations"

    # Benchmark dataset
    benchmark_dataset = teacher_hold_out_set / "benchmark_dataset"

    return {
        "DEBUG": debug,
        "NOTE": cfg["note"],
        "UNIQUE_CODE": code,
        "PATHS": {
            # Storage
            "storage": storage,
            "images": images,
            "survey_data": survey_data,
            # Raw data
            "raw_submissions": raw_submissions,
            "raw_defect_table": raw_defect_table,
            "raw_survey_feedback": raw_survey_feedback,
            "raw_survey_responses": raw_survey_responses,
            # Data partitions
            "train_set": train_set,
            "evaluation_set": evaluation_set,
            "teacher_hold_out_set": teacher_hold_out_set,
            "student_hold_out_set": student_hold_out_set,
            # Cached results
            "evaluation_trained_heuristics": evaluation_trained_heuristics,
            "hold_out_trained_heuristics": hold_out_trained_heuristics,
            "evaluation_prioritizations": evaluation_prioritizations,
            "teacher_hold_out_prioritizations": teacher_hold_out_prioritizations,
            "model_metrics": model_metrics,
            # Benchmark
            "benchmark_dataset": benchmark_dataset,
        },
        "DEFAULTS": cfg["defaults"],
        "LOADING_FLAGS": cfg["loading_flags"],
    }


config = load_config()
