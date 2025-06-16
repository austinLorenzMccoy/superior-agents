#!/usr/bin/env python3
"""
GigNova: Tests for data models
"""

import pytest
from pydantic import ValidationError

from gignova.models.base import JobPost, FreelancerProfile, JobMatch, QAResult


def test_job_post_valid():
    """Test valid job post creation"""
    job = JobPost(
        title="Test Job",
        description="This is a test job",
        skills=["python", "fastapi"],
        budget_min=500.0,
        budget_max=1000.0,
        deadline_days=14,
        client_id="client123"
    )
    
    assert job.title == "Test Job"
    assert job.budget_min == 500.0
    assert len(job.skills) == 2


def test_job_post_invalid_budget():
    """Test job post with invalid budget range"""
    with pytest.raises(ValidationError):
        JobPost(
            title="Test Job",
            description="This is a test job",
            skills=["python", "fastapi"],
            budget_min=1000.0,
            budget_max=500.0,  # Max less than min
            deadline_days=14,
            client_id="client123"
        )


def test_freelancer_profile_valid():
    """Test valid freelancer profile creation"""
    profile = FreelancerProfile(
        freelancer_id="freelancer123",
        name="Test Freelancer",
        bio="Experienced developer",
        skills=["python", "javascript"],
        hourly_rate=50.0,
        availability="full-time"
    )
    
    assert profile.name == "Test Freelancer"
    assert profile.hourly_rate == 50.0
    assert len(profile.skills) == 2


def test_job_match_valid():
    """Test valid job match creation"""
    match = JobMatch(
        job_id="job123",
        freelancer_id="freelancer123",
        confidence_score=0.85,
        match_reasons=["Skill match", "Budget match"]
    )
    
    assert match.job_id == "job123"
    assert match.confidence_score == 0.85
    assert len(match.match_reasons) == 2


def test_qa_result_valid():
    """Test valid QA result creation"""
    result = QAResult(
        job_id="job123",
        deliverable_hash="abc123",
        similarity_score=0.92,
        passed=True,
        feedback="Excellent work"
    )
    
    assert result.job_id == "job123"
    assert result.similarity_score == 0.92
    assert result.passed is True
