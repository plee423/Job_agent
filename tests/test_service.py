from service import TwoAgentService


def test_service_status_defaults():
    service = TwoAgentService()
    status = service.status()
    assert status["status"] == "stopped"
    assert status["queue_depth"] == 0
