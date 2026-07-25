"""
tests/unit/test_ssrf_guard.py

Unit tests for SSRF Target Guard (src/utils/ssrf_guard.py)
"""
from src.utils.ssrf_guard import validate_target_url


def test_ssrf_blocks_empty_or_non_http_urls():
    valid, err = validate_target_url("")
    assert not valid
    assert "non-empty string" in err

    valid, err = validate_target_url("ftp://example.com")
    assert not valid
    assert "start with http://" in err


def test_ssrf_blocks_cloud_metadata_ips():
    # AWS/GCP Metadata IP must ALWAYS be blocked
    valid, err = validate_target_url("http://169.254.169.254/latest/meta-data")
    assert not valid
    assert "reserved Cloud Metadata endpoint" in err


def test_ssrf_permits_valid_public_urls():
    valid, err = validate_target_url("https://example.com/ai-chat")
    assert valid
    assert err is None


def test_ssrf_localhost_allowed_in_dev_mode(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", "true")

    valid, err = validate_target_url("http://localhost:8000")
    assert valid
    assert err is None

    valid_ip, err_ip = validate_target_url("http://127.0.0.1:3000")
    assert valid_ip
    assert err_ip is None


def test_ssrf_localhost_blocked_in_production_mode(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", "false")

    valid, err = validate_target_url("http://127.0.0.1:8000")
    assert not valid
    assert "restricted in production" in err
