from app.services.vision_app.models import WorkspaceDefinition


def test_workspace_model_defaults_are_independent():
    a = WorkspaceDefinition(workspace_id="a", name="A", alias="a", camera_id="", input_binding="")
    b = WorkspaceDefinition(workspace_id="b", name="B", alias="b", camera_id="", input_binding="")
    a.master.rois.append({
        "roi_id": "r1",
        "name": "R1",
        "alias": "R1",
        "rect": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
        "enabled": True,
    })
    a.working.global_scope.filter_services.append({
        "binding_id": "b1",
        "service_id": "svc",
        "enabled": True,
        "label": "",
        "alias": "",
    })
    assert b.master.rois == []
    assert b.working.global_scope.filter_services == []
