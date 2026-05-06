http://localhost:8082/api/v1/users/me/social-level
{
    "success": false,
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "获取社交暴露级别失败",
        "details": null
    },
    "meta": {
        "timestamp": "2026-05-06T09:08:31.009194+00:00",
        "requestId": "298f0294-5233-4eee-b417-86a89e530995"
    }
}


http://localhost:8082/api/v1/users/me/profile-tags
{
    "success": false,
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "获取AI画像标签失败",
        "details": null
    },
    "meta": {
        "timestamp": "2026-05-06T09:08:31.127597+00:00",
        "requestId": "47eb63bd-e373-44e3-a635-055f4094509d"
    }
}

http://localhost:8082/api/v1/friend-requests
{
    "success": false,
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "获取好友申请列表失败",
        "details": null
    },
    "meta": {
        "timestamp": "2026-05-06T09:10:50.381417+00:00",
        "requestId": "675ab25c-0c73-4ca9-8687-0d8863a026d3"
    }
}

http://localhost:8082/api/v1/posts?page=1&page_size=20&sort_by=latest
{
    "success": false,
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "获取动态列表失败",
        "details": null
    },
    "meta": {
        "timestamp": "2026-05-06T09:10:46.117182+00:00",
        "requestId": "6d24cb9b-64d5-4c9c-943c-5164560188dc"
    }
}