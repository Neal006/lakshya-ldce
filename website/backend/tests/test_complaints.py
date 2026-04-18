import pytest
from app.models.models import CategoryEnum, PriorityEnum, StatusEnum, SubmittedViaEnum


@pytest.fixture
def admin_token(client, register_user):
    resp = register_user(email="admin@test.com", role="admin")
    return resp.json()["data"]["access_token"]


@pytest.fixture
def call_attender_token(client, register_user):
    resp = register_user(email="attender@test.com", role="call_attender")
    return resp.json()["data"]["access_token"]


@pytest.fixture
def qa_token(client, register_user):
    resp = register_user(email="qa@test.com", role="qa")
    return resp.json()["data"]["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def attender_headers(call_attender_token):
    return {"Authorization": f"Bearer {call_attender_token}"}

@pytest.fixture
def qa_headers(qa_token):
    return {"Authorization": f"Bearer {qa_token}"}


@pytest.fixture
def create_complaint(client, admin_headers):
    def _create(raw_text="Product stopped working after 2 days", submitted_via="call", **kwargs):
        data = {
            "customer_email": kwargs.get("customer_email", f"cust{pytest.id_tracker}@example.com"),
            "customer_name": kwargs.get("customer_name", "Jane Smith"),
            "customer_phone": kwargs.get("customer_phone", "+91-9876543210"),
            "raw_text": raw_text,
            "submitted_via": submitted_via,
        }
        resp = client.post("/complaints", json=data, headers=admin_headers)
        return resp
    return _create

pytest.id_tracker = 0


class TestCreateComplaintHappyPath:
    def test_create_returns_201(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "jane@example.com",
            "customer_name": "Jane Smith",
            "customer_phone": "+91-9876543210",
            "raw_text": "Product stopped working after 2 days",
            "submitted_via": "call",
        }, headers=admin_headers)
        assert resp.status_code == 201

    def test_create_response_has_data_complaint(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "jane2@example.com",
            "customer_name": "Jane Smith",
            "raw_text": "Packaging was broken on arrival",
            "submitted_via": "email",
        }, headers=admin_headers)
        body = resp.json()
        assert "data" in body
        assert "complaint" in body["data"]

    def test_create_complaint_has_id(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "jane3@example.com",
            "customer_name": "Jane Smith",
            "raw_text": "Trade order not delivered on time",
            "submitted_via": "dashboard",
        }, headers=admin_headers)
        complaint = resp.json()["data"]["complaint"]
        assert "id" in complaint
        assert len(complaint["id"]) > 0

    def test_create_complaint_has_customer(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "jane4@example.com",
            "customer_name": "Jane Four",
            "customer_phone": "+91-1111111111",
            "raw_text": "Product defective",
            "submitted_via": "call",
        }, headers=admin_headers)
        customer = resp.json()["data"]["complaint"]["customer"]
        assert customer["name"] == "Jane Four"
        assert customer["email"] == "jane4@example.com"

    def test_create_complaint_auto_classifies(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "classify@example.com",
            "customer_name": "Classifier",
            "raw_text": "Product stopped working after 2 days",
            "submitted_via": "call",
        }, headers=admin_headers)
        complaint = resp.json()["data"]["complaint"]
        assert "category" in complaint
        assert "priority" in complaint
        assert "sentiment_score" in complaint

    def test_create_complaint_has_resolution_steps(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "steps@example.com",
            "customer_name": "Steps User",
            "raw_text": "Product not working properly",
            "submitted_via": "call",
        }, headers=admin_headers)
        complaint = resp.json()["data"]["complaint"]
        assert "resolution_steps" in complaint
        assert isinstance(complaint["resolution_steps"], list)
        assert len(complaint["resolution_steps"]) > 0

    def test_create_complaint_status_is_open(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "openstatus@example.com",
            "customer_name": "Open User",
            "raw_text": "Something is wrong with packaging",
            "submitted_via": "call",
        }, headers=admin_headers)
        assert resp.json()["data"]["complaint"]["status"] == "open"

    def test_create_complaint_has_sla_deadline(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "sla@example.com",
            "customer_name": "SLA User",
            "raw_text": "Trade order delay",
            "submitted_via": "call",
        }, headers=admin_headers)
        complaint = resp.json()["data"]["complaint"]
        assert "sla_deadline" in complaint
        assert complaint["sla_deadline"] is not None

    def test_create_complaint_creates_timeline_entry(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "timeline@example.com",
            "customer_name": "Timeline User",
            "raw_text": "Need at least five chars here",
            "submitted_via": "call",
        }, headers=admin_headers)
        complaint = resp.json()["data"]["complaint"]
        cid = complaint["id"]
        detail = client.get(f"/complaints/{cid}", headers=admin_headers)
        timeline = detail.json()["data"]["complaint"]["timeline"]
        assert len(timeline) > 0
        assert timeline[0]["action"] == "complaint_created"

    def test_create_complaint_reuses_existing_customer(self, client, admin_headers):
        client.post("/complaints", json={
            "customer_email": "reuse@example.com",
            "customer_name": "Reuse Customer",
            "raw_text": "First complaint text here ok",
            "submitted_via": "call",
        }, headers=admin_headers)
        resp2 = client.post("/complaints", json={
            "customer_email": "reuse@example.com",
            "customer_name": "Reuse Customer",
            "raw_text": "Second complaint text here ok",
            "submitted_via": "email",
        }, headers=admin_headers)
        assert resp2.status_code == 201

    def test_call_attender_can_create(self, client, attender_headers):
        resp = client.post("/complaints", json={
            "customer_email": "attender@example.com",
            "customer_name": "Attender Test",
            "raw_text": "Call attender created this",
            "submitted_via": "call",
        }, headers=attender_headers)
        assert resp.status_code == 201


class TestCreateComplaintFailureModes:
    def test_qa_cannot_create(self, client, qa_headers):
        resp = client.post("/complaints", json={
            "customer_email": "qa@example.com",
            "customer_name": "QA User",
            "raw_text": "QA cannot create complaints",
            "submitted_via": "dashboard",
        }, headers=qa_headers)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create(self, client):
        resp = client.post("/complaints", json={
            "customer_email": "noauth@example.com",
            "customer_name": "No Auth",
            "raw_text": "Should not work at all",
            "submitted_via": "dashboard",
        })
        assert resp.status_code == 403

    def test_short_raw_text_returns_422(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "short@example.com",
            "customer_name": "Short Text",
            "raw_text": "hi",
            "submitted_via": "call",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_name": "No Email",
            "raw_text": "This is a complaint text",
            "submitted_via": "call",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "noname@example.com",
            "raw_text": "This is a complaint text",
            "submitted_via": "call",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_invalid_submitted_via_returns_422(self, client, admin_headers):
        resp = client.post("/complaints", json={
            "customer_email": "badvia@example.com",
            "customer_name": "Bad Via",
            "raw_text": "This is a complaint text",
            "submitted_via": "fax",
        }, headers=admin_headers)
        assert resp.status_code == 422


class TestListComplaints:
    def _create_complaint(self, client, admin_headers, idx, status_val=None, category=None, priority=None):
        data = {
            "customer_email": f"list{idx}@example.com",
            "customer_name": f"Customer {idx}",
            "raw_text": f"Complaint number {idx} about product issues",
            "submitted_via": "call",
        }
        resp = client.post("/complaints", json=data, headers=admin_headers)
        cid = resp.json()["data"]["complaint"]["id"]
        if status_val and status_val != "open":
            client.patch(f"/complaints/{cid}/status", json={"status": status_val, "notes": "Status change"}, headers=admin_headers)
        return cid

    def test_list_returns_200(self, client, admin_headers):
        self._create_complaint(client, admin_headers, 100)
        resp = client.get("/complaints", headers=admin_headers)
        assert resp.status_code == 200

    def test_list_has_pagination(self, client, admin_headers):
        self._create_complaint(client, admin_headers, 101)
        resp = client.get("/complaints", headers=admin_headers)
        body = resp.json()["data"]
        assert "complaints" in body
        assert "pagination" in body
        assert "page" in body["pagination"]
        assert "limit" in body["pagination"]
        assert "total" in body["pagination"]

    def test_list_filter_by_status(self, client, admin_headers):
        self._create_complaint(client, admin_headers, 102)
        resp = client.get("/complaints?status=open", headers=admin_headers)
        assert resp.status_code == 200
        complaints = resp.json()["data"]["complaints"]
        for c in complaints:
            assert c["status"] == "open"

    def test_list_filter_by_category(self, client, admin_headers):
        self._create_complaint(client, admin_headers, 103)
        resp = client.get("/complaints?category=Product", headers=admin_headers)
        assert resp.status_code == 200

    def test_list_pagination_params(self, client, admin_headers):
        self._create_complaint(client, admin_headers, 104)
        resp = client.get("/complaints?page=1&limit=5", headers=admin_headers)
        assert resp.status_code == 200
        pagination = resp.json()["data"]["pagination"]
        assert pagination["limit"] == 5

    def test_qa_can_list_complaints(self, client, qa_headers, admin_headers):
        self._create_complaint(client, admin_headers, 105)
        resp = client.get("/complaints", headers=qa_headers)
        assert resp.status_code == 200

    def test_call_attender_list_hides_category_priority(self, client, attender_headers, admin_headers):
        self._create_complaint(client, admin_headers, 106)
        resp = client.get("/complaints", headers=attender_headers)
        assert resp.status_code == 200
        complaints = resp.json()["data"]["complaints"]
        if len(complaints) > 0:
            assert "category" not in complaints[0]
            assert "priority" not in complaints[0]
            assert "resolution_steps" in complaints[0]


class TestGetComplaint:
    def test_get_complaint_returns_200(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "get@example.com",
            "customer_name": "Get User",
            "raw_text": "Detail view complaint test",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.get(f"/complaints/{cid}", headers=admin_headers)
        assert resp.status_code == 200

    def test_get_complaint_has_all_fields(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "fields@example.com",
            "customer_name": "Fields User",
            "customer_phone": "+91-9999999999",
            "raw_text": "Fields complaint test data",
            "submitted_via": "email",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.get(f"/complaints/{cid}", headers=admin_headers)
        complaint = resp.json()["data"]["complaint"]
        for field in ["id", "customer", "raw_text", "category", "priority", "resolution_steps",
                      "sentiment_score", "status", "submitted_via", "sla_deadline", "sla_breached",
                      "created_at", "timeline"]:
            assert field in complaint, f"Missing field: {field}"

    def test_get_complaint_has_timeline(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "tl@example.com",
            "customer_name": "Timeline",
            "raw_text": "Timeline test complaint here",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.get(f"/complaints/{cid}", headers=admin_headers)
        timeline = resp.json()["data"]["complaint"]["timeline"]
        assert isinstance(timeline, list)
        assert any(t["action"] == "complaint_created" for t in timeline)

    def test_get_nonexistent_complaint_returns_404(self, client, admin_headers):
        resp = client.get("/complaints/00000000-0000-0000-0000-000000000000", headers=admin_headers)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


class TestUpdateComplaintStatus:
    def test_open_to_in_progress(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "status1@example.com",
            "customer_name": "Status One",
            "raw_text": "Status transition test",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.patch(f"/complaints/{cid}/status", json={"status": "in_progress", "notes": "Working on it"}, headers=admin_headers)
        assert resp.status_code == 200

    def test_open_to_resolved(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "status2@example.com",
            "customer_name": "Status Two",
            "raw_text": "Direct resolve test",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.patch(f"/complaints/{cid}/status", json={"status": "resolved", "notes": "Resolved directly"}, headers=admin_headers)
        assert resp.status_code == 200

    def test_resolved_cannot_transition(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "status3@example.com",
            "customer_name": "Status Three",
            "raw_text": "Resolve then try to reopen",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]

        client.patch(f"/complaints/{cid}/status", json={"status": "resolved", "notes": "Done"}, headers=admin_headers)
        resp = client.patch(f"/complaints/{cid}/status", json={"status": "in_progress", "notes": "Try reopen"}, headers=admin_headers)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    def test_status_change_creates_timeline(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "timeline2@example.com",
            "customer_name": "Timeline Two",
            "raw_text": "Timeline after status change",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        client.patch(f"/complaints/{cid}/status", json={"status": "in_progress", "notes": "Started working"}, headers=admin_headers)
        detail = client.get(f"/complaints/{cid}", headers=admin_headers)
        timeline = detail.json()["data"]["complaint"]["timeline"]
        assert any(t["action"] == "status_changed" for t in timeline)

    def test_resolved_sets_resolved_at(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "resolvedat@example.com",
            "customer_name": "Resolved At",
            "raw_text": "Check resolved_at timestamp",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        client.patch(f"/complaints/{cid}/status", json={"status": "resolved", "notes": "Done"}, headers=admin_headers)
        detail = client.get(f"/complaints/{cid}", headers=admin_headers)
        complaint = detail.json()["data"]["complaint"]
        assert complaint["resolved_at"] is not None

    def test_qa_cannot_update_status(self, client, qa_headers, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "qaupdate@example.com",
            "customer_name": "QA Update Test",
            "raw_text": "QA should not be able to update",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.patch(f"/complaints/{cid}/status", json={"status": "in_progress"}, headers=qa_headers)
        assert resp.status_code == 403


class TestEscalateComplaint:
    def test_escalate_returns_200(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "esc1@example.com",
            "customer_name": "Escalate One",
            "raw_text": "Need to escalate this complaint",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.post(f"/complaints/{cid}/escalate", json={"reason": "Customer demanding supervisor"}, headers=admin_headers)
        assert resp.status_code == 200

    def test_escalate_sets_status_and_reason(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "esc2@example.com",
            "customer_name": "Escalate Two",
            "raw_text": "Another escalation test",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.post(f"/complaints/{cid}/escalate", json={"reason": "Customer is very upset"}, headers=admin_headers)
        data = resp.json()["data"]["complaint"]
        assert data["status"] == "escalated"
        assert data["escalation_reason"] == "Customer is very upset"
        assert data["escalated_at"] is not None

    def test_cannot_escalate_resolved(self, client, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "escres@example.com",
            "customer_name": "Esc Resolve",
            "raw_text": "Resolved complaint escalation",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        client.patch(f"/complaints/{cid}/status", json={"status": "resolved"}, headers=admin_headers)
        resp = client.post(f"/complaints/{cid}/escalate", json={"reason": "Try escalate resolved"}, headers=admin_headers)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    def test_escalate_nonexistent_complaint_404(self, client, admin_headers):
        resp = client.post("/complaints/00000000-0000-0000-0000-000000000000/escalate", json={"reason": "No such complaint"}, headers=admin_headers)
        assert resp.status_code == 404

    def test_qa_cannot_escalate(self, client, qa_headers, admin_headers):
        create_resp = client.post("/complaints", json={
            "customer_email": "qaesc@example.com",
            "customer_name": "QA Escalate",
            "raw_text": "QA should not escalate",
            "submitted_via": "call",
        }, headers=admin_headers)
        cid = create_resp.json()["data"]["complaint"]["id"]
        resp = client.post(f"/complaints/{cid}/escalate", json={"reason": "QA trying"}, headers=qa_headers)
        assert resp.status_code == 403