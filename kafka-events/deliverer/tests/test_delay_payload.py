import pytest

from deliverer import DelayPayload, OutboundPayload


@pytest.fixture
def outbound():
    yield OutboundPayload(
        headers={"Key": "Value"},
        endpoint="https://example.com",
        payload="eyJwcm90ZWN0ZWQiOiAiZXlKbGJtTWlPaUFpZUdOb1lXTm9ZVEl3Y0c5c2VURXpNRFZmYVdWMFppSXNJQ0owZVhBaU9pQWlTbGROTHpFdU1DSXNJQ0poYkdjaU9pQWlRWFYwYUdOeWVYQjBJaXdnSW5KbFkybHdhV1Z1ZEhNaU9pQmJleUpsYm1OeWVYQjBaV1JmYTJWNUlqb2dJakZqWjNsMFFtMTNNM0V4YUdkaVZ6Qkpiak50U0c4MldXaExUMnRwUnpWRWVUaHJSakpJV2pZeGNUSnZXV00zYm10dVN6bE9TVWMyU0VobFUyTm9lV0VpTENBaWFHVmhaR1Z5SWpvZ2V5SnJhV1FpT2lBaU5FUkNTalJhY0RnMU1XZHFlazUwU20xdGIwVTVOMWR4Vm5KWFRqTTJlVnBTWVVkcFpqUkJSM0o0ZDFFaUxDQWljMlZ1WkdWeUlqb2dJak5XY0hsU2NVRlpUV3N5Tms1RmMwUXpObU5mWjJnMFZIazBaamd3TUd4RFJHRXdNMWxsUlc1bVJYQm1WMmhKTFdkelpFY3RWR1JrTVdWTmFEbFpTWG8zTkhSRlN6SnNSMVZhVFhwZk5HdDFkMEpUVWtvMFRGOWhkMVJLUVZWVmQydFRWbmhyTXpSblVWVmZOV2RyZDFSa09FWTFUa0ZsU1U1UVZTSXNJQ0pwZGlJNklDSnFWVkpDUW1OaVQzZzNOa05zVmw4eGF6aFJNMjlyVW5KdFJHUTFhM0JwUWlKOWZWMTkiLCAiaXYiOiAiTVdnR3VRNF9ab2dxVVJUbiIsICJjaXBoZXJ0ZXh0IjogIlVNTGFQOU13ZF9wOFR1bWdwcVZWQWZTSWZXc1g3a0lWLUR4RndfVHRTQ2pWdTVTbG5RYmtkTVJLd3VyZGI1dmd6Q0tUNUFybFV0WEFMMm1sSUlpUGpSYzVmSzhLc013S0dFemkycEtrdmxDN1EzUXRKWTE5WmVTSjlYMGlUOWxOamNEM25KS0o1bzlkSjhVWGZpNU80ZEtaLWxlVy1qOHlzTEFTSTh1eEZYVVNoUmxlNy03bm5HZkZnRlZBRjNaWVpqNlRXUUJrdkdSUk96TzMwTHNEWHBzalNqMWZfd056RWdxTmpPMERZemRKa0lBNm1BQ1AiLCAidGFnIjogImVBZVFiakktVmpkN21hcWdTNElGTlEifQ==",
    )


def test_delay_from_outbound(outbound: OutboundPayload):
    delay = DelayPayload(topic="acapy-outbound-message", outbound=outbound)
    assert delay.outbound == outbound


def test_delay_to_queue(outbound: OutboundPayload):
    delay = DelayPayload(topic="acapy-outbound-message", outbound=outbound)
    assert delay.to_bytes()
    assert delay == DelayPayload.from_bytes(delay.to_bytes())
