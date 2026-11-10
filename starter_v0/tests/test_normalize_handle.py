from unittest.mock import patch

from tools.normalize_handle.tool import normalize_handle
from tools.timeline.tool import get_user_tweets


def test_normalize_handle_removes_at_and_spaces():
    assert normalize_handle("  @sama  ")["screenname"] == "sama"


def test_normalize_handle_rejects_non_string():
    assert normalize_handle(None)["error"] == "TypeError"


def test_timeline_uses_normalized_handle():
    with patch("tools.timeline.tool._twitter_get", return_value={"timeline": []}) as get:
        result = get_user_tweets("  @sama ")
    get.assert_called_once_with("/timeline.php", {"screenname": "sama"})
    assert result["screenname"] == "sama"
