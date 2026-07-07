from rate_agent.tempo_client import _extract_json_from_output, _is_wallet_ready, _redact_tempo_output


def test_extract_json_from_tempo_output_with_continue_line() -> None:
    output = (
        "Continue at: https://wallet.tempo.xyz/api/auth/cli?code=SECRET\n"
        '{"success":true,"data":[{"name":"Hà Nội","lat":21.0283334,"lon":105.854041}]}'
    )

    parsed = _extract_json_from_output(output)

    assert parsed["success"] is True
    assert parsed["data"][0]["name"] == "Hà Nội"


def test_extract_json_from_tempo_output_with_installer_lines_before_object() -> None:
    output = (
        "installing tempo-wallet ...\n"
        "installed tempo-wallet\n"
        '{\n  "ready": true,\n  "wallet": "0x8ef9"\n}\n'
    )

    parsed = _extract_json_from_output(output)

    assert parsed["ready"] is True


def test_redact_tempo_output_removes_cli_auth_code() -> None:
    output = "Continue at: https://wallet.tempo.xyz/api/auth/cli?code=SECRET"

    redacted = _redact_tempo_output(output)

    assert "SECRET" not in redacted
    assert "code=<redacted>" in redacted


def test_is_wallet_ready_accepts_json_format_output() -> None:
    output = '{"ready": true, "wallet": "0x8ef9"}'

    assert _is_wallet_ready(output) is True


def test_is_wallet_ready_accepts_yaml_like_output() -> None:
    output = "ready: true\nwallet: 0x8ef9"

    assert _is_wallet_ready(output) is True


def test_is_wallet_ready_rejects_not_ready_json_output() -> None:
    output = '{"ready": false, "wallet": "0x8ef9"}'

    assert _is_wallet_ready(output) is False
