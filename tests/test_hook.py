"""Mock API : teste le Hook sans lancer le réseau ni le serveur source."""
from unittest.mock import MagicMock, patch
import pytest

def test_hook_uses_bearer_token_without_hardcoding():
    pytest.importorskip('airflow')
    from marketplace_hook import MarketplaceAPIHook
    connection = MagicMock()
    connection.host = 'http://api-marketplace:5000'
    connection.password = 'token-from-connection'
    connection.schema = None
    connection.port = None
    response = MagicMock()
    response.json.return_value = [{'id':1}]
    with patch.object(MarketplaceAPIHook,'get_connection',return_value=connection),\
         patch('marketplace_hook.Session') as Session:
        session = Session.return_value
        session.get.return_value = response
        assert MarketplaceAPIHook().get_sellers() == [{'id':1}]
        assert session.headers.update.call_args.args[0]['Authorization'] == 'Bearer token-from-connection'
        session.get.assert_called_once()
