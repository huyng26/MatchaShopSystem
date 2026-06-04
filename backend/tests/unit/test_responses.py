from app.core.responses import paginated_response, success_response


def test_success_response_shape() -> None:
    response = success_response(data={"id": "abc"}, message="Created")

    assert response == {
        "success": True,
        "message": "Created",
        "data": {"id": "abc"},
    }


def test_paginated_response_shape() -> None:
    response = paginated_response(
        items=[{"id": 1}, {"id": 2}],
        total=5,
        page=2,
        page_size=2,
    )

    assert response["success"] is True
    assert response["data"] == {
        "items": [{"id": 1}, {"id": 2}],
        "page": 2,
        "page_size": 2,
        "total": 5,
        "total_pages": 3,
    }
